from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from src.graph.nodes.simple import simple_mode
from src.graph.pro_mode.aggregator import aggregator
from src.graph.pro_mode.decomposer import decomposer
from src.graph.pro_mode.facts_retriever import retrieve_facts
from src.graph.router.router import llm_call_router
from src.graph.states.state import State
from src.graph.validator.validator import define_validating_agent, validator_answer
from src.utils.token_tracker import add_tokens_to_statistics, extract_tokens_from_response

logger = logging.getLogger(__name__)

TaskStatus = Literal["pending", "running", "succeeded", "failed"]


@dataclass
class TaskDetails:
    mode: Optional[Literal["pro", "simple"]] = None
    thoughts: str = ""
    thoughts_data: Dict[str, Any] = field(default_factory=lambda: {"attempts": [], "current_attempt": 0})
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    validation_count: int = 0
    timing: Dict[str, float] = field(default_factory=dict)
    total_time: float = 0.0

    def append_thought(self, message: str) -> None:
        self.thoughts = f"{self.thoughts}\n{message}" if self.thoughts else message

    def add_step(
        self,
        attempt_number: int,
        step_type: str,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a structured step to thoughts_data"""
        if attempt_number > len(self.thoughts_data["attempts"]):
            self.thoughts_data["attempts"].append(
                {
                    "number": attempt_number,
                    "status": "in_progress",
                    "steps": [],
                }
            )
            self.thoughts_data["current_attempt"] = attempt_number

        if not self.thoughts_data["attempts"]:
            return

        current_attempt = self.thoughts_data["attempts"][-1]
        step = {
            "type": step_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if data:
            step["data"] = data
        current_attempt["steps"].append(step)

    def update_attempt_status(self, attempt_number: int, status: str) -> None:
        """Update attempt status: in_progress, completed, failed"""
        if attempt_number <= len(self.thoughts_data["attempts"]):
            self.thoughts_data["attempts"][attempt_number - 1]["status"] = status


@dataclass
class TaskRecord:
    task_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    details: Optional[TaskDetails] = None
    result: Optional[str] = None
    error: Optional[str] = None

    def to_response_payload(self) -> Dict[str, Any]:
        details_dict = None
        if self.details is not None and self.details.mode is not None:
            details_dict = {
                "mode": self.details.mode,
                "thoughts": self.details.thoughts,
                "thoughts_data": self.details.thoughts_data,
                "statistics": {
                    "total_tokens": self.details.total_tokens,
                    "prompt_tokens": self.details.prompt_tokens,
                    "completion_tokens": self.details.completion_tokens,
                    "validation_count": self.details.validation_count,
                    "timing": self.details.timing,
                    "total_time": self.details.total_time,
                } if self.details.total_tokens > 0 or self.details.total_time > 0 else None,
            }
        
        return {
            "task_id": self.task_id,
            "status": self.status,
            "details": details_dict,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
        }


class TaskManager:
    def __init__(self, max_validation_attempts: int = 3) -> None:
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock = asyncio.Lock()
        self._max_validation_attempts = max_validation_attempts

    async def create_task(
        self,
        query: str,
        forced_mode: Literal["pro", "simple"] | None = None,
    ) -> str:
        task_id = uuid4().hex
        now = datetime.now(timezone.utc)
        record = TaskRecord(
            task_id=task_id,
            status="pending",
            created_at=now,
            updated_at=now,
        )

        async with self._lock:
            self._tasks[task_id] = record

        query_preview = query[:100] + ("..." if len(query) > 100 else "")
        mode_str = f" (forced: {forced_mode})" if forced_mode else ""
        logger.info(f"[TASK {task_id[:8]}] Created task for query: {query_preview}{mode_str}")
        asyncio.create_task(self._process_task(task_id, query, forced_mode))
        return task_id

    async def get_task_payload(self, task_id: str) -> Dict[str, Any]:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(task_id)
            return task.to_response_payload()

    async def _process_task(
        self,
        task_id: str,
        query: str,
        forced_mode: Literal["pro", "simple"] | None,
    ) -> None:
        query_preview = query[:100] + ("..." if len(query) > 100 else "")
        logger.info(f"[TASK {task_id[:8]}] Starting task processing for query: {query_preview}")
        
        task_start_time = time.time()
        
        await self._update_task(task_id, status="running")
        state: State = {
            "input": query,
            "decision": "",
            "output": "",
            "validation_attempts": 0,
            "validation_result": "",
        }

        try:
            success, output = await self._execute_pipeline(task_id, state, forced_mode)
            
            total_time = time.time() - task_start_time
            async with self._lock:
                task = self._tasks[task_id]
                if task.details:
                    task.details.total_time = round(total_time, 2)
                    task.details.timing["total"] = round(total_time, 2)
                    
                    logger.info(
                        f"[TASK {task_id[:8]}] ═══ STATISTICS ═══\n"
                        f"  Total time: {task.details.total_time:.2f}s\n"
                        f"  Total tokens: {task.details.total_tokens} "
                        f"(prompt: {task.details.prompt_tokens}, completion: {task.details.completion_tokens})\n"
                        f"  Validation attempts: {task.details.validation_count}\n"
                        f"  Timing breakdown: {task.details.timing}"
                    )
            
            logger.info(f"[TASK {task_id[:8]}] Total execution time: {total_time:.2f}s")
            
        except Exception as exc:  # pylint: disable=broad-except
            total_time = time.time() - task_start_time
            logger.error(f"[TASK {task_id[:8]}] Task failed with error: {str(exc)} (time: {total_time:.2f}s)", exc_info=True)
            await self._update_task(
                task_id,
                status="failed",
                error=str(exc),
            )
        else:
            if success and output is not None:
                logger.info(f"[TASK {task_id[:8]}] Task completed successfully. Output length: {len(output)} chars")
                await self._update_task(task_id, status="succeeded", result=output)
            else:
                logger.warning(f"[TASK {task_id[:8]}] Task failed: Validation failed after maximum attempts")
                await self._update_task(
                    task_id,
                    status="failed",
                    error="Validation failed after maximum attempts.",
                )

    async def _execute_pipeline(
        self,
        task_id: str,
        state: State,
        forced_mode: Literal["pro", "simple"] | None,
    ) -> tuple[bool, Optional[str]]:
        validation_result: Optional[str] = None

        while state["validation_attempts"] < self._max_validation_attempts:
            attempt_number = state["validation_attempts"] + 1
            logger.info(f"[TASK {task_id[:8]}] Starting pipeline execution (attempt {attempt_number}/{self._max_validation_attempts})")
            
            if forced_mode is None:
                logger.info(f"[TASK {task_id[:8]}] Routing query to determine mode...")
                routing_start = time.time()
                decision_block = await llm_call_router(state)
                routing_time = time.time() - routing_start
                
                async with self._lock:
                    task = self._tasks[task_id]
                    if task.details:
                        tokens = extract_tokens_from_response(decision_block.get("_raw_response"))
                        add_tokens_to_statistics(
                            task.details,
                            tokens["prompt_tokens"],
                            tokens["completion_tokens"],
                            tokens["total_tokens"],
                        )
                        task.details.timing["routing"] = round(routing_time, 2)
                
                decision = decision_block["decision"]
                router_message = f"[Attempt {attempt_number}] Routed query to {decision.upper()} mode."
                logger.info(f"[TASK {task_id[:8]}] Router decision: {decision.upper()} mode (time: {routing_time:.2f}s)")
            else:
                decision = forced_mode
                router_message = f"[Attempt {attempt_number}] Forced mode set to {decision.upper()}."
                logger.info(f"[TASK {task_id[:8]}] Using forced mode: {decision.upper()}")
            state["decision"] = decision

            await self._set_mode(task_id, decision)
            await self._append_thought(task_id, router_message)
            await self._add_step(task_id, attempt_number, "mode", router_message)

            if decision == "pro":
                try:
                    logger.info(f"[TASK {task_id[:8]}] PRO MODE: Starting decomposition...")
                    decomp_start = time.time()
                    output_block = await decomposer(state)
                    decomp_time = time.time() - decomp_start
                    
                    async with self._lock:
                        task = self._tasks[task_id]
                        if task.details:
                            tokens = extract_tokens_from_response(output_block.get("_raw_response"))
                            add_tokens_to_statistics(
                                task.details,
                                tokens["prompt_tokens"],
                                tokens["completion_tokens"],
                                tokens["total_tokens"],
                            )
                            task.details.timing["decomposition"] = round(decomp_time, 2)
                    
                    state.update(output_block)
                    
                    if "decomposition_info" in output_block:
                        decomp_info = output_block["decomposition_info"]
                        subq_count = decomp_info['total_subquestions']
                        logger.info(f"[TASK {task_id[:8]}] PRO MODE: Decomposition completed. Subquestions: {subq_count}")
                        decomposition_text = f"[Attempt {attempt_number}] Декомпозиция вопроса:\n"
                        decomposition_text += f"Логика: {decomp_info['reasoning']}\n"
                        decomposition_text += f"Количество подвопросов: {decomp_info['total_subquestions']}\n"
                        decomposition_text += "Подвопросы:\n"
                        for i, subq in enumerate(decomp_info["subquestions"], 1):
                            decomposition_text += f"  {i}. {subq.text}\n"
                        await self._append_thought(task_id, decomposition_text)
                        
                        decomposition_data = {
                            "reasoning": decomp_info["reasoning"],
                            "total_subquestions": decomp_info["total_subquestions"],
                            "subquestions": [
                                {"number": i + 1, "text": subq.text}
                                for i, subq in enumerate(decomp_info["subquestions"])
                            ],
                        }
                        await self._add_step(
                            task_id,
                            attempt_number,
                            "decomposition",
                            "Декомпозиция вопроса",
                            decomposition_data,
                        )
                    else:
                        warning_msg = f"[Attempt {attempt_number}] WARNING: decomposition_info not found in output_block"
                        logger.warning(f"[TASK {task_id[:8]}] {warning_msg}")
                        await self._append_thought(task_id, warning_msg)
                        await self._add_step(task_id, attempt_number, "warning", warning_msg)
                    
                    progress_msg = f"[Attempt {attempt_number}] Retrieving facts for subquestions..."
                    logger.info(f"[TASK {task_id[:8]}] PRO MODE: Starting facts retrieval...")
                    await self._append_thought(task_id, progress_msg)
                    await self._add_step(task_id, attempt_number, "progress", progress_msg)
                    
                    facts_start = time.time()
                    facts_block = await retrieve_facts(state)
                    facts_time = time.time() - facts_start
                    
                    async with self._lock:
                        task = self._tasks[task_id]
                        if task.details:
                            raw_responses = facts_block.get("_raw_responses", [])
                            for raw_response in raw_responses:
                                tokens = extract_tokens_from_response(raw_response)
                                add_tokens_to_statistics(
                                    task.details,
                                    tokens["prompt_tokens"],
                                    tokens["completion_tokens"],
                                    tokens["total_tokens"],
                                )
                            task.details.timing["facts_retrieval"] = round(facts_time, 2)
                    
                    state.update(facts_block)
                    
                    facts_count = len(state.get("facts", []))
                    logger.info(f"[TASK {task_id[:8]}] PRO MODE: Facts retrieval completed. Facts sets: {facts_count} (time: {facts_time:.2f}s)")
                    facts_msg = f"[Attempt {attempt_number}] Facts retrieved: {facts_count} fact sets collected."
                    await self._append_thought(task_id, facts_msg)
                    await self._add_step(task_id, attempt_number, "progress", facts_msg)
                    
                    agg_msg = f"[Attempt {attempt_number}] Aggregating facts into final answer..."
                    logger.info(f"[TASK {task_id[:8]}] PRO MODE: Starting aggregation...")
                    await self._append_thought(task_id, agg_msg)
                    await self._add_step(task_id, attempt_number, "progress", agg_msg)
                    
                    agg_start = time.time()
                    aggregator_block = await aggregator(state)
                    agg_time = time.time() - agg_start
                    
                    async with self._lock:
                        task = self._tasks[task_id]
                        if task.details:
                            tokens = extract_tokens_from_response(aggregator_block.get("_raw_response"))
                            add_tokens_to_statistics(
                                task.details,
                                tokens["prompt_tokens"],
                                tokens["completion_tokens"],
                                tokens["total_tokens"],
                            )
                            task.details.timing["aggregation"] = round(agg_time, 2)
                    
                    state.update(aggregator_block)
                    
                    logger.info(f"[TASK {task_id[:8]}] PRO MODE: Aggregation completed")
                    success_msg = f"[Attempt {attempt_number}] Answer synthesized successfully."
                    await self._append_thought(task_id, success_msg)
                    await self._add_step(task_id, attempt_number, "completion", success_msg)
                    
                    if not state.get("output"):
                        warning_msg = f"[Attempt {attempt_number}] WARNING: state['output'] is empty after aggregation"
                        logger.warning(f"[TASK {task_id[:8]}] {warning_msg}")
                        await self._append_thought(task_id, warning_msg)
                        await self._add_step(task_id, attempt_number, "warning", warning_msg)
                    
                    final_msg = f"[Attempt {attempt_number}] Pro mode collected and synthesized information."
                    await self._append_thought(task_id, final_msg)
                    await self._add_step(task_id, attempt_number, "completion", final_msg)
                except Exception as e:
                    error_msg = f"[Attempt {attempt_number}] ERROR in pro mode: {str(e)}"
                    logger.error(f"[TASK {task_id[:8]}] {error_msg}", exc_info=True)
                    await self._append_thought(task_id, error_msg)
                    await self._add_step(task_id, attempt_number, "error", error_msg)
                    async with self._lock:
                        task = self._tasks[task_id]
                        if task.details:
                            task.details.update_attempt_status(attempt_number, "failed")
                    raise
            else:
                logger.info(f"[TASK {task_id[:8]}] SIMPLE MODE: Starting direct answer generation...")
                simple_start = time.time()
                output_block = await simple_mode(state)
                simple_time = time.time() - simple_start
                
                async with self._lock:
                    task = self._tasks[task_id]
                    if task.details:
                        tokens = extract_tokens_from_response(output_block.get("_raw_response"))
                        add_tokens_to_statistics(
                            task.details,
                            tokens["prompt_tokens"],
                            tokens["completion_tokens"],
                            tokens["total_tokens"],
                        )
                        task.details.timing["simple_mode"] = round(simple_time, 2)
                
                state.update(output_block)
                logger.info(f"[TASK {task_id[:8]}] SIMPLE MODE: Answer generated (time: {simple_time:.2f}s)")
                simple_msg = f"[Attempt {attempt_number}] Simple mode generated a direct answer."
                await self._append_thought(task_id, simple_msg)
                await self._add_step(task_id, attempt_number, "completion", simple_msg)

            logger.info(f"[TASK {task_id[:8]}] Starting validation...")
            validation_start = time.time()
            validation_block = await define_validating_agent(state)
            validation_time = time.time() - validation_start
            
            async with self._lock:
                task = self._tasks[task_id]
                if task.details:
                    tokens = extract_tokens_from_response(validation_block.get("_raw_response"))
                    add_tokens_to_statistics(
                        task.details,
                        tokens["prompt_tokens"],
                        tokens["completion_tokens"],
                        tokens["total_tokens"],
                    )
                    task.details.validation_count += 1
                    task.details.timing[f"validation_{task.details.validation_count}"] = round(validation_time, 2)
            
            state.update(validation_block)
            state["validation_attempts"] += 1

            validation_result = validator_answer(state)
            logger.info(f"[TASK {task_id[:8]}] Validation result: {validation_result} (time: {validation_time:.2f}s, count: {task.details.validation_count if task.details else 0})")
            validator_msg = f"[Attempt {attempt_number}] Validator response: {validation_result}."
            await self._append_thought(task_id, validator_msg)
            await self._add_step(task_id, attempt_number, "validation", validator_msg)

            if validation_result == "yes":
                logger.info(f"[TASK {task_id[:8]}] Validation passed. Task completed successfully")
                async with self._lock:
                    task = self._tasks[task_id]
                    if task.details:
                        task.details.update_attempt_status(attempt_number, "completed")
                return True, state["output"]

            if state["validation_attempts"] >= self._max_validation_attempts:
                max_attempts_msg = "Reached maximum validation attempts. Returning last draft."
                logger.warning(f"[TASK {task_id[:8]}] {max_attempts_msg}")
                await self._append_thought(task_id, max_attempts_msg)
                await self._add_step(task_id, attempt_number, "warning", max_attempts_msg)
                async with self._lock:
                    task = self._tasks[task_id]
                    if task.details:
                        task.details.update_attempt_status(attempt_number, "completed")
                last_output = state.get("output")
                if last_output:
                    return True, last_output
                else:
                    return False, None

            retry_msg = "Validator requested another attempt. Retrying..."
            logger.info(f"[TASK {task_id[:8]}] {retry_msg}")
            await self._append_thought(task_id, retry_msg)
            await self._add_step(task_id, attempt_number, "progress", retry_msg)

        return validation_result == "yes", state.get("output")

    async def _set_mode(self, task_id: str, mode: Literal["pro", "simple"]) -> None:
        async with self._lock:
            task = self._tasks[task_id]
            if task.details is None:
                task.details = TaskDetails(mode=mode)
            else:
                task.details.mode = mode
            task.updated_at = datetime.now(timezone.utc)

    async def _append_thought(self, task_id: str, message: str) -> None:
        async with self._lock:
            task = self._tasks[task_id]
            if task.details is None:
                task.details = TaskDetails(thoughts=message)
            else:
                task.details.append_thought(message)
            task.updated_at = datetime.now(timezone.utc)

    async def _add_step(
        self,
        task_id: str,
        attempt_number: int,
        step_type: str,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a structured step to thoughts_data"""
        async with self._lock:
            task = self._tasks[task_id]
            if task.details is None:
                task.details = TaskDetails()
            task.details.add_step(attempt_number, step_type, message, data)
            task.updated_at = datetime.now(timezone.utc)

    async def _update_task(
        self,
        task_id: str,
        *,
        status: Optional[TaskStatus] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        async with self._lock:
            task = self._tasks[task_id]
            if status is not None:
                task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            task.updated_at = datetime.now(timezone.utc)


task_manager = TaskManager()

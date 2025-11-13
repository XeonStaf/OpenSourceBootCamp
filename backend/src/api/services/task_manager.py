from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from src.graph.nodes.pro import pro_mode
from src.graph.nodes.simple import simple_mode
from src.graph.router.router import llm_call_router
from src.graph.states.state import State
from src.graph.validator.validator import define_validating_agent, validator_answer

TaskStatus = Literal["pending", "running", "succeeded", "failed"]


@dataclass
class TaskDetails:
    mode: Optional[Literal["pro", "simple"]] = None
    thoughts: str = ""

    def append_thought(self, message: str) -> None:
        self.thoughts = f"{self.thoughts}\n{message}" if self.thoughts else message


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
        return {
            "task_id": self.task_id,
            "status": self.status,
            "details": None
            if self.details is None or self.details.mode is None
            else {
                "mode": self.details.mode,
                "thoughts": self.details.thoughts,
            },
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
        }


class TaskManager:
    def __init__(self, max_validation_attempts: int = 3) -> None:
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock = asyncio.Lock()
        self._max_validation_attempts = max_validation_attempts

    async def create_task(self, query: str) -> str:
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

        asyncio.create_task(self._process_task(task_id, query))
        return task_id

    async def get_task_payload(self, task_id: str) -> Dict[str, Any]:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(task_id)
            return task.to_response_payload()

    async def _process_task(self, task_id: str, query: str) -> None:
        await self._update_task(task_id, status="running")
        state: State = {
            "input": query,
            "decision": "",
            "output": "",
            "validation_attempts": 0,
            "validation_result": "",
        }

        try:
            success, output = await self._execute_pipeline(task_id, state)
        except Exception as exc:  # pylint: disable=broad-except
            await self._update_task(
                task_id,
                status="failed",
                error=str(exc),
            )
        else:
            if success and output is not None:
                await self._update_task(task_id, status="succeeded", result=output)
            else:
                await self._update_task(
                    task_id,
                    status="failed",
                    error="Validation failed after maximum attempts.",
                )

    async def _execute_pipeline(self, task_id: str, state: State) -> tuple[bool, Optional[str]]:
        validation_result: Optional[str] = None

        while state["validation_attempts"] < self._max_validation_attempts:
            attempt_number = state["validation_attempts"] + 1
            decision_block = await asyncio.to_thread(llm_call_router, state)
            decision = decision_block["decision"]
            state["decision"] = decision

            await self._set_mode(task_id, decision)
            await self._append_thought(
                task_id,
                f"[Attempt {attempt_number}] Routed query to {decision.upper()} mode.",
            )

            if decision == "pro":
                output_block = await asyncio.to_thread(pro_mode, state)
                await self._append_thought(
                    task_id,
                    f"[Attempt {attempt_number}] Pro mode collected and synthesized information.",
                )
            else:
                output_block = await asyncio.to_thread(simple_mode, state)
                await self._append_thought(
                    task_id,
                    f"[Attempt {attempt_number}] Simple mode generated a direct answer.",
                )

            state.update(output_block)

            validation_block = await asyncio.to_thread(define_validating_agent, state)
            state.update(validation_block)
            state["validation_attempts"] += 1

            validation_result = await asyncio.to_thread(validator_answer, state)
            await self._append_thought(
                task_id,
                f"[Attempt {attempt_number}] Validator response: {validation_result}.",
            )

            if validation_result == "yes":
                return True, state["output"]

            if state["validation_attempts"] >= self._max_validation_attempts:
                await self._append_thought(
                    task_id,
                    "Reached maximum validation attempts. Returning last draft.",
                )
                break

            await self._append_thought(task_id, "Validator requested another attempt. Retrying...")

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


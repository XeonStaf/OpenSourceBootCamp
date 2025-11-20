import asyncio
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.config.search import search_settings
from src.graph.pro_mode.schemas.facts import Facts
from src.graph.pro_mode.schemas.foreign_question import ForeignQuestion
from src.graph.states.state import State
from src.models.llm import llm
from src.searches.extractor import fetch_and_extract
from src.utils.token_callback import TokenUsageCallback

logger = logging.getLogger(__name__)

llm_for_facts = llm.with_structured_output(Facts)
foreign_llm = llm.with_structured_output(ForeignQuestion)

BATCH_SIZE = 5


async def retrieve_facts(state: State):
    questions = [question.text[: search_settings.MAX_LEN] for question in state["sub_queries"]]
    logger.info(f"[FACTS] Starting facts retrieval for {len(questions)} subquestions")

    logger.info(f"[FACTS] Translating query...")
    translation_messages = [
        SystemMessage(
            content="""You are a professional multilingual translator specialized in query localization.

TRANSLATION PROTOCOL:
- Analyze the input query to determine its original language
- If the query is in ENGLISH → Translate to RUSSIAN
- If the query is in ANY OTHER LANGUAGE → Translate to ENGLISH
- Preserve technical terms, proper names, and contextual meaning
- Ensure the translation is natural and idiomatic in the target language

QUALITY STANDARDS:
- Maintain original intent and semantic accuracy
- Preserve domain-specific terminology
- Ensure grammatical correctness in target language
- Adapt cultural references when appropriate"""
        ),
        HumanMessage(
            content=f"""**QUERY TO TRANSLATE:**
{state["input"]}

TASK:
1. Identify the original language of this query
2. Apply the translation protocol to convert to the appropriate target language
3. Provide both the language classification and accurate translation"""
        ),
    ]
    
    translation_callback = TokenUsageCallback()
    foreign_question = await foreign_llm.ainvoke(translation_messages, config={"callbacks": [translation_callback]})
    translated_preview = foreign_question.translated_question[:100] + ("..." if len(foreign_question.translated_question) > 100 else "")
    logger.info(f"[FACTS] Translation completed: {foreign_question.language} -> {translated_preview}")

    country = "united states"
    if foreign_question.language == "eng":
        country = "russia"
    
    logger.info(f"[FACTS] Fetching and extracting data from Tavily (country: {country})...")
    retrieved_texts = await fetch_and_extract(
        questions, foreign_query=foreign_question.translated_question, country=country
    )
    logger.info(f"[FACTS] Retrieved {len(retrieved_texts)} text sets from Tavily")
    
    valid_texts = []
    for text in retrieved_texts:
        content = "------".join([article.get("raw_content", "") for article in text.get("results", [])])
        if content and len(content.strip()) > 0:
            valid_texts.append(text)
    
    valid_texts = valid_texts[:search_settings.MAX_TEXT_SETS_FOR_FACTS]
    logger.info(f"[FACTS] Processing {len(valid_texts)} valid text sets (max: {search_settings.MAX_TEXT_SETS_FOR_FACTS})")
    
    source_facts = []
    raw_responses = []
    
    translation_token_usage = translation_callback.get_token_usage()
    translation_raw = type("Response", (), {"response_metadata": {"token_usage": translation_token_usage}})()
    raw_responses.append(translation_raw)
    
    async def extract_facts_from_text(text, index):
        content = "------".join([article.get("raw_content", "") for article in text.get("results", [])])
        if not content or len(content.strip()) == 0:
            return None, None
        
        logger.info(f"[FACTS] Extracting facts from text set {index + 1}/{len(valid_texts)} (content length: {len(content)} chars)")
        
        fact_messages = [
            SystemMessage(
                content="""You are an expert information analyst specialized in fact extraction.

                    **YOUR ROLE:**
                    - Carefully analyze the provided text and identify ALL relevant facts
                    - Focus on factual information that helps answer the user's original question
                    - Extract numerical data, dates, names, relationships, and key statements
                    - Maintain objectivity and avoid interpretation or opinion

                    **EXTRACTION GUIDELINES:**
                    1. Extract complete facts with necessary context
                    2. Include quantitative data (numbers, statistics, measurements)
                    3. Capture qualitative information (relationships, properties, characteristics)
                    4. Preserve source credibility by maintaining factual accuracy
                    5. Focus on information directly relevant to answering the question

                    **OUTPUT:** Provide a comprehensive list of facts that your colleague can use to construct a complete answer."""
            ),
            HumanMessage(
                content=f"""**ORIGINAL QUESTION:** {state['input']}

                    **TEXT TO ANALYZE:**
                    {content}

                    **TASK:** Extract all relevant facts from the text above that help answer the original question."""
            ),
        ]
        
        fact_callback = TokenUsageCallback()
        collected_facts = await llm_for_facts.ainvoke(fact_messages, config={"callbacks": [fact_callback]})
        
        fact_token_usage = fact_callback.get_token_usage()
        fact_raw = type("Response", (), {"response_metadata": {"token_usage": fact_token_usage}})()
        
        logger.info(f"[FACTS] Extracted {len(collected_facts.facts)} facts from text set {index + 1}")
        return collected_facts, fact_raw
    
    for batch_start in range(0, len(valid_texts), BATCH_SIZE):
        batch = valid_texts[batch_start:batch_start + BATCH_SIZE]
        batch_indices = list(range(batch_start, batch_start + len(batch)))
        
        batch_results = await asyncio.gather(*[
            extract_facts_from_text(text, idx) 
            for text, idx in zip(batch, batch_indices)
        ])
        
        for collected_facts, fact_raw in batch_results:
            if collected_facts is not None:
                source_facts.append(collected_facts)
                raw_responses.append(fact_raw)
    
    logger.info(f"[FACTS] Facts retrieval completed. Total fact sets: {len(source_facts)}")
    return {"facts": source_facts, "_raw_responses": raw_responses}

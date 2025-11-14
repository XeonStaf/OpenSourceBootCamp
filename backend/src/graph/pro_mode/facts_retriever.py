import asyncio

from langchain_core.messages import HumanMessage, SystemMessage

from src.config.search import search_settings
from src.graph.pro_mode.schemas.facts import Facts
from src.graph.pro_mode.schemas.foreign_question import ForeignQuestion
from src.graph.states.state import State
from src.models.llm import llm
from src.searches.extractor import fetch_and_extract

llm_for_facts = llm.with_structured_output(Facts)
foreign_llm = llm.with_structured_output(ForeignQuestion)


def retrieve_facts(state: State):
    questions = [question.text[: search_settings.MAX_LEN] for question in state["sub_queries"]]

    foreign_question = foreign_llm.invoke(
        [
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
    )

    country = "united states"
    if foreign_question.language == "eng":
        country = "russia"

    retrieved_texts = asyncio.run(
        fetch_and_extract(questions, foreign_query=foreign_question.question, country=country)
    )
    source_facts = []
    for text in retrieved_texts:
        content = "------".join([article["raw_content"] for article in text["results"]])
        print(f"Content: {content[:100]}...")
        collected_facts = llm_for_facts.invoke(
            [
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
        )

        source_facts.append(collected_facts)
    print(f"Collected Facts: {source_facts}")
    return {"facts": source_facts}

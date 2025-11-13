from typing import List

from pydantic import BaseModel, Field


class Fact(BaseModel):
    text: str = Field(
        ...,
        description="""A single, precise factual statement extracted from source text that directly contributes to answering the user's question. \
        Each fact should be self-contained, objective, and verifiable.""",
    )


class Facts(BaseModel):
    summary: str = Field(
        ...,
        description="""Concise overview of the most relevant information from the text in relation to the user's query. \
            Highlights key findings and main points that address the original question.""",
    )
    facts: List[Fact] = Field(
        ...,
        description="""Comprehensive collection of ALL relevant factual statements, data points, and key information \
            extracted from the source text that collectively enable answering the user's question accurately and completely.""",
    )

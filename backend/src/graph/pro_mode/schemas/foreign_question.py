from pydantic import BaseModel, Field
from typing_extensions import Literal


class ForeignQuestion(BaseModel):
    translated_question: str = Field(
        ...,
        description="""Accurate translation of the original query following language rules:
        - If original is English → translate to Russian
        - If original is any other language → translate to English
        Maintain original meaning, context, and technical terminology.""",
    )
    language: Literal["eng", "other"] = Field(
        ...,
        description="""Language classification of the original query:
        - 'eng': Original query is in English
        - 'other': Original query is in any language other than English""",
    )

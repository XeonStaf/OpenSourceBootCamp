from pydantic import BaseModel, Field


class Validate(BaseModel):
    step = Field(
        None,
        description="""Validating agent for multi-agent system's (MAS') response. 
        Main goal is to check was the system answered the user's question or it's not""",
    )

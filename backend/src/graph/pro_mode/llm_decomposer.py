from src.graph.pro_mode.schemas.questions import QuestionBreakdown
from src.models.llm import llm

llm_decomposer = llm.with_structured_output(QuestionBreakdown)

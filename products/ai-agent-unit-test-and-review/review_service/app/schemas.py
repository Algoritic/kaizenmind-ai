from pydantic import BaseModel
from typing import Optional

class LlmConfig(BaseModel):
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens_review: Optional[int] = None
    llm_max_tokens_testgen: Optional[int] = None
    llm_max_tokens_doc_review: Optional[int] = None

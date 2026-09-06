from __future__ import annotations

from typing import Any

from deepeval.models import DeepEvalBaseLLM
from pydantic import BaseModel

from agent.llm import get_chat_model, invoke_structured
from backend.config import settings


class GroqJudge(DeepEvalBaseLLM):
    """DeepEval judge backed by the Groq router model."""

    def __init__(self) -> None:
        super().__init__(model=settings.router_model)
        self.model = get_chat_model(role="router")

    def load_model(self) -> Any:
        return self.model

    def get_model_name(self) -> str:
        return settings.router_model

    def supports_structured_outputs(self) -> bool:
        return True

    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> Any:
        llm = self.load_model()
        if schema is None:
            result = llm.invoke(prompt)
            return getattr(result, "content", str(result))
        schema_cls = schema if isinstance(schema, type) else type(schema)
        return invoke_structured(llm, schema_cls, [("human", prompt)])

    async def a_generate(self, prompt: str, schema: type[BaseModel] | None = None) -> Any:
        return self.generate(prompt, schema)

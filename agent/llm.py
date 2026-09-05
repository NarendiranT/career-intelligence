import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from backend.config import settings
from backend.errors import MissingLLMConfigError


def require_openai() -> None:
    key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key.strip():
        raise MissingLLMConfigError("OPENAI_API_KEY is not configured")
    os.environ["OPENAI_API_KEY"] = key


def get_chat_model(*, temperature: float = 0) -> ChatOpenAI:
    require_openai()
    return ChatOpenAI(model=settings.chat_model, temperature=temperature)


def get_embeddings() -> OpenAIEmbeddings:
    require_openai()
    return OpenAIEmbeddings(model=settings.embedding_model)

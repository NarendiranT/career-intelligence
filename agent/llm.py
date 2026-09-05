import os
from typing import Literal

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from backend.config import settings
from backend.errors import MissingLLMConfigError

ChatRole = Literal["extraction", "router", "generation"]


def require_groq() -> None:
    key = settings.groq_api_key or os.environ.get("GROQ_API_KEY", "")
    if not key.strip():
        raise MissingLLMConfigError("GROQ_API_KEY is not configured")
    os.environ["GROQ_API_KEY"] = key


def get_chat_model(*, role: ChatRole = "generation", temperature: float = 0) -> ChatGroq:
    require_groq()
    models = {
        "extraction": settings.extraction_model,
        "router": settings.router_model,
        "generation": settings.generation_model,
    }
    return ChatGroq(model=models[role], temperature=temperature)


def get_embeddings() -> HuggingFaceEmbeddings:
    token = settings.hf_token or os.environ.get("HF_TOKEN", "") or os.environ.get("HUGGINGFACEHUB_API_TOKEN", "")
    if token.strip():
        os.environ.setdefault("HF_TOKEN", token)
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": settings.embedding_device},
        encode_kwargs={"normalize_embeddings": True},
    )

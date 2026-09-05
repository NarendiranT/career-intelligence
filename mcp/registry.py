from __future__ import annotations

from collections.abc import Callable
from typing import Any


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        self._tools[name] = fn

    def invoke(self, name: str, **kwargs: Any) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name](**kwargs)

    def names(self) -> list[str]:
        return sorted(self._tools)


def build_registry() -> ToolRegistry:
    from mcp.tools import indexing as indexing_tools
    from mcp.tools import rag as rag_tools

    registry = ToolRegistry()
    registry.register("create_or_update_user", indexing_tools.create_or_update_user)
    registry.register("save_resume_profile", indexing_tools.save_resume_profile)
    registry.register("save_job_profile", indexing_tools.save_job_profile)
    registry.register("update_processing_status", indexing_tools.update_processing_status)
    registry.register("replace_document_chunks", indexing_tools.replace_document_chunks)
    registry.register("enrich_job_board", indexing_tools.enrich_job_board)
    registry.register("get_user_profile", rag_tools.get_user_profile)
    registry.register("fetch_document_metadata", rag_tools.fetch_document_metadata)
    registry.register("fetch_structured_profiles", rag_tools.fetch_structured_profiles)
    registry.register("save_conversation_message", rag_tools.save_conversation_message)
    registry.register("update_usage", rag_tools.update_usage)
    registry.register("web_search", rag_tools.web_search)
    return registry


tools = build_registry()

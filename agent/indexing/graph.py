from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from agent.indexing.nodes import (
    IndexingState,
    chunk_and_embed,
    load_document,
    persist_data,
    process_job,
    process_resume,
    route_document,
)


def _after_router(state: IndexingState) -> Literal["process_resume", "process_job", "persist_data"]:
    if state.get("error"):
        return "persist_data"
    if state.get("doc_type") == "job":
        return "process_job"
    return "process_resume"


def build_indexing_graph():
    graph = StateGraph(IndexingState)
    graph.add_node("load_document", load_document)
    graph.add_node("route_document", route_document)
    graph.add_node("process_resume", process_resume)
    graph.add_node("process_job", process_job)
    graph.add_node("chunk_and_embed", chunk_and_embed)
    graph.add_node("persist_data", persist_data)

    graph.add_edge(START, "load_document")
    graph.add_edge("load_document", "route_document")
    graph.add_conditional_edges(
        "route_document",
        _after_router,
        {
            "process_resume": "process_resume",
            "process_job": "process_job",
            "persist_data": "persist_data",
        },
    )
    graph.add_edge("process_resume", "chunk_and_embed")
    graph.add_edge("process_job", "chunk_and_embed")
    graph.add_edge("chunk_and_embed", "persist_data")
    graph.add_edge("persist_data", END)
    return graph.compile()


indexing_graph = build_indexing_graph()

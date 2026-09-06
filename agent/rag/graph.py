from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from agent.rag.nodes import (
    RagState,
    build_prompt,
    extract_interview_topics,
    generate_answer,
    identify_channel,
    input_guardrail,
    query_understanding,
    retrieve_context,
    retry_retrieval,
    stream_and_persist,
    validate_answer,
)


def _after_identify(state: RagState) -> Literal["extract_interview_topics", "input_guardrail", "__end__"]:
    if state.get("blocked"):
        return "__end__"
    if state.get("channel") == "extract_topics":
        return "extract_interview_topics"
    return "input_guardrail"


def _after_guard(state: RagState) -> Literal["query_understanding", "stream_and_persist"]:
    if state.get("blocked"):
        return "stream_and_persist"
    return "query_understanding"


def _after_generate(state: RagState) -> Literal["validate_answer", "stream_and_persist"]:
    if state.get("channel") == "interview":
        return "stream_and_persist"
    return "validate_answer"


def _after_validate(state: RagState) -> Literal["stream_and_persist", "retry_retrieval"]:
    if state.get("ok"):
        return "stream_and_persist"
    return "retry_retrieval"


def build_rag_graph():
    graph = StateGraph(RagState)
    graph.add_node("identify_channel", identify_channel)
    graph.add_node("extract_interview_topics", extract_interview_topics)
    graph.add_node("input_guardrail", input_guardrail)
    graph.add_node("query_understanding", query_understanding)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("build_prompt", build_prompt)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("validate_answer", validate_answer)
    graph.add_node("retry_retrieval", retry_retrieval)
    graph.add_node("stream_and_persist", stream_and_persist)

    graph.add_edge(START, "identify_channel")
    graph.add_conditional_edges(
        "identify_channel",
        _after_identify,
        {
            "extract_interview_topics": "extract_interview_topics",
            "input_guardrail": "input_guardrail",
            "__end__": END,
        },
    )
    graph.add_edge("extract_interview_topics", END)
    graph.add_conditional_edges(
        "input_guardrail",
        _after_guard,
        {
            "query_understanding": "query_understanding",
            "stream_and_persist": "stream_and_persist",
        },
    )
    graph.add_edge("query_understanding", "retrieve_context")
    graph.add_edge("retrieve_context", "build_prompt")
    graph.add_edge("build_prompt", "generate_answer")
    graph.add_conditional_edges(
        "generate_answer",
        _after_generate,
        {
            "validate_answer": "validate_answer",
            "stream_and_persist": "stream_and_persist",
        },
    )
    graph.add_conditional_edges(
        "validate_answer",
        _after_validate,
        {
            "stream_and_persist": "stream_and_persist",
            "retry_retrieval": "retry_retrieval",
        },
    )
    graph.add_edge("retry_retrieval", "retrieve_context")
    graph.add_edge("stream_and_persist", END)
    return graph.compile()


rag_graph = build_rag_graph()

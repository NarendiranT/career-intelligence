from pathlib import Path

from agent.indexing.loaders import extract_text
from mcp.registry import tools


def test_tool_registry_has_diagram_names():
    names = set(tools.names())
    for required in (
        "create_or_update_user",
        "save_resume_profile",
        "save_job_profile",
        "update_processing_status",
        "enrich_job_board",
        "get_user_profile",
        "fetch_document_metadata",
        "save_conversation_message",
        "update_usage",
        "web_search",
    ):
        assert required in names


def test_extract_text_txt(tmp_path: Path):
    path = tmp_path / "note.txt"
    path.write_text("hello career", encoding="utf-8")
    assert "hello career" in extract_text(path)

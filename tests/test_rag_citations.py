from agent.rag.nodes import _apply_filename_citations
from agent.schemas import GeneratedAnswer


def test_apply_filename_citations_uses_uploaded_filename():
    answer = GeneratedAnswer(
        text="ok",
        citations=[{"id": "doc-1", "label": "resume"}, {"id": "doc-2", "label": "job"}],
    )
    _apply_filename_citations(
        answer,
        {"document_names": {"doc-1": "Ada_Resume.pdf", "doc-2": "Staff_Engineer_JD.pdf"}},
    )
    assert [c.label for c in answer.citations] == ["Ada_Resume.pdf", "Staff_Engineer_JD.pdf"]


def test_apply_filename_citations_maps_type_ids_to_selected_files():
    answer = GeneratedAnswer(
        text="ok",
        citations=[{"id": "resume", "label": "resume"}, {"id": "job", "label": "job"}],
    )
    _apply_filename_citations(
        answer,
        {
            "resume_id": "doc-1",
            "job_ids": ["doc-2"],
            "document_names": {"doc-1": "Ada_Resume.pdf", "doc-2": "Staff_Engineer_JD.pdf"},
        },
    )
    assert [(c.id, c.label) for c in answer.citations] == [
        ("doc-1", "Ada_Resume.pdf"),
        ("doc-2", "Staff_Engineer_JD.pdf"),
    ]


def test_apply_filename_citations_strips_inline_markers_and_maps_filename():
    answer = GeneratedAnswer(
        text="Here is the match 【Narendiran_T_resume.pdf】",
        citations=[{"id": "Resume", "label": "Resume"}, {"id": "Job", "label": "Job"}],
        strengths=["Python production-level coding 【Narendiran_T_resume.pdf】"],
        gaps=["No Kubernetes listed"],
    )
    _apply_filename_citations(
        answer,
        {
            "resume_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "job_ids": ["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"],
            "document_names": {
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": "Narendiran_T_resume.pdf",
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb": "Staff_Engineer_JD.pdf",
            },
        },
    )
    assert "【" not in answer.text
    assert answer.strengths == ["Python production-level coding"]
    assert [(c.id, c.label) for c in answer.citations] == [
        ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "Narendiran_T_resume.pdf"),
        ("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "Staff_Engineer_JD.pdf"),
    ]


def test_apply_filename_citations_maps_job_alias_when_multiple_jobs():
    answer = GeneratedAnswer(text="ok", citations=[{"id": "job", "label": "Job"}])
    _apply_filename_citations(
        answer,
        {
            "resume_id": "doc-1",
            "job_ids": ["doc-2", "doc-3"],
            "document_names": {
                "doc-1": "Ada_Resume.pdf",
                "doc-2": "Role_A.pdf",
                "doc-3": "Role_B.pdf",
            },
        },
    )
    assert [(c.id, c.label) for c in answer.citations] == [
        ("doc-2", "Role_A.pdf"),
        ("doc-3", "Role_B.pdf"),
    ]

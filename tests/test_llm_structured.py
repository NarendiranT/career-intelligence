from agent.context_budget import compact_chunks, compact_profiles, truncate_text
from agent.llm import chat_model_kwargs, invoke_structured, invoke_structured_tracked
from agent.schemas import QueryPlan, ResumeProfile
from agent.usage import extract_token_usage, summarize_usage


class _Runnable:
    def __init__(self, method: str, fail: bool = False):
        self.method = method
        self.fail = fail

    def invoke(self, _messages):
        if self.fail:
            raise RuntimeError("Error code: 400 - Failed to parse tool call arguments as JSON tool_use_failed")
        return QueryPlan(intent="resume", rewritten_query=self.method)


class _Model:
    def __init__(self, fail_schema: bool = False):
        self.fail_schema = fail_schema
        self.methods: list[str] = []

    def with_structured_output(self, _schema, method="function_calling", **_kwargs):
        self.methods.append(method)
        return _Runnable(method, fail=self.fail_schema and method == "json_schema")


class _LegacyModel:
    def with_structured_output(self, _schema):
        class R:
            def invoke(self, _messages):
                return QueryPlan(intent="job", rewritten_query="legacy")

        return R()


class _UsageRaw:
    usage_metadata = {"input_tokens": 11, "output_tokens": 4, "total_tokens": 15}
    response_metadata = {}


class _UsageModel:
    model = "openai/gpt-oss-20b"

    def with_structured_output(self, _schema, **_kwargs):
        class R:
            def invoke(self, _messages):
                return {
                    "parsed": QueryPlan(intent="resume", rewritten_query="skills"),
                    "raw": _UsageRaw(),
                }

        return R()


def test_invoke_structured_uses_json_schema_first():
    model = _Model()
    result = invoke_structured(model, QueryPlan, [("human", "skills?")])
    assert result.rewritten_query == "json_schema"
    assert model.methods == ["json_schema"]


def test_invoke_structured_falls_back_to_json_mode_on_tool_json_error():
    model = _Model(fail_schema=True)
    result = invoke_structured(model, QueryPlan, [("system", "x"), ("human", "skills?")])
    assert result.rewritten_query == "json_mode"
    assert model.methods == ["json_schema", "json_mode"]


def test_invoke_structured_supports_schema_only_wrappers():
    result = invoke_structured(_LegacyModel(), QueryPlan, [("human", "hi")])
    assert result.intent == "job"


def test_extract_token_usage_from_langchain_metadata():
    class Raw:
        usage_metadata = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
        response_metadata = {}

    assert extract_token_usage(Raw()) == {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}


def test_extract_token_usage_from_groq_token_usage():
    class Raw:
        usage_metadata = {}
        response_metadata = {"token_usage": {"prompt_tokens": 3, "completion_tokens": 7, "total_tokens": 10}}

    assert extract_token_usage(Raw()) == {"input_tokens": 3, "output_tokens": 7, "total_tokens": 10}


def test_summarize_usage_rolls_up_events():
    summary = summarize_usage(
        [
            {"input_tokens": 10, "output_tokens": 2, "tokens": 12},
            {"input_tokens": 4, "output_tokens": 6, "tokens": 10},
        ]
    )
    assert summary == {"tokens": 22, "prompt_tokens": 14, "completion_tokens": 8}


def test_invoke_structured_tracked_reads_raw_usage():
    parsed, usage = invoke_structured_tracked(
        _UsageModel(),
        QueryPlan,
        [("human", "skills?")],
        event_type="rag.generate",
    )
    assert parsed.rewritten_query == "skills"
    assert usage["event_type"] == "rag.generate"
    assert usage["model"] == "openai/gpt-oss-20b"
    assert usage["tokens"] == 15
    assert usage["input_tokens"] == 11
    assert usage["output_tokens"] == 4
    assert usage["latency_ms"] >= 0


def test_chat_model_kwargs_always_sets_max_tokens():
    router = chat_model_kwargs(role="router")
    assert router["max_tokens"] == 768
    assert router["reasoning_effort"] == "low"
    generation = chat_model_kwargs(role="generation", max_tokens=4096, top_p=0.9)
    assert generation["max_tokens"] == 1536
    assert generation["model_kwargs"]["top_p"] == 0.9


def test_compact_context_stays_small():
    chunks = [{"filename": "resume.txt", "content": "x" * 4000} for _ in range(10)]
    profiles = {
        "resumes": [{"filename": "resume.txt", "name": "Ada", "skills": ["Python"], "summary": "s" * 2000}],
        "jobs": [],
    }
    text = compact_chunks(chunks) + compact_profiles(profiles)
    assert len(text) < 8000
    assert "Python" in compact_profiles(
        {
            "resumes": [
                {
                    "filename": "resume.txt",
                    "name": "Ada",
                    "skills": [{"name": "Python", "category": "Programming Languages", "proficiency": 5}],
                    "summary": "s",
                }
            ],
            "jobs": [],
        }
    )
    assert truncate_text("abcdef", 4).endswith("…")
    assert len(truncate_text("abcdef", 4)) == 4


def test_resume_profile_coerces_string_skills():
    profile = ResumeProfile(name="Jane Candidate", skills=["Python", "FastAPI"])
    dumped = profile.model_dump()
    assert dumped["skills"] == [
        {"name": "Python", "category": "Other Skills", "proficiency": 3},
        {"name": "FastAPI", "category": "Other Skills", "proficiency": 3},
    ]

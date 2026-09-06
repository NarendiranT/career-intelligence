from agent.context_budget import compact_chunks, compact_profiles, truncate_text
from agent.llm import chat_model_kwargs, invoke_structured, invoke_structured_tracked
from agent.schemas import GeneratedAnswer, QueryPlan, ResumeProfile
from agent.usage import extract_token_usage, salvage_structured, summarize_usage, unwrap_structured


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


class _NullThenJsonMode:
    def __init__(self):
        self.methods: list[str] = []

    def with_structured_output(self, _schema, method="function_calling", **_kwargs):
        self.methods.append(method)

        class R:
            def invoke(self, _messages):
                if method == "json_schema":
                    return {"parsed": None, "raw": _UsageRaw(), "parsing_error": None}
                return QueryPlan(intent="resume", rewritten_query="json_mode")

        return R()


def test_unwrap_structured_recovers_resume_from_raw_json():
    class Raw:
        content = '{"name": "Ada", "skills": ["Python"]}'

    parsed, raw = unwrap_structured({"parsed": None, "raw": Raw()}, ResumeProfile)
    assert parsed.name == "Ada"
    assert parsed.skills[0].name == "Python"
    assert isinstance(raw, Raw)


def test_invoke_structured_falls_back_when_json_schema_parses_none():
    model = _NullThenJsonMode()
    result = invoke_structured(model, QueryPlan, [("human", "skills?")])
    assert result.rewritten_query == "json_mode"
    assert model.methods == ["json_schema", "json_mode"]


def test_resume_profile_coerces_string_skills():
    profile = ResumeProfile(name="Jane Candidate", skills=["Python", "FastAPI"])
    dumped = profile.model_dump()
    assert dumped["skills"] == [
        {"name": "Python", "category": "Other Skills", "proficiency": 3},
        {"name": "FastAPI", "category": "Other Skills", "proficiency": 3},
    ]


def test_resume_profile_coerces_unknown_skill_categories():
    profile = ResumeProfile(
        name="Jane Candidate",
        skills=[
            {"name": "Kafka", "category": "Messaging & Async", "proficiency": 4},
            {"name": "GitHub Actions", "category": "DevOps & CI/CD", "proficiency": 9},
        ],
    )
    dumped = {item["name"]: item for item in profile.model_dump()["skills"]}
    assert dumped["Kafka"]["category"] == "Other Skills"
    assert dumped["GitHub Actions"]["category"] == "Cloud & DevOps"
    assert dumped["GitHub Actions"]["proficiency"] == 5


class _AlwaysFail:
    def __init__(self, body: dict):
        self.body = body

    def with_structured_output(self, _schema, **_kwargs):
        body = self.body

        class R:
            def invoke(self, _messages):
                raise _GroqJsonError(body)

        return R()


class _GroqJsonError(Exception):
    def __init__(self, body: dict):
        super().__init__("Error code: 400 - json_validate_failed")
        self.body = body


def test_salvage_broken_generated_answer_from_groq():
    blob = (
        '{\n  "text": "To quantify your Generative AI experience for the interview", '
        '"frame your achievements with concrete metrics and tie them directly to the job":'
        '"s key responsibilities. Use STAR stories.\\n\\n",'
        '"https":null}'
    )
    err = _GroqJsonError({"error": {"code": "json_validate_failed", "failed_generation": blob}})
    answer = salvage_structured(GeneratedAnswer, err)
    assert "quantify your Generative AI experience" in answer.text
    assert "STAR" in answer.text


def test_invoke_structured_salvages_json_validate_failed():
    blob = '{"text": "Lists are mutable; tuples are not.", "citations": []}'
    model = _AlwaysFail({"error": {"failed_generation": blob}})
    result = invoke_structured(model, GeneratedAnswer, [("human", "lists vs tuples")])
    assert result.text.startswith("Lists are mutable")


def test_invoke_structured_plain_text_fallback_for_answers():
    class _FailThenPlain:
        def with_structured_output(self, _schema, **_kwargs):
            class R:
                def invoke(self, _messages):
                    raise RuntimeError("json_validate_failed")

            return R()

        def invoke(self, _messages):
            class Msg:
                content = "Keep answers short."
                usage_metadata = {"input_tokens": 2, "output_tokens": 3, "total_tokens": 5}

            return Msg()

    result = invoke_structured(_FailThenPlain(), GeneratedAnswer, [("human", "tip")])
    assert result.text == "Keep answers short."

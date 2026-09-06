from __future__ import annotations

import os
import uuid

import pytest

from backend.config import settings
from mcp.registry import tools
from tests.conftest import postgres_available, requires_postgres

pytest.importorskip("deepeval")

from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    GEval,
)
from deepeval.test_case import LLMTestCase, SingleTurnParams

from evals.deepeval_llm import GroqJudge
from evals.run_eval import (
    build_eval_corpus,
    keyword_hit,
    load_goldenset,
    profile_output,
    run_rag_case,
)

_THRESHOLD = 0.5
_INDEX_GOLDENS = load_goldenset("indexing.json")
_RAG_GOLDENS = load_goldenset("rag.json")

requires_eval = pytest.mark.skipif(
    os.environ.get("RUN_EVALS") != "1"
    or not (settings.groq_api_key or os.environ.get("GROQ_API_KEY", "")).strip(),
    reason="set RUN_EVALS=1 and GROQ_API_KEY",
)


@pytest.fixture(scope="module")
def eval_user():
    if os.environ.get("RUN_EVALS") != "1":
        pytest.skip("set RUN_EVALS=1 and GROQ_API_KEY")
    if not (settings.groq_api_key or os.environ.get("GROQ_API_KEY", "")).strip():
        pytest.skip("set RUN_EVALS=1 and GROQ_API_KEY")
    if not postgres_available():
        pytest.skip("postgres is not running")
    user_id = uuid.uuid4()
    tools.invoke("create_or_update_user", user_id=user_id, email=f"{user_id}@example.com")
    return user_id


@pytest.fixture(scope="module")
def eval_corpus(eval_user, tmp_path_factory):
    return build_eval_corpus(eval_user, tmp_path_factory.mktemp("eval_docs"))


@pytest.fixture(scope="module")
def judge():
    return GroqJudge()


def _indexing_metrics(judge: GroqJudge):
    return [
        GEval(
            name="IndexingCorrectness",
            criteria="The extracted profile JSON contains the key facts in expected output (names, titles, companies, skills).",
            evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
            threshold=_THRESHOLD,
            model=judge,
            async_mode=False,
        ),
        FaithfulnessMetric(threshold=_THRESHOLD, model=judge, async_mode=False),
    ]


def _rag_metrics(judge: GroqJudge):
    return [
        ContextualRelevancyMetric(threshold=_THRESHOLD, model=judge, async_mode=False),
        ContextualRecallMetric(threshold=_THRESHOLD, model=judge, async_mode=False),
        FaithfulnessMetric(threshold=_THRESHOLD, model=judge, async_mode=False),
        AnswerRelevancyMetric(threshold=_THRESHOLD, model=judge, async_mode=False),
    ]


@pytest.mark.eval
@requires_eval
@requires_postgres
@pytest.mark.parametrize("golden", _INDEX_GOLDENS, ids=lambda item: item["id"])
def test_indexing_goldenset(eval_corpus, judge, golden):
    result = eval_corpus.indexing[golden["id"]]
    actual = profile_output(result)
    context = [result.get("raw_text") or ""]
    keywords = golden.get("context_keywords") or []
    assert keyword_hit(actual, keywords), actual
    assert_test(
        LLMTestCase(
            input=golden["input"],
            actual_output=actual,
            expected_output=golden["expected_output"],
            retrieval_context=context,
        ),
        _indexing_metrics(judge),
        run_async=False,
    )


@pytest.mark.eval
@requires_eval
@requires_postgres
@pytest.mark.parametrize("golden", _RAG_GOLDENS, ids=lambda item: item["id"])
def test_rag_goldenset(eval_corpus, judge, golden):
    run = run_rag_case(eval_corpus, golden)
    keywords = golden.get("context_keywords") or []
    blob = "\n".join(run["retrieval_context"])
    assert keyword_hit(blob, keywords), blob
    assert_test(
        LLMTestCase(
            input=golden["input"],
            actual_output=run["text"],
            expected_output=golden["expected_output"],
            retrieval_context=run["retrieval_context"],
        ),
        _rag_metrics(judge),
        run_async=False,
    )

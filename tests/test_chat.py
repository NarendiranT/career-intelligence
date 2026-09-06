from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app import app
from backend.api_schemas import ChatRequest, ChatResponse
from tests.conftest import requires_postgres
from tests.test_auth import _register, auth_headers

client = TestClient(app)


@requires_postgres
def test_chat_websocket_streams_tokens(monkeypatch):
    captured: dict = {}

    def fake_invoke(user_id, body: ChatRequest):
        captured["user_id"] = user_id
        captured["body"] = body
        return {
            "conversation_id": str(uuid.uuid4()),
            "answer": {
                "text": "Python is listed on your resume.",
                "citations": [{"id": "doc-1", "label": "resume.txt"}],
                "strengths": ["Python"],
                "gaps": ["Kubernetes"],
            },
        }

    monkeypatch.setattr("backend.routers.ws.invoke_rag", fake_invoke)

    with TestClient(app) as ws_client:
        token = ws_client.post(
            "/v1/auth/register",
            json={
                "full_name": "Ada Lovelace",
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Passw0rd!",
            },
        ).json()["access_token"]
        resume_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        with ws_client.websocket_connect(f"/v1/ws/chat?token={token}") as websocket:
            websocket.send_json(
                {
                    "type": "chat.ask",
                    "question": "What skills are on my resume?",
                    "resume_id": resume_id,
                    "job_ids": [job_id],
                    "stream": True,
                    "temperature": 0.4,
                    "top_p": 0.8,
                    "max_tokens": 512,
                    "system_prompt": "Be concise.",
                    "web_search": True,
                    "model": "deep-research",
                }
            )
            status = websocket.receive_json()
            assert status == {"type": "chat.status", "status": "running"}
            tokens: list[str] = []
            done = None
            while True:
                event = websocket.receive_json()
                if event["type"] == "chat.token":
                    tokens.append(event["text"])
                    continue
                if event["type"] == "chat.done":
                    done = event
                    break
                raise AssertionError(event)
            assert "".join(tokens) == "Python is listed on your resume."
            assert done["text"] == "Python is listed on your resume."
            assert done["strengths"] == ["Python"]
            assert done["gaps"] == ["Kubernetes"]
            assert done["citations"][0]["label"] == "resume.txt"
            assert done["conversation_id"]
            assert done["validated"] is False
            assert done.get("message_id") is None

    body = captured["body"]
    assert body.temperature == 0.4
    assert body.top_p == 0.8
    assert body.max_tokens == 512
    assert body.system_prompt == "Be concise."
    assert body.web_search is True
    assert body.model == "deep-research"
    assert str(body.resume_id) == resume_id
    assert [str(i) for i in body.job_ids] == [job_id]


@requires_postgres
def test_chat_websocket_without_stream_sends_done_only(monkeypatch):
    monkeypatch.setattr(
        "backend.routers.ws.invoke_rag",
        lambda user_id, body: {
            "conversation_id": str(uuid.uuid4()),
            "answer": {"text": "OK", "citations": [], "strengths": [], "gaps": []},
        },
    )
    with TestClient(app) as ws_client:
        token = ws_client.post(
            "/v1/auth/register",
            json={
                "full_name": "Ada Lovelace",
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Passw0rd!",
            },
        ).json()["access_token"]
        with ws_client.websocket_connect(f"/v1/ws/chat?token={token}") as websocket:
            websocket.send_json({"type": "chat.ask", "question": "Hello", "stream": False})
            assert websocket.receive_json()["type"] == "chat.status"
            done = websocket.receive_json()
            assert done["type"] == "chat.done"
            assert done["text"] == "OK"


@requires_postgres
def test_chat_websocket_rejects_missing_token():
    with TestClient(app) as ws_client:
        try:
            with ws_client.websocket_connect("/v1/ws/chat") as websocket:
                websocket.receive_text()
            raise AssertionError("expected websocket to be rejected")
        except WebSocketDisconnect as exc:
            assert exc.code in {4401, 1008, 1006, 403}
        except Exception as exc:
            assert type(exc).__name__ in {"WebSocketDisconnect", "WebSocketDenialResponse"}


@requires_postgres
def test_chat_rest_passes_settings(monkeypatch):
    captured: dict = {}

    def fake_invoke(user_id, body: ChatRequest):
        captured["body"] = body
        return {
            "conversation_id": str(uuid.uuid4()),
            "answer": {"text": "OK", "citations": [], "strengths": [], "gaps": []},
        }

    monkeypatch.setattr("backend.routers.chat.invoke_rag", fake_invoke)
    token = _register()["access_token"]
    response = client.post(
        "/v1/chat",
        json={
            "question": "What skills are on my resume?",
            "stream": False,
            "temperature": 1.2,
            "web_search": True,
            "system_prompt": "Stay grounded.",
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert ChatResponse.model_validate(response.json()).text == "OK"
    assert captured["body"].temperature == 1.2
    assert captured["body"].web_search is True
    assert captured["body"].system_prompt == "Stay grounded."


@requires_postgres
def test_chat_websocket_interview_and_extract_channels(monkeypatch):
    captured: dict = {}

    def fake_invoke(user_id, body: ChatRequest):
        captured["body"] = body
        if body.channel == "extract_topics":
            return {
                "channel": "extract_topics",
                "conversation_id": str(body.source_conversation_id) if body.source_conversation_id else None,
                "topics": [{"id": str(uuid.uuid4()), "label": "Python", "slug": "python"}],
                "answer": {"text": "Created interview topics: Python", "citations": [], "strengths": [], "gaps": []},
            }
        return {
            "channel": "interview",
            "topic_id": str(body.topic_id) if body.topic_id else None,
            "conversation_id": str(uuid.uuid4()),
            "answer": {
                "text": "Lists are mutable.",
                "citations": [],
                "strengths": [],
                "gaps": [],
                "table": {"headers": ["Feature", "List"], "rows": [["Mutability", "Mutable"]]},
                "code": {"language": "python", "content": "xs = []"},
            },
        }

    monkeypatch.setattr("backend.routers.ws.invoke_rag", fake_invoke)

    with TestClient(app) as ws_client:
        token = ws_client.post(
            "/v1/auth/register",
            json={
                "full_name": "Ada Lovelace",
                "email": f"{uuid.uuid4()}@example.com",
                "password": "Passw0rd!",
            },
        ).json()["access_token"]
        topic_id = str(uuid.uuid4())
        with ws_client.websocket_connect(f"/v1/ws/chat?token={token}") as websocket:
            websocket.send_json(
                {
                    "type": "chat.ask",
                    "question": "Explain lists",
                    "channel": "interview",
                    "topic_id": topic_id,
                    "stream": True,
                    "system_prompt": "You are a practice coach for Python.",
                }
            )
            assert websocket.receive_json()["type"] == "chat.status"
            done = None
            while True:
                event = websocket.receive_json()
                if event["type"] == "chat.token":
                    continue
                if event["type"] == "chat.done":
                    done = event
                    break
                raise AssertionError(event)
            assert done["text"] == "Lists are mutable."
            assert done["table"]["headers"] == ["Feature", "List"]
            assert done["code"]["language"] == "python"
            assert captured["body"].channel == "interview"
            assert str(captured["body"].topic_id) == topic_id

            websocket.send_json(
                {
                    "type": "chat.ask",
                    "question": "Python is a strength on your resume.",
                    "channel": "extract_topics",
                    "stream": False,
                    "source_conversation_id": str(uuid.uuid4()),
                }
            )
            assert websocket.receive_json()["type"] == "chat.status"
            extracted = websocket.receive_json()
            assert extracted["type"] == "chat.done"
            assert extracted["topics"][0]["label"] == "Python"
            assert captured["body"].channel == "extract_topics"

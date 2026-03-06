from __future__ import annotations

import importlib.util

import pytest

from deid_local.adapters.llm.base import LLMResponse
from deid_local.core.chat_service import ChatSession, create_chat_app


class _RecordingProvider:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def infer(self, request):  # type: ignore[no-untyped-def]
        self.prompts.append(request.prompt)
        return LLMResponse(
            text=f"reply-{len(self.prompts)}",
            provider_name="fake",
            model="fake-model",
        )


def test_chat_app_routes_and_clear_behavior() -> None:
    if importlib.util.find_spec("flask") is None:
        pytest.skip("Install the optional `chat` extra to run the chat app integration test")

    provider = _RecordingProvider()
    session = ChatSession()
    app = create_chat_app(provider, session=session)
    client = app.test_client()

    home_response = client.get("/")
    assert home_response.status_code == 200
    assert "deid-local Chat" in home_response.get_data(as_text=True)

    chat_response = client.post("/chat", json={"message": "hello"})
    assert chat_response.status_code == 200
    assert chat_response.get_json() == {"response": "reply-1"}
    assert provider.prompts[0].endswith("USER:\nhello\n\nASSISTANT:")

    second_response = client.post("/chat", json={"message": "again"})
    assert second_response.status_code == 200
    assert "ASSISTANT:\nreply-1" in provider.prompts[1]

    clear_response = client.post("/clear")
    assert clear_response.status_code == 200
    assert clear_response.get_json() == {"status": "cleared"}
    assert session.turns == ()

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.get_json() == {"status": "ok"}

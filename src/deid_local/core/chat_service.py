"""Local browser chat service used for smoke testing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from deid_local.adapters.llm.base import LLMProvider, LLMRequest


@dataclass(frozen=True, slots=True)
class ChatTurn:
    """Single process-local chat turn."""

    role: str
    content: str


class ChatSession:
    """In-memory chat history with deterministic prompt formatting."""

    def __init__(self, *, max_turns: int = 20) -> None:
        self.max_turns = max_turns
        self._turns: list[ChatTurn] = []

    @property
    def turns(self) -> tuple[ChatTurn, ...]:
        return tuple(self._turns)

    def add_turn(self, role: str, content: str) -> None:
        normalized = content.strip()
        if not normalized:
            return
        self._turns.append(ChatTurn(role=role, content=normalized))
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns :]

    def clear(self) -> None:
        self._turns.clear()

    def format_prompt(self, message: str) -> str:
        normalized = message.strip()
        sections = [f"{turn.role.upper()}:\n{turn.content}" for turn in self._turns]
        sections.append(f"USER:\n{normalized}")
        sections.append("ASSISTANT:")
        return "\n\n".join(sections)


def create_chat_app(
    provider: LLMProvider,
    *,
    system_prompt: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    session: ChatSession | None = None,
) -> Any:
    """Create a Flask app that serves a local single-user chat window."""

    flask = _import_flask()
    chat_session = session or ChatSession()
    app = flask["Flask"](__name__)

    @app.get("/")
    def home() -> str:
        return flask["render_template_string"](_CHAT_TEMPLATE)

    @app.post("/chat")
    def chat():
        payload = flask["request"].get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        if not message:
            return flask["jsonify"]({"error": "message is required"}), 400
        prompt = chat_session.format_prompt(message)
        response = provider.infer(
            LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        )
        chat_session.add_turn("user", message)
        chat_session.add_turn("assistant", response.text)
        return flask["jsonify"]({"response": response.text})

    @app.post("/clear")
    def clear():
        chat_session.clear()
        return flask["jsonify"]({"status": "cleared"})

    @app.get("/health")
    def health():
        return flask["jsonify"]({"status": "ok"})

    return app


def _import_flask() -> dict[str, Callable[..., Any] | Any]:
    try:
        from flask import Flask, jsonify, render_template_string, request
    except ImportError as exc:  # pragma: no cover - exercised via runtime behavior
        raise RuntimeError("Flask is not installed. Install the optional `chat` extra.") from exc
    return {
        "Flask": Flask,
        "jsonify": jsonify,
        "render_template_string": render_template_string,
        "request": request,
    }


_CHAT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>deid-local Chat</title>
    <style>
      body {
        font-family: monospace;
        margin: 2rem auto;
        max-width: 48rem;
        padding: 0 1rem;
      }
      #chatbox {
        border: 1px solid #444;
        min-height: 20rem;
        padding: 1rem;
        margin-bottom: 1rem;
        overflow-y: auto;
        white-space: pre-wrap;
      }
      .controls {
        display: flex;
        gap: 0.5rem;
      }
      input {
        flex: 1;
        padding: 0.75rem;
      }
      button {
        padding: 0.75rem 1rem;
      }
    </style>
  </head>
  <body>
    <h1>deid-local Chat</h1>
    <div id="chatbox"></div>
    <div class="controls">
      <input id="userInput" type="text" placeholder="Type your message">
      <button id="sendButton">Send</button>
      <button id="clearButton">Clear</button>
    </div>
    <script>
      const chatbox = document.getElementById("chatbox");
      const userInput = document.getElementById("userInput");
      const sendButton = document.getElementById("sendButton");
      const clearButton = document.getElementById("clearButton");

      function appendMessage(role, content) {
        chatbox.textContent += `${role}: ${content}\n\n`;
        chatbox.scrollTop = chatbox.scrollHeight;
      }

      async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) {
          return;
        }
        appendMessage("You", message);
        userInput.value = "";
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message })
        });
        const payload = await response.json();
        if (payload.response) {
          appendMessage("Assistant", payload.response);
        }
      }

      async function clearHistory() {
        await fetch("/clear", { method: "POST" });
        chatbox.textContent = "";
      }

      sendButton.addEventListener("click", sendMessage);
      clearButton.addEventListener("click", clearHistory);
      userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
          sendMessage();
        }
      });
    </script>
  </body>
</html>
"""

from deid_local.core.chat_service import ChatSession


def test_chat_session_formats_history_deterministically() -> None:
    session = ChatSession()
    session.add_turn("user", "first question")
    session.add_turn("assistant", "first answer")

    prompt = session.format_prompt("second question")

    assert prompt == (
        "USER:\nfirst question\n\nASSISTANT:\nfirst answer\n\nUSER:\nsecond question\n\nASSISTANT:"
    )


def test_chat_session_caps_turn_history() -> None:
    session = ChatSession(max_turns=4)

    for index in range(6):
        session.add_turn("user", f"message {index}")

    assert [turn.content for turn in session.turns] == [
        "message 2",
        "message 3",
        "message 4",
        "message 5",
    ]

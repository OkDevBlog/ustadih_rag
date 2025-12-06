import types
import pytest
from types import SimpleNamespace

from app.tutoring.routes import ask_question
from app.schemas import TutoringSessionQuestion


class FakeQuery:
    def __init__(self, row):
        self._row = row

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._row


class FakeDB:
    def __init__(self, row):
        self._row = row
        self.committed = False

    def query(self, model):
        return FakeQuery(self._row)

    def commit(self):
        self.committed = True


class FakePipeline:
    def __init__(self, answer_markdown):
        self._answer_markdown = answer_markdown

    def answer_question(self, query, subject=None, user_id=None):
        return {
            "query": query,
            "answer": "plain text fallback",
            "answer_markdown": self._answer_markdown,
            "sources": [{"type": "study_material", "id": "mat1", "title": "Mat 1"}],
            "retrieved_context": {}
        }


@pytest.fixture(autouse=True)
def patch_get_rag_pipeline(monkeypatch):
    # Patch the get_rag_pipeline function in the module to return our fake pipeline
    import app.rag.pipeline as pipeline_mod
    import app.tutoring.routes as tutoring_mod

    def _get():
        return FakePipeline(answer_markdown="# Heading\nThis is **markdown** answer")

    # Patch both the pipeline module and the tutoring routes' reference
    monkeypatch.setattr(pipeline_mod, "get_rag_pipeline", _get)
    monkeypatch.setattr(tutoring_mod, "get_rag_pipeline", _get)
    yield


def test_answer_markdown_stored_and_returned():
    session_id = "ts_test_123"
    user_id = "user_1"

    # Create a fake tutoring session row
    fake_row = SimpleNamespace(
        id=session_id,
        user_id=user_id,
        messages=[],
        materials_used=[],
        subject="Science",
        topic="Photosynthesis"
    )

    fake_db = FakeDB(fake_row)

    # Provide a question with markdown
    q = TutoringSessionQuestion(message="plain question", message_markdown="**ما هو الضوء؟**")

    # Call the route function directly
    result = ask_question(session_id=session_id, question_data=q, user_id=user_id, db=fake_db)

    # Validate returned structure contains answer_markdown
    assert result.answer_markdown is not None
    assert "# Heading" in result.answer_markdown

    # Validate session messages stored the assistant markdown
    assert isinstance(fake_row.messages, list)
    # last message should be assistant
    assistant_msg = fake_row.messages[-1]
    assert assistant_msg.get("content_markdown") == result.answer_markdown

    # Validate materials_used updated
    assert "mat1" in fake_row.materials_used

    # Validate DB commit called
    assert fake_db.committed is True

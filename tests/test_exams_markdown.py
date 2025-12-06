import pytest
from types import SimpleNamespace
from app.exams.routes import add_question_to_exam, add_ministry_question
from app.schemas import QuestionCreate, MinistryQuestionCreate


class FakeQuery:
    def __init__(self, row):
        self._row = row

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._row


class FakeDB:
    def __init__(self, exam_row=None):
        self.exam_row = exam_row
        self.added = []
        self.committed = False

    def query(self, model):
        # Return exam row when querying Exam, otherwise a simple no-op
        return FakeQuery(self.exam_row)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        # Simulate DB assigning timestamps
        try:
            import datetime
            if not getattr(obj, 'created_at', None):
                obj.created_at = datetime.datetime.utcnow()
            obj.updated_at = datetime.datetime.utcnow()
        except Exception:
            pass


def make_fake_exam():
    return SimpleNamespace(id='exam_1', title='Test Exam', total_questions=0)


def test_add_question_to_exam_accepts_markdown():
    fake_exam = make_fake_exam()
    fake_db = FakeDB(exam_row=fake_exam)

    qdata = QuestionCreate(
        question_text='plain text',
        answer_text='plain answer',
        topic='Biology',
        subject='Science',
        question_type='short_answer',
        difficulty_level='intermediate',
        question_markdown='# سؤال: ما هو الضوء؟',
        answer_markdown='### الجواب\nالضوء هو...'
    )

    result = add_question_to_exam(exam_id='exam_1', question_data=qdata, user_id='admin', db=fake_db)

    # The route returns a Question ORM-like object; ensure markdown was preferred
    assert hasattr(result, 'question_text')
    assert result.question_text.startswith('# سؤال')
    # Transient attribute should be set for response
    assert getattr(result, 'question_markdown', None) is not None
    assert getattr(result, 'answer_markdown', None) is not None
    assert fake_db.committed is True


def test_add_ministry_question_accepts_markdown():
    fake_db = FakeDB()

    mqdata = MinistryQuestionCreate(
        subject='Physics',
        grade='12',
        year=2024,
        session='first',
        question_text='plain question',
        answer_key='plain answer',
        question_markdown='**ما هو الضوء؟**',
        answer_key_markdown='الضوء هو...'
    )

    result = add_ministry_question(question_data=mqdata, user_id='admin', db=fake_db)

    assert hasattr(result, 'question_text')
    assert result.question_text.startswith('**ما هو')
    assert getattr(result, 'question_markdown', None) is not None
    assert getattr(result, 'answer_key_markdown', None) is not None
    assert fake_db.committed is True

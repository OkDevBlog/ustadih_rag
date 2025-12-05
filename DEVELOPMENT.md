# Ustadih RAG - Development Guide

This guide provides instructions for developers working on the Ustadih RAG system.

## Project Structure

```
ustadih_rag/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app setup and routing
│   ├── config.py                 # Configuration management
│   ├── schemas.py                # Pydantic validation models
│   ├── auth/                     # Authentication module
│   │   ├── routes.py            # Auth endpoints
│   │   └── google_oauth.py       # OAuth configuration
│   ├── core/                     # Core utilities
│   │   └── security.py           # JWT and password utilities
│   ├── db/                       # Database layer
│   │   ├── models.py            # SQLAlchemy models
│   │   └── session.py           # Database connection setup
│   ├── rag/                      # RAG (Retrieval-Augmented Generation)
│   │   ├── embeddings.py        # Embedding service
│   │   ├── vector_store.py      # ChromaDB management
│   │   └── pipeline.py          # RAG pipeline with Gemini
│   ├── users/                    # User management
│   │   └── routes.py            # User endpoints
│   ├── tutoring/                 # Tutoring system
│   │   └── routes.py            # Tutoring endpoints
│   └── exams/                    # Exam management
│       └── routes.py            # Exam endpoints
├── .env                          # Environment variables (create this)
├── .env.example                  # Example environment file
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
├── GEMINI.md                     # Gemini AI integration guide
├── verify_setup.py               # Setup verification script
└── devserver.sh                  # Development server startup
```

## Development Setup

### 1. Initial Setup
```bash
# Clone and navigate
cd ustadih_rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 2. Database Setup
```bash
# Create tables (first time only)
python -c "from app.db.models import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"

# Verify connection
python verify_setup.py
```

### 3. Run Development Server
```bash
# With auto-reload
uvicorn app.main:app --reload

# Manual reload
uvicorn app.main:app

# Specify port
uvicorn app.main:app --port 8001
```

## Module Organization

### Authentication (`app/auth/`)
- Handles Google OAuth flow
- Generates and manages JWT tokens
- Endpoints: `/auth/google/login`, `/auth/google/callback`

**Key files to modify for additional auth:**
- `google_oauth.py` - Add new OAuth providers here
- `routes.py` - Add new auth endpoints

### RAG System (`app/rag/`)

#### `vector_store.py`
- Manages ChromaDB collections
- Handles document storage and retrieval
- Methods:
  - `add_study_material()` - Add educational content
  - `search_study_materials()` - Semantic search
  - `add_question()` - Add exam questions
  - `search_questions()` - Search questions

#### `embeddings.py`
- Sentence-Transformer embedding service
- Methods:
  - `embed_text()` - Single text embedding
  - `embed_texts()` - Batch embedding
  - `semantic_similarity()` - Calculate similarity
  - `chunk_text()` - Split text into chunks

#### `pipeline.py`
- Complete RAG workflow
- Integrates Gemini AI
- Methods:
  - `retrieve_context()` - Get relevant materials
  - `generate_response()` - Generate LLM response
  - `answer_question()` - Full RAG pipeline

### Database Models (`app/db/models.py`)

**User** - Student accounts
```python
User(
    id: str,
    email: str,
    full_name: str,
    google_id: str (optional),
    is_active: bool,
    created_at: datetime,
    updated_at: datetime
)
```

**StudyMaterial** - Educational content
```python
StudyMaterial(
    id: str,
    title: str,
    content: str,
    topic: str,
    subject: str,
    difficulty_level: str,
    chromadb_id: str (vector store reference)
)
```

**Question** - Exam questions
```python
Question(
    id: str,
    exam_id: str (foreign key),
    question_text: str,
    answer_text: str,
    question_type: str,  # multiple_choice, short_answer, essay
    topic: str,
    subject: str,
    difficulty_level: str,
    options: JSON,  # For multiple choice
    correct_option: str
)
```

**Exam** - Exam definitions
```python
Exam(
    id: str,
    title: str,
    subject: str,
    grade_level: str,
    total_questions: int,
    total_time_minutes: int,
    passing_score: float,
    instructions: str
)
```

**ExamAttempt** - Student exam submissions
```python
ExamAttempt(
    id: str,
    user_id: str (foreign key),
    exam_id: str (foreign key),
    score: float,
    answers: JSON,  # {question_id: answer}
    is_completed: bool,
    submitted_at: datetime
)
```

**TutoringSession** - Chat/tutoring sessions
```python
TutoringSession(
    id: str,
    user_id: str (foreign key),
    topic: str,
    subject: str,
    messages: JSON,  # Chat history
    materials_used: JSON,  # Referenced materials
    rating: int (1-5)
)
```

## API Development

### Adding a New Endpoint

1. **Define schema in `app/schemas.py`:**
```python
class NewFeatureRequest(BaseModel):
    field1: str
    field2: int = Field(default=0, gt=0)

class NewFeatureResponse(BaseModel):
    id: str
    field1: str
    field2: int
```

2. **Add route in appropriate module:**
```python
from fastapi import APIRouter, Depends, HTTPException
from app.db.session import SessionLocal

router = APIRouter()

@router.post("/endpoint", response_model=NewFeatureResponse)
def create_feature(
    data: NewFeatureRequest,
    db: Session = Depends(get_db)
):
    """Create a new feature."""
    # Implementation
    return {"id": "...", "field1": data.field1, "field2": data.field2}
```

3. **Register in `app/main.py`:**
```python
app.include_router(router, prefix="/module", tags=["module"])
```

### Query Parameters
```python
@router.get("/items")
def list_items(
    skip: int = 0,
    limit: int = 10,
    subject: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Item)
    if subject:
        query = query.filter(Item.subject == subject)
    return query.offset(skip).limit(limit).all()
```

## Security

### Adding Authentication
```python
from app.core.security import verify_token

def get_current_user(token: str = Header(...)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401)
    return payload.get("sub")

@router.get("/protected")
def protected_route(user_id: str = Depends(get_current_user)):
    return {"user": user_id}
```

### Password Hashing
```python
from app.core.security import hash_password, verify_password

# Hash password
hashed = hash_password("plaintext_password")

# Verify password
if verify_password("plaintext_password", hashed):
    # Correct
```

## Testing RAG

### Test Vector Store
```python
from app.rag.vector_store import get_vector_store

vs = get_vector_store()
# Add material
vs.add_study_material(
    "mat_1",
    "Photosynthesis is...",
    {"topic": "Biology", "subject": "Science"}
)
# Search
results = vs.search_study_materials("photosynthesis", top_k=3)
```

### Test Embeddings
```python
from app.rag.embeddings import get_embedding_service

embed = get_embedding_service()
# Single embedding
vec = embed.embed_text("What is machine learning?")
# Similarity
sim = embed.semantic_similarity("ML is AI", "Machine learning is artificial intelligence")
```

### Test RAG Pipeline
```python
from app.rag.pipeline import get_rag_pipeline

pipeline = get_rag_pipeline()
# Answer question
result = pipeline.answer_question(
    query="What is photosynthesis?",
    subject="Science"
)
print(result["answer"])
```

## Common Tasks

### Add Study Material
```python
from app.rag.pipeline import get_rag_pipeline

pipeline = get_rag_pipeline()
pipeline.add_study_material(
    material_id="bio_001",
    title="Photosynthesis Basics",
    content="Photosynthesis is the process...",
    topic="Photosynthesis",
    subject="Biology"
)
```

### Create Exam
```python
# Via API
POST /exams/ 
{
    "title": "Biology Final Exam",
    "subject": "Biology",
    "grade_level": "Grade 10",
    "total_time_minutes": 90,
    "passing_score": 60
}
```

### Add Exam Question
```python
POST /exams/{exam_id}/questions
{
    "question_text": "What is photosynthesis?",
    "answer_text": "Process of converting light to chemical energy",
    "question_type": "short_answer",
    "topic": "Photosynthesis",
    "subject": "Biology"
}
```

### Start Tutoring Session
```python
POST /tutoring/sessions/start
{
    "topic": "Photosynthesis",
    "subject": "Biology",
    "title": "Learning Photosynthesis"
}
```

## Debugging

### Enable SQL Logging
```python
# In app/db/session.py
from sqlalchemy import event
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Check ChromaDB
```bash
# View ChromaDB data
ls -la ./chromadb_data/

# Python check
from app.rag.vector_store import get_vector_store
vs = get_vector_store()
print(vs.study_materials_collection.count())
```

### API Testing
```bash
# Using curl
curl -X GET "http://localhost:8000/health"

# Using Python requests
import requests
response = requests.get("http://localhost:8000/health")
print(response.json())
```

## Performance Tips

1. **Database Indexing:** Add indexes to frequently searched fields
2. **Caching:** Implement Redis for session storage
3. **Batch Operations:** Process multiple embeddings at once
4. **Connection Pooling:** Configure in `app/db/session.py`
5. **Pagination:** Always limit list endpoints

## Deployment Considerations

- Set `DEBUG=False` in production
- Use strong `SECRET_KEY`
- Configure restrictive CORS
- Enable HTTPS
- Set up monitoring (logs, errors, metrics)
- Use environment-specific `.env` files
- Implement rate limiting
- Set up backup strategy for PostgreSQL

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Google Generative AI](https://ai.google.dev/)

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test
3. Commit with clear messages
4. Push and create pull request
5. Wait for review

---

Happy coding! 🚀

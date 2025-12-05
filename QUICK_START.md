# Ustadih RAG - Quick Reference Guide

## 🚀 Getting Started (5 minutes)

### 1. Install & Configure
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env (already created, verify contents)
cat .env

# Verify setup
python verify_setup.py
```

### 2. Start Server
```bash
uvicorn app.main:app --reload
```

### 3. Access API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Root**: http://localhost:8000/

## 📚 Core Concepts

### RAG (Retrieval-Augmented Generation)
1. **Retrieve**: Search ChromaDB for relevant materials
2. **Augment**: Add context to prompt
3. **Generate**: Use Gemini AI to create response

### Data Flow
```
User Question
    ↓
Embedding Service (Sentence-Transformers)
    ↓
Vector Search (ChromaDB)
    ↓
Retrieval Results
    ↓
Prompt Augmentation
    ↓
Gemini AI Generation
    ↓
Response to User
```

## 🎯 Quick API Examples

### Start Tutoring Session
```bash
curl -X POST http://localhost:8000/tutoring/sessions/start \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Photosynthesis",
    "subject": "Biology"
  }'
```

### Ask a Question (RAG)
```bash
curl -X POST http://localhost:8000/tutoring/sessions/{session_id}/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is photosynthesis?",
    "subject": "Biology"
  }'
```

### Create Exam
```bash
curl -X POST http://localhost:8000/exams/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Biology Quiz",
    "subject": "Biology",
    "grade_level": "Grade 10",
    "passing_score": 60
  }'
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | Configuration & secrets |
| `app/main.py` | FastAPI app setup |
| `app/db/models.py` | Database schemas |
| `app/rag/pipeline.py` | RAG workflow |
| `app/rag/vector_store.py` | ChromaDB management |
| `app/auth/routes.py` | Authentication |
| `README.md` | Full documentation |
| `verify_setup.py` | Setup verification |

## 🔑 Configuration Keys

```env
DATABASE_URL=...           # PostgreSQL connection
SECRET_KEY=...             # JWT signing key
GOOGLE_CLIENT_ID=...       # OAuth credentials
GOOGLE_CLIENT_SECRET=...   # OAuth credentials
GEMINI_API_KEY=...         # Gemini AI key
```

## 🧪 Testing Components

### Test RAG Pipeline
```python
from app.rag.pipeline import get_rag_pipeline

pipeline = get_rag_pipeline()
result = pipeline.answer_question("What is AI?", subject="Computer Science")
print(result["answer"])
```

### Test Vector Store
```python
from app.rag.vector_store import get_vector_store

vs = get_vector_store()
vs.add_study_material("mat_1", "AI is...", {"topic": "AI"})
results = vs.search_study_materials("artificial intelligence")
```

### Test Embeddings
```python
from app.rag.embeddings import get_embedding_service

embed = get_embedding_service()
similarity = embed.semantic_similarity("ML is AI", "Machine learning")
print(similarity)  # 0.0 to 1.0
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Database connection fails | Check `DATABASE_URL` in `.env` and PostgreSQL running |
| RAG not working | Verify `GEMINI_API_KEY` in `.env` |
| ChromaDB errors | Run `rm -rf ./chromadb_data && python verify_setup.py` |
| Port 8000 in use | Run on different port: `uvicorn app.main:app --port 8001` |

## 📊 Database

### Create Tables
```bash
python -c "from app.db.models import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"
```

### Check Connection
```bash
python -c "from app.db.session import engine; print(engine.url)"
```

## 🔐 Security

- Never commit `.env` to git
- Rotate `SECRET_KEY` regularly
- Use HTTPS in production
- Set `DEBUG=False` in production

## 📞 Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/google/login` | OAuth login |
| POST | `/tutoring/sessions/start` | Start tutoring |
| POST | `/tutoring/sessions/{id}/ask` | Ask question (RAG) |
| POST | `/exams/` | Create exam |
| POST | `/exams/{id}/attempts/start` | Start exam |
| GET | `/users/{id}` | Get profile |
| GET | `/health` | Health check |

## 🎓 Learning Path

1. Read `README.md` - Overview
2. Run `verify_setup.py` - Check setup
3. Read `DEVELOPMENT.md` - Code structure
4. Try API examples above
5. Read `GEMINI.md` - RAG details
6. Explore source code

## 🚀 Next Steps

- [ ] Add study materials to RAG
- [ ] Create test exam
- [ ] Test tutoring with RAG
- [ ] Monitor performance
- [ ] Set up logging
- [ ] Configure deployment

## 📝 Common Tasks

### Add Study Material
```bash
# Via database insert or API
POST /materials/
{
    "title": "Photosynthesis",
    "content": "Photosynthesis is...",
    "topic": "Photosynthesis",
    "subject": "Biology"
}
```

### Get User Progress
```bash
curl http://localhost:8000/users/{user_id}/learning-progress
```

### List Exams
```bash
curl http://localhost:8000/exams/?subject=Biology
```

## 🏆 Project Highlights

✅ Complete RAG system with Gemini AI  
✅ Full exam management  
✅ User authentication with OAuth  
✅ Learning progress tracking  
✅ Comprehensive API (30+ endpoints)  
✅ Production-ready code  
✅ Extensive documentation  

## 📖 Documentation Files

- `README.md` - Main documentation
- `GEMINI.md` - Gemini AI integration
- `DEVELOPMENT.md` - Development guide
- `IMPLEMENTATION_SUMMARY.md` - What was built
- This file - Quick reference

## 💡 Pro Tips

1. Use Swagger UI (`/docs`) to explore and test APIs
2. Enable SQL logging for debugging database queries
3. Check `verify_setup.py` before troubleshooting
4. Review ChromaDB data: `ls -la ./chromadb_data/`
5. Use `git` to track changes during development

## 🔗 Useful Links

- FastAPI Docs: https://fastapi.tiangolo.com/
- ChromaDB: https://docs.trychroma.com/
- Gemini API: https://ai.google.dev/
- SQLAlchemy: https://docs.sqlalchemy.org/

---

**Ready to build? Start with:** `uvicorn app.main:app --reload` 🚀

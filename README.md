# Ustadih RAG - Educational AI Tutor for Iraqi Students

An intelligent tutoring system powered by Retrieval-Augmented Generation (RAG) technology, designed to provide personalized learning experiences for Iraqi students. The system combines FastAPI, PostgreSQL, ChromaDB, and Google Gemini AI to deliver context-aware tutoring, exam management, and progress tracking.

## 🎯 Features

### Core Functionality
- **RAG-Powered Tutoring**: Intelligent Q&A system that retrieves relevant study materials and generates contextual answers
- **Exam Management**: Create, manage, and take exams with automatic scoring and feedback
- **Progress Tracking**: Monitor learning progress with detailed statistics and analytics
- **Study Materials Management**: Upload and organize educational content by subject and topic
- **Tutoring Sessions**: Interactive tutoring sessions with chat history and resource tracking
- **Multi-subject Support**: Support for various subjects with difficulty levels

### Authentication
- **Google OAuth**: Secure authentication via Google accounts
- **JWT Tokens**: Session management with JWT-based access tokens
- **User Profiles**: User profile management and preferences

### Technical Stack
- **Backend Framework**: FastAPI (Python)
- **Database**: PostgreSQL for structured data
- **Vector Store**: ChromaDB for embeddings and semantic search
- **Embeddings**: Sentence-Transformers (multilingual - Arabic/English)
- **LLM**: Google Gemini AI for response generation
- **Authentication**: OAuth2 with JWT

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Google Cloud credentials (for Gemini API)
- Google OAuth credentials

### Installation

1. **Navigate to project directory**
```bash
cd ustadih_rag
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the project root:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ustadih_db

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# LLM Provider
GEMINI_API_KEY=your-gemini-api-key

# Application
APP_ENV=development
DEBUG=True
```

5. **Initialize database**
```bash
python -c "from app.db.models import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"
```

6. **Run the development server**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Auto-generated Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication Endpoints
```
POST   /auth/google/login           - Initiate Google OAuth login
GET    /auth/google/callback         - OAuth callback handler
POST   /auth/token                   - Get access token (for testing)
GET    /auth/ping                    - Health check
```

### User Management
```
GET    /users/{user_id}                      - Get user profile
PUT    /users/{user_id}                      - Update user profile
GET    /users/{user_id}/learning-progress    - Get progress statistics
GET    /users/{user_id}/exam-history         - Get exam attempt history
GET    /users/{user_id}/tutoring-history     - Get tutoring session history
DELETE /users/{user_id}                      - Delete user account
GET    /users/ping                           - Health check
```

### Tutoring Endpoints
```
POST   /tutoring/sessions/start                  - Start new tutoring session
POST   /tutoring/sessions/{session_id}/ask       - Ask a question (RAG-powered)
GET    /tutoring/sessions/{session_id}          - Get session details
GET    /tutoring/sessions                       - List user's sessions
POST   /tutoring/sessions/{session_id}/rate     - Rate a session
DELETE /tutoring/sessions/{session_id}          - Delete a session
GET    /tutoring/ping                           - Health check
```

### Exam Endpoints
```
POST   /exams/                                    - Create exam
GET    /exams/                                    - List exams
GET    /exams/{exam_id}                           - Get exam details
POST   /exams/{exam_id}/questions                 - Add question
GET    /exams/{exam_id}/questions                 - Get questions
POST   /exams/{exam_id}/attempts/start            - Start exam
POST   /exams/{exam_id}/attempts/{attempt_id}/submit  - Submit answers
GET    /exams/{exam_id}/attempts/{attempt_id}    - Get results
GET    /exams/user/{user_id}/attempts            - Get user attempts
POST   /exams/{exam_id}/attempts/{attempt_id}/retake - Retake exam
GET    /exams/ping                               - Health check
```

## 🏗️ Architecture

### Data Models
- **User**: Student profiles with authentication
- **StudyMaterial**: Educational content indexed for RAG
- **Question**: Exam questions with metadata
- **Exam**: Exam definitions and structure
- **ExamAttempt**: Student exam attempts with scores
- **TutoringSession**: Interactive tutoring sessions

### RAG Pipeline
1. **Retrieval**: Semantic search in ChromaDB for relevant materials
2. **Augmentation**: Format context for LLM consumption
3. **Generation**: Use Google Gemini to generate contextual responses

### Vector Store
- ChromaDB collections for study materials and questions
- Cosine similarity search for semantic relevance
- Persistent storage with metadata filtering

## 🔐 Security Features

- Environment-based configuration (no hardcoded secrets)
- Password hashing with bcrypt
- JWT token verification
- CORS middleware configuration
- Google OAuth integration
- Pydantic input validation

## 📊 Data Persistence

- **PostgreSQL**: Structured data (users, exams, attempts, sessions)
- **ChromaDB**: Vector embeddings for semantic search
- **JSON Storage**: Session chat history and structured data

## 🌍 Multilingual Support

- Arabic and English support
- Multilingual embeddings (multilingual-MiniLM-L12-v2)
- Bilingual LLM responses

## 🔧 Configuration

### Environment Variables
See `.env` file template in Quick Start section

### Database Configuration
Modify connection settings in `app/db/session.py`

### RAG Settings
Tune parameters in `app/rag/pipeline.py`:
- Retrieval parameters (top_k results)
- Embedding model selection
- LLM provider configuration

## 🚀 Deployment

### Docker
```bash
docker build -t ustadih-rag .
docker run -p 8000:8000 --env-file .env ustadih-rag
```

### Google Cloud Run
```bash
gcloud run deploy ustadih-rag --source . --allow-unauthenticated
```

### Production Checklist
- [ ] Strong `SECRET_KEY` configured
- [ ] Production PostgreSQL instance
- [ ] Restrictive CORS origins
- [ ] HTTPS enabled
- [ ] Monitoring and logging setup
- [ ] Rate limiting configured
- [ ] Error tracking (Sentry)

## 📈 Performance

- Database connection pooling
- Embedding caching in ChromaDB
- Pagination on list endpoints
- Efficient async/await patterns

## 🐛 Troubleshooting

### Database Issues
```bash
python -c "from app.db.session import engine; print(engine.url)"
```

### ChromaDB Initialization
```bash
rm -rf ./chromadb_data
python -c "from app.rag.vector_store import get_vector_store; get_vector_store()"
```

### RAG Issues
- Verify Gemini API key in `.env`
- Check study materials in vector store
- Review ChromaDB logs

## 📝 Development

### Adding Features
1. Define models in `app/db/models.py`
2. Create schemas in `app/schemas.py`
3. Implement routes in module `routes.py`
4. Add tests

### RAG Tuning
1. Adjust retrieval parameters
2. Try different embedding models
3. Implement custom chunking strategies

## 📞 Support

Open issues on the repository for bugs and feature requests.

## 📄 License

MIT License

---

**Ustadih RAG** - Your intelligent educational companion 🎓

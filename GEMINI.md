# Google Gemini AI Integration for Ustadih RAG

This document outlines the integration of Google Gemini AI with the Ustadih RAG tutoring system.

## 🤖 Overview

Ustadih RAG uses Google Gemini AI (specifically `gemini-pro` model) to generate intelligent, context-aware responses for student queries. The system retrieves relevant study materials using ChromaDB's semantic search, then augments the LLM prompt with this context to provide accurate, grounded responses.

## 🔧 Setup

### 1. Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key" 
3. Copy the generated key

### 2. Configure Environment

Add to `.env` file:
```env
GEMINI_API_KEY=your-api-key-here
```

The configuration is automatically loaded in `app/config.py` via pydantic-settings.

## 📝 Integration Points

### RAG Pipeline (`app/rag/pipeline.py`)

The `RAGPipeline` class handles Gemini integration:

```python
from app.rag.pipeline import get_rag_pipeline

# Get pipeline instance
pipeline = get_rag_pipeline()

# Answer a question with RAG
result = pipeline.answer_question(
    query="What is photosynthesis?",
    subject="Biology",
    user_id="user_123"
)
```

### Prompt Structure

The system constructs prompts in three parts:

1. **System Prompt**: Defines Gemini's role as an educational tutor
2. **Context**: Retrieved study materials and reference questions
3. **User Query**: The student's actual question

Example:
```
System: You are an expert educational tutor for Iraqi students...

CONTEXT FROM STUDY MATERIALS:
=== STUDY MATERIALS ===
Topic: Photosynthesis
Content: Photosynthesis is the process by which plants...

=== REFERENCE QUESTIONS & ANSWERS ===
Q: What is the role of chlorophyll?...

STUDENT QUESTION:
What is photosynthesis?

RESPONSE:
```

## 🎓 Educational Features

### 1. Context-Aware Responses
- Retrieves 5 relevant study materials by default
- Includes 3 reference questions for additional context
- Grounds responses in curriculum materials

### 2. Bilingual Support
- Supports Arabic and English questions
- Responds in appropriate language
- Uses multilingual embeddings for search

### 3. Adaptive Difficulty
- Questions tagged with difficulty levels
- Responses can be calibrated per student level
- Supports various subject areas

## 📊 Supported Subjects

The system can handle questions across:
- Mathematics (الرياضيات)
- Science (العلوم) - Physics, Chemistry, Biology
- English Language (اللغة الإنجليزية)
- Arabic Language (اللغة العربية)
- Social Studies (الدراسات الاجتماعية)
- History (التاريخ)
- And more...

## 🔍 Retrieval Strategy

### Vector Store Collections

1. **Study Materials** (`study_materials`)
   - Content: Full educational text
   - Metadata: topic, subject, difficulty, title

2. **Questions** (`questions`)
   - Content: Question + Answer combined
   - Metadata: Question text, answer, topic, subject, type

### Search Parameters

```python
# Customize retrieval
context = pipeline.retrieve_context(
    query="سؤالك هنا",  # Arabic or English
    subject="Mathematics",
    top_k=5  # Number of results
)
```

## 🛡️ Error Handling

### Fallback Responses

If Gemini API fails:
1. System automatically provides fallback response
2. Uses top retrieved materials directly
3. Informs student of limitation

```python
def _generate_fallback_response(self, query: str, context: Dict) -> str:
    # Returns response based on retrieved materials only
```

### Common Issues

| Issue | Solution |
|-------|----------|
| API Key invalid | Verify key in `.env` and Google AI Console |
| Rate limited | Implement caching layer or upgrade API tier |
| No materials found | Add more study materials to vector store |
| Poor response quality | Refine system prompt or add more context |

## 📈 Performance Optimization

### 1. Caching
- ChromaDB caches embeddings
- Avoid re-encoding identical queries
- Reduce API calls with response caching

### 2. Batch Processing
- Process multiple questions efficiently
- Use batch embedding for bulk content uploads
- Implement async processing for scalability

### 3. Resource Management
```python
# Load embedding model once (singleton pattern)
embedding_service = get_embedding_service()

# Use global pipeline instance
pipeline = get_rag_pipeline()
```

## 🔐 Security & Compliance

### API Key Management
- Never commit `.env` to version control
- Rotate keys regularly in production
- Use separate keys for dev/staging/production

### Data Privacy
- Student queries are sent to Gemini
- Configure request retention settings in Google Cloud Console
- Comply with GDPR/data protection requirements

### Content Safety
- Gemini has built-in safety filters
- System enforces educational content guidelines
- Logs all interactions for audit trail

## 💡 Customization

### Custom System Prompts

Override system prompt for specific use cases:

```python
custom_prompt = """You are a specialized math tutor for Iraqi high school students.
Focus on step-by-step problem solving.
Explain concepts in Arabic when students ask in Arabic.
Use real-world examples relevant to Iraqi context."""

response = pipeline.generate_response(
    query="كيف أحل هذه المسألة؟",
    context=context,
    system_prompt=custom_prompt
)
```

### Model Selection

Switch between Gemini models:

```python
# In app/rag/pipeline.py, modify:
self.model = genai.GenerativeModel('gemini-pro-vision')  # For multimodal
self.model = genai.GenerativeModel('gemini-ultra')        # For advanced
```

### Adding New Subjects

1. Add subject metadata to study materials
2. Update retrieval filters
3. Create subject-specific prompts

## 🚀 Advanced Features

### 1. Exam Question Generation
```python
# Generate practice questions based on materials
questions = pipeline.generate_exam_questions(
    topic="Photosynthesis",
    difficulty="intermediate",
    count=5
)
```

### 2. Student Progress Analysis
```python
# Analyze learning patterns
analysis = pipeline.analyze_student_progress(
    user_id="user_123",
    time_period="month"
)
```

### 3. Content Recommendations
```python
# Recommend materials based on weak areas
recommendations = pipeline.get_recommendations(
    user_id="user_123"
)
```

## 📚 Learning Resources

- [Google Generative AI Documentation](https://ai.google.dev/)
- [Gemini API Quickstart](https://ai.google.dev/tutorials/quickstart)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers Guide](https://www.sbert.net/)

## 🤝 Contributing

To improve Gemini integration:

1. Test with diverse student queries
2. Collect feedback on response quality
3. Refine system prompts based on results
4. Document improvements

## 📞 Support

For Gemini-specific issues:
- Check [Google AI Help Center](https://support.google.com/ai/)
- Review API status on [Google Cloud Console](https://console.cloud.google.com/)
- Open issues on repository for bugs

## 🔮 Future Enhancements

- [ ] Multi-turn conversational memory
- [ ] Real-time translation support
- [ ] Video content analysis with Gemini Vision
- [ ] Automated curriculum generation
- [ ] Teacher dashboard for content management
- [ ] Integration with additional LLM providers
- [ ] Fine-tuned models for Iraqi curriculum

---

**Last Updated**: December 2024
**Gemini Integration Version**: 1.0.0

"""Minimal test to verify server starts."""
import sys
print("Python:", sys.version)
print("Importing app modules...")

try:
    print("  Importing config...")
    from app.config import settings
    print("    OK")
    
    print("  Importing models...")
    from app.db.models import Exam, MinistryExamAttempt
    print("    OK")
    
    print("  Importing schemas...")
    from app.schemas import MinistryExamAttemptResponse
    print("    OK")
    
    print("  Importing RAG pipeline...")
    from app.rag.pipeline import get_rag_pipeline
    print("    OK")
    
    print("  Getting RAG pipeline instance...")
    pipeline = get_rag_pipeline()
    print("    OK - pipeline created")
    
    print("  Testing grade_answer method...")
    result = pipeline.grade_answer(
        question_text="What is 2+2?",
        model_answer="4",
        student_answer="4"
    )
    print(f"    OK - result keys: {list(result.keys())}")
    
    print("\nAll imports and tests passed!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

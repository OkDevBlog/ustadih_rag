"""
Verification script to test Ustadih RAG setup and components.
Run this after installation to verify everything is working.
"""

import sys
import os

def check_imports():
    """Check if all required packages are installed."""
    print("✓ Checking imports...")
    try:
        import fastapi
        import sqlalchemy
        import chromadb
        import sentence_transformers
        import google.generativeai
        import jose
        import passlib
        import pydantic
        print("  ✓ All core packages imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        print("  Run: pip install -r requirements.txt")
        return False


def check_environment():
    """Check environment variables."""
    print("\n✓ Checking environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
    ]
    
    optional_vars = ['GEMINI_API_KEY']
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"  ✓ {var} set")
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"  ✓ {var} set (optional)")
        else:
            print(f"  ⚠ {var} not set (optional for RAG)")
    
    if missing_required:
        print(f"\n  ✗ Missing required variables: {', '.join(missing_required)}")
        print("  Create .env file with required settings")
        return False
    
    return True


def check_database():
    """Check database connection."""
    print("\n✓ Checking database connection...")
    try:
        from app.db.session import engine
        with engine.connect() as connection:
            print("  ✓ PostgreSQL connection successful")
            return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        print("  Verify DATABASE_URL and PostgreSQL is running")
        return False


def check_models():
    """Check database models can be imported."""
    print("\n✓ Checking database models...")
    try:
        from app.db.models import (
            User, StudyMaterial, Question, Exam, 
            ExamAttempt, TutoringSession, Base
        )
        print("  ✓ All models imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Model import failed: {e}")
        return False


def check_rag_components():
    """Check RAG components."""
    print("\n✓ Checking RAG components...")
    try:
        from app.rag.vector_store import get_vector_store
        from app.rag.embeddings import get_embedding_service
        from app.rag.pipeline import get_rag_pipeline
        
        print("  ✓ Vector store initialization...")
        vector_store = get_vector_store()
        
        print("  ✓ Embedding service initialization...")
        embeddings = get_embedding_service()
        
        print("  ✓ RAG pipeline initialization...")
        pipeline = get_rag_pipeline()
        
        print("  ✓ All RAG components loaded successfully")
        return True
    except Exception as e:
        print(f"  ✗ RAG component error: {e}")
        return False


def check_fastapi():
    """Check FastAPI app can be loaded."""
    print("\n✓ Checking FastAPI application...")
    try:
        from app.main import app
        print("  ✓ FastAPI app initialized")
        
        # Check routes are registered
        routes_count = len([r for r in app.routes])
        print(f"  ✓ {routes_count} routes registered")
        
        return True
    except Exception as e:
        print(f"  ✗ FastAPI app error: {e}")
        return False


def check_security():
    """Check security modules."""
    print("\n✓ Checking security modules...")
    try:
        from app.core.security import (
            create_access_token,
            verify_token,
            hash_password,
            verify_password
        )
        
        # Test token creation and verification
        test_data = {"sub": "test_user"}
        token = create_access_token(test_data)
        verified = verify_token(token)
        
        if verified and verified.get("sub") == "test_user":
            print("  ✓ JWT token creation and verification working")
        
        # Test password hashing
        password = "test_password"
        hashed = hash_password(password)
        if verify_password(password, hashed):
            print("  ✓ Password hashing and verification working")
        
        return True
    except Exception as e:
        print(f"  ✗ Security module error: {e}")
        return False


def print_summary(results):
    """Print summary of checks."""
    print("\n" + "="*50)
    print("VERIFICATION SUMMARY")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{check:30} {status}")
    
    print("-"*50)
    print(f"Total: {passed}/{total} checks passed")
    print("="*50)
    
    if passed == total:
        print("\n✓ All checks passed! Your Ustadih RAG setup is ready.")
        print("\nTo start the development server, run:")
        print("  uvicorn app.main:app --reload")
        return 0
    else:
        print(f"\n✗ {total - passed} check(s) failed. Please fix the issues above.")
        return 1


def main():
    """Run all verification checks."""
    print("="*50)
    print("USTADIH RAG SETUP VERIFICATION")
    print("="*50)
    
    results = {}
    
    results["Imports"] = check_imports()
    if not results["Imports"]:
        print("\n✗ Cannot continue without imports. Install dependencies first.")
        return 1
    
    results["Environment"] = check_environment()
    results["Database"] = check_database()
    results["Models"] = check_models()
    results["RAG Components"] = check_rag_components()
    results["Security"] = check_security()
    results["FastAPI"] = check_fastapi()
    
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import re

from app.db.session import SessionLocal
from app.db.models import StudyMaterial
from app.schemas import StudyMaterialUpload, StudyMaterialResponse
from app.rag.pipeline import get_rag_pipeline

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def markdown_to_text(md: str) -> str:
    """Simple markdown -> plain text converter for storing content.

    This removes code fences, inline code, images, links (keeps link text), headings,
    and basic formatting. It's intentionally lightweight to avoid additional deps.
    """
    text = md
    # remove code fences ``` ```
    text = re.sub(r"```[\s\S]*?```", "\n", text)
    # remove inline code `code`
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # replace images ![alt](url) with alt
    text = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", text)
    # replace links [text](url) with text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # remove headings (#, ##...)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # remove emphasis markers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    # collapse multiple newlines
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


@router.post("/materials/upload-markdown", response_model=StudyMaterialResponse)
def upload_markdown_material(
    payload: StudyMaterialUpload,
    user_id: str = None,
    db: Session = Depends(get_db)
):
    """Upload a Markdown document, convert to text, store in ChromaDB and create a StudyMaterial record.

    - `payload.material_id` can be provided to control the stored id; otherwise a new id `mat_<uuid>` is generated.
    - Returns the created `StudyMaterial` record.
    """
    # Basic auth check: ensure user exists if user_id passed (optional flow in this endpoint)
    if user_id:
        from app.db.models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    material_id = payload.material_id or f"mat_{uuid.uuid4().hex[:12]}"

    # Convert markdown to plain text for embedding
    content_text = markdown_to_text(payload.content_markdown)

    pipeline = get_rag_pipeline()
    try:
        chroma_id = pipeline.add_study_material(
            material_id=material_id,
            title=payload.title,
            content=content_text,
            topic=payload.topic,
            subject=payload.subject,
            difficulty=payload.difficulty_level or "intermediate"
        )
    except Exception as e:
        # Catch vector-store/telemetry/internal errors and return a clear 500
        # while logging the original exception for debugging.
        print(f"Error adding material to vector store: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Vector store error: {e}")

    if not chroma_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add material to vector store")

    # Persist StudyMaterial in DB (simpler ORM-only flow)
    try:
        # If a material with this id already exists, update it instead of inserting
        existing = None
        try:
            existing = db.get(StudyMaterial, material_id)
        except Exception:
            # Fallback to query if Session.get isn't available for some reason
            existing = db.query(StudyMaterial).filter(StudyMaterial.id == material_id).first()

        now = __import__('datetime').datetime.utcnow()

        if existing:
            # Prevent accidental overwrite: return 409 Conflict instead of auto-update.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"StudyMaterial with id '{material_id}' already exists. Use update endpoint (PUT) to modify."
            )

        else:
            # Create new record
            study_material = StudyMaterial(
                id=material_id,
                title=payload.title,
                content=content_text,
                topic=payload.topic,
                subject=payload.subject,
                difficulty_level=payload.difficulty_level or "intermediate",
                chromadb_id=chroma_id,
                created_at=now,
                updated_at=now,
            )

            if getattr(payload, 'grade', None) is not None:
                try:
                    study_material.grade = payload.grade
                except Exception:
                    pass

            db.add(study_material)
            try:
                db.commit()
                db.refresh(study_material)
            except Exception as e:
                # Handle race where another transaction inserted the same id
                try:
                    from sqlalchemy.exc import IntegrityError
                except Exception:
                    IntegrityError = None

                if IntegrityError is not None and isinstance(e, IntegrityError):
                    try:
                        db.rollback()
                    except Exception:
                        pass
                    # Fetch the existing row and return it
                    try:
                        existing = db.get(StudyMaterial, material_id)
                    except Exception:
                        existing = db.query(StudyMaterial).filter(StudyMaterial.id == material_id).first()
                    if existing:
                        return existing
                try:
                    db.rollback()
                except Exception:
                    pass
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to persist study material: {e}")

    except HTTPException:
        raise
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to persist study material: {e}")

    return study_material

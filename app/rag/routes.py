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
    added = pipeline.add_study_material(
        material_id=material_id,
        title=payload.title,
        content=content_text,
        topic=payload.topic,
        subject=payload.subject,
        difficulty=payload.difficulty_level or "intermediate"
    )

    if not added:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add material to vector store")

    # Persist StudyMaterial in DB
    try:
        # Inspect table columns to avoid inserting unknown columns when migrations
        # have not been applied. This makes the endpoint resilient in development.
        from sqlalchemy import inspect
        bind = db.get_bind() if hasattr(db, 'get_bind') else getattr(db, 'bind', None)
        has_grade = False
        if bind is not None:
            inspector = inspect(bind)
            if inspector.has_table('study_materials'):
                existing_columns = [c['name'] for c in inspector.get_columns('study_materials')]
                has_grade = 'grade' in existing_columns

                # If the table exists but the column is missing and the caller provided a grade,
                # attempt a safe runtime ALTER TABLE to add the column. This mirrors the
                # development-time convenience used elsewhere and prevents a hard 500.
                if not has_grade and getattr(payload, 'grade', None) is not None:
                    try:
                        from sqlalchemy import text
                        alter_sql = "ALTER TABLE study_materials ADD COLUMN IF NOT EXISTS grade VARCHAR"
                        bind.execute(text(alter_sql))
                        # Refresh inspection
                        existing_columns = [c['name'] for c in inspector.get_columns('study_materials')]
                        has_grade = 'grade' in existing_columns
                    except Exception:
                        # If ALTER fails, continue without grade to avoid masking the real error.
                        has_grade = False

        # Insert without grade first to avoid failing when the column is missing.
        study_material_kwargs = dict(
            id=material_id,
            title=payload.title,
            content=content_text,
            topic=payload.topic,
            subject=payload.subject,
            difficulty_level=payload.difficulty_level or "intermediate",
        )

        study_material = StudyMaterial(**study_material_kwargs)
        db.add(study_material)
        db.commit()
        db.refresh(study_material)

        # If a grade was provided, ensure the column exists and update the row.
        if getattr(payload, 'grade', None) is not None:
            try:
                from sqlalchemy import text
                # Add column if missing (idempotent)
                bind.execute(text("ALTER TABLE study_materials ADD COLUMN IF NOT EXISTS grade VARCHAR"))
                # Update the just-created record with the grade
                update_sql = text("UPDATE study_materials SET grade = :grade WHERE id = :id")
                bind.execute(update_sql, {"grade": payload.grade, "id": material_id})
                db.commit()
                # Refresh ORM object
                db.refresh(study_material)
            except Exception:
                # If update fails, rollback but keep the created record without grade
                try:
                    db.rollback()
                except Exception:
                    pass
    except Exception as e:
        # Rollback to keep session clean and provide clearer error to client
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to persist study material: {e}")

    return study_material

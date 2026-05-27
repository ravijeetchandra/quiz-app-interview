from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from auth import get_current_user, require_user
from schemas import QuizConfig, QuizSessionOut
from services.file_processor import process_upload, validate_file_extension, get_document_preview
from services.llm_service import classify_domain, generate_quiz_content
from config import settings
import uuid
import json
import openai

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form(default="auto"),
    user: User = Depends(get_current_user),
):
    if not validate_file_extension(file.filename):
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: pdf, doc, docx, txt")

    content = await file.read()

    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    text = await process_upload(content, file.filename)
    preview = get_document_preview(text)

    if domain.lower() == "auto":
        try:
            detected_domain = await classify_domain(preview, settings.domain_list)
        except Exception:
            detected_domain = "General / Other"
    elif domain.lower() == "general / other":
        detected_domain = "General / Other"
    else:
        try:
            detected_domain = await classify_domain(preview, settings.domain_list)
        except Exception as e:
            detected_domain = "Unknown"

    return {
        "filename": file.filename,
        "text_preview": preview,
        "text_length": len(text),
        "full_text": text,
        "detected_domain": detected_domain,
        "selected_domain": domain,
        "domain_match": domain.lower() != "auto" and (domain.lower() == "general / other" or detected_domain.lower() == domain.lower()),
    }


@router.post("/generate", response_model=QuizSessionOut)
async def generate_quiz(
    config: str = Form(...),
    file_text: str = Form(default=""),
    filename: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from models import QuizSession, Question

    try:
        config_data = json.loads(config)
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid config format: {str(e)}")

    domain = config_data.get("domain", "")
    mcq_count = config_data.get("mcq_count", 10)
    has_long = config_data.get("has_long_questions", False)
    passing_pct = config_data.get("passing_percentage", 70.0)
    source_type = config_data.get("source_type", "file")

    if domain not in settings.domain_list:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Choose from: {settings.domain_list}")

    if not isinstance(mcq_count, int) or mcq_count < 1 or mcq_count > 20:
        raise HTTPException(status_code=400, detail="mcq_count must be an integer between 1 and 20")

    try:
        result = await generate_quiz_content(file_text, domain, mcq_count, has_long, source_type)
        mcq_data = result["mcq_questions"]
        long_data = result["long_questions"]
        sections = result["sections"]
    except openai.RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"Groq daily token limit reached. Try again later or upgrade: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM service error: {str(e)[:200]}")

    user_id = user.id if user else None
    guest_id = str(uuid.uuid4()) if not user else None

    doc_name = filename if filename else f"General - {domain}"

    session = QuizSession(
        id=uuid.uuid4(),
        user_id=user_id,
        domain=domain,
        document_name=doc_name,
        mcq_count=mcq_count,
        has_long_questions=has_long,
        passing_percentage=passing_pct,
        is_guest=user is None,
        guest_session_id=guest_id,
    )
    db.add(session)
    await db.flush()

    questions = []
    for i, q in enumerate(mcq_data):
        question = Question(
            id=uuid.uuid4(),
            session_id=session.id,
            question_type="mcq",
            question_text=q["question"],
            options=json.dumps(q["options"]),
            correct_answer=q["correct_answer"],
            order=i + 1,
            time_limit_seconds=30,
        )
        questions.append(question)
        db.add(question)

    for i, q in enumerate(long_data):
        question = Question(
            id=uuid.uuid4(),
            session_id=session.id,
            question_type="long",
            question_text=q["question"],
            correct_answer="",
            order=len(mcq_data) + i + 1,
            time_limit_seconds=120,
        )
        questions.append(question)
        db.add(question)

    await db.commit()

    for q in questions:
        await db.refresh(q)

    return QuizSessionOut(
        id=session.id,
        domain=session.domain,
        document_name=session.document_name,
        mcq_count=session.mcq_count,
        has_long_questions=session.has_long_questions,
        passing_percentage=session.passing_percentage,
        questions=[
            {
                "id": q.id,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "options": q.options,
                "order": q.order,
                "time_limit_seconds": q.time_limit_seconds,
            }
            for q in questions
        ],
        started_at=session.started_at,
    )

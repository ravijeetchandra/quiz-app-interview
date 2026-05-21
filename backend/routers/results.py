from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, QuizSession, Question, UserAnswer
from auth import get_current_user
from schemas import QuizSubmit, QuizResultOut, AnswerResult, SectionResult, QuizHistoryItem, UserDashboard
from services.llm_service import evaluate_long_answer
import uuid
import json
from datetime import timezone, datetime

router = APIRouter(prefix="/api/quiz", tags=["Quiz Results"])


@router.post("/{session_id}/submit", response_model=QuizResultOut)
async def submit_quiz(
    session_id: uuid.UUID,
    data: QuizSubmit,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(QuizSession).where(QuizSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.completed_at:
        raise HTTPException(status_code=400, detail="Quiz already submitted")

    result_query = await db.execute(
        select(Question).where(Question.session_id == session_id).order_by(Question.order)
    )
    questions = result_query.scalars().all()

    questions_map = {str(q.id): q for q in questions}
    answer_results = []
    total_score = 0.0
    total_possible = 0.0

    for i, q in enumerate(questions):
        total_possible += 1.0 if q.question_type == "mcq" else 10.0

    sections_data = {}
    mcq_correct = 0

    for ans_data in data.answers:
        q_id_str = str(ans_data.question_id)
        question = questions_map.get(q_id_str)
        if not question:
            continue

        is_correct = None
        score = 0.0
        strengths = None
        weaknesses = None
        model_answer = None

        if question.question_type == "mcq":
            is_correct = ans_data.selected_answer and ans_data.selected_answer.strip() == question.correct_answer.strip()
            score = 1.0 if is_correct else 0.0
            if is_correct:
                mcq_correct += 1
        else:
            try:
                eval_result = await evaluate_long_answer(
                    question=question.question_text,
                    answer=ans_data.selected_answer or "",
                    context=question.question_text,
                )
                raw_score = eval_result.get("score", 0)
                if not isinstance(raw_score, (int, float)):
                    raw_score = 0
                score = max(0, min(10, float(raw_score))) / 10.0
                strengths = json.dumps(eval_result.get("strengths", []) or [])
                weaknesses = json.dumps(eval_result.get("weaknesses", []) or [])
                model_answer = eval_result.get("model_answer", "")
            except Exception:
                score = 0
                strengths = json.dumps([])
                weaknesses = json.dumps(["Evaluation unavailable due to API limits"])
                model_answer = "Evaluation could not be completed. Please try again later."

        total_score += score

        answer = UserAnswer(
            id=uuid.uuid4(),
            question_id=question.id,
            session_id=session_id,
            selected_answer=ans_data.selected_answer,
            is_correct=is_correct,
            score=score,
            time_taken=ans_data.time_taken,
            timed_out=ans_data.timed_out,
            strengths=strengths,
            weaknesses=weaknesses,
            model_answer=model_answer,
        )
        db.add(answer)

        answer_results.append(AnswerResult(
            question_id=question.id,
            question_text=question.question_text,
            question_type=question.question_type,
            your_answer=ans_data.selected_answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
            score=score,
            time_taken=ans_data.time_taken,
            timed_out=ans_data.timed_out,
            strengths=strengths,
            weaknesses=weaknesses,
            model_answer=model_answer,
        ))

    percentage = (total_score / total_possible * 100) if total_possible > 0 else 0
    passed = percentage >= session.passing_percentage

    mcq_questions = [q for q in questions if q.question_type == "mcq"]
    long_questions = [q for q in questions if q.question_type == "long"]

    section_results = []
    if mcq_questions:
        section_results.append(SectionResult(
            section_name="Multiple Choice Questions",
            score=float(mcq_correct),
            possible=float(len(mcq_questions)),
            percentage=(mcq_correct / len(mcq_questions) * 100),
        ))

    if long_questions:
        long_ids = {str(q.id) for q in long_questions}
        long_score = sum(ar.score for ar in answer_results if str(ar.question_id) in long_ids)
        section_results.append(SectionResult(
            section_name="Long Answer Questions",
            score=long_score,
            possible=float(len(long_questions) * 10),
            percentage=(long_score / (len(long_questions) * 10) * 100),
        ))

    now = datetime.now(timezone.utc)
    session.total_score = total_score
    session.total_possible = total_possible
    session.percentage = percentage
    session.passed = passed
    session.completed_at = now
    session.section_results = json.dumps([s.model_dump() for s in section_results])

    await db.commit()

    return QuizResultOut(
        session_id=session.id,
        domain=session.domain,
        document_name=session.document_name,
        total_score=total_score,
        total_possible=total_possible,
        percentage=percentage,
        passed=passed,
        passing_percentage=session.passing_percentage,
        answer_results=answer_results,
        section_results=section_results,
        completed_at=now,
    )


@router.get("/history", response_model=list)
async def get_quiz_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    result = await db.execute(
        select(QuizSession)
        .where(QuizSession.user_id == user.id, QuizSession.completed_at.isnot(None))
        .order_by(QuizSession.completed_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "domain": s.domain,
            "document_name": s.document_name,
            "mcq_count": s.mcq_count,
            "has_long_questions": s.has_long_questions,
            "percentage": s.percentage,
            "passed": s.passed,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in sessions
    ]


@router.get("/{session_id}/result", response_model=QuizResultOut)
async def get_quiz_result(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(QuizSession).where(QuizSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    ans_result = await db.execute(
        select(UserAnswer).where(UserAnswer.session_id == session_id)
    )
    answers = ans_result.scalars().all()

    q_result = await db.execute(
        select(Question).where(Question.session_id == session_id).order_by(Question.order)
    )
    questions = q_result.scalars().all()
    questions_map = {str(q.id): q for q in questions}

    answer_results = []
    for ans in answers:
        q = questions_map.get(str(ans.question_id))
        answer_results.append(AnswerResult(
            question_id=ans.question_id,
            question_text=q.question_text if q else "",
            question_type=q.question_type if q else "",
            your_answer=ans.selected_answer,
            correct_answer=q.correct_answer if q else "",
            is_correct=ans.is_correct,
            score=ans.score,
            time_taken=ans.time_taken or 0,
            timed_out=ans.timed_out,
            strengths=ans.strengths,
            weaknesses=ans.weaknesses,
            model_answer=ans.model_answer,
        ))

    section_results = []
    if session.section_results:
        try:
            section_results = [SectionResult(**s) for s in json.loads(session.section_results)]
        except (json.JSONDecodeError, TypeError):
            section_results = []

    return QuizResultOut(
        session_id=session.id,
        domain=session.domain,
        document_name=session.document_name,
        total_score=session.total_score or 0,
        total_possible=session.total_possible or 0,
        percentage=session.percentage or 0,
        passed=session.passed or False,
        passing_percentage=session.passing_percentage,
        answer_results=answer_results,
        section_results=section_results,
        completed_at=session.completed_at,
    )


@router.get("/dashboard", response_model=UserDashboard)
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    result = await db.execute(
        select(QuizSession)
        .where(QuizSession.user_id == user.id, QuizSession.completed_at.isnot(None))
        .order_by(QuizSession.completed_at.desc())
    )
    sessions = result.scalars().all()

    total_quizzes = len(sessions)
    if total_quizzes == 0:
        return UserDashboard(
            total_quizzes=0,
            average_score=0,
            best_score=0,
            quizzes_by_domain=[],
            recent_quizzes=[],
            score_trend=[],
        )

    avg_score = sum(s.percentage or 0 for s in sessions) / total_quizzes
    best_score = max(s.percentage or 0 for s in sessions)

    domain_stats = {}
    for s in sessions:
        domain_stats.setdefault(s.domain, []).append(s.percentage or 0)

    quizzes_by_domain = [
        {"domain": d, "count": len(v), "average": sum(v) / len(v)}
        for d, v in domain_stats.items()
    ]

    recent = [
        QuizHistoryItem(
            id=s.id,
            domain=s.domain,
            document_name=s.document_name,
            mcq_count=s.mcq_count,
            has_long_questions=s.has_long_questions,
            percentage=s.percentage or 0,
            passed=s.passed or False,
            started_at=s.started_at,
            completed_at=s.completed_at,
        )
        for s in sessions[:10]
    ]

    # sessions is DESC (newest first), take first 20 for trend
    score_trend = [
        {
            "date": s.completed_at.isoformat() if s.completed_at else None,
            "score": s.percentage or 0,
            "domain": s.domain,
        }
        for s in sessions[:20]
    ]

    return UserDashboard(
        total_quizzes=total_quizzes,
        average_score=round(avg_score, 1),
        best_score=round(best_score, 1),
        quizzes_by_domain=quizzes_by_domain,
        recent_quizzes=recent,
        score_trend=score_trend,
    )

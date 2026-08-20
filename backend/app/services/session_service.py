import asyncio
import logging
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.session import Session as SessionModel
from app.models.user import User
from app.models.skill import Skill
from app.models.mentor_availability import MentorAvailability
from app.repositories.session_repository import (
    create_session,
    get_sessions_by_user,
    get_session_by_id,
    find_conflicting_mentor_session,
    find_conflicting_requester_session,
    get_sessions_by_status,
    count_sessions_by_status
)
from app.repositories.availability_repository import get_availability_for_day
from app.services.availability_service import invalidate_mentor_availability_cache
from app.services.reward_service import reward_session_completion
from app.services.notification_service import create_user_notification
from app.services.wallet_service import debit_wallet, credit_wallet
from app.core.logging import log_structured_event
from app.core.websocket_manager import manager

logger = logging.getLogger("skillswap.sessions")


def _enrich_session(db: Session, session: SessionModel) -> SessionModel:
    mentor = db.query(User).filter(User.id == session.mentor_id).first()
    requester = db.query(User).filter(User.id == session.requester_id).first()
    skill = db.query(Skill).filter(Skill.id == session.skill_id).first()

    session.mentor_name = mentor.name if mentor else "Unknown Mentor"
    session.learner_name = requester.name if requester else "Unknown Learner"
    session.skill_name = skill.name if skill else "Peer Mentoring"
    return session


def _enrich_sessions_list(db: Session, sessions: list[SessionModel]) -> list[SessionModel]:
    if not sessions:
        return []
    # Collect unique user & skill IDs to optimize lookups
    user_ids = {s.mentor_id for s in sessions} | {s.requester_id for s in sessions}
    skill_ids = {s.skill_id for s in sessions}

    users_map = {u.id: u.name for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    skills_map = {sk.id: sk.name for sk in db.query(Skill).filter(Skill.id.in_(skill_ids)).all()} if skill_ids else {}

    for s in sessions:
        s.mentor_name = users_map.get(s.mentor_id, "Unknown Mentor")
        s.learner_name = users_map.get(s.requester_id, "Unknown Learner")
        s.skill_name = skills_map.get(s.skill_id, "Peer Mentoring")
    return sessions


def schedule_session(
    db: Session,
    requester_id: int,
    mentor_id: int,
    skill_id: int,
    scheduled_at: datetime,
    duration_minutes: int = 60,
    meeting_link: str | None = None
) -> SessionModel:
    """
    Authoritative, concurrency-safe session scheduling in PostgreSQL.
    Enforces row locks, future timestamps, strict availability windows,
    conflict detection, wallet coin deduction, persistent notifications,
    and Redis cache invalidation.
    """
    log_structured_event(
        "booking_attempt",
        requester_id=requester_id,
        mentor_id=mentor_id,
        skill_id=skill_id,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes
    )

    # 1. Validation: Self-booking prevention
    if requester_id == mentor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot book a mentoring session with yourself."
        )

    # 2. Validation: Future time check
    now_utc = datetime.utcnow()
    naive_scheduled_at = scheduled_at.replace(tzinfo=None) if scheduled_at.tzinfo is not None else scheduled_at
    if naive_scheduled_at <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a session in the past. Please choose a future date and time."
        )

    if duration_minutes <= 0 or duration_minutes > 180:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session duration. Must be between 15 and 180 minutes."
        )

    # 3. Enter safe database transaction & lock mentor and requester rows
    try:
        # SQLite does not support SELECT FOR UPDATE, so we guard against dialect
        if db.bind and db.bind.dialect.name == "postgresql":
            db.query(User).filter(User.id == mentor_id).with_for_update().first()
            db.query(User).filter(User.id == requester_id).with_for_update().first()

        # Verify mentor exists
        mentor = db.query(User).filter(User.id == mentor_id).first()
        if not mentor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected mentor does not exist."
            )

        # Verify skill exists
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected skill does not exist."
            )

        # 4. Authoritative Availability Window Verification
        day_of_week = naive_scheduled_at.strftime("%A")
        availability_windows = get_availability_for_day(db, mentor_id, day_of_week, active_only=True)

        if not availability_windows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mentor has not configured availability for {day_of_week}s."
            )

        session_start_time = naive_scheduled_at.time()
        session_end_dt = naive_scheduled_at + timedelta(minutes=duration_minutes)
        session_end_time = session_end_dt.time()

        # Check if session fits entirely inside at least one active window
        fits_in_window = False
        for window in availability_windows:
            if session_start_time >= window.start_time and session_end_time <= window.end_time:
                fits_in_window = True
                break

        if not fits_in_window:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested time falls outside the mentor's active availability hours."
            )

        # 5. Authoritative Conflict Check: Mentor double-booking check
        conflicting_mentor = find_conflicting_mentor_session(
            db,
            mentor_id,
            naive_scheduled_at,
            duration_minutes
        )
        if conflicting_mentor:
            log_structured_event(
                "booking_conflict",
                requester_id=requester_id,
                mentor_id=mentor_id,
                scheduled_at=naive_scheduled_at,
                reason="mentor_slot_occupied"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This slot was just booked by another learner. Please choose another time."
            )

        # 6. Authoritative Conflict Check: Requester overlapping session check
        conflicting_requester = find_conflicting_requester_session(
            db,
            requester_id,
            naive_scheduled_at,
            duration_minutes
        )
        if conflicting_requester:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active session scheduled during this time slot."
            )

        # 7. Wallet Deduction (Atomic within booking transaction)
        debit_wallet(
            db,
            requester_id,
            5,
            f"Session Booking with {mentor.name}"
        )

        # 8. Meeting link generation
        if not meeting_link:
            room_id = f"skillswap-{mentor_id}-{requester_id}-{int(naive_scheduled_at.timestamp())}"
            meeting_link = f"https://meet.jit.si/{room_id}"

        # 9. Create Session
        new_session = SessionModel(
            requester_id=requester_id,
            mentor_id=mentor_id,
            skill_id=skill_id,
            scheduled_at=naive_scheduled_at,
            duration_minutes=duration_minutes,
            meeting_link=meeting_link,
            status="scheduled"
        )
        db.add(new_session)
        db.flush()

        # 10. Create Persistent Notification for Mentor
        requester = db.query(User).filter(User.id == requester_id).first()
        learner_name = requester.name if requester else f"Learner #{requester_id}"
        formatted_dt = naive_scheduled_at.strftime("%a, %b %d at %I:%M %p")

        create_user_notification(
            db=db,
            user_id=mentor_id,
            title="New Session Booked 📌",
            message=f"{learner_name} booked a {skill.name} session with you for {formatted_dt}.",
            type="SESSION_BOOKED",
            related_session_id=new_session.id
        )

        # Commit everything atomically
        db.commit()
        db.refresh(new_session)

    except IntegrityError as ie:
        db.rollback()
        log_structured_event(
            "booking_conflict",
            requester_id=requester_id,
            mentor_id=mentor_id,
            scheduled_at=naive_scheduled_at,
            reason="db_unique_constraint_violation"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot was just booked by another learner. Please choose another time."
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error scheduling session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while booking the session. Please try again."
        )

    # 11. Invalidate Redis Availability Cache
    invalidate_mentor_availability_cache(mentor_id)

    # 12. Structured Logging
    log_structured_event(
        "booking_created",
        session_id=new_session.id,
        requester_id=requester_id,
        mentor_id=mentor_id,
        skill_id=skill_id,
        scheduled_at=new_session.scheduled_at,
        duration_minutes=new_session.duration_minutes
    )

    # 13. Async WebSocket Notification delivery if online
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.send_notification_payload(
                mentor_id,
                {
                    "type": "SESSION_BOOKED",
                    "session_id": new_session.id,
                    "message": f"New session booked by {learner_name} for {formatted_dt}"
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

    return _enrich_session(db, new_session)


def my_sessions(
    db: Session,
    user_id: int
) -> list[SessionModel]:
    sessions = get_sessions_by_user(db, user_id)
    return _enrich_sessions_list(db, sessions)


def upcoming_sessions(
    db: Session,
    user_id: int
) -> list[SessionModel]:
    sessions = get_sessions_by_status(db, user_id, "scheduled")
    return _enrich_sessions_list(db, sessions)


def completed_sessions_list(
    db: Session,
    user_id: int
) -> list[SessionModel]:
    sessions = get_sessions_by_status(db, user_id, "completed")
    return _enrich_sessions_list(db, sessions)


def cancelled_sessions_list(
    db: Session,
    user_id: int
) -> list[SessionModel]:
    sessions = get_sessions_by_status(db, user_id, "cancelled")
    return _enrich_sessions_list(db, sessions)


def cancel_session(
    db: Session,
    session_id: int,
    current_user_id: int
) -> SessionModel:
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Authorization check
    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to cancel this session."
        )

    if session.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a session that is already {session.status}."
        )

    session.status = "cancelled"

    # Refund coins to requester if cancelled by mentor or advance cancellation
    try:
        credit_wallet(
            db,
            session.requester_id,
            5,
            "Refund for cancelled session",
            reference_id=f"REFUND_SESSION_{session.id}",
            transaction_type="REFUND"
        )
    except Exception as e:
        logger.warning(f"Could not refund wallet on cancellation: {e}")

    # Notify other party
    is_mentor_cancelling = (current_user_id == session.mentor_id)
    recipient_id = session.requester_id if is_mentor_cancelling else session.mentor_id
    cancelled_by_role = "Mentor" if is_mentor_cancelling else "Learner"

    create_user_notification(
        db=db,
        user_id=recipient_id,
        title="Session Cancelled ⚠️",
        message=f"Your scheduled session on {session.scheduled_at.strftime('%a, %b %d at %I:%M %p')} was cancelled by the {cancelled_by_role}.",
        type="SESSION_CANCELLED",
        related_session_id=session.id
    )

    db.commit()
    db.refresh(session)

    invalidate_mentor_availability_cache(session.mentor_id)

    log_structured_event(
        "booking_cancelled",
        session_id=session.id,
        cancelled_by=current_user_id,
        mentor_id=session.mentor_id,
        requester_id=session.requester_id
    )

    return _enrich_session(db, session)


def complete_session(
    db: Session,
    session_id: int,
    current_user_id: int
) -> SessionModel:
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Authorization check
    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to complete this session."
        )

    if session.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete a session that is already {session.status}."
        )

    session.status = "completed"

    # Reward mentor
    reward_session_completion(
        db,
        session.mentor_id
    )

    # Notify participants
    create_user_notification(
        db=db,
        user_id=session.requester_id,
        title="Session Completed 🎉",
        message=f"Your session on {session.scheduled_at.strftime('%a, %b %d')} has been marked completed. Don't forget to leave feedback!",
        type="SESSION_COMPLETED",
        related_session_id=session.id
    )

    db.commit()
    db.refresh(session)

    invalidate_mentor_availability_cache(session.mentor_id)

    log_structured_event(
        "session_completed",
        session_id=session.id,
        completed_by=current_user_id,
        mentor_id=session.mentor_id,
        requester_id=session.requester_id
    )

    return _enrich_session(db, session)


def session_dashboard(
    db: Session,
    user_id: int
) -> dict:
    return {
        "upcoming_sessions": count_sessions_by_status(db, user_id, "scheduled"),
        "completed_sessions": count_sessions_by_status(db, user_id, "completed"),
        "cancelled_sessions": count_sessions_by_status(db, user_id, "cancelled")
    }
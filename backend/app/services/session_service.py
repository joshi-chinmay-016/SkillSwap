import asyncio
import logging
import uuid
from datetime import datetime, timedelta, time, timezone
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
from app.core.distributed_lock import distributed_booking_lock
from app.core.redis import redis_client

logger = logging.getLogger("skillswap.sessions")


def _calculate_actual_duration(session: SessionModel) -> int | None:
    if session.started_at and session.completed_at:
        diff = session.completed_at - session.started_at
        return max(1, int(diff.total_seconds() / 60))
    elif session.started_at and session.status == "in_progress":
        now = datetime.now(timezone.utc)
        started_dt = session.started_at if session.started_at.tzinfo else session.started_at.replace(tzinfo=timezone.utc)
        diff = now - started_dt
        return max(1, int(diff.total_seconds() / 60))
    return None


def _enrich_session(db: Session, session: SessionModel) -> SessionModel:
    mentor = db.query(User).filter(User.id == session.mentor_id).first()
    requester = db.query(User).filter(User.id == session.requester_id).first()
    skill = db.query(Skill).filter(Skill.id == session.skill_id).first()

    session.mentor_name = mentor.name if mentor else "Unknown Mentor"
    session.learner_name = requester.name if requester else "Unknown Learner"
    session.skill_name = skill.name if skill else "Peer Mentoring"
    session.actual_duration_minutes = _calculate_actual_duration(session)
    return session


def _enrich_sessions_list(db: Session, sessions: list[SessionModel]) -> list[SessionModel]:
    if not sessions:
        return []
    user_ids = {s.mentor_id for s in sessions} | {s.requester_id for s in sessions}
    skill_ids = {s.skill_id for s in sessions}

    users_map = {u.id: u.name for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    skills_map = {sk.id: sk.name for sk in db.query(Skill).filter(Skill.id.in_(skill_ids)).all()} if skill_ids else {}

    for s in sessions:
        s.mentor_name = users_map.get(s.mentor_id, "Unknown Mentor")
        s.learner_name = users_map.get(s.requester_id, "Unknown Learner")
        s.skill_name = skills_map.get(s.skill_id, "Peer Mentoring")
        s.actual_duration_minutes = _calculate_actual_duration(s)
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
    Authoritative, concurrency-safe session scheduling.
    Flow:
      1. Validation (self-booking, future date, duration bounds).
      2. Distributed Redis Lock per mentor slot.
      3. PostgreSQL transaction with row locks.
      4. Authoritative mentor availability check.
      5. Authoritative conflict check (mentor & learner).
      6. Atomic wallet debit (5 coins).
      7. Persistent meeting room generation.
      8. Persist session & notification in PostgreSQL.
      9. Release Redis lock on exit.
      10. Invalidate Redis availability cache.
      11. Broadcast real-time WebSocket event to mentor.
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

    # 2. Validation: Future time check (timezone-safe)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
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

    session_end_dt = naive_scheduled_at + timedelta(minutes=duration_minutes)

    # 3. Enter Distributed Lock and PostgreSQL Transaction
    with distributed_booking_lock(mentor_id, naive_scheduled_at, session_end_dt):
        try:
            # SQLite does not support SELECT FOR UPDATE, guard by dialect
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
            target_date = naive_scheduled_at.date()
            day_of_week = naive_scheduled_at.strftime("%A")
            from app.repositories.availability_repository import get_availability_for_date_or_day
            availability_windows = get_availability_for_date_or_day(db, mentor_id, target_date, day_of_week, active_only=True)

            if not availability_windows:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mentor has not configured availability for {target_date} ({day_of_week})."
                )

            session_start_time = naive_scheduled_at.time()
            session_end_time = session_end_dt.time()

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

            # 8. Stable meeting room ID and link generation
            room_id = f"skillswap-room-{mentor_id}-{requester_id}-{uuid.uuid4().hex[:8]}"
            if not meeting_link:
                meeting_link = f"https://meet.jit.si/{room_id}"

            # 9. Create Session
            new_session = SessionModel(
                requester_id=requester_id,
                mentor_id=mentor_id,
                skill_id=skill_id,
                scheduled_at=naive_scheduled_at,
                duration_minutes=duration_minutes,
                meeting_room_id=room_id,
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

            # Record learning activity for requester
            try:
                from app.repositories.learning_activity_repository import create_learning_activity
                create_learning_activity(
                    db=db,
                    user_id=requester_id,
                    activity_type="session_booked",
                    entity_type="session",
                    entity_id=new_session.id,
                    activity_data={
                        "title": f"Booked Mentoring: {skill.name} with {mentor.name}",
                        "skill_name": skill.name,
                        "mentor_name": mentor.name,
                        "scheduled_at": naive_scheduled_at.isoformat()
                    }
                )
            except Exception:
                pass

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

    # 13. Async WebSocket Notification delivery to mentor
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.send_notification_payload(
                mentor_id,
                {
                    "type": "BOOKING_CREATED",
                    "session_id": new_session.id,
                    "learner_id": requester_id,
                    "learner_name": learner_name,
                    "skill_name": skill.name,
                    "scheduled_at": new_session.scheduled_at.isoformat(),
                    "message": f"New session booked by {learner_name} for {formatted_dt}"
                }
            )
        )
    except RuntimeError:
        pass
    except Exception as e:
        logger.debug(f"Could not dispatch real-time ws event: {e}")

    return _enrich_session(db, new_session)


def get_session_by_id_authorized(
    db: Session,
    session_id: int,
    current_user_id: int
) -> SessionModel:
    """
    Authoritatively fetches a session by ID and verifies participation.
    Returns 404 if not found, 403 if user is not a participant.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this session."
        )

    return _enrich_session(db, session)


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
    from sqlalchemy import or_
    sessions = (
        db.query(SessionModel)
        .filter(
            or_(
                SessionModel.requester_id == user_id,
                SessionModel.mentor_id == user_id
            ),
            SessionModel.status.in_(["scheduled", "in_progress"])
        )
        .order_by(SessionModel.scheduled_at.asc())
        .all()
    )
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


def start_session(
    db: Session,
    session_id: int,
    current_user_id: int
) -> SessionModel:
    """
    Authoritative state transition: scheduled -> in_progress (LIVE).
    Enforces participant authorization and valid state transitions.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    # Authorization check
    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to start this session."
        )

    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start a session that is already completed."
        )

    if session.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start a session that has been cancelled."
        )

    session.status = "in_progress"
    if not session.started_at:
        session.started_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(session)

    log_structured_event(
        "session_started",
        session_id=session.id,
        started_by=current_user_id,
        mentor_id=session.mentor_id,
        requester_id=session.requester_id,
        started_at=session.started_at.isoformat() if session.started_at else None
    )

    # Dispatch real-time WebSocket event to other participant
    try:
        loop = asyncio.get_running_loop()
        other_user = session.mentor_id if current_user_id == session.requester_id else session.requester_id
        loop.create_task(
            manager.send_notification_payload(
                other_user,
                {
                    "type": "SESSION_STARTED",
                    "session_id": session.id,
                    "started_by": current_user_id,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "meeting_link": session.meeting_link,
                    "message": "Your session is now LIVE. Click to join the Jitsi room."
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

    return _enrich_session(db, session)


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

    if session.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a session that is already {session.status}."
        )

    session.status = "cancelled"

    # Clean up Redis presence
    try:
        redis_client.delete(
            f"presence:session:{session.id}:user:{session.mentor_id}",
            f"presence:session:{session.id}:user:{session.requester_id}"
        )
    except Exception:
        pass

    # Refund coins to requester if cancelled
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

    # Real-time WebSocket event
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.send_notification_payload(
                recipient_id,
                {
                    "type": "BOOKING_CANCELLED",
                    "session_id": session.id,
                    "cancelled_by": current_user_id,
                    "message": f"Session was cancelled by {cancelled_by_role}."
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

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

    if session.status not in ("scheduled", "in_progress"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete a session that is already {session.status}."
        )

    session.status = "completed"
    if not session.completed_at:
        session.completed_at = datetime.now(timezone.utc)
    if not session.started_at:
        session.started_at = session.scheduled_at

    # Reward mentor
    reward_session_completion(
        db,
        session.mentor_id
    )

    # Record learning activity for learner & mentor with strict activity type distinction
    try:
        from app.services.learning_activity_service import record_learning_activity, invalidate_user_learning_cache
        from app.services.achievement_engine import evaluate_user_achievements
        from app.models.skill import Skill
        skill_obj = db.query(Skill).filter(Skill.id == session.skill_id).first() if session.skill_id else None
        skill_name = skill_obj.name if skill_obj else "Peer Mentoring"

        # Learner activity: session_completed
        record_learning_activity(
            db,
            user_id=session.requester_id,
            activity_type="session_completed",
            entity_type="session",
            entity_id=session.id,
            activity_data={
                "session_id": session.id,
                "title": f"Mentoring Session ({skill_name})",
                "skill_name": skill_name,
                "role": "learner",
                "duration_minutes": session.duration_minutes
            }
        )

        # Mentor activity: teaching_completed (distinct from learner progress)
        record_learning_activity(
            db,
            user_id=session.mentor_id,
            activity_type="teaching_completed",
            entity_type="session",
            entity_id=session.id,
            activity_data={
                "session_id": session.id,
                "title": f"Peer Teaching Session ({skill_name})",
                "skill_name": skill_name,
                "role": "mentor",
                "duration_minutes": session.duration_minutes
            }
        )

        # Invalidate streak, heatmap, and analytics caches for both users
        invalidate_user_learning_cache(session.requester_id)
        invalidate_user_learning_cache(session.mentor_id)

        # Evaluate achievements
        try:
            evaluate_user_achievements(db, session.requester_id)
            evaluate_user_achievements(db, session.mentor_id)
        except Exception:
            pass

    except Exception as e:
        logger.warning(f"Failed to record learning activities for completed session {session.id}: {e}")

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

    # Automatically generate grounded AI session intelligence from captured notes/topics
    try:
        from app.services.session_intelligence_service import generate_session_intelligence
        generate_session_intelligence(db, session.id, current_user_id)
    except Exception as e:
        logger.warning(f"Could not auto-generate session intelligence on completion: {e}")

    log_structured_event(
        "session_completed",
        session_id=session.id,
        completed_by=current_user_id,
        mentor_id=session.mentor_id,
        requester_id=session.requester_id,
        completed_at=session.completed_at.isoformat() if session.completed_at else None
    )

    # Real-time WebSocket event
    try:
        loop = asyncio.get_running_loop()
        other_user = session.mentor_id if current_user_id == session.requester_id else session.requester_id
        loop.create_task(
            manager.send_notification_payload(
                other_user,
                {
                    "type": "SESSION_COMPLETED",
                    "session_id": session.id,
                    "completed_by": current_user_id,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "message": "Session has been marked completed."
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

    return _enrich_session(db, session)


def join_session(
    db: Session,
    session_id: int,
    current_user_id: int
) -> dict:
    """
    Authoritative join handler. Verifies participant, ensures session is not cancelled,
    records ephemeral Redis presence, and emits real-time PARTICIPANT_JOINED event.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to join this session."
        )

    if session.status in ("cancelled", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot join a session that has been {session.status}."
        )

    user_obj = db.query(User).filter(User.id == current_user_id).first()
    user_name = user_obj.name if user_obj else f"User #{current_user_id}"
    role = "mentor" if current_user_id == session.mentor_id else "learner"

    # Record ephemeral presence in Redis with 60s TTL
    try:
        redis_client.set(f"presence:session:{session_id}:user:{current_user_id}", "online", ex=60)
    except Exception:
        pass

    # Real-time WebSocket notification to other participant
    try:
        other_user = session.mentor_id if current_user_id == session.requester_id else session.requester_id
        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.send_notification_payload(
                other_user,
                {
                    "type": "PARTICIPANT_JOINED",
                    "session_id": session.id,
                    "user_id": current_user_id,
                    "user_name": user_name,
                    "role": role,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": f"{user_name} joined the session room."
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

    log_structured_event(
        "session_joined",
        session_id=session.id,
        user_id=current_user_id,
        mentor_id=session.mentor_id,
        requester_id=session.requester_id
    )

    return {
        "session_id": session.id,
        "meeting_link": session.meeting_link,
        "meeting_room_id": session.meeting_room_id,
        "status": session.status
    }


def leave_session(
    db: Session,
    session_id: int,
    current_user_id: int
) -> dict:
    """
    Cleans up ephemeral presence on exit and emits PARTICIPANT_LEFT event.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized for this session."
        )

    try:
        redis_client.delete(f"presence:session:{session_id}:user:{current_user_id}")
    except Exception:
        pass

    try:
        other_user = session.mentor_id if current_user_id == session.requester_id else session.requester_id
        user_obj = db.query(User).filter(User.id == current_user_id).first()
        user_name = user_obj.name if user_obj else f"User #{current_user_id}"
        role = "mentor" if current_user_id == session.mentor_id else "learner"

        loop = asyncio.get_running_loop()
        loop.create_task(
            manager.send_notification_payload(
                other_user,
                {
                    "type": "PARTICIPANT_LEFT",
                    "session_id": session.id,
                    "user_id": current_user_id,
                    "user_name": user_name,
                    "role": role,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": f"{user_name} left the session room."
                }
            )
        )
    except RuntimeError:
        pass
    except Exception:
        pass

    log_structured_event(
        "session_left",
        session_id=session.id,
        user_id=current_user_id
    )

    return {"message": "Left session room successfully."}


def record_session_heartbeat(
    db: Session,
    session_id: int,
    current_user_id: int
) -> dict:
    """
    Refreshes the ephemeral Redis presence TTL (60s) for an active participant.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized for this session."
        )

    if session.status in ("cancelled", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot maintain presence in a cancelled session."
        )

    try:
        redis_client.set(f"presence:session:{session_id}:user:{current_user_id}", "online", ex=60)
    except Exception:
        pass

    mentor_present = bool(redis_client.get(f"presence:session:{session_id}:user:{session.mentor_id}"))
    learner_present = bool(redis_client.get(f"presence:session:{session_id}:user:{session.requester_id}"))

    return {
        "session_id": session_id,
        "mentor_id": session.mentor_id,
        "mentor_present": mentor_present,
        "learner_id": session.requester_id,
        "learner_present": learner_present,
        "both_present": mentor_present and learner_present
    }


def get_session_presence(
    db: Session,
    session_id: int,
    current_user_id: int
) -> dict:
    """
    Retrieves ephemeral active participants in the session room from Redis.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this session's presence."
        )

    mentor_present = bool(redis_client.get(f"presence:session:{session_id}:user:{session.mentor_id}"))
    learner_present = bool(redis_client.get(f"presence:session:{session_id}:user:{session.requester_id}"))

    return {
        "session_id": session_id,
        "mentor_id": session.mentor_id,
        "mentor_present": mentor_present,
        "learner_id": session.requester_id,
        "learner_present": learner_present,
        "both_present": mentor_present and learner_present
    }


def get_session_timeline(
    db: Session,
    session_id: int,
    current_user_id: int
) -> dict:
    """
    Builds an authoritative, chronological session timeline from genuine database records.
    Never fabricates events.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this session's timeline."
        )

    mentor = db.query(User).filter(User.id == session.mentor_id).first()
    learner = db.query(User).filter(User.id == session.requester_id).first()
    skill = db.query(Skill).filter(Skill.id == session.skill_id).first()

    mentor_name = mentor.name if mentor else "Mentor"
    learner_name = learner.name if learner else "Learner"
    skill_name = skill.name if skill else "Peer Mentoring"

    events = []

    # 1. Booking creation event
    if session.created_at:
        events.append({
            "id": f"booking-{session.id}",
            "timestamp": session.created_at,
            "type": "session_booked",
            "title": f"Session Booked: {skill_name}",
            "description": f"{learner_name} scheduled a mentoring session with {mentor_name}.",
            "actor_id": session.requester_id,
            "actor_name": learner_name,
            "actor_role": "learner",
            "metadata": {"scheduled_at": session.scheduled_at.isoformat() if session.scheduled_at else None}
        })

    # 2. Session started event
    if session.started_at:
        events.append({
            "id": f"start-{session.id}",
            "timestamp": session.started_at,
            "type": "session_started",
            "title": "Live Session Commenced",
            "description": "Participants opened the interactive workspace and Jitsi meeting.",
            "actor_id": session.mentor_id,
            "actor_name": mentor_name,
            "actor_role": "mentor",
            "metadata": {}
        })

    # 3. Discussion Topics
    from app.models.session_topic import SessionTopic
    topics = db.query(SessionTopic).filter(SessionTopic.session_id == session_id).order_by(SessionTopic.created_at.asc()).all()
    for top in topics:
        events.append({
            "id": f"topic-{top.id}",
            "timestamp": top.created_at,
            "type": "topic_added",
            "title": f"Topic Tagged: #{top.topic_name}",
            "description": f"Discussion topic '{top.topic_name}' recorded during peer collaboration.",
            "actor_id": None,
            "actor_name": None,
            "actor_role": "system" if top.source == "ai_extracted" else "collaborator",
            "metadata": {"source": top.source, "confidence": top.confidence}
        })

    # 4. Session Notes (Mentor & Learner updates)
    from app.models.session_note import SessionNote
    notes = db.query(SessionNote).filter(SessionNote.session_id == session_id).all()
    for note in notes:
        role_label = "Mentor" if note.role == "mentor" else "Learner"
        user_label = mentor_name if note.role == "mentor" else learner_name
        timestamp = note.updated_at or note.created_at
        notes_count = sum(len(v) for v in note.notes_data.values() if isinstance(v, list))
        if notes_count > 0:
            events.append({
                "id": f"note-{note.id}",
                "timestamp": timestamp,
                "type": "note_saved",
                "title": f"{role_label} Notes Captured",
                "description": f"{user_label} recorded {notes_count} learning notes/takeaways.",
                "actor_id": note.user_id,
                "actor_name": user_label,
                "actor_role": note.role,
                "metadata": {"notes_count": notes_count}
            })

    # 5. Action Items (Created & Completed)
    from app.models.session_action_item import SessionActionItem
    action_items = db.query(SessionActionItem).filter(SessionActionItem.session_id == session_id).all()
    for item in action_items:
        owner_name = mentor_name if item.user_id == session.mentor_id else learner_name
        owner_role = "mentor" if item.user_id == session.mentor_id else "learner"

        events.append({
            "id": f"action-create-{item.id}",
            "timestamp": item.created_at,
            "type": "action_item_created",
            "title": f"Action Item Assigned: {item.title}",
            "description": item.description or f"Next step assigned to {owner_name}.",
            "actor_id": item.user_id,
            "actor_name": owner_name,
            "actor_role": owner_role,
            "metadata": {"status": item.status, "source": item.source}
        })

        if item.status == "completed" and item.completed_at:
            events.append({
                "id": f"action-complete-{item.id}",
                "timestamp": item.completed_at,
                "type": "action_item_completed",
                "title": f"Action Item Completed: {item.title}",
                "description": f"{owner_name} marked this action item complete.",
                "actor_id": item.user_id,
                "actor_name": owner_name,
                "actor_role": owner_role,
                "metadata": {"status": "completed"}
            })

    # 6. Session Completion
    if session.status == "completed":
        comp_time = session.completed_at or session.updated_at
        events.append({
            "id": f"complete-{session.id}",
            "timestamp": comp_time,
            "type": "session_completed",
            "title": "Session Completed & Verified",
            "description": "Peer learning concluded. Learning activities recorded and AI intelligence generated.",
            "actor_id": session.mentor_id,
            "actor_name": mentor_name,
            "actor_role": "mentor",
            "metadata": {}
        })

    # 7. Feedback Submissions
    from app.models.feedback import Feedback
    feedbacks = db.query(Feedback).filter(Feedback.session_id == session_id).all()
    for fb in feedbacks:
        reviewer_name = mentor_name if fb.reviewer_id == session.mentor_id else learner_name
        reviewer_role = "mentor" if fb.reviewer_id == session.mentor_id else "learner"
        events.append({
            "id": f"feedback-{fb.id}",
            "timestamp": fb.created_at if hasattr(fb, "created_at") and fb.created_at else session.updated_at,
            "type": "feedback_submitted",
            "title": f"Review Submitted by {reviewer_name}",
            "description": f"Rated {fb.rating:.1f}/5.0 stars with comments.",
            "actor_id": fb.reviewer_id,
            "actor_name": reviewer_name,
            "actor_role": reviewer_role,
            "metadata": {"rating": fb.rating}
        })

    # Sort all events chronologically (with timezone handling)
    def _sort_key(ev):
        t = ev["timestamp"]
        if t.tzinfo is None:
            return t.replace(tzinfo=timezone.utc)
        return t

    events.sort(key=_sort_key)

    actual_duration = _calculate_actual_duration(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "scheduled_at": session.scheduled_at,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "duration_minutes": session.duration_minutes,
        "actual_duration_minutes": actual_duration,
        "events": events
    }


def get_session_participants(
    db: Session,
    session_id: int,
    current_user_id: int
) -> dict:
    """
    Authoritatively returns structured participant cards (Mentor & Learner)
    with real database user and profile metadata.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if current_user_id not in (session.mentor_id, session.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this session's participants."
        )

    mentor = db.query(User).filter(User.id == session.mentor_id).first()
    learner = db.query(User).filter(User.id == session.requester_id).first()
    skill = db.query(Skill).filter(Skill.id == session.skill_id).first()

    def _extract_profile(user_obj):
        if not user_obj or not getattr(user_obj, "profile", None):
            return None
        prof = user_obj.profile
        if isinstance(prof, list):
            return prof[0] if prof else None
        return prof

    m_prof = _extract_profile(mentor)
    l_prof = _extract_profile(learner)

    from app.services.feedback_service import my_rating

    mentor_data = {
        "id": mentor.id if mentor else session.mentor_id,
        "name": mentor.name if mentor else "Mentor",
        "email": mentor.email if mentor else "",
        "avatar_url": m_prof.avatar_url if m_prof else None,
        "department": m_prof.department if m_prof else None,
        "year": m_prof.year if m_prof and m_prof.year else 1,
        "bio": m_prof.bio if m_prof else None,
        "average_rating": my_rating(db, mentor.id) if mentor else 0.0,
    }

    learner_data = {
        "id": learner.id if learner else session.requester_id,
        "name": learner.name if learner else "Learner",
        "email": learner.email if learner else "",
        "avatar_url": l_prof.avatar_url if l_prof else None,
        "department": l_prof.department if l_prof else None,
        "year": l_prof.year if l_prof and l_prof.year else 1,
        "bio": l_prof.bio if l_prof else None,
    }

    skill_data = {
        "id": skill.id if skill else session.skill_id,
        "name": skill.name if skill else "Peer Mentoring",
        "category": skill.category if skill else "General"
    }

    current_role = "mentor" if current_user_id == session.mentor_id else "learner"

    return {
        "session_id": session.id,
        "current_user_role": current_role,
        "mentor": mentor_data,
        "learner": learner_data,
        "skill": skill_data,
        "status": session.status,
        "scheduled_at": session.scheduled_at.isoformat() if session.scheduled_at else None,
        "duration_minutes": session.duration_minutes,
        "meeting_link": session.meeting_link,
        "meeting_room_id": session.meeting_room_id
    }


def session_dashboard(
    db: Session,
    user_id: int
) -> dict:
    return {
        "upcoming_sessions": count_sessions_by_status(db, user_id, "scheduled") + count_sessions_by_status(db, user_id, "in_progress"),
        "completed_sessions": count_sessions_by_status(db, user_id, "completed"),
        "cancelled_sessions": count_sessions_by_status(db, user_id, "cancelled")
    }
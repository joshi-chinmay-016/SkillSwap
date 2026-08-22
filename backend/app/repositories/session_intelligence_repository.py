from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.session_note import SessionNote
from app.models.session_topic import SessionTopic
from app.models.session_action_item import SessionActionItem
from app.models.session_intelligence import SessionIntelligence


# --- Session Notes Repository ---
def get_session_note_by_user(db: Session, session_id: int, user_id: int) -> Optional[SessionNote]:
    return (
        db.query(SessionNote)
        .filter(SessionNote.session_id == session_id, SessionNote.user_id == user_id)
        .first()
    )


def get_all_notes_for_session(db: Session, session_id: int) -> List[SessionNote]:
    return (
        db.query(SessionNote)
        .filter(SessionNote.session_id == session_id)
        .order_by(SessionNote.created_at.asc())
        .all()
    )


def upsert_session_note(
    db: Session,
    session_id: int,
    user_id: int,
    role: str,
    notes_data: dict
) -> SessionNote:
    note = get_session_note_by_user(db, session_id, user_id)
    if note:
        note.notes_data = notes_data
        note.role = role
        note.updated_at = datetime.now(timezone.utc)
    else:
        note = SessionNote(
            session_id=session_id,
            user_id=user_id,
            role=role,
            notes_data=notes_data
        )
        db.add(note)

    db.commit()
    db.refresh(note)
    return note


# --- Session Topics Repository ---
def get_session_topics(db: Session, session_id: int) -> List[SessionTopic]:
    return (
        db.query(SessionTopic)
        .filter(SessionTopic.session_id == session_id)
        .order_by(SessionTopic.created_at.asc())
        .all()
    )


def create_session_topic(
    db: Session,
    session_id: int,
    topic_name: str,
    skill_id: Optional[int] = None,
    source: str = "user_input",
    confidence: float = 1.0
) -> SessionTopic:
    # Check for existing topic on session to avoid duplicates
    existing = (
        db.query(SessionTopic)
        .filter(
            SessionTopic.session_id == session_id,
            SessionTopic.topic_name.ilike(topic_name.strip())
        )
        .first()
    )
    if existing:
        return existing

    topic = SessionTopic(
        session_id=session_id,
        topic_name=topic_name.strip(),
        skill_id=skill_id,
        source=source,
        confidence=confidence
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


# --- Session Action Items Repository ---
def get_session_action_items(db: Session, session_id: int) -> List[SessionActionItem]:
    return (
        db.query(SessionActionItem)
        .filter(SessionActionItem.session_id == session_id)
        .order_by(SessionActionItem.created_at.asc())
        .all()
    )


def create_action_item(
    db: Session,
    session_id: int,
    user_id: int,
    title: str,
    description: Optional[str] = None,
    source: str = "user_input"
) -> SessionActionItem:
    item = SessionActionItem(
        session_id=session_id,
        user_id=user_id,
        title=title.strip(),
        description=description.strip() if description else None,
        status="pending",
        source=source
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_action_item_by_id(db: Session, item_id: int) -> Optional[SessionActionItem]:
    return db.query(SessionActionItem).filter(SessionActionItem.id == item_id).first()


def update_action_item(
    db: Session,
    item: SessionActionItem,
    status: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> SessionActionItem:
    if status is not None:
        item.status = status
        if status == "completed":
            item.completed_at = datetime.now(timezone.utc)
        else:
            item.completed_at = None

    if title is not None:
        item.title = title.strip()
    if description is not None:
        item.description = description.strip()

    db.commit()
    db.refresh(item)
    return item


def delete_action_item(db: Session, item: SessionActionItem) -> None:
    db.delete(item)
    db.commit()


# --- Session Intelligence Repository ---
def get_session_intelligence(db: Session, session_id: int) -> Optional[SessionIntelligence]:
    return (
        db.query(SessionIntelligence)
        .filter(SessionIntelligence.session_id == session_id)
        .first()
    )


def upsert_session_intelligence(
    db: Session,
    session_id: int,
    status: str,
    summary: Optional[str],
    topics_covered: list,
    skills_taught: list,
    skills_learned: list,
    key_takeaways: list,
    mentor_notes_summary: Optional[str],
    learner_notes_summary: Optional[str],
    recommended_next_steps: list,
    provenance: dict
) -> SessionIntelligence:
    intel = get_session_intelligence(db, session_id)
    if intel:
        intel.status = status
        intel.summary = summary
        intel.topics_covered = topics_covered
        intel.skills_taught = skills_taught
        intel.skills_learned = skills_learned
        intel.key_takeaways = key_takeaways
        intel.mentor_notes_summary = mentor_notes_summary
        intel.learner_notes_summary = learner_notes_summary
        intel.recommended_next_steps = recommended_next_steps
        intel.provenance = provenance
        intel.updated_at = datetime.now(timezone.utc)
    else:
        intel = SessionIntelligence(
            session_id=session_id,
            status=status,
            summary=summary,
            topics_covered=topics_covered,
            skills_taught=skills_taught,
            skills_learned=skills_learned,
            key_takeaways=key_takeaways,
            mentor_notes_summary=mentor_notes_summary,
            learner_notes_summary=learner_notes_summary,
            recommended_next_steps=recommended_next_steps,
            provenance=provenance
        )
        db.add(intel)

    db.commit()
    db.refresh(intel)
    return intel

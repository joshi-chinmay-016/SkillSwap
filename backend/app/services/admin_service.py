"""
SkillSwap Arena — Admin Operations Service (Phase 8.3)

Provides authoritative backend business logic for all administrative console operations,
ensuring security, transactional integrity, and comprehensive audit logging.
"""
import time
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.session import Session as SessionModel
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.report import Report
from app.models.admin_audit_log import AdminAuditLog
from app.services.audit_service import log_admin_action
from app.infrastructure.redis import check_redis_health

START_TIME = time.time()


# =========================================================================
# 1. Admin Dashboard Real Metrics
# =========================================================================
def get_admin_dashboard_metrics(db: Session) -> Dict[str, Any]:
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    suspended_users = total_users - active_users

    # Verified mentors (distinct users with verified teaching capability)
    verified_mentors = (
        db.query(func.count(func.distinct(UserSkill.user_id)))
        .filter(UserSkill.type == "TEACH", UserSkill.verification_status == "VERIFIED")
        .scalar()
        or 0
    )

    # Session metrics
    sessions_completed = (
        db.query(func.count(SessionModel.id))
        .filter(SessionModel.status == "completed")
        .scalar()
        or 0
    )
    upcoming_sessions = (
        db.query(func.count(SessionModel.id))
        .filter(SessionModel.status == "scheduled")
        .scalar()
        or 0
    )
    cancelled_sessions = (
        db.query(func.count(SessionModel.id))
        .filter(SessionModel.status == "cancelled")
        .scalar()
        or 0
    )
    total_sessions = db.query(func.count(SessionModel.id)).scalar() or 0

    # Verification queue
    pending_verifications = (
        db.query(func.count(UserSkill.id))
        .filter(UserSkill.type == "TEACH", UserSkill.verification_status == "CLAIMED")
        .scalar()
        or 0
    )

    # Moderation reports
    open_reports = (
        db.query(func.count(Report.id))
        .filter(Report.status.in_(["OPEN", "UNDER_REVIEW"]))
        .scalar()
        or 0
    )

    # Wallet metrics
    total_transactions = db.query(func.count(WalletTransaction.id)).scalar() or 0
    total_coin_circulation = db.query(func.sum(Wallet.balance)).scalar() or 0

    # Redis health
    redis_health = check_redis_health()

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "suspended": suspended_users,
        },
        "mentors": {
            "verified_count": verified_mentors,
            "pending_verifications": pending_verifications,
        },
        "sessions": {
            "total": total_sessions,
            "completed": sessions_completed,
            "upcoming": upcoming_sessions,
            "cancelled": cancelled_sessions,
            "completion_rate": round((sessions_completed / total_sessions * 100), 1) if total_sessions > 0 else 0.0,
        },
        "wallet": {
            "total_circulation": total_coin_circulation,
            "total_transactions": total_transactions,
        },
        "moderation": {
            "open_reports": open_reports,
        },
        "system": {
            "status": "healthy" if redis_health["status"] in ("healthy", "degraded") else "degraded",
            "redis": redis_health["status"],
            "uptime_seconds": int(time.time() - START_TIME),
        }
    }


# =========================================================================
# 2. User Management
# =========================================================================
def get_admin_users(
    db: Session,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    size: int = 20,
) -> Dict[str, Any]:
    query = db.query(User)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.name.ilike(term), User.email.ilike(term)))

    if role and role.strip():
        query = query.filter(User.role == role.strip().upper())

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    offset = (page - 1) * size
    users = query.order_by(desc(User.id)).offset(offset).limit(size).all()

    items = []
    for u in users:
        profile = getattr(u, "profile", None)
        wallet = db.query(Wallet).filter(Wallet.user_id == u.id).first()

        teach_skills = [
            {"name": us.skill.name, "status": us.verification_status, "score": us.score}
            for us in getattr(u, "user_skills", [])
            if (us.type or "").upper() == "TEACH" and getattr(us, "skill", None)
        ]
        learn_skills = [
            us.skill.name
            for us in getattr(u, "user_skills", [])
            if (us.type or "").upper() == "LEARN" and getattr(us, "skill", None)
        ]

        mentor_session_count = db.query(func.count(SessionModel.id)).filter(SessionModel.mentor_id == u.id).scalar() or 0
        learner_session_count = db.query(func.count(SessionModel.id)).filter(SessionModel.requester_id == u.id).scalar() or 0

        items.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "oauth_provider": u.oauth_provider,
            "avatar_url": getattr(profile, "avatar_url", None),
            "department": getattr(profile, "department", None),
            "year": getattr(profile, "year", None),
            "wallet_balance": wallet.balance if wallet else 0,
            "teaching_skills": teach_skills,
            "learning_skills": learn_skills,
            "sessions": {
                "as_mentor": mentor_session_count,
                "as_learner": learner_session_count,
                "total": mentor_session_count + learner_session_count,
            }
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size if size > 0 else 1,
    }


def suspend_user(
    db: Session,
    admin_user_id: int,
    target_user_id: int,
    reason: str,
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin_user_id:
        raise HTTPException(status_code=400, detail="Cannot suspend your own administrator account.")

    user.is_active = False
    db.commit()
    db.refresh(user)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="SUSPEND_USER",
        target_type="USER",
        target_id=str(user.id),
        reason=reason,
        metadata={"user_email": user.email, "user_name": user.name},
        ip_address=ip_address,
    )

    return {"message": f"User {user.email} suspended successfully", "user_id": user.id, "is_active": False}


def reactivate_user(
    db: Session,
    admin_user_id: int,
    target_user_id: int,
    reason: str,
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()
    db.refresh(user)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="REACTIVATE_USER",
        target_type="USER",
        target_id=str(user.id),
        reason=reason,
        metadata={"user_email": user.email, "user_name": user.name},
        ip_address=ip_address,
    )

    return {"message": f"User {user.email} reactivated successfully", "user_id": user.id, "is_active": True}


def update_user_role(
    db: Session,
    admin_user_id: int,
    target_user_id: int,
    new_role: str,
    reason: str,
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    role_norm = new_role.strip().upper()
    if role_norm not in ["USER", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Invalid role. Supported roles: USER, ADMIN.")

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = role_norm
    db.commit()
    db.refresh(user)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="UPDATE_USER_ROLE",
        target_type="USER",
        target_id=str(user.id),
        reason=reason,
        metadata={"previous_role": old_role, "new_role": role_norm, "user_email": user.email},
        ip_address=ip_address,
    )

    return {"message": f"Role for {user.email} updated to {role_norm}", "user_id": user.id, "role": role_norm}


# =========================================================================
# 3. Platform Skill Management
# =========================================================================
def get_admin_skills(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> Dict[str, Any]:
    query = db.query(Skill)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(Skill.name.ilike(term), Skill.category.ilike(term)))

    if category and category.strip():
        query = query.filter(Skill.category == category.strip())

    total = query.count()
    offset = (page - 1) * size
    skills = query.order_by(Skill.name.asc()).offset(offset).limit(size).all()

    items = []
    for s in skills:
        verified_mentor_count = (
            db.query(func.count(func.distinct(UserSkill.user_id)))
            .filter(UserSkill.skill_id == s.id, UserSkill.type == "TEACH", UserSkill.verification_status == "VERIFIED")
            .scalar()
            or 0
        )
        learner_count = (
            db.query(func.count(func.distinct(UserSkill.user_id)))
            .filter(UserSkill.skill_id == s.id, UserSkill.type == "LEARN")
            .scalar()
            or 0
        )
        session_count = (
            db.query(func.count(SessionModel.id))
            .filter(SessionModel.skill_id == s.id)
            .scalar()
            or 0
        )

        items.append({
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "description": s.description,
            "verified_mentors_count": verified_mentor_count,
            "learners_count": learner_count,
            "total_sessions_count": session_count,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size if size > 0 else 1,
    }


def create_platform_skill(
    db: Session,
    admin_user_id: int,
    name: str,
    category: str,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Skill:
    clean_name = name.strip()
    existing = db.query(Skill).filter(Skill.name.ilike(clean_name)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Skill '{clean_name}' already exists.")

    skill = Skill(
        name=clean_name,
        category=category.strip(),
        description=description.strip() if description else None
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="CREATE_SKILL",
        target_type="SKILL",
        target_id=str(skill.id),
        reason="Admin skill creation",
        metadata={"name": skill.name, "category": skill.category},
        ip_address=ip_address,
    )

    return {
        "id": skill.id,
        "name": skill.name,
        "category": skill.category,
        "description": skill.description
    }


def update_platform_skill(
    db: Session,
    admin_user_id: int,
    skill_id: int,
    name: str,
    category: str,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    old_meta = {"name": skill.name, "category": skill.category}
    skill.name = name.strip()
    skill.category = category.strip()
    if description is not None:
        skill.description = description.strip()

    db.commit()
    db.refresh(skill)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="UPDATE_SKILL",
        target_type="SKILL",
        target_id=str(skill.id),
        reason="Admin skill update",
        metadata={"before": old_meta, "after": {"name": skill.name, "category": skill.category}},
        ip_address=ip_address,
    )

    return {
        "id": skill.id,
        "name": skill.name,
        "category": skill.category,
        "description": skill.description
    }


# =========================================================================
# 4. Mentor / Skill Verification Queue
# =========================================================================
def get_admin_verifications(
    db: Session,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> Dict[str, Any]:
    query = (
        db.query(UserSkill, User, Skill)
        .join(User, UserSkill.user_id == User.id)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.type == "TEACH")
    )

    if status_filter and status_filter.strip():
        query = query.filter(UserSkill.verification_status == status_filter.strip().upper())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.name.ilike(term), User.email.ilike(term), Skill.name.ilike(term)))

    total = query.count()
    offset = (page - 1) * size
    results = query.order_by(desc(UserSkill.claimed_at)).offset(offset).limit(size).all()

    items = []
    for us, user, skill in results:
        items.append({
            "id": us.id,
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email,
            "skill_id": skill.id,
            "skill_name": skill.name,
            "skill_category": skill.category,
            "verification_status": us.verification_status,
            "score": us.score,
            "claimed_at": us.claimed_at.isoformat() if us.claimed_at else None,
            "verified_at": us.verified_at.isoformat() if us.verified_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size if size > 0 else 1,
    }


def approve_skill_verification(
    db: Session,
    admin_user_id: int,
    user_skill_id: int,
    reason: str,
    score_override: Optional[float] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    us = db.query(UserSkill).filter(UserSkill.id == user_skill_id).first()
    if not us:
        raise HTTPException(status_code=404, detail="Verification record not found")

    us.verification_status = "VERIFIED"
    us.verified_at = datetime.now(timezone.utc)
    if score_override is not None:
        us.score = score_override
    elif us.score is None:
        us.score = 100.0

    db.commit()
    db.refresh(us)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="APPROVE_VERIFICATION",
        target_type="USER_SKILL",
        target_id=str(us.id),
        reason=reason,
        metadata={"user_id": us.user_id, "skill_id": us.skill_id, "score": us.score},
        ip_address=ip_address,
    )

    return {"message": "Skill verification approved successfully", "id": us.id, "status": "VERIFIED"}


def reject_skill_verification(
    db: Session,
    admin_user_id: int,
    user_skill_id: int,
    reason: str,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    us = db.query(UserSkill).filter(UserSkill.id == user_skill_id).first()
    if not us:
        raise HTTPException(status_code=404, detail="Verification record not found")

    us.verification_status = "REJECTED"
    db.commit()
    db.refresh(us)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="REJECT_VERIFICATION",
        target_type="USER_SKILL",
        target_id=str(us.id),
        reason=reason,
        metadata={"user_id": us.user_id, "skill_id": us.skill_id},
        ip_address=ip_address,
    )

    return {"message": "Skill verification rejected", "id": us.id, "status": "REJECTED"}


# =========================================================================
# 5. Admin Session Management & Cancellations
# =========================================================================
def get_admin_sessions(
    db: Session,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> Dict[str, Any]:
    query = (
        db.query(SessionModel)
    )

    if status_filter and status_filter.strip():
        query = query.filter(SessionModel.status == status_filter.strip().lower())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.join(Skill, SessionModel.skill_id == Skill.id).filter(Skill.name.ilike(term))

    total = query.count()
    offset = (page - 1) * size
    sessions = query.order_by(desc(SessionModel.scheduled_at)).offset(offset).limit(size).all()

    items = []
    for s in sessions:
        items.append({
            "id": s.id,
            "scheduled_at": s.scheduled_at.isoformat() if s.scheduled_at else None,
            "duration_minutes": s.duration_minutes,
            "status": s.status,
            "meeting_link": s.meeting_link,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "mentor": {
                "id": s.mentor.id if s.mentor else s.mentor_id,
                "name": s.mentor.name if s.mentor else "Unknown",
                "email": s.mentor.email if s.mentor else "Unknown",
            },
            "learner": {
                "id": s.requester.id if s.requester else s.requester_id,
                "name": s.requester.name if s.requester else "Unknown",
                "email": s.requester.email if s.requester else "Unknown",
            },
            "skill": {
                "id": s.skill.id if s.skill else s.skill_id,
                "name": s.skill.name if s.skill else "Unknown",
            }
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size if size > 0 else 1,
    }


def cancel_session_administratively(
    db: Session,
    admin_user_id: int,
    session_id: int,
    reason: str,
    refund_coins: bool = True,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel a session in status '{session.status}'.")

    session.status = "cancelled"

    # Optional refund coins to learner
    refund_issued = False
    if refund_coins:
        learner_wallet = db.query(Wallet).filter(Wallet.user_id == session.requester_id).first()
        if learner_wallet:
            learner_wallet.balance += 1
            tx = WalletTransaction(
                user_id=session.requester_id,
                amount=1,
                type="REFUND",
                reason=f"Administrative session refund: {reason.strip()}"
            )
            db.add(tx)
            refund_issued = True

    db.commit()
    db.refresh(session)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="ADMIN_CANCEL_SESSION",
        target_type="SESSION",
        target_id=str(session.id),
        reason=reason,
        metadata={
            "session_id": session.id,
            "mentor_id": session.mentor_id,
            "learner_id": session.requester_id,
            "refund_issued": refund_issued
        },
        ip_address=ip_address,
    )

    return {
        "message": "Session cancelled administratively",
        "session_id": session.id,
        "status": "cancelled",
        "refund_issued": refund_issued
    }


# =========================================================================
# 6. Moderation / Report Management
# =========================================================================
def get_admin_reports(
    db: Session,
    status_filter: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> Dict[str, Any]:
    query = db.query(Report)

    if status_filter and status_filter.strip():
        query = query.filter(Report.status == status_filter.strip().upper())

    total = query.count()
    offset = (page - 1) * size
    reports = query.order_by(desc(Report.created_at)).offset(offset).limit(size).all()

    items = []
    for r in reports:
        items.append({
            "id": r.id,
            "reason": r.reason,
            "status": r.status,
            "resolution_notes": r.resolution_notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            "reporter": {
                "id": r.reporter.id if r.reporter else r.reporter_id,
                "name": r.reporter.name if r.reporter else "Unknown",
                "email": r.reporter.email if r.reporter else "Unknown",
            },
            "reported_user": {
                "id": r.reported_user.id if r.reported_user else r.reported_user_id,
                "name": r.reported_user.name if r.reported_user else "None",
                "email": r.reported_user.email if r.reported_user else "None",
            } if r.reported_user_id else None,
            "session_id": r.session_id,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size if size > 0 else 1,
    }


def resolve_report(
    db: Session,
    admin_user_id: int,
    report_id: int,
    status: str,
    resolution_notes: str,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    valid_statuses = ["UNDER_REVIEW", "RESOLVED", "DISMISSED"]
    norm_status = status.strip().upper()
    if norm_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {valid_statuses}")

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = norm_status
    report.resolution_notes = resolution_notes.strip()
    report.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(report)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="RESOLVE_REPORT",
        target_type="REPORT",
        target_id=str(report.id),
        reason=resolution_notes,
        metadata={"new_status": norm_status, "report_id": report.id},
        ip_address=ip_address,
    )

    return {"message": f"Report #{report.id} updated to {norm_status}", "id": report.id, "status": norm_status}


# =========================================================================
# 7. Wallet Oversight & Administrative Adjustments
# =========================================================================
def get_admin_wallet_overview(
    db: Session,
    page: int = 1,
    size: int = 50,
) -> Dict[str, Any]:
    total_circulation = db.query(func.sum(Wallet.balance)).scalar() or 0
    total_tx_count = db.query(func.count(WalletTransaction.id)).scalar() or 0

    offset = (page - 1) * size
    txs = (
        db.query(WalletTransaction, User)
        .join(User, WalletTransaction.user_id == User.id)
        .order_by(desc(WalletTransaction.created_at))
        .offset(offset)
        .limit(size)
        .all()
    )

    items = []
    for tx, user in txs:
        items.append({
            "id": tx.id,
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email,
            "amount": tx.amount,
            "type": tx.type,
            "reason": tx.reason,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        })

    return {
        "total_circulation": total_circulation,
        "total_transactions": total_tx_count,
        "items": items,
        "page": page,
        "size": size,
        "total_pages": (total_tx_count + size - 1) // size if size > 0 else 1,
    }


def adjust_user_wallet(
    db: Session,
    admin_user_id: int,
    target_user_id: int,
    amount: int,
    reason: str,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    if amount == 0:
        raise HTTPException(status_code=400, detail="Adjustment amount cannot be zero.")

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wallet = db.query(Wallet).filter(Wallet.user_id == target_user_id).first()
    if not wallet:
        wallet = Wallet(user_id=target_user_id, balance=0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    if wallet.balance + amount < 0:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Current balance is {wallet.balance}.")

    wallet.balance += amount
    tx_type = "REWARD" if amount > 0 else "PENALTY"
    tx = WalletTransaction(
        user_id=target_user_id,
        amount=amount,
        type=tx_type,
        reason=f"Admin adjustment: {reason.strip()}"
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)

    log_admin_action(
        db=db,
        admin_user_id=admin_user_id,
        action="ADJUST_WALLET",
        target_type="WALLET",
        target_id=str(wallet.id),
        reason=reason,
        metadata={"user_id": target_user_id, "amount": amount, "new_balance": wallet.balance},
        ip_address=ip_address,
    )

    return {
        "message": f"Successfully adjusted wallet for {user.email} by {amount} coins.",
        "user_id": target_user_id,
        "new_balance": wallet.balance,
        "amount_adjusted": amount
    }


# =========================================================================
# 8. Platform Analytics (Real DB Aggregations)
# =========================================================================
def get_admin_analytics(db: Session) -> Dict[str, Any]:
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_sessions = db.query(func.count(SessionModel.id)).scalar() or 0
    completed_sessions = db.query(func.count(SessionModel.id)).filter(SessionModel.status == "completed").scalar() or 0
    cancelled_sessions = db.query(func.count(SessionModel.id)).filter(SessionModel.status == "cancelled").scalar() or 0

    # Top popular skills by verified mentors and sessions
    top_skills_raw = (
        db.query(Skill.name, func.count(UserSkill.id).label("mentor_count"))
        .join(UserSkill, Skill.id == UserSkill.skill_id)
        .filter(UserSkill.type == "TEACH", UserSkill.verification_status == "VERIFIED")
        .group_by(Skill.id, Skill.name)
        .order_by(desc("mentor_count"))
        .limit(8)
        .all()
    )
    top_skills = [{"name": name, "mentors": count} for name, count in top_skills_raw]

    # Session status breakdown
    status_counts = (
        db.query(SessionModel.status, func.count(SessionModel.id))
        .group_by(SessionModel.status)
        .all()
    )
    session_breakdown = [{"status": s.capitalize(), "count": count} for s, count in status_counts]

    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "cancelled_sessions": cancelled_sessions,
        "completion_rate": round((completed_sessions / total_sessions * 100), 1) if total_sessions > 0 else 0.0,
        "top_skills": top_skills,
        "session_breakdown": session_breakdown,
    }


# =========================================================================
# 9. Operational System Diagnostics
# =========================================================================
def get_admin_system_health(db: Session) -> Dict[str, Any]:
    # 1. DB ping & latency
    db_start = time.time()
    try:
        db.execute(sa_text("SELECT 1"))
        db_latency_ms = round((time.time() - db_start) * 1000, 2)
        db_status = "healthy"
    except Exception as e:
        db_latency_ms = -1
        db_status = f"unhealthy ({str(e)})"

    # 2. Redis status & latency
    redis_info = check_redis_health()

    # 3. Process & Memory stats
    uptime_sec = int(time.time() - START_TIME)

    return {
        "status": "healthy" if db_status == "healthy" and redis_info["status"] in ("healthy", "degraded") else "degraded",
        "database": {
            "status": db_status,
            "latency_ms": db_latency_ms,
        },
        "redis": {
            "status": redis_info["status"],
            "latency_ms": redis_info.get("latency_ms", 0),
        },
        "environment": os.getenv("ENVIRONMENT", "production"),
        "version": "1.0.0",
        "uptime_seconds": uptime_sec,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }

from sqlalchemy import text as sa_text

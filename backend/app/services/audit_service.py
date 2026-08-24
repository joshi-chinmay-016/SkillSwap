"""
SkillSwap Arena — Admin Audit Logging Service (Phase 8.4)

Provides append-only, tamper-resistant audit logging for all administrative operations.
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.admin_audit_log import AdminAuditLog
from app.models.user import User

logger = logging.getLogger("skillswap.audit")


def log_admin_action(
    db: Session,
    admin_user_id: Optional[int],
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AdminAuditLog:
    """
    Appends an immutable audit log entry for sensitive administrative operations.
    """
    metadata_str = None
    if metadata is not None:
        try:
            metadata_str = json.dumps(metadata, default=str)
        except Exception:
            metadata_str = str(metadata)

    log_entry = AdminAuditLog(
        admin_user_id=admin_user_id,
        action=action.upper().strip(),
        target_type=target_type.upper().strip(),
        target_id=str(target_id) if target_id is not None else None,
        reason=reason.strip() if reason else None,
        metadata_json=metadata_str,
        ip_address=ip_address,
    )

    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    logger.info(
        f"ADMIN_AUDIT: admin={admin_user_id} action={log_entry.action} target={log_entry.target_type}:{log_entry.target_id} reason={log_entry.reason}"
    )
    return log_entry


def get_audit_logs(
    db: Session,
    action: Optional[str] = None,
    admin_user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> Dict[str, Any]:
    """
    Retrieves filtered, paginated audit logs for administrative inspection.
    """
    query = db.query(AdminAuditLog)

    if action and action.strip():
        query = query.filter(AdminAuditLog.action.ilike(f"%{action.strip()}%"))

    if admin_user_id is not None:
        query = query.filter(AdminAuditLog.admin_user_id == admin_user_id)

    if target_type and target_type.strip():
        query = query.filter(AdminAuditLog.target_type == target_type.strip().upper())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (AdminAuditLog.action.ilike(term))
            | (AdminAuditLog.reason.ilike(term))
            | (AdminAuditLog.target_id.ilike(term))
            | (AdminAuditLog.target_type.ilike(term))
        )

    total_count = query.count()

    offset = (page - 1) * size
    items = (
        query.order_by(desc(AdminAuditLog.created_at))
        .offset(offset)
        .limit(size)
        .all()
    )

    # Format entries
    formatted = []
    for item in items:
        admin_name = item.admin_user.name if item.admin_user else "System / CLI"
        admin_email = item.admin_user.email if item.admin_user else None

        parsed_meta = {}
        if item.metadata_json:
            try:
                parsed_meta = json.loads(item.metadata_json)
            except Exception:
                parsed_meta = {"raw": item.metadata_json}

        formatted.append({
            "id": item.id,
            "admin_user_id": item.admin_user_id,
            "admin_name": admin_name,
            "admin_email": admin_email,
            "action": item.action,
            "target_type": item.target_type,
            "target_id": item.target_id,
            "reason": item.reason,
            "metadata": parsed_meta,
            "ip_address": item.ip_address,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })

    return {
        "items": formatted,
        "total": total_count,
        "page": page,
        "size": size,
        "total_pages": (total_count + size - 1) // size if size > 0 else 1,
    }

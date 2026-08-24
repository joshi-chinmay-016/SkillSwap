"""
SkillSwap Arena — Admin API Endpoints (Phase 8.3 & 8.4)

Protected platform administration routes. All routes strictly require ADMIN role.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_guards import require_admin
from app.models.user import User
from app.infrastructure.redis import get_client_ip
from app.services.admin_service import (
    get_admin_dashboard_metrics,
    get_admin_users,
    suspend_user,
    reactivate_user,
    update_user_role,
    get_admin_skills,
    create_platform_skill,
    update_platform_skill,
    get_admin_verifications,
    approve_skill_verification,
    reject_skill_verification,
    get_admin_sessions,
    cancel_session_administratively,
    get_admin_reports,
    resolve_report,
    get_admin_wallet_overview,
    adjust_user_wallet,
    get_admin_analytics,
    get_admin_system_health,
)
from app.services.audit_service import get_audit_logs

router = APIRouter(
    prefix="/admin",
    tags=["Admin Platform"],
    dependencies=[Depends(require_admin)]
)


# =========================================================================
# Request Schemas
# =========================================================================
class ReasonRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Mandatory explanation for audit trail")


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(USER|ADMIN)$", description="New platform role")
    reason: str = Field(..., min_length=3, description="Audit reason for role change")


class CreateSkillRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class UpdateSkillRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class VerificationApprovalRequest(BaseModel):
    reason: str = Field(..., min_length=3)
    score_override: Optional[float] = Field(None, ge=0.0, le=100.0)


class SessionCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3)
    refund_coins: bool = True


class ReportResolveRequest(BaseModel):
    status: str = Field(..., pattern="^(UNDER_REVIEW|RESOLVED|DISMISSED)$")
    resolution_notes: str = Field(..., min_length=3)


class WalletAdjustRequest(BaseModel):
    target_user_id: int
    amount: int = Field(..., description="Positive for reward, negative for deduction")
    reason: str = Field(..., min_length=3)


# =========================================================================
# 1. Dashboard
# =========================================================================
@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_dashboard_metrics(db)


# =========================================================================
# 2. User Management
# =========================================================================
@router.get("/users")
def list_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_users(db, search=search, role=role, is_active=is_active, page=page, size=size)


@router.post("/users/{user_id}/suspend")
def suspend_user_endpoint(
    user_id: int,
    body: ReasonRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return suspend_user(db, admin_user_id=admin.id, target_user_id=user_id, reason=body.reason, ip_address=client_ip)


@router.post("/users/{user_id}/reactivate")
def reactivate_user_endpoint(
    user_id: int,
    body: ReasonRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return reactivate_user(db, admin_user_id=admin.id, target_user_id=user_id, reason=body.reason, ip_address=client_ip)


@router.post("/users/{user_id}/role")
def change_user_role_endpoint(
    user_id: int,
    body: RoleUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return update_user_role(db, admin_user_id=admin.id, target_user_id=user_id, new_role=body.role, reason=body.reason, ip_address=client_ip)


# =========================================================================
# 3. Platform Skills
# =========================================================================
@router.get("/skills")
def list_skills(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_skills(db, search=search, category=category, page=page, size=size)


@router.post("/skills")
def create_skill_endpoint(
    body: CreateSkillRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return create_platform_skill(
        db, admin_user_id=admin.id, name=body.name, category=body.category, description=body.description, ip_address=client_ip
    )


@router.put("/skills/{skill_id}")
def update_skill_endpoint(
    skill_id: int,
    body: UpdateSkillRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return update_platform_skill(
        db, admin_user_id=admin.id, skill_id=skill_id, name=body.name, category=body.category, description=body.description, ip_address=client_ip
    )


# =========================================================================
# 4. Mentor / Skill Verification
# =========================================================================
@router.get("/verification")
def list_verifications(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_verifications(db, status_filter=status, search=search, page=page, size=size)


@router.post("/verification/{user_skill_id}/approve")
def approve_verification_endpoint(
    user_skill_id: int,
    body: VerificationApprovalRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return approve_skill_verification(
        db, admin_user_id=admin.id, user_skill_id=user_skill_id, reason=body.reason, score_override=body.score_override, ip_address=client_ip
    )


@router.post("/verification/{user_skill_id}/reject")
def reject_verification_endpoint(
    user_skill_id: int,
    body: ReasonRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return reject_skill_verification(
        db, admin_user_id=admin.id, user_skill_id=user_skill_id, reason=body.reason, ip_address=client_ip
    )


# =========================================================================
# 5. Sessions
# =========================================================================
@router.get("/sessions")
def list_sessions(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_sessions(db, status_filter=status, search=search, page=page, size=size)


@router.post("/sessions/{session_id}/cancel")
def cancel_session_endpoint(
    session_id: int,
    body: SessionCancelRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return cancel_session_administratively(
        db, admin_user_id=admin.id, session_id=session_id, reason=body.reason, refund_coins=body.refund_coins, ip_address=client_ip
    )


# =========================================================================
# 6. Moderation Reports
# =========================================================================
@router.get("/reports")
def list_reports(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_reports(db, status_filter=status, page=page, size=size)


@router.post("/reports/{report_id}/resolve")
def resolve_report_endpoint(
    report_id: int,
    body: ReportResolveRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return resolve_report(
        db, admin_user_id=admin.id, report_id=report_id, status=body.status, resolution_notes=body.resolution_notes, ip_address=client_ip
    )


# =========================================================================
# 7. Wallet Oversight
# =========================================================================
@router.get("/wallet")
def get_wallet_feed(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_wallet_overview(db, page=page, size=size)


@router.post("/wallet/adjust")
def adjust_wallet_endpoint(
    body: WalletAdjustRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    client_ip = get_client_ip(http_request)
    return adjust_user_wallet(
        db, admin_user_id=admin.id, target_user_id=body.target_user_id, amount=body.amount, reason=body.reason, ip_address=client_ip
    )


# =========================================================================
# 8. Analytics
# =========================================================================
@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_analytics(db)


# =========================================================================
# 9. System Diagnostics
# =========================================================================
@router.get("/system/health")
def get_system_health(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_admin_system_health(db)


# =========================================================================
# 10. Audit Logs
# =========================================================================
@router.get("/audit-logs")
def list_audit_logs(
    action: Optional[str] = Query(None),
    admin_user_id: Optional[int] = Query(None),
    target_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return get_audit_logs(
        db, action=action, admin_user_id=admin_user_id, target_type=target_type, search=search, page=page, size=size
    )

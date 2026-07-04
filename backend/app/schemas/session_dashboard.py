from pydantic import BaseModel


class SessionDashboardResponse(
    BaseModel
):

    upcoming_sessions: int

    completed_sessions: int

    cancelled_sessions: int
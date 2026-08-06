from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware
)

app = FastAPI(
    title="SkillSwap Arena",
    version="1.0.0"
)

from app.models.base import Base
from app.core.database import engine
import app.models.mentor_memory as _mentor_memory  # Ensures MentorMemory model is registered
import app.models.document as _document  # Ensures Document model is registered

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Auto table creation error: {e}")



origins = [

    "http://localhost:5173",

    "http://127.0.0.1:5173",

    "http://localhost:5174",

    "http://127.0.0.1:5174",

    "http://localhost:3000",

    "http://127.0.0.1:3000",

]

app.add_middleware(

    CORSMiddleware,

    allow_origins=origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"], 

)
from app.api.auth import router as auth_router

from app.api.profiles import (
    router as profiles_router
)

from app.api.skills import (
    router as skills_router
)
from app.api.matches import (
    router as matches_router
)

from app.api.session_requests import (
    router as request_router
)

from app.api.notifications import (
    router as notifications_router
)

from app.api.sessions import (
    router as session_router
)

from app.api.feedback import (
    router as feedback_router
)

from app.api.leaderboard import (
    router as leaderboard_router
)

from app.api.badges import (
    router as badge_router
)

from app.api.dashboard import (
    router as dashboard_router
)
from app.api.recommendations import (
    router as recommendation_router
)
from app.api.analytics import (
    router as analytics_router
)
from app.api.mentors import (
    router as mentor_router
)
from app.api.availability import (
    router as availability_router
)

from app.api.reminders import (
    router as reminder_router
)
from app.api.websocket import (
    router as websocket_router
)
from app.api.wallet import (
    router as wallet_router
)

from app.api.learning_activities import (
    router as learning_activities_router,
    activities_router
)

from app.api.journeys import (
    router as journeys_router
)

from app.api.achievements import (
    router as achievements_router
)

from app.api.ai_context_router import (
    router as ai_context_router
)

from app.api.mentor_memory_router import (
    router as mentor_memory_router
)

from app.api.document_router import (
    router as document_router
)

from app.api.learning_sessions import (
    journey_sessions_router as learning_sessions_journey_router,
    sessions_router as learning_sessions_router
)

""" from here market model"""
from app.market import models as _market_models



# Optional AI routes – guarded to avoid import errors when AI dependencies are missing
try:
    from app.ai.api import (
        ai_router,
        roadmap_router,
        skill_gap_router,
        session_summary_router,
        mentor_recommendation_router,
        ai_mentor_router,
        mentor_conversations_router,
    )
except Exception as e:
    # Log the import error and skip AI routers in environments without the required packages
    import logging
    logging.getLogger(__name__).warning(f"AI routers not loaded due to import error: {e}")
    ai_router = roadmap_router = skill_gap_router = session_summary_router = mentor_recommendation_router = ai_mentor_router = mentor_conversations_router = None

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(skills_router)
app.include_router(matches_router)
app.include_router(request_router)
app.include_router(learning_sessions_journey_router)
app.include_router(learning_sessions_router)
app.include_router(session_router)
app.include_router(feedback_router)
app.include_router(leaderboard_router)
app.include_router(badge_router)
app.include_router(dashboard_router)
app.include_router(recommendation_router)
app.include_router(analytics_router)
app.include_router(mentor_router)
app.include_router(availability_router)
app.include_router(reminder_router)
app.include_router(websocket_router)
app.include_router(wallet_router)
app.include_router(learning_activities_router)
app.include_router(activities_router)
app.include_router(journeys_router)
app.include_router(achievements_router)
app.include_router(ai_context_router)
app.include_router(mentor_memory_router)
app.include_router(document_router)

# Include optional AI routers only if they were successfully imported
if ai_router:
    app.include_router(ai_router)
if roadmap_router:
    app.include_router(roadmap_router)
if skill_gap_router:
    app.include_router(skill_gap_router)
if session_summary_router:
    app.include_router(session_summary_router)
if mentor_recommendation_router:
    app.include_router(mentor_recommendation_router)
if ai_mentor_router:
    app.include_router(ai_mentor_router)
if mentor_conversations_router:
    app.include_router(mentor_conversations_router)




@app.get("/")
def root():
    return {
        "message": "SkillSwap Arena API"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
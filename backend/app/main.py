from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware
)

app = FastAPI(
    title="SkillSwap Arena",
    version="1.0.0"
)

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
    router as learning_activities_router
)

from app.api.journeys import (
    router as journeys_router
)

""" from here market model"""
from app.market import models as _market_models



from app.ai.api import (
    ai_router,
    roadmap_router,
    skill_gap_router,
    session_summary_router,
    mentor_recommendation_router
)

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(skills_router)
app.include_router(matches_router)
app.include_router(request_router)
app.include_router(notifications_router)
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
app.include_router(journeys_router)
app.include_router(ai_router)
app.include_router(roadmap_router)
app.include_router(skill_gap_router)
app.include_router(session_summary_router)
app.include_router(mentor_recommendation_router)

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
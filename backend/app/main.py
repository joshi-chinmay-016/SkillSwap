from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware
)

from app.infrastructure.redis import (
    redis_client,
    check_redis_health,
    start_pubsub_listener,
    stop_pubsub_listener,
)
from app.core.websocket_manager import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await start_pubsub_listener(manager.send_local_notification_payload)
    except Exception as e:
        import logging
        logging.getLogger("skillswap.startup").debug(f"Pub/Sub startup skipped: {e}")
    yield
    # Shutdown
    try:
        await stop_pubsub_listener()
        redis_client.close()
    except Exception:
        pass

app = FastAPI(
    title="SkillSwap Arena",
    version="1.0.0",
    lifespan=lifespan
)

from app.models.base import Base
from app.core.database import engine
import app.models.mentor_memory as _mentor_memory  # Ensures MentorMemory model is registered
import app.models.document as _document  # Ensures Document model is registered
import app.models.parsed_document as _parsed_document  # Ensures ParsedDocument model is registered
import app.models.chunk as _chunk  # Ensures Chunk model is registered (Day 68)
import app.models.embedding as _embedding  # Ensures Embedding model is registered (Day 69)
import app.models.vector_index_entry as _vector_index_entry  # Ensures VectorIndexEntry model is registered (Day 70)


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

from app.api.retrieval_router import (
    router as retrieval_router
)

from app.api.verification import (
    router as verification_router
)

from app.api.session_intelligence import (
    router as session_intelligence_router
)

from app.api.admin import (
    router as admin_router
)


# Optional RAG router — guarded to avoid import errors when RAG deps are missing
try:
    from app.api.rag_router import router as rag_router
except Exception as _rag_import_err:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "RAG router not loaded due to import error: %s", _rag_import_err
    )
    rag_router = None

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
app.include_router(notifications_router)

app.include_router(session_router)
app.include_router(learning_sessions_journey_router)
app.include_router(learning_sessions_router)

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
app.include_router(retrieval_router)
app.include_router(verification_router)
app.include_router(session_intelligence_router)
app.include_router(admin_router)

if rag_router:
    app.include_router(rag_router)

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
    redis_health = check_redis_health()
    return {
        "status": "healthy" if redis_health["status"] in ("healthy", "degraded") else "degraded",
        "redis": redis_health["status"],
    }


@app.get("/health/redis")
def health_redis():
    """Returns safe, unprivileged Redis infrastructure health and latency."""
    return check_redis_health()
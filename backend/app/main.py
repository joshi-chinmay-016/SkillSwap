from fastapi import FastAPI

from app.api.auth import router as auth_router

app = FastAPI(
    title="SkillSwap Arena",
    version="1.0.0"
)
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



app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(skills_router)
app.include_router(matches_router)
app.include_router(request_router)

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
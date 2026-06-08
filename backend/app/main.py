from fastapi import FastAPI

app = FastAPI(
    title="SkillSwap Arena",
    version="1.0.0"
)

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
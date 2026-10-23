from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth import router as auth_router
from backend.api.evaluate import router as evaluate_router
from backend.api.health import router as health_router
from backend.database import initialize_database


app = FastAPI(
    title="AegisEval API",
    description="Automated LLM evaluation and hallucination detection system.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    initialize_database()


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "service": "AegisEval API",
        "message": "Backend is running",
    }


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(evaluate_router)

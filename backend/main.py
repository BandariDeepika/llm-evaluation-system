from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health import router as health_router
from backend.api.evaluate import router as evaluate_router


app = FastAPI(
	title="LLM Evaluation API",
	description="Backend foundation for the automated LLM evaluation system.",
	version="0.1.0",
)

# Development-only CORS settings for the local Streamlit frontend.
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
	"""Return basic information about the API."""
	return {
		"service": "LLM Evaluation API",
		"message": "Backend is running",
	}


app.include_router(health_router)
app.include_router(evaluate_router)

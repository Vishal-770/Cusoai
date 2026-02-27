import logging
import os
import sys
from contextlib import asynccontextmanager

import faiss
import fasttext
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .models import HealthResponse, ModelStatus
from .routers import classify, urgency, pipeline, chat, analyze

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path helpers  (resolve relative to project root regardless of cwd)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FASTTEXT_MODEL_PATH = os.path.join(BASE_DIR, "models", "fasttext_category.bin")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "embeddings", "kb_index.faiss")
KB_METADATA_PATH = os.path.join(BASE_DIR, "embeddings", "kb_metadata.txt")


# ---------------------------------------------------------------------------
# Lifespan — load all models once at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            logger.info("Gemini API configured.")
        except Exception as e:
            logger.warning("Gemini configuration failed: %s — AI replies disabled.", e)
            gemini_key = None
    else:
        logger.warning("GEMINI_API_KEY not set — AI replies disabled.")

    app.state.gemini_api_key = gemini_key

    # --- FastText (critical) ---
    app.state.ft_model = None
    try:
        if not os.path.exists(FASTTEXT_MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {FASTTEXT_MODEL_PATH}")
        logger.info("Loading FastText model from %s …", FASTTEXT_MODEL_PATH)
        app.state.ft_model = fasttext.load_model(FASTTEXT_MODEL_PATH)
        logger.info("FastText model loaded.")
    except Exception as e:
        logger.error("CRITICAL — FastText model failed to load: %s", e)

    # --- VADER (critical) ---
    app.state.vader_analyzer = None
    try:
        app.state.vader_analyzer = SentimentIntensityAnalyzer()
        logger.info("VADER analyzer ready.")
    except Exception as e:
        logger.error("CRITICAL — VADER failed to initialize: %s", e)

    # --- RAG pipeline (optional) ---
    app.state.rag_available = False
    app.state.embed_model = None
    app.state.faiss_index = None
    app.state.policies = {}

    try:
        logger.info("Loading SentenceTransformer …")
        app.state.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer loaded.")

        if not os.path.exists(FAISS_INDEX_PATH):
            raise FileNotFoundError(f"FAISS index not found: {FAISS_INDEX_PATH}")
        app.state.faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        logger.info("FAISS index loaded (%d vectors).", app.state.faiss_index.ntotal)

        if not os.path.exists(KB_METADATA_PATH):
            raise FileNotFoundError(f"KB metadata not found: {KB_METADATA_PATH}")
        policies = {}
        with open(KB_METADATA_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|", 2)
                if len(parts) == 3:
                    idx, fname, content = parts
                    policies[int(idx)] = {"file": fname, "text": content.replace("[NEWLINE]", "\n")}
        app.state.policies = policies
        logger.info("KB metadata loaded (%d entries).", len(policies))

        app.state.rag_available = True
        logger.info("RAG pipeline ready.")
    except Exception as e:
        logger.warning("RAG pipeline disabled: %s", e)

    logger.info(
        "Startup complete — FastText=%s | VADER=%s | RAG=%s",
        app.state.ft_model is not None,
        app.state.vader_analyzer is not None,
        app.state.rag_available,
    )

    yield  # ---- app is running ----

    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Support Ticket AI Engine",
    description="FastText category classification + VADER urgency detection + optional RAG reply generation.",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(classify.router)
app.include_router(urgency.router)
app.include_router(pipeline.router)
app.include_router(chat.router)
app.include_router(analyze.router)


# ---------------------------------------------------------------------------
# Health & root
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Support Ticket AI Engine", "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse, tags=["Meta"], summary="Service health check")
async def health():
    ft_ok = app.state.ft_model is not None
    vader_ok = app.state.vader_analyzer is not None
    rag_ok = app.state.rag_available

    status = "ok" if (ft_ok and vader_ok) else "degraded"
    http_status = 200 if status == "ok" else 503

    return JSONResponse(
        status_code=http_status,
        content={
            "status": status,
            "models": {"fasttext": ft_ok, "vader": vader_ok, "rag": rag_ok},
        },
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

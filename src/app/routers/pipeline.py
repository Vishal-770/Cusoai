import logging
import uuid

from fastapi import APIRouter, HTTPException, Request, Response

from ..models import PipelineResponse, TicketRequest, UrgencyFactors
from ..services.fasttext_service import predict_category
from ..services.vader_service import analyze_urgency
from ..services.rag_service import retrieve_policy, generate_reply

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/process_ticket", tags=["Full Pipeline"])


@router.post("", response_model=PipelineResponse, summary="Full pipeline: classify + urgency + RAG + AI reply")
async def process_ticket(request: TicketRequest, raw: Request, response: Response):
    request_id = str(uuid.uuid4())
    response.headers["X-Request-ID"] = request_id
    logger.info("[%s] /process_ticket — description length=%d", request_id, len(request.description))

    # --- Core models (required) ---
    ft_model = getattr(raw.app.state, "ft_model", None)
    vader_analyzer = getattr(raw.app.state, "vader_analyzer", None)

    if ft_model is None or vader_analyzer is None:
        raise HTTPException(
            status_code=503,
            detail="Core models (FastText / VADER) are not loaded. Check server startup logs.",
        )

    # Step 1: Category (FastText) — required
    try:
        category, confidence = predict_category(ft_model, request.description)
    except RuntimeError as e:
        logger.error("[%s] FastText failed: %s", request_id, e)
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")

    # Step 2: Urgency (VADER + user context) — required
    try:
        urgency, compound, _, urgency_factors = analyze_urgency(
            vader_analyzer, request.description, request.user_context
        )
    except RuntimeError as e:
        logger.error("[%s] VADER failed: %s", request_id, e)
        raise HTTPException(status_code=500, detail=f"Urgency analysis failed: {e}")

    # Step 3: RAG retrieval — optional (degrades gracefully)
    rag_available = raw.app.state.rag_available
    policy_text: str | None = None

    if rag_available:
        embed_model = raw.app.state.embed_model
        faiss_index = raw.app.state.faiss_index
        policies = raw.app.state.policies
        policy_text, _ = retrieve_policy(embed_model, faiss_index, policies, request.description)
        if policy_text is None:
            logger.warning("[%s] FAISS retrieval returned nothing; RAG degraded.", request_id)
            rag_available = False

    # Step 4: AI reply — optional (degrades gracefully)
    gemini_key = getattr(raw.app.state, "gemini_api_key", None)
    ai_reply = generate_reply(gemini_key, request.description, policy_text or "")

    logger.info(
        "[%s] /process_ticket → category=%s urgency=%s rag=%s",
        request_id, category, urgency, rag_available,
    )

    return PipelineResponse(
        category=category,
        category_confidence=confidence,
        urgency=urgency,
        urgency_score=compound,
        urgency_factors=UrgencyFactors(**urgency_factors),
        retrieved_policy=policy_text,
        rag_available=rag_available,
        ai_draft_reply=ai_reply,
    )

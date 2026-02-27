import logging
import uuid

from fastapi import APIRouter, HTTPException, Request, Response

from ..models import TicketRequest, UrgencyFactors, UrgencyResponse, VaderScores
from ..services.vader_service import analyze_urgency

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/urgency", tags=["Urgency"])


@router.post("", response_model=UrgencyResponse, summary="Predict ticket urgency (VADER + user/company context)")
async def urgency_ticket(request: TicketRequest, raw: Request, response: Response):
    request_id = str(uuid.uuid4())
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "[%s] /urgency — length=%d user_tier=%s company=%s open_tickets=%s",
        request_id,
        len(request.description),
        request.user_context.user_tier if request.user_context else "standard",
        request.user_context.company_tier if request.user_context else None,
        request.user_context.previous_open_tickets if request.user_context else 0,
    )

    vader_analyzer = getattr(raw.app.state, "vader_analyzer", None)
    if vader_analyzer is None:
        raise HTTPException(
            status_code=503,
            detail="Urgency model is not loaded. Check server startup logs.",
        )

    try:
        urgency, compound, all_scores, factors = analyze_urgency(
            vader_analyzer, request.description, request.user_context
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    logger.info("[%s] /urgency → %s (composite=%.2f)", request_id, urgency, factors["composite_score"])
    return UrgencyResponse(
        urgency=urgency,
        compound_score=compound,
        all_scores=VaderScores(**all_scores),
        factors=UrgencyFactors(**factors),
    )

import logging
import uuid

from fastapi import APIRouter, HTTPException, Request, Response

from ..models import ClassifyResponse, TicketRequest
from ..services.fasttext_service import predict_category

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/classify", tags=["Classification"])


@router.post("", response_model=ClassifyResponse, summary="Predict issue category (FastText)")
async def classify_ticket(request: TicketRequest, raw: Request, response: Response):
    request_id = str(uuid.uuid4())
    response.headers["X-Request-ID"] = request_id
    logger.info("[%s] /classify — description length=%d", request_id, len(request.description))

    ft_model = getattr(raw.app.state, "ft_model", None)
    if ft_model is None:
        raise HTTPException(
            status_code=503,
            detail="Classification model is not loaded. Check server startup logs.",
        )

    try:
        category, confidence = predict_category(ft_model, request.description)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    logger.info("[%s] /classify → %s (%.4f)", request_id, category, confidence)
    return ClassifyResponse(category=category, confidence=confidence)

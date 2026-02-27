import logging
from typing import Optional

from fastapi import APIRouter, Request

from ..models import ImageAnalysisRequest, ImageAnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze_image", tags=["Vision"])


@router.post("", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest, raw: Request):
    gemini_key: Optional[str] = getattr(raw.app.state, "gemini_api_key", None)
    if not gemini_key:
        return ImageAnalysisResponse(analysis=None, error="Gemini API not configured.")
    try:
        import google.generativeai as genai
        import httpx

        genai.configure(api_key=gemini_key)
        async with httpx.AsyncClient(timeout=15.0) as client:
            img_response = await client.get(request.image_url)
            img_response.raise_for_status()

        image_bytes = img_response.content
        content_type = img_response.headers.get("content-type", "image/jpeg")

        prompt = (
            "You are analyzing an image attached to a customer support ticket.\n\n"
            "Describe EXACTLY what you see:\n"
            "- If it shows a device screen/UI: describe the app, page, and any visible error messages (quote them verbatim)\n"
            "- If it shows an error code or message: state it explicitly\n"
            "- If it shows a document, invoice, or receipt: summarize the key details\n"
            "- If the image appears completely unrelated to any technical, billing, account, or product support issue: "
            "state 'UNRELATED: This image does not appear to relate to a support issue.' and describe what it actually shows\n\n"
            "Be concise (3-5 sentences max). Do not speculate beyond what is visible."
        )

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            {"mime_type": content_type, "data": image_bytes},
            prompt,
        ])
        analysis = response.text.strip()
        logger.info("Image analyzed successfully: %d chars", len(analysis))
        return ImageAnalysisResponse(analysis=analysis)

    except Exception as e:
        logger.error("Image analysis failed: %s", e, exc_info=True)
        return ImageAnalysisResponse(analysis=None, error=str(e))

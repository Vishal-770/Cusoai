import logging
import numpy as np
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def retrieve_policy(embed_model, faiss_index, policies: dict, description: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Embed description and retrieve the best-matching policy from FAISS.
    Returns (policy_text, policy_filename) or (None, None) on failure.
    """
    try:
        query_vector = embed_model.encode([description])
        distances, indices = faiss_index.search(np.array(query_vector).astype("float32"), k=1)
        best_idx = int(indices[0][0])
        entry = policies[best_idx]
        logger.debug("FAISS retrieved policy: %s (dist=%.4f)", entry["file"], distances[0][0])
        return entry["text"], entry["file"]
    except Exception as e:
        logger.error("FAISS retrieval failed: %s", e, exc_info=True)
        return None, None


def generate_reply(gemini_api_key: Optional[str], description: str, policy_text: str) -> str:
    """
    Generate a draft customer reply using Gemini 1.5 Flash.
    Returns fallback string if key is missing or generation fails.
    """
    if not gemini_api_key:
        return "AI draft unavailable: GEMINI_API_KEY not configured."

    try:
        import google.generativeai as genai

        prompt = f"""You are a helpful customer support agent.
A customer sent this ticket: "{description}"
Our internal policy for this issue is: "{policy_text}"

TASK:
1. Analyze the customer's language.
2. Draft a polite, helpful response that solves their problem using ONLY the policy provided.
3. OUTPUT THE RESPONSE IN THE CUSTOMER'S NATIVE LANGUAGE."""

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error("Gemini generation failed: %s", e, exc_info=True)
        # Return a safe human-readable message — never expose raw traceback to client
        reason = type(e).__name__
        return f"AI draft generation failed ({reason}). Please compose a response manually."

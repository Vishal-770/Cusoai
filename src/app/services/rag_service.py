import logging
import numpy as np
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

TOP_K = 3  # number of KB chunks to retrieve


def retrieve_policy(
    embed_model,
    faiss_index,
    policies: dict,
    description: str,
    k: int = TOP_K,
) -> List[Tuple[str, str]]:
    """
    Embed description and retrieve the top-k matching policies from FAISS.
    Returns a list of (policy_text, policy_filename) tuples, ordered by relevance.
    Returns an empty list on failure.
    """
    try:
        n_indexed = faiss_index.ntotal
        k_actual = min(k, n_indexed)  # cannot retrieve more than what is indexed
        query_vector = embed_model.encode([description])
        distances, indices = faiss_index.search(np.array(query_vector).astype("float32"), k=k_actual)
        results: List[Tuple[str, str]] = []
        for rank, idx in enumerate(indices[0]):
            entry = policies[int(idx)]
            logger.debug(
                "FAISS top-%d: %s (dist=%.4f)", rank + 1, entry["file"], distances[0][rank]
            )
            results.append((entry["text"], entry["file"]))
        return results
    except Exception as e:
        logger.error("FAISS retrieval failed: %s", e, exc_info=True)
        return []


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

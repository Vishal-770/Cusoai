import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

_POWER_WORD_PATTERN = re.compile(
    r"\b(asap|urgent|emergency|directly|now|broken|lost|stolen|hacked|immediately|threat)\b",
    re.IGNORECASE,
)


def predict_category(ft_model, description: str) -> Tuple[str, float]:
    """
    Run FastText category prediction.
    Returns (category_label, confidence).
    Raises RuntimeError on failure.
    """
    try:
        desc_clean = description.lower().replace("\n", " ")
        labels, probs = ft_model.predict(desc_clean)
        category = labels[0].replace("__label__", "").replace("_", " ")
        confidence = float(probs[0])
        logger.debug("FastText prediction: %s (%.4f)", category, confidence)
        return category, confidence
    except Exception as e:
        logger.error("FastText prediction failed: %s", e, exc_info=True)
        raise RuntimeError(f"FastText prediction failed: {e}") from e

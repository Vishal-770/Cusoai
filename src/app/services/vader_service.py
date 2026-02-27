"""
Context-aware urgency service.

Urgency is calculated as a weighted composite score (0-14):

  composite = vader_base + user_tier_delta + company_tier_delta + history_delta

Mapping:
  composite >= 10  -> "Critical"
  composite >=  6  -> "High"
  composite >=  3  -> "Medium"
  composite  <  3  -> "Low"

Factor weights:
  vader base (High)      : +7.0
  vader base (Medium)    : +4.0
  vader base (Low)       : +1.5
  user: enterprise       : +3.0
  user: premium          : +2.0
  user: standard         :  0.0
  user: free             : -0.5
  company: enterprise    : +2.0
  company: business      : +1.0
  open tickets >= 5      : +2.0
  open tickets 3-4       : +1.0
  open tickets 1-2       : +0.5
  repeat within 7 days   : +1.0
  account < 30 days old  : +0.5
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_POWER_WORD_PATTERN = re.compile(
    r"\b(asap|urgent|emergency|directly|now|broken|lost|stolen|hacked|immediately|threat)\b",
    re.IGNORECASE,
)

_VADER_BASE: Dict[str, float] = {"High": 7.0, "Medium": 4.0, "Low": 1.5}

_USER_TIER_DELTA: Dict[str, float] = {
    "enterprise": 3.0,
    "premium": 2.0,
    "standard": 0.0,
    "free": -0.5,
}

_COMPANY_TIER_DELTA: Dict[Optional[str], float] = {
    "enterprise": 2.0,
    "business": 1.0,
    "startup": 0.0,
    "individual": 0.0,
    None: 0.0,
}


def _vader_base_urgency(compound: float, has_power_word: bool) -> str:
    """Raw VADER-only urgency (unchanged from v1 — used as the base score)."""
    if compound < -0.5 or has_power_word:
        return "High"
    elif compound > 0.5:
        return "Low"
    return "Medium"


def _map_score(composite: float) -> str:
    if composite >= 10.0:
        return "Critical"
    elif composite >= 6.0:
        return "High"
    elif composite >= 3.0:
        return "Medium"
    return "Low"


def analyze_urgency(
    vader_analyzer,
    description: str,
    user_context=None,  # Optional[UserContext] — typed loosely to avoid circular import
) -> Tuple[str, float, Dict[str, float], Dict]:
    """
    Context-aware urgency analysis.

    Returns:
        (urgency_label, compound_score, all_vader_scores, factors_dict)

    factors_dict is ready to be unpacked into UrgencyFactors(**factors_dict).
    """
    try:
        # --- VADER ---
        scores = vader_analyzer.polarity_scores(description)
        compound: float = scores["compound"]
        has_power_word = bool(_POWER_WORD_PATTERN.search(description))
        vader_base = _vader_base_urgency(compound, has_power_word)

        # --- Context defaults when no user_context provided ---
        user_tier = "standard"
        company_tier = None
        previous_open = 0
        days_since_last = None
        account_age = None

        if user_context is not None:
            user_tier = user_context.user_tier
            company_tier = user_context.company_tier
            previous_open = user_context.previous_open_tickets or 0
            days_since_last = user_context.days_since_last_ticket
            account_age = user_context.account_age_days

        # --- Score contributions ---
        s_vader = _VADER_BASE[vader_base]
        s_user = _USER_TIER_DELTA.get(user_tier, 0.0)
        s_company = _COMPANY_TIER_DELTA.get(company_tier, 0.0)

        s_history = 0.0
        if previous_open >= 5:
            s_history += 2.0
        elif previous_open >= 3:
            s_history += 1.0
        elif previous_open >= 1:
            s_history += 0.5

        if days_since_last is not None and days_since_last <= 7:
            s_history += 1.0  # repeat issue within a week

        if account_age is not None and account_age < 30:
            s_history += 0.5  # brand-new account — needs extra care

        composite = s_vader + s_user + s_company + s_history
        urgency = _map_score(composite)

        factors = {
            "vader_base_urgency": vader_base,
            "vader_compound": compound,
            "user_tier": user_tier,
            "company_tier": company_tier,
            "previous_open_tickets": previous_open,
            "days_since_last_ticket": days_since_last,
            "composite_score": round(composite, 3),
            "score_breakdown": {
                "vader_base": s_vader,
                "user_tier": s_user,
                "company_tier": s_company,
                "ticket_history": round(s_history, 3),
            },
        }

        logger.info(
            "Urgency: %s (composite=%.2f) | vader=%s user=%s company=%s open=%d",
            urgency, composite, vader_base, user_tier, company_tier, previous_open,
        )
        return urgency, compound, scores, factors

    except Exception as e:
        logger.error("VADER analysis failed: %s", e, exc_info=True)
        raise RuntimeError(f"VADER analysis failed: {e}") from e

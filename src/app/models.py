from pydantic import BaseModel, Field
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# User / company context (optional — enriches urgency scoring)
# ---------------------------------------------------------------------------
class UserContext(BaseModel):
    """Optional caller context that feeds the context-aware urgency scorer."""

    user_tier: Literal["free", "standard", "premium", "enterprise"] = Field(
        default="standard",
        description="Subscription tier of the user.",
    )
    company_tier: Optional[Literal["individual", "startup", "business", "enterprise"]] = Field(
        default=None,
        description="Size / tier of the customer's organisation.",
    )
    previous_open_tickets: int = Field(
        default=0,
        ge=0,
        le=10000,
        description="Number of currently open tickets for this user.",
    )
    days_since_last_ticket: Optional[int] = Field(
        default=None,
        ge=0,
        description="Days elapsed since the user's previous ticket. None = first ticket.",
    )
    account_age_days: Optional[int] = Field(
        default=None,
        ge=0,
        description="Age of the user's account in days.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_tier": "premium",
                "company_tier": "enterprise",
                "previous_open_tickets": 3,
                "days_since_last_ticket": 2,
                "account_age_days": 730,
            }
        }
    }


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------
class TicketRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        strip_whitespace=True,
        description="Customer support ticket description text.",
    )
    user_context: Optional[UserContext] = Field(
        default=None,
        description="Optional user / company context for enriched urgency scoring.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "I cannot login to my account. It says invalid credentials.",
                "user_context": {
                    "user_tier": "premium",
                    "company_tier": "enterprise",
                    "previous_open_tickets": 2,
                    "days_since_last_ticket": 5,
                },
            }
        }
    }


# ---------------------------------------------------------------------------
# /classify response
# ---------------------------------------------------------------------------
class ClassifyResponse(BaseModel):
    category: str = Field(..., description="Predicted issue category.")
    confidence: float = Field(..., description="Prediction confidence (0-1).")


# ---------------------------------------------------------------------------
# /urgency response
# ---------------------------------------------------------------------------
class VaderScores(BaseModel):
    neg: float
    neu: float
    pos: float
    compound: float


class UrgencyFactors(BaseModel):
    """Breakdown of what drove the final urgency score."""

    vader_base_urgency: str = Field(..., description="Raw urgency from VADER alone.")
    vader_compound: float
    user_tier: str
    company_tier: Optional[str]
    previous_open_tickets: int
    days_since_last_ticket: Optional[int]
    composite_score: float = Field(..., description="Weighted urgency score (0-14).")
    score_breakdown: dict = Field(..., description="Per-factor score contributions.")


class UrgencyResponse(BaseModel):
    urgency: str = Field(..., description="Final urgency level: Critical, High, Medium, or Low.")
    compound_score: float = Field(..., description="VADER compound sentiment score (-1 to 1).")
    all_scores: VaderScores
    factors: UrgencyFactors


# ---------------------------------------------------------------------------
# /process_ticket response
# ---------------------------------------------------------------------------
class PipelineResponse(BaseModel):
    category: str
    category_confidence: float
    urgency: str
    urgency_score: float
    urgency_factors: UrgencyFactors
    retrieved_policy: Optional[str] = None
    rag_available: bool
    ai_draft_reply: str


# ---------------------------------------------------------------------------
# /chat  — multi-turn RAG chat
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["customer", "ai"]
    content: str


class ChatRequest(BaseModel):
    ticket_description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Original ticket description used as permanent context.",
    )
    ticket_category: Optional[str] = Field(
        default=None,
        description="ML-predicted category of the ticket.",
    )
    ticket_urgency: Optional[str] = Field(
        default=None,
        description="ML-predicted urgency level (Critical, High, Medium, Low).",
    )
    conversation_history: list[ChatMessage] = Field(
        default=[],
        description="All previous messages in this thread (oldest first).",
    )
    user_message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        strip_whitespace=True,
        description="The new message from the customer.",
    )
    image_analyses: list[str] = Field(
        default=[],
        description="Textual descriptions of images attached to the ticket, from vision analysis.",
    )


class ChatResponse(BaseModel):
    reply: str = Field(..., description="AI-generated reply.")
    policy_used: Optional[str] = Field(
        default=None,
        description="Filename of the KB policy used for retrieval.",
    )
    context_summarized: bool = Field(
        default=False,
        description="True if older conversation history was summarized due to context limits.",
    )


# ---------------------------------------------------------------------------
# /analyze_image  — vision analysis of an attached image
# ---------------------------------------------------------------------------
class ImageAnalysisRequest(BaseModel):
    image_url: str = Field(
        ...,
        description="Publicly accessible URL of the image to analyze.",
    )


class ImageAnalysisResponse(BaseModel):
    analysis: Optional[str] = Field(
        default=None,
        description="Textual description of the image contents.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if analysis failed.",
    )


# ---------------------------------------------------------------------------
# /health response
# ---------------------------------------------------------------------------
class ModelStatus(BaseModel):
    fasttext: bool
    vader: bool
    rag: bool


class HealthResponse(BaseModel):
    status: str
    models: ModelStatus

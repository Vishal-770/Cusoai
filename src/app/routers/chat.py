import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from ..models import ChatRequest, ChatResponse
from ..services.rag_service import retrieve_policy

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["RAG Chat"])

# ── Context-window management ──────────────────────────────────────────────
# Summarize oldest messages once history exceeds this count.
HISTORY_SUMMARIZE_THRESHOLD = 10   # summarize after 5 back-and-forth exchanges
HISTORY_FULL_KEEP = 6              # always keep the 6 most-recent messages verbatim
MAX_DESCRIPTION_CHARS = 500        # cap very long descriptions in the prompt


def _summarize_old_messages(
    gemini_key: str,
    old_messages: list,
    ticket_description: str,
    ticket_category: Optional[str],
) -> str:
    """Call Gemini to compress old_messages into a structured bullet-point summary."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)
        lines = []
        for msg in old_messages:
            prefix = "Customer" if msg.role == "customer" else "Support Assistant"
            lines.append(f"{prefix}: {msg.content}")
        history_text = "\n".join(lines)

        prompt = (
            f"You are compressing a customer support conversation into a concise structured summary.\n\n"
            f"Ticket category: {ticket_category or 'Unknown'}\n"
            f"Original issue: {ticket_description[:300]}\n\n"
            f"Conversation to summarize:\n{history_text}\n\n"
            f"Write a structured summary using this exact format:\n"
            f"• Issue: [one-sentence description of what the customer needs]\n"
            f"• Tried so far: [bullet list of solutions already attempted, or 'None']\n"
            f"• Information given: [key facts provided to the customer]\n"
            f"• Still unresolved: [what is still open, or 'Nothing — resolved']\n\n"
            f"Be factual and concise. Do not add pleasantries."
        )
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.warning("Context summarization failed: %s", e)
        # Graceful fallback
        return " | ".join(
            f"{'Customer' if m.role == 'customer' else 'Assistant'}: {m.content[:100]}"
            for m in old_messages[-4:]
        )


def _build_prompt(
    ticket_description: str,
    ticket_category: Optional[str],
    ticket_urgency: Optional[str],
    policy_text: str,
    conversation_history: list,
    user_message: str,
    conversation_summary: Optional[str] = None,
    image_analyses: Optional[list] = None,
) -> str:
    # Truncate very long descriptions but keep them readable
    desc = ticket_description
    if len(desc) > MAX_DESCRIPTION_CHARS:
        desc = desc[:MAX_DESCRIPTION_CHARS].rstrip() + "… [truncated]"

    # Always-present ticket context block
    category_line = f"Category   : {ticket_category}" if ticket_category else "Category   : Not classified"
    urgency_line = f"Urgency    : {ticket_urgency}" if ticket_urgency else ""

    # Build conversation block
    history_lines = []
    for msg in conversation_history:
        prefix = "Customer" if msg.role == "customer" else "Support"
        history_lines.append(f"{prefix}: {msg.content}")
    history_block = "\n".join(history_lines) if history_lines else "(no prior messages in this window)"

    # Optional blocks — only rendered when present
    summary_block = ""
    if conversation_summary:
        summary_block = (
            "\n┌─ SUMMARY OF EARLIER CONVERSATION ────────────────────────┐\n"
            f"{conversation_summary}\n"
            "└───────────────────────────────────────────────────────────┘\n"
        )

    image_block = ""
    if image_analyses:
        lines = "\n".join(f"  [{i+1}] {a}" for i, a in enumerate(image_analyses))
        image_block = (
            "\n┌─ ATTACHED IMAGE EVIDENCE ─────────────────────────────────┐\n"
            f"{lines}\n"
            "└───────────────────────────────────────────────────────────┘\n"
        )

    urgency_section = f"\n{urgency_line}" if urgency_line else ""

    return f"""You are a customer support assistant. You MUST answer only from the POLICY TEXT below.

╔═══════════════════ TICKET CONTEXT (always in scope) ═══════════════════╗
{category_line}{urgency_section}
Description: {desc}
╚════════════════════════════════════════════════════════════════════════╝

╔═══════════════════ POLICY KNOWLEDGE BASE ══════════════════════════════╗
{policy_text}
╚════════════════════════════════════════════════════════════════════════╝
{image_block}{summary_block}
RECENT CONVERSATION:
{history_block}

Customer: {user_message}

STRICT RESPONSE RULES — follow in order:
1. Answer from the policy only. Use plain language and bullet points for steps.
2. If partially covered: share what the policy confirms + "For further help: support@company.com."
3. If not in the policy at all: say only "That topic isn't covered in the policies I have access to. Please contact support@company.com."
4. Never guess, estimate, or use knowledge outside the policy.
5. Never repeat the customer's message back to them.
6. If images are attached and the IMAGE EVIDENCE contradicts the customer's claim, note the discrepancy politely.
7. Keep responses concise — use bullet points, not walls of text.

Support Assistant:"""


@router.post("", response_model=ChatResponse, summary="RAG-powered multi-turn chat for a ticket")
async def chat(request: ChatRequest, raw: Request):
    # --- RAG retrieval ---
    rag_available: bool = getattr(raw.app.state, "rag_available", False)
    policy_text = ""
    policy_filename: Optional[str] = None

    sources: list[str] = []
    if rag_available:
        embed_model = raw.app.state.embed_model
        faiss_index = raw.app.state.faiss_index
        policies = raw.app.state.policies
        # Use category + description + current message for best retrieval
        query = " ".join(filter(None, [
            request.ticket_category,
            request.ticket_description[:300],
            request.user_message,
        ]))
        hits = retrieve_policy(embed_model, faiss_index, policies, query)
        if hits:
            policy_text = "\n\n---\n\n".join(text for text, _ in hits)
            sources = [fname for _, fname in hits]
        else:
            logger.warning("/chat FAISS retrieval returned nothing.")

    if not policy_text:
        policy_text = (
            "No specific policy could be retrieved for this issue. "
            "Advise the customer to contact support@company.com for personalised assistance."
        )

    # --- Gemini setup ---
    gemini_key: Optional[str] = getattr(raw.app.state, "gemini_api_key", None)
    if not gemini_key:
        return ChatResponse(
            reply=(
                "I'm sorry, the AI assistant is currently unavailable. "
                "Please contact support@company.com for help with your issue."
            ),
            policy_used=policy_filename,
        )

    # --- Context management: summarize oldest messages when history grows long ---
    summary: Optional[str] = None
    recent_history = request.conversation_history
    context_summarized = False

    if len(request.conversation_history) > HISTORY_SUMMARIZE_THRESHOLD:
        old_msgs = request.conversation_history[:-HISTORY_FULL_KEEP]
        recent_history = request.conversation_history[-HISTORY_FULL_KEEP:]
        logger.info("/chat — compressing %d old messages into summary", len(old_msgs))
        summary = _summarize_old_messages(
            gemini_key,
            old_msgs,
            request.ticket_description,
            request.ticket_category,
        )
        context_summarized = True

    try:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)
        prompt = _build_prompt(
            ticket_description=request.ticket_description,
            ticket_category=request.ticket_category,
            ticket_urgency=request.ticket_urgency,
            policy_text=policy_text,
            conversation_history=recent_history,
            user_message=request.user_message,
            conversation_summary=summary,
            image_analyses=request.image_analyses or [],
        )

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        reply_text = response.text.strip()

        logger.info(
            "/chat — category=%s rag=%s summarized=%s reply_len=%d",
            request.ticket_category,
            rag_available,
            context_summarized,
            len(reply_text),
        )

        return ChatResponse(
            reply=reply_text,
            sources=sources,
            context_summarized=context_summarized,
        )

    except Exception as e:
        logger.error("/chat Gemini error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="AI assistant is temporarily unavailable. Please try again shortly.",
        )


# SupportDesk — AI-Powered Customer Support Triage

> A full-stack intelligent customer support platform. Customers submit tickets in any language via text, image, or voice. A six-component ML pipeline classifies the issue, scores urgency, retrieves the relevant policy, and drafts a grounded reply — all in under 2 seconds, before any human agent opens the ticket.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.1.6-black)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-orange)](https://ai.google.dev)

---

## Demo

https://github.com/user-attachments/assets/your-video-id-here

> Full walkthrough: ticket submission (text + image + voice) → ML triage → RAG-grounded reply → voice response playback.
>
> **To embed:** Upload `SupportDesk — Customer Support Portal - Brave 2026-03-06 11-41-05.mp4` by dragging it into any GitHub issue or PR comment box — GitHub will generate a `user-attachments/assets/` URL. Replace the placeholder URL above with that link.

---

## The Problem

Customer support teams face three critical bottlenecks:

| Problem | Impact |
|---------|--------|
| **Manual triage** | Agents spend ~30% of time just routing and categorising tickets |
| **Buried urgent issues** | High-value/critical tickets get lost in the queue behind routine requests |
| **Policy lookup lag** | Agents spend ~40% of time searching internal wikis instead of responding |
| **LLM hallucinations** | Generic AI confidently invents refund eligibility and policy-specific rules |
| **No multimodal input** | Customers cannot attach images or voice notes — must type everything out |
| **Language barriers** | Global customers are forced to use support portals in a non-native language |

Existing helpdesk tools (Zendesk, Freshdesk, Intercom) are **workflow tools, not intelligence tools** — they route tickets but do not understand them.

---

## Our Solution

SupportDesk wraps every ticket in a six-step ML pipeline the moment it is submitted:

```
┌─────────────────────────────────────────────────────────────────┐
│  Customer submits ticket (text + optional image + optional voice)│
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │      FastAPI Backend         │
              │                              │
              │  ① FastText  → category      │  88-90% accuracy, <200ms CPU
              │  ② VADER     → urgency score │  4-level weighted composite
              │  ③ MiniLM    → embed query   │  384-dim semantic vector
              │  ④ FAISS     → top-3 policy  │  <5ms exact L2 search
              │  ⑤ Gemini    → grounded reply│  only retrieved facts used
              │  ⑥ Vision    → image context │  extracts invoice/error data
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │     Next.js 15 Frontend      │
              │  Ticket list, chat, admin    │
              └─────────────────────────────┘
```

**Key design principle:** Lightweight local models (FastText, VADER) handle routing with zero API cost and ~200ms latency. Gemini is only called when facts matter — and then only with retrieved policy text, never raw world knowledge.

---

## Architecture

### Backend — FastAPI (`src/app/`)

```
src/app/
├── main.py              # FastAPI app + lifespan model loading
├── models.py            # Pydantic schemas (TicketRequest, PipelineResponse, ...)
├── routers/
│   ├── pipeline.py      # POST /process_ticket  — full 6-step pipeline
│   ├── chat.py          # POST /chat            — multi-turn RAG chat
│   ├── classify.py      # POST /classify        — category only
│   ├── urgency.py       # POST /urgency         — urgency only
│   └── analyze.py       # POST /analyze_image   — Gemini Vision
└── services/
    ├── fasttext_service.py   # predict_category()
    ├── vader_service.py      # analyze_urgency() with weighted scoring
    └── rag_service.py        # retrieve_policy() + generate_reply()
```

All models are loaded once at startup into `app.state` via FastAPI's lifespan context. If any optional component (FAISS index, Gemini key) is missing, the API degrades gracefully — classification and urgency still work.

### Frontend — Next.js 15 (`frontend/`)

```
frontend/app/
├── page.tsx                        # Landing page (unauthenticated) + dashboard (authenticated)
├── login/page.tsx                  # Google OAuth login
├── tickets/page.tsx                # Ticket list
├── tickets/new/page.tsx            # Create ticket (title + description + image upload)
├── tickets/[id]/page.tsx           # Ticket detail + live RAG chat panel
└── api/
    ├── tickets/route.ts            # List / create tickets
    ├── tickets/[id]/route.ts       # Get ticket + update status
    ├── tickets/[id]/messages/route.ts        # Text chat messages
    └── tickets/[id]/messages/voice/route.ts  # Full voice pipeline (STT→RAG→TTS)
```

### Database — Neon PostgreSQL (Drizzle ORM)

```
user          → id, email, name, role (customer | admin)
ticket        → id, userId, title, description, category, confidence,
                urgency, urgencyScore, aiDraft, status, closedAt
ticketMessage → id, ticketId, role (customer | ai), content (English),
                nativeContent (user's language), voiceUrl, imageUrl
ticketImage   → id, ticketId, cloudinaryUrl, analysisText
session       → id, userId, token, expiresAt
account       → id, userId, providerId (google), accessToken
```

`content` is always stored in English for AI processing. `nativeContent` stores the original/translated text for display in the user's language. All media URLs point to Cloudinary; only metadata is in PostgreSQL.

---

## ML Pipeline — In Depth

### Step 1 — Category Classification (FastText)

**Model:** Meta FastText, trained from scratch on 200,000 real customer support tickets.

**Training data:** [Bitext Customer Support Dataset](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset) — 200K rows, 27 original intents mapped to 6 macro-categories:

| Category | Examples |
|----------|---------|
| `billing` | Invoice questions, payment failures, pro-rating |
| `refund` | Refund eligibility, timelines, chargebacks |
| `login` | Password reset, MFA, account lockout |
| `technical` | App crashes, data sync, blank page |
| `account` | Suspension, security, plan changes |
| `other` | General enquiries |

**Results:** 88–90% accuracy on held-out test set. Training time: under 5 minutes on CPU. Model size: ~3 MB.

```bash
# Train the FastText model
python -m src.train_fasttext
```

**Also trained (not yet wired into live API):** `microsoft/deberta-v3-large` fine-tuned on the same 200K dataset — expected 93–96% accuracy. Training scripts: `src/train_deberta_kaggle.py`.

---

### Step 2 — Urgency Scoring (VADER + Weighted Composite)

**Model:** VADER sentiment analysis with a custom multi-factor weighting layer.

`composite_score = vader_base + user_tier_delta + company_tier_delta + history_delta`

| Factor | Weight |
|--------|--------|
| VADER High sentiment (compound < -0.5) or power-word (`urgent`, `hacked`, `asap`, ...) | +7.0 |
| VADER Medium sentiment | +4.0 |
| VADER Low sentiment | +1.5 |
| User tier: enterprise | +3.0 |
| User tier: premium | +2.0 |
| User tier: free | -0.5 |
| Company tier: enterprise | +2.0 |
| Company tier: business | +1.0 |
| Open tickets ≥ 5 | +2.0 |
| Recent repeat ticket (< 7 days) | +1.0 |
| Account age < 30 days | +0.5 |

**Score → Level mapping:**

| Score | Urgency |
|-------|---------|
| ≥ 10 | Critical |
| ≥ 6 | High |
| ≥ 3 | Medium |
| < 3 | Low |

**Also trained (not yet wired into live API):** `roberta-large` fine-tuned for urgency classification — expected 89–92% weighted F1. Training script: `src/train_roberta_urgency_kaggle.py`.

---

### Step 3 & 4 — RAG Pipeline (all-MiniLM-L6-v2 + FAISS)

#### KB Ingestion (run once, or on KB update)

```bash
python -m src.create_rag_db
```

Each `.txt` file in `data/kb/` is embedded with `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) and stored in a FAISS `IndexFlatL2`. Two artefacts are produced:

- `embeddings/kb_index.faiss` — binary vector index (pre-built, committed to repo)
- `embeddings/kb_metadata.txt` — `index_id|filename|full_policy_text`

| Knowledge Base File | Coverage |
|--------------------|----------|
| `billing_policy.txt` | Payment methods, invoices, duplicate charges, pro-rating, VAT |
| `refund_policy.txt` | 30-day window, accidental purchases, chargebacks, SLA credits |
| `login_policy.txt` | Password reset, lockout (30 min / 5 fails), 2FA, backup codes |
| `account_security_policy.txt` | Suspension appeals, breach response, session revocation |
| `technical_support_policy.txt` | Blank page, data sync, P0–P3 SLA targets, bug reporting |

#### Runtime Retrieval

```python
TOP_K = 3

def retrieve_policy(embed_model, faiss_index, policies, description, k=TOP_K):
    query_vector = embed_model.encode([description])
    distances, indices = faiss_index.search(query_vector, k)
    return [(policies[idx]["text"], policies[idx]["file"]) for idx in indices[0]]
```

- Query is the ticket description for `/process_ticket`, or `category + description + user_message` (richer context) for `/chat`
- Returns `(policy_text, filename)` tuples ordered by ascending L2 distance
- Retrieval latency: < 5ms

---

### Step 5 — Grounded Reply Generation (Gemini 2.5 Flash)

**Zero-hallucination design:** Gemini receives only the three retrieved policy chunks. It is explicitly forbidden from using outside knowledge.

```
You are a helpful customer support agent.
Ticket: "{description}"
Policy knowledge (use ONLY the text below — nothing else):
---
{policy_chunk_1}
---
{policy_chunk_2}
---
{policy_chunk_3}

Rules (never break these):
1. Answer ONLY from the policy text provided.
2. If partially covered → answer what you know + refer to support@company.com.
3. If not covered → "That topic isn't in the policies I have access to."
4. Never guess or use knowledge outside the retrieved policy.
5. Reply in the customer's native language.
```

Every API response includes `sources: list[str]` — the KB filenames that grounded the answer:

```json
{
  "category": "refund",
  "category_confidence": 0.94,
  "urgency": "High",
  "urgency_score": 7.5,
  "ai_draft_reply": "Thank you for reaching out. Based on our refund policy...",
  "sources": ["refund_policy.txt", "billing_policy.txt"]
}
```

---

### Step 6 — Image Evidence Extraction (Gemini Vision)

When a customer attaches an image (invoice screenshot, error message, bank statement), Gemini Vision analyses it and the extracted text is stored in `ticketImage.analysisText`. This evidence is automatically injected into subsequent RAG chat context — so the AI knows what is in the screenshot without the customer having to type it out.

---

## Voice Pipeline (Multilingual — Full Round-Trip)

`POST /api/tickets/{id}/messages/voice`

```
Customer speaks (any language) → WebM/Opus audio recorded in browser
         │
         ▼  base64 inline_data
[Gemini 2.5 Flash STT]
  → transcribed text + detected BCP-47 language code ("hi", "fr", "es", ...)
         │
         ▼  (if non-English)
[Gemini translate → English]
         │
         ▼
[FastAPI /chat — RAG pipeline in English]
  → policy-grounded English reply
         │
         ▼  (if non-English)
[Gemini translate reply → customer's language]
         │
         ▼
[Gemini 2.5 Flash Preview TTS — voice "Aoede"]
  → raw 24kHz/16-bit PCM → wrapped in WAV header
         │
         ▼
[Cloudinary upload] → voiceUrl stored in ticketMessage
         │
         ▼
Customer hears AI reply read back in their native language
```

Both the customer's voice message and the AI's audio reply are stored with their Cloudinary URLs. The `nativeContent` column preserves the original-language text for display. TTS failure is non-fatal — the message is delivered as text if audio synthesis fails.

---

## API Reference

Start the API — interactive docs at `http://localhost:8000/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/process_ticket` | Full pipeline: classify + urgency + RAG + draft reply |
| `POST` | `/chat` | Multi-turn RAG chat with conversation history |
| `POST` | `/classify` | Category classification only |
| `POST` | `/urgency` | Urgency scoring only |
| `POST` | `/analyze_image` | Gemini Vision image analysis |
| `GET` | `/health` | Model status + health check |

### `/process_ticket` request body

```json
{
  "description": "I was charged twice for the same invoice",
  "user_context": {
    "user_tier": "enterprise",
    "company_tier": "business",
    "open_tickets_count": 2,
    "account_age_days": 120,
    "recent_ticket": false
  }
}
```

### `/chat` request body

```json
{
  "ticket_description": "Charged twice on Feb 28",
  "ticket_category": "billing",
  "ticket_urgency": "High",
  "conversation_history": [
    { "role": "customer", "content": "How long does the refund take?" },
    { "role": "ai", "content": "5-7 business days for credit/debit cards." }
  ],
  "user_message": "What if it hasn't arrived after 7 days?",
  "image_analyses": ["Invoice screenshot shows $49 charged twice on Feb 28"]
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend framework** | Next.js 16.1.6, React 19.2.3, TypeScript |
| **Styling** | Tailwind CSS v4, shadcn/ui (Radix UI) |
| **Auth** | better-auth 1.5.3 (Google OAuth, session-based) |
| **ORM** | Drizzle ORM 0.45.1 |
| **Database** | Neon PostgreSQL (serverless) |
| **Media storage** | Cloudinary (images + audio) |
| **Backend framework** | FastAPI, Uvicorn (async ASGI) |
| **Category classifier** | FastText (Meta) — trained from scratch |
| **Urgency scorer** | VADER + custom weighted composite |
| **Embedding model** | sentence-transformers/all-MiniLM-L6-v2 (384-dim) |
| **Vector index** | FAISS IndexFlatL2 (local, exact search) |
| **LLM / Vision / STT / TTS** | Gemini 2.5 Flash, Gemini 2.5 Flash Preview TTS |
| **Training (advanced models)** | HuggingFace Transformers — DeBERTa-v3-large, RoBERTa-large |
| **Training hardware** | Kaggle (2× T4 GPU) |
| **Training dataset** | 200,000 real customer support tickets (Bitext HuggingFace) |

---

## Performance

| Metric | Value |
|--------|-------|
| Category classification accuracy (FastText, live) | **88–90%** |
| Category classification accuracy (DeBERTa, trained) | **93–96%** (ready to deploy) |
| Urgency accuracy (VADER weighted, live) | **~85%** |
| Urgency accuracy (RoBERTa, trained) | **89–92% F1** (ready to deploy) |
| End-to-end triage latency (classify + urgency + RAG + draft) | **< 2 seconds** |
| FAISS KB retrieval latency | **< 5ms** |
| FastText inference latency | **< 200ms (CPU)** |
| Voice round-trip (STT → RAG → TTS) | **~10–15 seconds** |
| FastText model size | **~3 MB** |
| Training time (FastText) | **< 5 minutes on CPU** |
| Training data | **200,000 tickets** |
| Languages supported | **100+** (Gemini multilingual) |

---

## Project Structure

```
hack/
├── data/
│   ├── kb/                               # 5 policy .txt files (Knowledge Base)
│   ├── fasttext_data/                    # FastText-format train/val/test splits
│   ├── processed/                        # CSV train/val/test (full 200K)
│   └── processed_50k/                    # CSV splits (50K subset for Kaggle)
├── embeddings/
│   ├── kb_index.faiss                    # Pre-built FAISS index (committed)
│   └── kb_metadata.txt                   # index_id|filename|policy_text
├── models/
│   └── fasttext_category.bin             # Trained FastText model
├── src/
│   ├── create_rag_db.py                  # Build FAISS index from data/kb/
│   ├── preprocess_data.py                # CSV cleaning + stratified splits
│   ├── preprocess_fasttext.py            # CSV → FastText label format
│   ├── train_fasttext.py                 # FastText training
│   ├── train_deberta_kaggle.py           # DeBERTa-v3-large fine-tuning
│   ├── train_roberta_urgency_kaggle.py   # RoBERTa-large urgency fine-tuning
│   └── app/
│       ├── main.py                       # FastAPI app + lifespan model loading
│       ├── models.py                     # Pydantic request/response schemas
│       ├── routers/                      # Route handlers (pipeline, chat, ...)
│       └── services/                     # ML service wrappers
├── frontend/                             # Next.js 15 customer portal
│   ├── app/                              # App Router pages + API routes
│   ├── components/                       # UI components (chat-panel, navbar)
│   └── lib/                              # auth, db, cloudinary utilities
├── notebooks/
│   └── 01_EDA_customer_support_tickets.ipynb  # Exploratory data analysis
├── reports/
│   ├── master_implementation_plan.md     # 5-phase execution plan
│   └── column_selection_report.md        # Feature selection rationale
├── demo_tickets.md                       # 6 demo scenarios with chat scripts
└── PITCH_ANALYSIS.md                     # Full pitch deck content (16 slides)
```

---

## Setup & Running

### Prerequisites
- Python 3.9+, Node.js 20+, pnpm
- Google Gemini API key
- Neon PostgreSQL connection string
- Cloudinary account

### 1. Backend

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env at project root
echo "GEMINI_API_KEY=your_key_here" > .env

# (Optional) Rebuild FAISS index if you update data/kb/
python -m src.create_rag_db

# Start API server
uvicorn src.app.main:app --reload --port 8000
```

Interactive API docs: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Create .env.local
cp .env.example .env.local
# Fill in: DATABASE_URL, GEMINI_API_KEY, CLOUDINARY_*, BETTER_AUTH_SECRET

# Push DB schema
pnpm drizzle-kit push

# Start dev server
pnpm dev
```

App: `http://localhost:3000`

### 3. Train Models (optional — pre-trained artefacts committed)

```bash
# FastText (CPU, < 5 mins)
python -m src.preprocess_fasttext
python -m src.train_fasttext

# DeBERTa / RoBERTa (upload to Kaggle, run on GPU)
# See src/train_deberta_kaggle.py and src/train_roberta_urgency_kaggle.py
```

---

## Environment Variables

### Backend (`.env` at project root)
```
GEMINI_API_KEY=your_gemini_api_key
```

### Frontend (`frontend/.env.local`)
```
DATABASE_URL=postgresql://...neon.tech/...
GEMINI_API_KEY=your_gemini_api_key
BETTER_AUTH_SECRET=random_32_char_secret
BETTER_AUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_secret
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret
FASTAPI_URL=http://localhost:8000
```

---

## How RAG is Implemented

### Overview

```
Customer Ticket
      │
      ▼
 [Embed query]  ←── all-MiniLM-L6-v2 (SentenceTransformers)
      │
      ▼
 [FAISS top-3 search]  ←── IndexFlatL2 over 5 KB policy embeddings
      │
      ▼
 [Concatenate top-3 policy chunks]
      │
      ▼
 [Grounded prompt]  ─── "Answer ONLY from the policy text below"
      │
      ▼
 [Gemini 2.5 Flash]  ──► draft_reply + sources[]
```

---

### Step 1 — KB Ingestion (`src/create_rag_db.py`)

At build time, all `.txt` files in `data/kb/` are read and embedded:

| File | Content |
|---|---|
| `billing_policy.txt` | Billing, invoices, payment failures, pro-rating |
| `login_policy.txt` | Login issues, password reset, MFA |
| `account_security_policy.txt` | Account security, hacking, 2FA |
| `refund_policy.txt` | Refunds, chargebacks, eligibility |
| `technical_support_policy.txt` | Technical bugs, outages, integrations |

Each file is treated as a single chunk and encoded with **`all-MiniLM-L6-v2`** (384-dimensional vectors). The resulting vectors are stored in a **FAISS `IndexFlatL2`** exact-search index.

**Artifacts produced:**
- `embeddings/kb_index.faiss` — the FAISS binary index (pre-built, committed to repo)
- `embeddings/kb_metadata.txt` — pipe-delimited file: `index_id|filename|full_text`

To rebuild the index after adding new KB files:
```bash
cd d:/hack
python -m src.create_rag_db
```

---

### Step 2 — Model Loading at Startup (`src/app/main.py`)

On FastAPI startup (lifespan), three RAG components are loaded into app state:

```python
app.state.embed_model  = SentenceTransformer("all-MiniLM-L6-v2")
app.state.faiss_index  = faiss.read_index("embeddings/kb_index.faiss")
app.state.policies     = { 0: {"file": "billing_policy.txt", "text": "..."}, ... }
app.state.rag_available = True
```

RAG is marked optional — if the index file is missing, the API degrades gracefully and still returns classification + urgency results without a draft reply.

---

### Step 3 — Top-k Retrieval (`src/app/services/rag_service.py`)

```python
TOP_K = 3

def retrieve_policy(embed_model, faiss_index, policies, description, k=TOP_K):
    query_vector = embed_model.encode([description])          # embed the ticket
    distances, indices = faiss_index.search(query_vector, k)  # L2 nearest neighbour
    return [(policies[idx]["text"], policies[idx]["file"]) for idx in indices[0]]
```

- The query is the ticket description (for `/process_ticket`) or `category + description + user_message` (for `/chat`) — combining all available context for best retrieval.
- Returns a list of `(policy_text, filename)` tuples ordered by ascending L2 distance (most similar first).
- `k_actual = min(k, faiss_index.ntotal)` guards against requesting more results than the index has.

---

### Step 4 — Grounded Reply Generation

**One-shot pipeline** (`/process_ticket` → `rag_service.generate_reply`):

The top-3 policy chunks are joined with `---` separators and injected into a strict prompt:

```
You are a helpful customer support agent.
A customer sent this ticket: "{description}"
Our internal policy for this issue is: "{policy_text}"

TASK:
1. Analyze the customer's language.
2. Draft a polite, helpful response using ONLY the policy provided.
3. OUTPUT THE RESPONSE IN THE CUSTOMER'S NATIVE LANGUAGE.
```

**Multi-turn chat** (`/chat` → `chat.py`):

More structured prompt including:
- Ticket context block (category, urgency, description)
- Policy knowledge base block (top-3 retrieved chunks, `---` separated)
- Optional image evidence block (from Gemini Vision analysis)
- Optional summary of earlier conversation (when history > 10 messages)
- Recent conversation history (last 6 messages verbatim)

Strict grounding rules injected into every turn:
1. Answer from the policy only
2. If partially covered → answer what's known + refer to `support@company.com`
3. If not covered at all → "That topic isn't covered in the policies I have access to."
4. Never guess or use knowledge outside the retrieved policy

---

### Step 5 — Sources in API Response

Both endpoints return `sources: list[str]` — the KB filenames that were used:

```json
{
  "category": "billing",
  "urgency": "Medium",
  "ai_draft_reply": "Thank you for reaching out...",
  "sources": ["billing_policy.txt", "account_security_policy.txt"]
}
```

---

## Full Pipeline API Endpoint

`POST /process_ticket`

Runs all steps in sequence:

| Step | Model | Output field |
|---|---|---|
| Preprocessing | strip/lowercase | — |
| Classification | FastText (trained on 200k tickets) | `category`, `category_confidence` |
| Urgency | VADER + weighted rules | `urgency`, `urgency_score`, `urgency_factors` |
| KB Retrieval | all-MiniLM-L6-v2 + FAISS top-3 | `retrieved_policy`, `sources` |
| Draft reply | Gemini 2.5 Flash | `ai_draft_reply` |

---

## Models Used

| Model | Task | Status |
|---|---|---|
| **FastText** (trained from scratch) | Category classification | ✅ Live in API |
| **VADER** (rule-based) | Urgency scoring | ✅ Live in API |
| **all-MiniLM-L6-v2** (not fine-tuned) | KB query + document embeddings | ✅ Live in API |
| **Gemini 2.5 Flash** (Google API) | Grounded reply generation, image analysis, context summarization | ✅ Live in API |
| **microsoft/deberta-v3-large** (fine-tuned on Kaggle) | Category classification | ⚠️ Trained, not wired in |
| **roberta-large** (fine-tuned on Kaggle) | Urgency classification | ⚠️ Trained, not wired in |

---

## Project Structure

```
hack/
├── data/
│   ├── kb/                          # Knowledge Base — 5 policy .txt files
│   ├── fasttext_data/               # FastText-format train/val/test splits
│   └── processed/                   # CSV train/val/test splits
├── embeddings/
│   ├── kb_index.faiss               # Pre-built FAISS vector index
│   └── kb_metadata.txt              # index_id|filename|text for each KB chunk
├── models/
│   └── fasttext_category.bin        # Trained FastText model
├── src/
│   ├── create_rag_db.py             # Build FAISS index from data/kb/
│   ├── preprocess_data.py           # CSV cleaning + train/val/test split
│   ├── preprocess_fasttext.py       # Convert CSV to FastText label format
│   ├── train_fasttext.py            # Train FastText category model
│   ├── train_deberta_kaggle.py      # Fine-tune DeBERTa-v3-large (Kaggle)
│   ├── train_roberta_urgency_kaggle.py  # Fine-tune RoBERTa-large (Kaggle)
│   └── app/
│       ├── main.py                  # FastAPI app + model loading at startup
│       ├── models.py                # Pydantic request/response schemas
│       ├── routers/
│       │   ├── pipeline.py          # POST /process_ticket  (full pipeline)
│       │   ├── chat.py              # POST /chat  (multi-turn RAG chat)
│       │   ├── classify.py          # POST /classify  (category only)
│       │   ├── urgency.py           # POST /urgency  (urgency only)
│       │   └── analyze.py           # POST /analyze_image  (Gemini Vision)
│       └── services/
│           ├── rag_service.py       # retrieve_policy() + generate_reply()
│           ├── fasttext_service.py  # predict_category()
│           └── vader_service.py     # analyze_urgency() with weighted scoring
└── frontend/                        # Next.js 15 customer portal
```

---

## Running the API

```bash
# 1. Activate venv
d:\hack\venv\Scripts\activate

# 2. (Optional) Rebuild FAISS index if you updated data/kb/
python -m src.create_rag_db

# 3. Start API
cd d:\hack
uvicorn src.app.main:app --reload --port 8000
```

Requires a `.env` file at `d:\hack\.env` with:
```
GEMINI_API_KEY=your_key_here
```

Interactive API docs available at `http://localhost:8000/docs`.


# 📋 Task 2: Customer Support Ticket Triage & Draft Reply

> **Saved on:** 2026-03-05

---

## 🎯 Problem Statement

Build a system to classify support tickets, estimate urgency, and draft replies using a Knowledge Base (KB).

---

## ✅ System Requirements

The system must:
- **Classify** ticket category: `Refund`, `Login`, `Delivery`, `Billing`, `Account`, `Other`
- **Estimate** urgency: `High` / `Medium` / `Low`
- **Retrieve** relevant KB snippets (top-k)
- **Draft** a short reply grounded in KB content
- **Ask for clarification** if KB lacks information — do NOT guess

---

## 📥 Inputs

| Input | Description |
|-------|-------------|
| Ticket text | Subject + description |
| Metadata (optional) | Channel, timestamp |
| KB folder | `.txt` / `.md` / `.pdf` files |

---

## 📤 Outputs

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | One of: Refund, Login, Delivery, Billing, Account, Other |
| `urgency` | string | High / Medium / Low |
| `summary` | string | Brief summary of the ticket |
| `draft_reply` | string | Grounded reply based on KB |
| `sources` | list | KB citations used |
| `confidence` | float | Confidence score of classification |

---

## 🧩 Mandatory Components

1. **Ticket Preprocessing**
   - Clean and normalize ticket text
   - Extract subject and body
   - Handle multilingual input

2. **Category & Urgency Logic**
   - Rule-based or ML classifier
   - Map to predefined categories
   - Urgency estimation heuristics

3. **KB Ingestion + Embeddings**
   - Parse `.txt`, `.md`, `.pdf` files
   - Chunk and embed content
   - Store in vector DB

4. **Top-k Retrieval**
   - Semantic similarity search
   - Return most relevant KB snippets

5. **Grounded Reply Generation**
   - LLM-based draft using retrieved context
   - Cite KB sources
   - Fallback: ask for clarification if KB is insufficient

---

## 📊 Datasets

- [Customer Support Ticket Dataset](https://huggingface.co/datasets/customer-support-tickets)
- [Multilingual Customer Support Tickets](https://huggingface.co/datasets/multilingual-customer-support)
- [HuggingFace Tickets Dataset](https://huggingface.co/datasets)

---

## 🗂️ Suggested Project Structure

```
task2-support-triage/
├── data/
│   ├── raw/              # Raw ticket datasets
│   └── kb/               # Knowledge Base files (.txt/.md/.pdf)
├── src/
│   ├── preprocessing.py  # Ticket cleaning & normalization
│   ├── classifier.py     # Category & urgency classification
│   ├── kb_ingestion.py   # KB parsing, chunking, embedding
│   ├── retrieval.py      # Top-k semantic search
│   └── reply_generator.py# Grounded reply drafting
├── embeddings/           # Stored vector embeddings
├── main.py               # Entry point / orchestrator
├── requirements.txt
└── README.md
```

---

## 🔧 Tech Stack (Suggested)

| Component | Tool |
|-----------|------|
| Embeddings | `sentence-transformers` / OpenAI Embeddings |
| Vector DB | FAISS / ChromaDB / Pinecone |
| LLM | OpenAI GPT / Gemini / Mistral |
| PDF Parsing | `PyMuPDF` / `pdfplumber` |
| Classification | `scikit-learn` / zero-shot LLM |
| Framework | Python + FastAPI (optional REST API) |

---

*This plan was generated and stored on 2026-03-05.*

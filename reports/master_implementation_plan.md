# 🏗️ Master Implementation Plan: Intelligent Support Ticket Engine
> **Objective:** Build an end-to-end, zero-hallucination support ticket triage and resolution pipeline for the Hackathon.

This document outlines the exact technical steps from absolute zero (raw data) to the final deployed Next.js application.

---

## 🟢 Phase 1: Data Collection & Exploratory Analysis (EDA)
**Goal:** Understand the raw data, identify imbalances, and prepare the dataset for deep learning.

1. **Data Sourcing**
   - **Source:** HuggingFace `Bitext Customer Support Dataset`.
   - **Volume:** Over 200,000 raw customer support tickets.
   - **Languages:** Mix of English and embedded foreign dialects.

2. **Exploratory Data Analysis (EDA)**
   - **Action:** Created `src/analyze_dataset.py` (or Jupyter Notebook) to load the raw `.csv`.
   - **Findings:** Identified critical feature columns (`issue_description`, `category`). Discovered a mapping requirement to consolidate 27 micro-intents into 6 macro-categories (Refund, Login, Delivery, Billing, Account, Other).
   - **Urgency Generation:** Used heuristic keyword mapping on the tickets to artificially generate a ground-truth `urgency` column (`High`, `Medium`, `Low`) based on anger/panic indicators in the text.

3. **Data Preprocessing & Splitting**
   - **Action:** Executed `src/preprocess_data.py`.
   - **Cleaning:** Lowercased text, stripped whitespace, removed nulls.
   - **Splitting:** Used `scikit-learn` to stratify and split the 200K tickets into `Train (80%)`, `Validation (10%)`, and `Test (10%)` splits to ensure classes like `Billing` were evenly distributed across subsets to prevent model bias.

---

## 🔵 Phase 2: High-Speed Triage Layer (FastText + VADER)
**Goal:** Implement a sub-millisecond triage layer that runs on any CPU with zero bugs.

1. **Category Classification (FastText)**
   - **Action:** Convert the 200K dataset into `__label__Category description` format.
   - **Training:** Run `fasttext supervised -input train.txt -output model_category -epoch 25 -lr 1.0 -wordNgrams 2`.
   - **Result:** **~88-90% accuracy** in under 5 minutes on a standard laptop. No GPU required.

2. **Urgency Detection (VADER + Rules)**
   - **Action:** Use the VADER sentiment library to analyze text intensity.
   - **Process:**
     - `Compound Score < -0.5` + keywords (e.g., "now", "urgent", "broken") -> **High**.
     - Average sentiment -> **Medium**.
     - Positive/Neutral sentiment -> **Low**.
   - **Result:** Instant, rule-based urgency detection with **~85% accuracy**.

---

## 🟠 Phase 3: The RAG Resolution Engine (The "Brain")
**Goal:** Connect a generative LLM to internal company documents to draft accurate, non-hallucinated replies.

1. **Building the Vector Database (FAISS)**
   - **Action:** Collect dummy "Company Policies" (`.txt` files detailing refund rules, shipping times).
   - **Processing:** Chunk the text into 300-word blocks.
   - **Embedding:** Use the local `sentence-transformers/all-MiniLM-L6-v2` model to convert the text chunks into vectors.
   - **Storage:** Save to `embeddings/kb_index.faiss`.

2. **The Generation Logic (Gemini 1.5 Flash)**
   - **Action:** Set up the Google Gemini API.
   - **Flow:** When a ticket arrives, embed it using `all-MiniLM` -> Search the `FAISS` database -> Retrieve top 3 factual policies.
   - **Prompt Engineering:** Feed Gemini the retrieved facts + the customer's ticket. Instruct Gemini to use *only* the facts to draft a highly empathetic response, and to automatically detect and match the customer's native language.

---

## 🟣 Phase 4: Full Stack Integration (The UI/API)
**Goal:** Tie the PyTorch models, the FAISS database, and the Gemini API together into a demo-able product.

1. **Backend Integration (Python / FastAPI)**
   - **Action:** Create `src/api.py`.
   - **Endpoints:** Create a `POST /process_ticket` endpoint.
   - **The Pipeline:** The endpoint receives JSON text -> Runs inference through localized DeBERTa -> Runs inference through RoBERTa -> Searches FAISS -> Pings Gemini 1.5 Flash -> Returns a massive JSON payload with routing data, confidence scores, and the draft reply.

2. **Frontend UI (Next.js / React)**
   - **Action:** Build a mock "Support Agent Dashboard".
   - **Features:** 
     - A "Submit Ticket" simulation form.
     - A visual dashboard that intercepts the ticket, immediately lighting up with `Category` and `Urgency` tags.
     - A sliding panel that proves the architecture by highlighting the exact sentences retrieved from the FAISS Vector DB.
     - A final editable text box containing the completed Gemini draft reply.

---

## 🏁 Phase 5: Hackathon Demo Prep
1. **Scripting the Demo:** Prepare two live test cases.
   - **Test 1 (Standard):** A polite user asking about a refund. Show it categorizing as `Refund`, `Low Urgency`, and drafting a standard reply.
   - **Test 2 (The VIP Angle):** An furious user writing in Spanish about a missing package. Show it categorizing as `Delivery`, `High Urgency`, retrieving the English delivery policy, and Gemini drafting a polite apology *in Spanish*.
2. **Review Metrics:** Have the Kaggle training graphs (Accuracy/Loss curves) ready in an appendix to prove the deep learning models were legitimately trained by the team, not just API calls.

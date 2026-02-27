# 🧠 RAG Implementation Plan

> **Goal:** Deploy the Vector Database (FAISS) and Google Gemini 1.5 Flash generation layer to create grounded, zero-hallucination draft replies in any language.

---

## 🏗️ Architecture Stack
1. **Embedding Model:** `all-MiniLM-L6-v2` (Local, ultra-fast)
2. **Vector Database:** `FAISS` (Facebook AI Similarity Search)
3. **Generative API:** `Google Gemini 1.5 Flash` (High speed, Multilingual)
4. **Backend:** Python `FastAPI`
5. **Frontend:** React / `Next.js`

---

## 🛠️ Step-by-Step Implementation

### Phase 1: Vector Database Creation (The "Brain")
1. **Gather Knowledge Base (KB):** Collect the company's factual support documents, return policies, and shipping timelines (stored as `.txt` or `.md` in `data/kb`).
2. **Chunking Text:** Write a Python script (`src/create_rag_db.py`) to split those large documents into manageable 300-word "chunks".
3. **Embedding:** Pass each chunk through `all-MiniLM-L6-v2` to convert the text into mathematical vectors.
4. **Store in FAISS:** Save the vectors to a local database file (`embeddings/kb_index.faiss`).

### Phase 2: Building the RAG Pipeline API
Create a new endpoint in your FastAPI server (`src/app.py`).

1. **Receive the Target Query:** The API receives the customer's raw ticket (e.g., *"Mi paquete se perdió"*).
2. **Retrieval (Semantic Search):**
   - Convert the incoming ticket into a vector.
   - Run a similarity search against FAISS.
   - Extract the top 3 closest matching policy chunks.
3. **Augmentation (Prompt Engineering):**
   - Inject the user's raw ticket and the 3 retrieved English policies into a strict system prompt.
   - **Crucial Instruction Addition:** Instruct Gemini to reply *strictly* using the provided policy facts, and to *output the reply in the exact same language* the user initiated the ticket in.
4. **Generation (Gemini 1.5 Flash):**
   - Send the full prompt to the Gemini API.
   - Await the generated draft.

### Phase 3: The Next.js Frontend Integration
1. **User Submission Form:** A simple text box mimicking a support UI where the user pastes the angry ticket.
2. **Fetch API:** The Next.js client sends the ticket to the FastAPI backend.
3. **Display Results Component:**
   - **Top Left:** Show the **FastText** "Category" and Confidence %.
   - **Top Right:** Show the **VADER** "Urgency" and Sentiment Score.
   - **Middle Tier:** Display the retrieved raw English policies from FAISS to prove the system isn't guessing.
   - **Bottom Tier:** Render the final, localized Gemini/Claude draft reply for the agent to review.

---

## 🔒 Safety Nets & Edge Cases
- **No Vectors Found / Low Confidence:** If FAISS cannot find a text chunk with a similarity score > 60%, the Gemini prompt dynamically switches to an escalation message: *"I need to transfer you to a human agent, no policy found."*
- **Multilingual Integrity:** Gemini 1.5 Flash handles cross-lingual generation natively. It reads the English policy but outputs the correct language based on the user's input, bypassing the need for a separate translation API.

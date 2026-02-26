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

Deep Learning Plan with 200K Dataset
Your Advantage with 200K Data
Less data  (<10K)  → Use pretrained zero-shot
Medium     (10-50K) → Fine-tune small model
Large      (200K)  → Fine-tune large model properly
                     = Maximum accuracy possible ✅

Best Models for 200K Data
For Classification (Category)
ModelWhy Good for 200KDeBERTa-v3-largeBest accuracy, 200K is perfect size to fine-tuneRoBERTa-largeProven on large datasets, very stableBERT-largeClassic, reliable, well documented
Winner → DeBERTa-v3-large

200K data is exactly what it needs to shine
Disentangled attention = better text understanding
State of the art on text classification benchmarks


For Urgency Detection
ModelWhyRoBERTa-largeBest at capturing tone & emotion in textDeBERTa-v3-baseLighter, still very accurateELECTRA-largeExcellent discriminator, great for subtle urgency
Winner → RoBERTa-large

Urgency is about tone/emotion
RoBERTa reads tone better than BERT
Large variant needs 200K+ to perform well


Training Strategy with 200K
200K tickets
     ↓
Split:
├── 160K → Training   (80%)
├── 20K  → Validation (10%)
└── 20K  → Testing    (10%)
Key Decisions
DecisionChoiceWhyEpochs3-5200K data = less epochs neededBatch size32-64More data = bigger batchesLearning rate1e-5 to 3e-5Standard for large modelsWarmup10% of stepsPrevents early instabilitySchedulerCosine decayBest for large datasetsEarly stoppingAfter 2 bad epochsPrevent overfitting

What Accuracy to Expect
With 200K data + DeBERTa-v3-large:

Classification:
Refund    → 95-97%
Login     → 94-96%
Delivery  → 93-95%
Billing   → 95-97%
Account   → 93-95%
Other     → 90-92%
Overall   → 93-96% ✅

Urgency (RoBERTa-large):
High      → 91-93%
Medium    → 88-91%
Low       → 90-92%
Overall   → 89-92% ✅

Training Pipeline Overview
Raw 200K tickets
      ↓
Preprocessing
├── Clean text
├── Remove duplicates
├── Handle class imbalance (oversample rare classes)
└── Translate non-English (if multilingual)
      ↓
Tokenization
├── Max length 256 tokens
└── WordPiece tokenizer
      ↓
Model Fine-tuning
├── DeBERTa-v3-large (classification)
└── RoBERTa-large (urgency)
      ↓
Evaluation
├── Accuracy
├── F1 Score (weighted)
├── Confusion Matrix
└── Per-class precision & recall
      ↓
Save best checkpoint

Hardware You Need
HardwareTime for 200KRecommendationGoogle Colab Free (T4)4-6 hoursOK for testingColab Pro (A100)1-2 hoursBest valueKaggle (2x T4)3-4 hoursFree optionLocal RTX 30902-3 hoursIf you have it
Recommendation → Kaggle (free) or Colab Pro

Class Imbalance Strategy
200K tickets might be unbalanced:
Refund   → 60K  (too many)
Login    → 40K
Delivery → 35K
Billing  → 30K
Account  → 25K
Other    → 10K  (too few)
     ↓
Solutions:
1. Oversample minority classes
2. Use weighted loss function
3. SMOTE for text augmentation

Evaluation Metrics to Track
MetricWhat it tells youAccuracyOverall correctnessF1 WeightedAccuracy accounting for imbalanceConfusion MatrixWhich categories get confusedPer-class F1Which category needs improvementConfidence scoreHow sure the model is

Full Model Stack
Ticket comes in
      ↓
DeBERTa-v3-large  → Category (93-96%)
RoBERTa-large     → Urgency  (89-92%)
      ↓
If confidence < 0.7
      ↓
Claude API fallback → handles edge cases
      ↓
RAG Pipeline → KB retrieval → Draft reply

One Line Summary

200K data + DeBERTa-v3-large = production-grade classifier. Best combination you can use without building from scratch.

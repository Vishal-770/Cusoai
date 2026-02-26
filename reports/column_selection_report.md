# 📊 Column Selection Report — Task 2
> **Dataset:** `customer_support_tickets_200k.csv` (200K rows, 30 columns)  
> **Reduced to:** `tickets_for_training.csv` (9 columns, 37.89 MB from 70.42 MB)  
> **Date:** 2026-03-05

---

## Why We Reduced Columns

The DL plan uses **pure text-based models**:
- **DeBERTa-v3-large** → reads `issue_description`, predicts `category`
- **RoBERTa-large** → reads `issue_description`, predicts `urgency`

These transformer models **only accept text tokens**. They do not accept tabular numbers or categorical metadata as direct inputs. So any column that isn't the input text, a training label, or essential for preprocessing/RAG is **irrelevant** to the models and should be dropped.

---

## ✅ 9 Columns Kept

| # | Column | Role | Why Kept |
|---|--------|------|----------|
| 1 | `ticket_id` | Identifier | Needed to trace tickets during eval and inference |
| 2 | `issue_description` | **Primary model input** | The text both DeBERTa and RoBERTa read — the only input feature |
| 3 | `category` | **DeBERTa label** | Ground truth label for fine-tuning DeBERTa-v3-large |
| 4 | `priority` | Urgency source | Raw field; kept for auditability before mapping |
| 5 | `urgency` | **RoBERTa label** | Mapped from priority (Urgent/High→High, Medium→Medium, Low→Low). Ground truth for RoBERTa-large |
| 6 | `resolution_notes` | **RAG Knowledge Base** | Extracted into `data/kb/` as the document store for retrieval + grounded reply drafting |
| 7 | `language` | Preprocessing flag | Needed to detect non-English tickets and route them through a translation step before tokenization |
| 8 | `channel` | Metadata input | Required by the problem statement as optional metadata input |
| 9 | `ticket_created_date` | Metadata input | Required by the problem statement as optional timestamp input |

---

## ❌ 21 Columns Dropped

### 🔴 PII — Personal Identifiable Information
| Column | Reason |
|--------|--------|
| `customer_name` | Not a feature. Privacy violation risk. Models don't use names. |
| `customer_email` | Not a feature. PII — must be removed before any training. |

### 🔴 Outcome / Result Columns (Data Leakage Risk)
These columns are **produced after** the ticket is resolved — at inference time they don't exist yet. Using them in training would cause data leakage.

| Column | Reason |
|--------|--------|
| `status` | Open/Closed — known only after resolution, not at ticket submission time |
| `escalated` | Determined after the ticket is handled — not available at prediction time |
| `sla_breached` | Known only after resolution — future leakage |
| `first_response_time_hours` | Post-resolution metric — leakage |
| `resolution_time_hours` | Post-resolution metric — leakage |
| `ticket_resolved_date` | Exists only after resolution — leakage |

### 🟡 Tabular Metadata — Not Used by Transformer Models
DeBERTa and RoBERTa are text-only models. They **cannot** accept numeric/categorical columns directly. These features provide no benefit unless you build a separate tabular model.

| Column | Reason |
|--------|--------|
| `customer_age` | Demographic — no bearing on text classification |
| `customer_gender` | Demographic — irrelevant for ticket triage |
| `customer_tenure_months` | Account metric — transformer doesn't use it |
| `previous_tickets` | Count metric — not a text signal |
| `customer_satisfaction_score` | Post-resolution rating — both leakage and not model input |
| `subscription_type` | Could signal urgency, but RoBERTa infers urgency from tone — not metadata |
| `customer_segment` | Business segment — RoBERTa doesn't need this for urgency detection |
| `issue_complexity_score` | Post-assessment score — potential leakage, not available pre-classification |

### 🟡 Too Granular / Low Signal
| Column | Reason |
|--------|--------|
| `operating_system` | Too specific; already implied in `issue_description` text |
| `browser` | Edge case tech detail; captured inside the issue text anyway |
| `payment_method` | Billing-specific; issue_description already mentions payment context |
| `preferred_contact_time` | Scheduling preference — zero relevance to classification or urgency |
| `region` | Geography has no consistent mapping to category or urgency in text data |
| `product` | Product name is almost always mentioned inside `issue_description` itself — redundant |

---

## 📉 Impact Summary

| Metric | Before | After |
|--------|--------|-------|
| Columns | 30 | 9 |
| File size | 70.42 MB | 37.89 MB |
| PII columns | 2 | 0 |
| Leakage-risk columns | 6 | 0 |
| Irrelevant metadata | 13 | 0 |

---

## 🏗️ How Each Kept Column Is Used

```
ticket_id            → trace/debug only (not fed to model)
issue_description    ──┬──→ DeBERTa-v3-large ──→ predicts category
                       └──→ RoBERTa-large    ──→ predicts urgency
category             ──→ training label for DeBERTa
urgency              ──→ training label for RoBERTa
priority             ──→ audit trail (source of urgency mapping)
resolution_notes     ──→ extracted to data/kb/ → RAG retrieval → draft reply
language             ──→ translation pipeline (non-English → English before tokenization)
channel              ──→ passed as system metadata in final JSON output
ticket_created_date  ──→ passed as system metadata in final JSON output
```

---

*Report generated on 2026-03-05 based on DL plan in TASK2_PLAN.md*

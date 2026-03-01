"""
TF-IDF + Logistic Regression — Urgency Classifier
===================================================
Trains on data/processed/train.csv, evaluates on test.csv.
Saves model to models/tfidf_urgency.pkl
Saves plots  to data/plots/

Run:
    python -m src.train_tfidf_urgency
"""

import os
import pickle
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_CSV  = os.path.join(BASE_DIR, "data", "processed", "train.csv")
VAL_CSV    = os.path.join(BASE_DIR, "data", "processed", "val.csv")
TEST_CSV   = os.path.join(BASE_DIR, "data", "processed", "test.csv")
PLOT_DIR   = os.path.join(BASE_DIR, "data", "plots")
MODEL_DIR  = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "tfidf_urgency.pkl")

os.makedirs(PLOT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.05)
PALETTE = sns.color_palette("muted")
CLASSES = ["High", "Low", "Medium"]


# ── Load data ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  TF-IDF + LOGISTIC REGRESSION — URGENCY CLASSIFIER")
print("=" * 60)

train_df = pd.read_csv(TRAIN_CSV).dropna(subset=["issue_description", "urgency"])
val_df   = pd.read_csv(VAL_CSV).dropna(subset=["issue_description", "urgency"])
test_df  = pd.read_csv(TEST_CSV).dropna(subset=["issue_description", "urgency"])

print(f"Train : {len(train_df):,} rows")
print(f"Val   : {len(val_df):,} rows")
print(f"Test  : {len(test_df):,} rows")
print(f"\nTrain urgency distribution:\n{train_df['urgency'].value_counts().to_string()}")

# Combine text + category + channel (exclude priority — direct label proxy)
def make_features(df):
    return (
        "category:" + df["category"].fillna("unknown").str.replace(" ", "_") + " "
        + "channel:" + df["channel"].fillna("unknown") + " "
        + df["issue_description"].astype(str)
    )

X_train = make_features(train_df)
y_train = train_df["urgency"]
X_val   = make_features(val_df)
y_val   = val_df["urgency"]
X_test  = make_features(test_df)
y_test  = test_df["urgency"]


# ── Build pipeline ─────────────────────────────────────────────────────────
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=50_000,
        ngram_range=(1, 2),     # unigrams + bigrams
        sublinear_tf=True,      # log-scaled TF
        min_df=2,
        strip_accents="unicode",
        analyzer="word",
    )),
    ("lr", LogisticRegression(
        max_iter=1000,
        C=5.0,
        solver="lbfgs",
        class_weight="balanced",   # compensate for High=50% dominance
        n_jobs=-1,
        random_state=42,
    )),
])


# ── Train ──────────────────────────────────────────────────────────────────
print("\nTraining…")
t0 = time.time()
pipeline.fit(X_train, y_train)
elapsed = time.time() - t0
print(f"Training time : {elapsed:.1f}s")


# ── Val accuracy ───────────────────────────────────────────────────────────
val_preds  = pipeline.predict(X_val)
val_acc    = accuracy_score(y_val, val_preds)
print(f"Val   accuracy : {val_acc:.4f}")


# ── Test accuracy ──────────────────────────────────────────────────────────
test_preds = pipeline.predict(X_test)
test_acc   = accuracy_score(y_test, test_preds)
print(f"Test  accuracy : {test_acc:.4f}")

report_dict = classification_report(y_test, test_preds, output_dict=True)
report_str  = classification_report(y_test, test_preds)
print(f"\nPer-class report (test set):\n\n{report_str}")


# ── Save model ─────────────────────────────────────────────────────────────
with open(MODEL_PATH, "wb") as f:
    pickle.dump(pipeline, f)
print(f"Model saved → {MODEL_PATH}")


# ── Plot 1: Confusion Matrix ───────────────────────────────────────────────
classes_present = sorted(y_test.unique())
cm = confusion_matrix(y_test, test_preds, labels=classes_present)

fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=classes_present, yticklabels=classes_present,
            linewidths=0.5, ax=ax)
ax.set_xlabel("Predicted", fontsize=11)
ax.set_ylabel("True", fontsize=11)
ax.set_title(f"TF-IDF + LR — Confusion Matrix  (acc={test_acc:.3f})")
plt.tight_layout()
path = os.path.join(PLOT_DIR, "tfidf_lr_confusion_matrix.png")
fig.savefig(path, dpi=150)
plt.close(fig)
print(f"Saved → {path}")


# ── Plot 2: Per-class F1 ───────────────────────────────────────────────────
f1_scores = [report_dict[c]["f1-score"] for c in classes_present]
prec      = [report_dict[c]["precision"] for c in classes_present]
recall    = [report_dict[c]["recall"] for c in classes_present]

x = np.arange(len(classes_present))
w = 0.25
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - w,   prec,      w, label="Precision", color=PALETTE[0])
ax.bar(x,       recall,    w, label="Recall",    color=PALETTE[1])
ax.bar(x + w,   f1_scores, w, label="F1",        color=PALETTE[2])
for bars in ax.patches:
    ax.text(bars.get_x() + bars.get_width() / 2,
            bars.get_height() + 0.012,
            f"{bars.get_height():.3f}",
            ha="center", va="bottom", fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels(classes_present)
ax.set_ylim(0, 1.15)
ax.set_ylabel("Score")
ax.set_title("TF-IDF + LR — Precision / Recall / F1 per urgency class")
ax.legend()
plt.tight_layout()
path = os.path.join(PLOT_DIR, "tfidf_lr_per_class_metrics.png")
fig.savefig(path, dpi=150)
plt.close(fig)
print(f"Saved → {path}")


# ── Plot 3: VADER vs TF-IDF+LR accuracy comparison ────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
models  = ["VADER\n(baseline)", "TF-IDF +\nLogistic Reg"]
accs    = [0.2758, test_acc]
colors  = [PALETTE[3], PALETTE[2]]
bars = ax.bar(models, accs, color=colors, edgecolor="white", width=0.4)
ax.bar_label(bars, fmt="%.4f", padding=6, fontsize=12, fontweight="bold")
ax.set_ylim(0, 1.15)
ax.set_ylabel("Test Accuracy")
ax.set_title("Urgency Model Comparison — VADER vs TF-IDF + LR")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
plt.tight_layout()
path = os.path.join(PLOT_DIR, "urgency_model_comparison.png")
fig.savefig(path, dpi=150)
plt.close(fig)
print(f"Saved → {path}")


# ── Plot 4: Predicted vs Actual distribution ───────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
colors_map = {"High": PALETTE[3], "Medium": PALETTE[1], "Low": PALETTE[2]}

actual_counts = pd.Series(y_test).value_counts()
pred_counts   = pd.Series(test_preds).value_counts()

for ax, counts, title in zip(axes,
                              [actual_counts, pred_counts],
                              ["Actual Distribution", "Predicted Distribution"]):
    bars = ax.bar(counts.index, counts.values,
                  color=[colors_map.get(l, PALETTE[0]) for l in counts.index],
                  edgecolor="white")
    ax.bar_label(bars, padding=4, fontsize=9)
    ax.set_title(title)
    ax.set_ylabel("Count")
    ax.set_ylim(0, counts.max() * 1.15)

fig.suptitle("TF-IDF + LR — Actual vs Predicted Urgency Distribution")
plt.tight_layout()
path = os.path.join(PLOT_DIR, "tfidf_lr_distribution.png")
fig.savefig(path, dpi=150)
plt.close(fig)
print(f"Saved → {path}")


print("\n✅  Done.")
print(f"   Test Accuracy : {test_acc:.4f}")
print(f"   Val  Accuracy : {val_acc:.4f}")
print(f"   Macro F1      : {report_dict['macro avg']['f1-score']:.4f}")

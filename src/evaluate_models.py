"""
Model Evaluation: FastText Category Classifier + VADER Urgency Engine
======================================================================
Produces a full test-set evaluation report with:
  - FastText: per-class precision / recall / F1, confusion matrix, confidence histogram
  - VADER:    per-class precision / recall / F1, confusion matrix, score distribution
  - Combined: side-by-side accuracy comparison bar chart
  - All plots saved to data/plots/

Run from d:/hack:
    python -m src.evaluate_models
"""

import os
import re
import sys

import fasttext
import matplotlib
matplotlib.use("Agg")           # headless – no display required
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FASTTEXT_MODEL = os.path.join(BASE_DIR, "models", "fasttext_category.bin")
FASTTEXT_TEST  = os.path.join(BASE_DIR, "data", "fasttext_data", "test.txt")
CSV_TEST       = os.path.join(BASE_DIR, "data", "processed", "test.csv")
PLOT_DIR       = os.path.join(BASE_DIR, "data", "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

POWER_WORD_RE = re.compile(
    r"\b(asap|urgent|emergency|directly|now|broken|lost|stolen|hacked|immediately|threat)\b",
    re.IGNORECASE,
)

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.05)
PALETTE = sns.color_palette("muted")


# ═══════════════════════════════════════════════════════════════════════════
# 1.  FastText Evaluation
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_fasttext():
    print("\n" + "=" * 60)
    print("  FASTTEXT — CATEGORY CLASSIFICATION")
    print("=" * 60)

    model = fasttext.load_model(FASTTEXT_MODEL)

    # --- read test.txt ---
    texts, true_labels = [], []
    with open(FASTTEXT_TEST, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[0].startswith("__label__"):
                label = parts[0].replace("__label__", "").replace("_", " ")
                true_labels.append(label)
                texts.append(parts[1])

    print(f"Test samples : {len(texts)}")

    # --- predict ---
    pred_labels, confidences = [], []
    for text in texts:
        labels, probs = model.predict(text.lower())
        pred_labels.append(labels[0].replace("__label__", "").replace("_", " "))
        confidences.append(float(probs[0]))

    # --- overall metrics ---
    correct = sum(t == p for t, p in zip(true_labels, pred_labels))
    accuracy = correct / len(true_labels)
    print(f"Overall Accuracy : {accuracy:.4f}  ({correct}/{len(true_labels)})")

    report = classification_report(true_labels, pred_labels, output_dict=True)
    report_str = classification_report(true_labels, pred_labels)
    print("\nPer-class report:\n")
    print(report_str)

    classes = sorted(set(true_labels))

    # ── Plot 1: Per-class F1 bar chart ─────────────────────────────────────
    f1_scores = [report[c]["f1-score"] for c in classes]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(classes, f1_scores, color=PALETTE[0], edgecolor="white")
    ax.bar_label(bars, fmt="%.3f", padding=4, fontsize=9)
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("F1-score")
    ax.set_title(f"FastText — Per-class F1  (overall acc = {accuracy:.3f})")
    ax.axvline(accuracy, color="red", linestyle="--", linewidth=1.2, label=f"Overall acc {accuracy:.3f}")
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "fasttext_per_class_f1.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")

    # ── Plot 2: Confusion Matrix ────────────────────────────────────────────
    cm = confusion_matrix(true_labels, pred_labels, labels=classes)
    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=classes,
        yticklabels=classes,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("True", fontsize=11)
    ax.set_title("FastText — Confusion Matrix (test set)")
    plt.xticks(rotation=35, ha="right", fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "fasttext_confusion_matrix.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")

    # ── Plot 3: Prediction confidence histogram ─────────────────────────────
    correct_conf = [c for c, t, p in zip(confidences, true_labels, pred_labels) if t == p]
    wrong_conf   = [c for c, t, p in zip(confidences, true_labels, pred_labels) if t != p]
    fig, ax = plt.subplots(figsize=(8, 4))
    bins = np.linspace(0, 1, 30)
    ax.hist(correct_conf, bins=bins, alpha=0.7, label=f"Correct  (n={len(correct_conf)})", color=PALETTE[2])
    ax.hist(wrong_conf,   bins=bins, alpha=0.7, label=f"Wrong    (n={len(wrong_conf)})", color=PALETTE[3])
    ax.set_xlabel("Prediction confidence")
    ax.set_ylabel("Count")
    ax.set_title("FastText — Confidence distribution (correct vs wrong)")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "fasttext_confidence_histogram.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")

    return accuracy, report


# ═══════════════════════════════════════════════════════════════════════════
# 2.  VADER Urgency Evaluation
# ═══════════════════════════════════════════════════════════════════════════

def vader_predict(analyzer, text: str) -> str:
    if not isinstance(text, str):
        return "Medium"
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    has_power = bool(POWER_WORD_RE.search(text))
    if compound < -0.5 or has_power:
        return "High"
    elif compound > 0.5:
        return "Low"
    return "Medium"


def evaluate_vader():
    print("\n" + "=" * 60)
    print("  VADER — URGENCY CLASSIFICATION")
    print("=" * 60)

    df = pd.read_csv(CSV_TEST)

    # Drop rows with missing urgency label
    df = df.dropna(subset=["urgency", "issue_description"])
    print(f"Test samples : {len(df)}")
    print(f"Label dist   :\n{df['urgency'].value_counts().to_string()}\n")

    analyzer = SentimentIntensityAnalyzer()
    df["predicted_urgency"] = df["issue_description"].apply(
        lambda x: vader_predict(analyzer, str(x))
    )
    df["compound"] = df["issue_description"].apply(
        lambda x: analyzer.polarity_scores(str(x))["compound"]
    )

    true_labels = df["urgency"].tolist()
    pred_labels = df["predicted_urgency"].tolist()
    classes = sorted(set(true_labels))

    correct = sum(t == p for t, p in zip(true_labels, pred_labels))
    accuracy = correct / len(true_labels)
    print(f"Overall Accuracy : {accuracy:.4f}  ({correct}/{len(true_labels)})")

    report_str = classification_report(true_labels, pred_labels, labels=classes)
    report = classification_report(true_labels, pred_labels, labels=classes, output_dict=True)
    print("\nPer-class report:\n")
    print(report_str)

    # ── Plot 4: Per-class F1 bar chart ─────────────────────────────────────
    f1_scores = [report[c]["f1-score"] for c in classes]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(classes, f1_scores, color=PALETTE[1], edgecolor="white", width=0.5)
    ax.bar_label(bars, fmt="%.3f", padding=4, fontsize=10)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("F1-score")
    ax.set_title(f"VADER — Per-class F1  (overall acc = {accuracy:.3f})")
    ax.axhline(accuracy, color="red", linestyle="--", linewidth=1.2, label=f"Overall acc {accuracy:.3f}")
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "vader_per_class_f1.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")

    # ── Plot 5: Confusion Matrix ────────────────────────────────────────────
    cm = confusion_matrix(true_labels, pred_labels, labels=classes)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=classes,
        yticklabels=classes,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("True", fontsize=11)
    ax.set_title("VADER — Confusion Matrix (test set)")
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "vader_confusion_matrix.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")

    # ── Plot 6: Compound score distribution by true label ──────────────────
    fig, ax = plt.subplots(figsize=(8, 4))
    for label, color in zip(classes, PALETTE):
        subset = df[df["urgency"] == label]["compound"]
        ax.hist(subset, bins=40, alpha=0.6, label=label, color=color, density=True)
    ax.axvline(-0.5, color="black", linestyle="--", linewidth=1, label="threshold −0.5")
    ax.axvline(0.5,  color="grey",  linestyle="--", linewidth=1, label="threshold +0.5")
    ax.set_xlabel("VADER compound score")
    ax.set_ylabel("Density")
    ax.set_title("VADER — Compound score distribution by true urgency")
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "vader_compound_distribution.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")

    # ── Plot 7: Precision / Recall / F1 grouped bar ─────────────────────────
    metrics = ["precision", "recall", "f1-score"]
    x = np.arange(len(classes))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (metric, color) in enumerate(zip(metrics, PALETTE)):
        vals = [report[c][metric] for c in classes]
        ax.bar(x + i * width, vals, width, label=metric.replace("-", " ").title(), color=color)
    ax.set_xticks(x + width)
    ax.set_xticklabels(classes)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Score")
    ax.set_title("VADER — Precision / Recall / F1 per class")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "vader_precision_recall_f1.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")

    return accuracy, report


# ═══════════════════════════════════════════════════════════════════════════
# 3.  Side-by-side summary
# ═══════════════════════════════════════════════════════════════════════════

def plot_summary(ft_acc: float, vader_acc: float, ft_report: dict, vader_report: dict):
    print("\n" + "=" * 60)
    print("  COMBINED SUMMARY")
    print("=" * 60)
    print(f"  FastText accuracy  : {ft_acc:.4f}")
    print(f"  VADER accuracy     : {vader_acc:.4f}")

    # ── Plot 8: Overall accuracy comparison ────────────────────────────────
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        ["FastText\n(Category)", "VADER\n(Urgency)"],
        [ft_acc, vader_acc],
        color=[PALETTE[0], PALETTE[1]],
        edgecolor="white",
        width=0.4,
    )
    ax.bar_label(bars, fmt="%.4f", padding=6, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Accuracy (test set)")
    ax.set_title("Model Accuracy Comparison")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "model_accuracy_comparison.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\nSaved → {path}")

    # ── Plot 9: Macro F1 comparison ────────────────────────────────────────
    ft_f1    = ft_report["macro avg"]["f1-score"]
    vader_f1 = vader_report["macro avg"]["f1-score"]
    ft_prec    = ft_report["macro avg"]["precision"]
    vader_prec = vader_report["macro avg"]["precision"]
    ft_rec    = ft_report["macro avg"]["recall"]
    vader_rec = vader_report["macro avg"]["recall"]

    metrics = ["Precision", "Recall", "F1"]
    ft_vals    = [ft_prec,    ft_rec,    ft_f1]
    vader_vals = [vader_prec, vader_rec, vader_f1]

    x = np.arange(len(metrics))
    width = 0.32
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - width / 2, ft_vals,    width, label="FastText (Category)", color=PALETTE[0])
    ax.bar(x + width / 2, vader_vals, width, label="VADER (Urgency)",     color=PALETTE[1])
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Macro-avg score")
    ax.set_title("Macro-avg Precision / Recall / F1 — FastText vs VADER")
    ax.legend()
    for bar in ax.patches:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.015,
            f"{bar.get_height():.3f}",
            ha="center", va="bottom", fontsize=9,
        )
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "model_macro_comparison.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")


# ═══════════════════════════════════════════════════════════════════════════
# 4.  FastText training curve  (re-trains for 25 epochs, records val acc)
# ═══════════════════════════════════════════════════════════════════════════

def plot_fasttext_training_curve():
    print("\n" + "=" * 60)
    print("  FASTTEXT TRAINING CURVE  (epochs 1 → 25)")
    print("=" * 60)
    print("Training epoch checkpoints… (this takes ~1-2 min)")

    train_file = os.path.join(BASE_DIR, "data", "fasttext_data", "train.txt")
    val_file   = os.path.join(BASE_DIR, "data", "fasttext_data", "val.txt")

    epoch_points = [1, 3, 5, 8, 10, 13, 15, 18, 20, 23, 25]
    val_precisions = []

    for ep in epoch_points:
        m = fasttext.train_supervised(
            input=train_file,
            lr=1.0,
            epoch=ep,
            wordNgrams=2,
            bucket=200000,
            dim=50,
            loss="softmax",
            verbose=0,
        )
        _, p, _ = m.test(val_file)
        val_precisions.append(p)
        print(f"  epoch {ep:>2}  →  val precision @ 1 = {p:.4f}")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(epoch_points, val_precisions, marker="o", color=PALETTE[0], linewidth=2, markersize=6)
    ax.fill_between(epoch_points, val_precisions, alpha=0.12, color=PALETTE[0])
    ax.set_xlabel("Epochs")
    ax.set_ylabel("Validation Precision @ 1")
    ax.set_title("FastText — Training Curve (val precision vs epochs)")
    ax.set_ylim(max(0, min(val_precisions) - 0.05), 1.02)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
    for ep, p in zip(epoch_points, val_precisions):
        ax.annotate(f"{p:.3f}", (ep, p), textcoords="offset points", xytext=(4, 6), fontsize=8)
    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "fasttext_training_curve.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved → {path}")


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🔍  Evaluating FastText + VADER models on held-out test set")
    print(f"    Plots will be saved to: {PLOT_DIR}\n")

    ft_acc, ft_report = evaluate_fasttext()
    vader_acc, vader_report = evaluate_vader()
    plot_summary(ft_acc, vader_acc, ft_report, vader_report)
    plot_fasttext_training_curve()

    print("\n✅  All evaluations complete.")
    print(f"    Open data/plots/ to view all {len(os.listdir(PLOT_DIR))} charts.")

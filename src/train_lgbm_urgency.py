"""
TF-IDF + LightGBM — Urgency Classifier
=======================================
Trains on data/processed/train.csv, evaluates on test.csv.
Saves model  → models/lgbm_urgency.pkl
Saves plots  → data/plots/

Run:
    python -m src.train_lgbm_urgency
"""

import os
import pickle
import time
import warnings
warnings.filterwarnings("ignore")

import lightgbm as lgb
from sklearn.utils.class_weight import compute_sample_weight
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.preprocessing import LabelEncoder

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_CSV  = os.path.join(BASE_DIR, "data", "processed", "train.csv")
VAL_CSV    = os.path.join(BASE_DIR, "data", "processed", "val.csv")
TEST_CSV   = os.path.join(BASE_DIR, "data", "processed", "test.csv")
PLOT_DIR   = os.path.join(BASE_DIR, "data", "plots")
MODEL_PATH = os.path.join(BASE_DIR, "models", "lgbm_urgency.pkl")
os.makedirs(PLOT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.05)
PALETTE = sns.color_palette("muted")

# ── Load ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  TF-IDF + LightGBM — URGENCY CLASSIFIER")
print("=" * 60)

train_df = pd.read_csv(TRAIN_CSV).dropna(subset=["issue_description", "urgency"])
val_df   = pd.read_csv(VAL_CSV).dropna(subset=["issue_description", "urgency"])
test_df  = pd.read_csv(TEST_CSV).dropna(subset=["issue_description", "urgency"])

print(f"Train : {len(train_df):,}  |  Val : {len(val_df):,}  |  Test : {len(test_df):,}")
print(f"\nTrain urgency dist:\n{train_df['urgency'].value_counts().to_string()}\n")

# Text + category + channel (NO priority — it's a label proxy)
def make_text(df):
    return (
        "category:" + df["category"].fillna("unknown").str.replace(" ", "_") + " "
        + "channel:" + df["channel"].fillna("unknown") + " "
        + df["issue_description"].astype(str)
    )

X_train_raw = make_text(train_df)
X_val_raw   = make_text(val_df)
X_test_raw  = make_text(test_df)

# ── TF-IDF ─────────────────────────────────────────────────────────────────
print("Fitting TF-IDF…")
tfidf = TfidfVectorizer(
    max_features=80_000,
    ngram_range=(1, 2),
    sublinear_tf=True,
    min_df=2,
    strip_accents="unicode",
)
X_train = tfidf.fit_transform(X_train_raw)
X_val   = tfidf.transform(X_val_raw)
X_test  = tfidf.transform(X_test_raw)

le = LabelEncoder()
y_train = le.fit_transform(train_df["urgency"])
y_val   = le.transform(val_df["urgency"])
y_test  = le.transform(test_df["urgency"])
class_names = le.classes_
print(f"Classes  : {list(class_names)}")
print(f"Features : {X_train.shape[1]:,}")

# ── LightGBM ───────────────────────────────────────────────────────────────
print("\nTraining LightGBM…")

# sample weights to compensate for High=50% dominance
sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)

ds_train = lgb.Dataset(X_train, label=y_train, weight=sample_weights)
ds_val   = lgb.Dataset(X_val,   label=y_val,   reference=ds_train)

params = {
    "objective":        "multiclass",
    "num_class":        len(class_names),
    "metric":           "multi_logloss",
    "learning_rate":    0.1,
    "num_leaves":       127,
    "min_data_in_leaf": 20,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq":     5,
    "verbosity":        -1,
    "n_jobs":           -1,
    "seed":             42,
}

evals_result = {}
callbacks = [
    lgb.early_stopping(30, verbose=False),
    lgb.log_evaluation(period=20),
    lgb.record_evaluation(evals_result),
]

t0 = time.time()
model = lgb.train(
    params,
    ds_train,
    num_boost_round=300,
    valid_sets=[ds_train, ds_val],
    valid_names=["train", "val"],
    callbacks=callbacks,
)
elapsed = time.time() - t0
print(f"Training time : {elapsed:.1f}s  |  Best round: {model.best_iteration}")

# ── Evaluate ───────────────────────────────────────────────────────────────
def predict(X):
    proba = model.predict(X, num_iteration=model.best_iteration)
    return np.argmax(proba, axis=1)

val_preds  = predict(X_val)
test_preds = predict(X_test)

val_acc  = accuracy_score(y_val,  val_preds)
test_acc = accuracy_score(y_test, test_preds)

val_preds_str  = le.inverse_transform(val_preds)
test_preds_str = le.inverse_transform(test_preds)
y_test_str     = le.inverse_transform(y_test)

print(f"\nVal  accuracy : {val_acc:.4f}")
print(f"Test accuracy : {test_acc:.4f}")

report_dict = classification_report(y_test_str, test_preds_str, output_dict=True)
print(f"\nPer-class report (test):\n\n{classification_report(y_test_str, test_preds_str)}")

# ── Save model ─────────────────────────────────────────────────────────────
with open(MODEL_PATH, "wb") as f:
    pickle.dump({"model": model, "tfidf": tfidf, "le": le}, f)
print(f"Saved → {MODEL_PATH}")

classes_present = sorted(test_df["urgency"].unique())

# ── Plot 1: Confusion matrix ───────────────────────────────────────────────
cm = confusion_matrix(y_test_str, test_preds_str, labels=classes_present)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=classes_present, yticklabels=classes_present,
            linewidths=0.5, ax=ax)
ax.set_xlabel("Predicted"); ax.set_ylabel("True")
ax.set_title(f"LightGBM — Confusion Matrix (acc={test_acc:.3f})")
plt.tight_layout()
path = os.path.join(PLOT_DIR, "lgbm_confusion_matrix.png")
fig.savefig(path, dpi=150); plt.close(fig)
print(f"Saved → {path}")

# ── Plot 2: Per-class P / R / F1 ──────────────────────────────────────────
metrics = ["precision", "recall", "f1-score"]
x = np.arange(len(classes_present))
w = 0.25
fig, ax = plt.subplots(figsize=(8, 5))
for i, (metric, color) in enumerate(zip(metrics, PALETTE)):
    vals = [report_dict[c][metric] for c in classes_present]
    bars = ax.bar(x + i * w, vals, w, label=metric.title(), color=color)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.012,
                f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=8)
ax.set_xticks(x + w); ax.set_xticklabels(classes_present)
ax.set_ylim(0, 1.15); ax.set_ylabel("Score")
ax.set_title("LightGBM — Precision / Recall / F1 per urgency class")
ax.legend(); plt.tight_layout()
path = os.path.join(PLOT_DIR, "lgbm_per_class_metrics.png")
fig.savefig(path, dpi=150); plt.close(fig)
print(f"Saved → {path}")

# ── Plot 3: Training loss curve ────────────────────────────────────────────
train_loss = evals_result["train"]["multi_logloss"]
val_loss   = evals_result["val"]["multi_logloss"]
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(train_loss, label="Train loss", color=PALETTE[0], linewidth=1.5)
ax.plot(val_loss,   label="Val loss",   color=PALETTE[1], linewidth=1.5)
ax.axvline(model.best_iteration - 1, color="red", linestyle="--",
           linewidth=1.2, label=f"Best round {model.best_iteration}")
ax.set_xlabel("Boosting round"); ax.set_ylabel("Multi-logloss")
ax.set_title("LightGBM — Training & Validation Loss Curve")
ax.legend(); plt.tight_layout()
path = os.path.join(PLOT_DIR, "lgbm_loss_curve.png")
fig.savefig(path, dpi=150); plt.close(fig)
print(f"Saved → {path}")

# ── Plot 4: Comparison VADER vs TF-IDF+LR vs LightGBM ─────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
model_names = ["VADER\n(baseline)", "TF-IDF +\nLogistic Reg", "TF-IDF +\nLightGBM"]
accs        = [0.2758,              0.3084,                    test_acc]
colors      = [PALETTE[3], PALETTE[1], PALETTE[0]]
bars = ax.bar(model_names, accs, color=colors, edgecolor="white", width=0.45)
ax.bar_label(bars, fmt="%.4f", padding=6, fontsize=12, fontweight="bold")
ax.set_ylim(0, 1.1); ax.set_ylabel("Test Accuracy")
ax.set_title("Urgency Model Comparison")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
plt.tight_layout()
path = os.path.join(PLOT_DIR, "urgency_model_comparison.png")
fig.savefig(path, dpi=150); plt.close(fig)
print(f"Saved → {path}")

# ── Top features ───────────────────────────────────────────────────────────
print("\nTop 20 most important features:")
feat_names = tfidf.get_feature_names_out()
importance = model.feature_importance(importance_type="gain")
top_idx    = np.argsort(importance)[-20:][::-1]
for i, idx in enumerate(top_idx):
    print(f"  {i+1:>2}. {feat_names[idx]:<30} {importance[idx]:.1f}")

print(f"\n✅  Done.  Test acc: {test_acc:.4f}  |  Macro F1: {report_dict['macro avg']['f1-score']:.4f}")

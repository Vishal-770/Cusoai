import pandas as pd

df = pd.read_csv("d:/hack/data/tickets_for_training.csv")
print("Columns:", df.columns.tolist())
print("Shape:", df.shape)
print("\nCategory value counts:")
print(df["category"].value_counts())
print("\nSample rows (category vs description):")
for _, row in df.head(10).iterrows():
    cat = str(row["category"])
    desc = str(row["issue_description"])[:80]
    print(f"  [{cat:<28}]  {desc}")

# Also check if descriptions ever contain category keywords per row
# to see if labels are truly mismatched or just noisy
import re
kw_map = {
    "Login Issue": ["login", "sign in", "signin", "password", "credentials", "log in"],
    "Bug Report": ["bug", "error", "crash", "broken", "glitch", "fails", "issue"],
    "Payment Problem": ["payment", "charge", "invoice", "billing", "transaction"],
    "Subscription Cancellation": ["cancel", "cancellation", "subscription"],
    "Refund Request": ["refund", "reimburse", "money back"],
    "Security Concern": ["hack", "security", "phish", "unauthor"],
    "Account Suspension": ["suspend", "locked", "banned", "block"],
    "Feature Request": ["feature", "add", "request", "suggest", "would love"],
    "Data Sync Issue": ["sync", "synchron"],
    "Performance Issue": ["slow", "performance", "latency", "timeout", "speed"],
}

mismatches = 0
total = min(500, len(df))
for _, row in df.head(total).iterrows():
    cat = str(row["category"])
    desc = str(row["issue_description"]).lower()
    kws = kw_map.get(cat, [])
    if kws and not any(k in desc for k in kws):
        mismatches += 1

print(f"\nKeyword-mismatch rate (first {total} rows): {mismatches}/{total} ({mismatches/total*100:.1f}%)")
print("(High % = labels don't match content = training data is corrupted)")

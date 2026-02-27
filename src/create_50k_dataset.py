import pandas as pd
from sklearn.model_selection import train_test_split
import os

DATA_PATH = "data/tickets_for_training.csv"
OUTPUT_DIR = "data/processed_50k/"

print("Loading full 200K dataset...")
df = pd.read_csv(DATA_PATH)

print(f"Total rows: {len(df)}")
print(f"Categories: {df['category'].nunique()} -> {sorted(df['category'].unique())}")
print(f"Languages: {df['language'].nunique()} -> {sorted(df['language'].unique())}")

# ==============================================================================
# Target: 50,000 rows
# Strategy: Stratify by BOTH category AND language equally
# 10 categories × 6 languages = 60 unique buckets
# 50,000 / 60 = ~833 rows per bucket
# ==============================================================================

ROWS_PER_BUCKET = 833  # 833 × 60 = 49,980 ≈ 50K
print(f"\nSampling {ROWS_PER_BUCKET} rows per (category × language) bucket...")

sampled_parts = []
for (cat, lang), group in df.groupby(['category', 'language']):
    if len(group) >= ROWS_PER_BUCKET:
        sampled_parts.append(group.sample(n=ROWS_PER_BUCKET, random_state=42))
    else:
        # If a bucket doesn't have enough rows, take all of them
        print(f"  WARNING: '{cat}' x '{lang}' only has {len(group)} rows, taking all.")
        sampled_parts.append(group)

sampled = pd.concat(sampled_parts).sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\nFinal dataset: {len(sampled)} rows")
print(f"\nCategory distribution:")
print(sampled['category'].value_counts())
print(f"\nLanguage distribution:")
print(sampled['language'].value_counts())

# ==============================================================================
# Split: 80% Train (40K), 10% Val (5K), 10% Test (5K)
# Stratify by category to keep all classes balanced in each split
# ==============================================================================
print("\nSplitting 80/10/10...")
train_df, temp_df = train_test_split(
    sampled, test_size=0.2, random_state=42, stratify=sampled['category']
)
val_df, test_df = train_test_split(
    temp_df, test_size=0.5, random_state=42, stratify=temp_df['category']
)

print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

# Save
os.makedirs(OUTPUT_DIR, exist_ok=True)
train_df.to_csv(os.path.join(OUTPUT_DIR, "train.csv"), index=False)
val_df.to_csv(os.path.join(OUTPUT_DIR, "val.csv"), index=False)
test_df.to_csv(os.path.join(OUTPUT_DIR, "test.csv"), index=False)

print(f"\nAll splits saved to '{OUTPUT_DIR}'")
print("Upload train.csv and val.csv from this folder to Kaggle!")

import pandas as pd
from sklearn.model_selection import train_test_split
import os

DATA_PATH = "data/tickets_for_training.csv"
OUTPUT_DIR = "data/processed_30k/"

print("Loading full 200K dataset...")
df = pd.read_csv(DATA_PATH)

print(f"Total rows: {len(df)}")
print(f"Categories: {df['category'].nunique()}")
print(f"Languages: {df['language'].nunique()}")

# =============================================================================
# Sample exactly 3,000 rows per category = 30,000 total
# This ensures all 10 categories are perfectly balanced
# Also uses stratify on both category AND language for language diversity
# =============================================================================
print("\nSampling 3,000 rows per category (30K total)...")

sampled = df.groupby('category', group_keys=False).apply(
    lambda x: x.sample(n=3000, random_state=42)
)

# Shuffle so categories are mixed (not sorted)
sampled = sampled.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"\nFinal 30K dataset: {len(sampled)} rows")
print(f"Category distribution:\n{sampled['category'].value_counts()}")
print(f"\nLanguage distribution:\n{sampled['language'].value_counts()}")

# =============================================================================
# Split into 80/10/10 (24K train, 3K val, 3K test)
# Stratify by category to keep classes balanced in each split
# =============================================================================
print("\nSplitting 80/10/10...")
train_df, temp_df = train_test_split(
    sampled, test_size=0.2, random_state=42, stratify=sampled['category']
)
val_df, test_df = train_test_split(
    temp_df, test_size=0.5, random_state=42, stratify=temp_df['category']
)

print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

# Save to disk
os.makedirs(OUTPUT_DIR, exist_ok=True)
train_df.to_csv(os.path.join(OUTPUT_DIR, "train.csv"), index=False)
val_df.to_csv(os.path.join(OUTPUT_DIR, "val.csv"), index=False)
test_df.to_csv(os.path.join(OUTPUT_DIR, "test.csv"), index=False)

print(f"\nAll splits saved to '{OUTPUT_DIR}'")
print("Upload the train.csv and val.csv from this folder to Kaggle!")

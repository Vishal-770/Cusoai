import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer
import os

# Define paths - FIXED to use correct local paths based on the actual d:\hack\data directory
DATA_PATH = "data/tickets_for_training.csv"
OUTPUT_DIR = "data/processed/"

def preprocess_and_split():
    print("Loading dataset...")
    # 1. Load data
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"Error: {DATA_PATH} not found. Please ensure the file exists in the correct directory.")
        return

    print(f"Original Dataset Size: {len(df)} rows")

    # 2. Clean Text (Basic)
    print("Cleaning text data...")
    df['issue_description'] = df['issue_description'].astype(str)
    df['issue_description'] = df['issue_description'].str.strip()
    df['issue_description'] = df['issue_description'].str.lower()
    
    # 3. Create Splits (80/10/10)
    print("Splitting data (80% Train, 10% Val, 10% Test)...")
    train_df, temp_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['category'])
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42, stratify=temp_df['category'])

    print(f"Train size: {len(train_df)}")
    print(f"Validation size: {len(val_df)}")
    print(f"Test size: {len(test_df)}")

    # 4. Save splits
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    train_df.to_csv(os.path.join(OUTPUT_DIR, "train.csv"), index=False)
    val_df.to_csv(os.path.join(OUTPUT_DIR, "val.csv"), index=False)
    test_df.to_csv(os.path.join(OUTPUT_DIR, "test.csv"), index=False)
    
    print(f"Splits saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    preprocess_and_split()

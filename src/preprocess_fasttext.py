import pandas as pd
import re
import os
from sklearn.model_selection import train_test_split

# Paths
INPUT_CSV = "data/tickets_for_training.csv"
OUTPUT_DIR = "data/fasttext_data"
TRAIN_FILE = os.path.join(OUTPUT_DIR, "train.txt")
VAL_FILE = os.path.join(OUTPUT_DIR, "val.txt")

def clean_text(text):
    """
    Basic cleaning for FastText: lowercase, remove punctuation except spaces,
    and remove newlines.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text) # Remove punctuation
    text = re.sub(r'\s+', ' ', text)      # Collapse multiple spaces
    return text.strip()

def format_fasttext_label(label):
    """
    FastText labels must be prefix with __label__ and shouldn't have spaces.
    Example: 'Login Issue' -> '__label__Login_Issue'
    """
    return "__label__" + label.replace(" ", "_")

def main():
    print(f"Loading dataset from {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    
    # We only need the description and the category
    print("Preprocessing text for FastText...")
    df['clean_description'] = df['issue_description'].apply(clean_text)
    df['ft_label'] = df['category'].apply(format_fasttext_label)
    
    # Combine label and description: "__label__Category description text"
    df['ft_line'] = df['ft_label'] + " " + df['clean_description']
    
    # Split into Train (160K), Validation (20K), and Test (20K)
    print("Splitting data (80/10/10)...")
    train, temp = train_test_split(df['ft_line'], test_size=0.2, random_state=42, stratify=df['category'])
    val, test = train_test_split(temp, test_size=0.5, random_state=42, stratify=temp.apply(lambda x: x.split()[0]))
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Saving files to {OUTPUT_DIR}...")
    train.to_csv(TRAIN_FILE, index=False, header=False, sep='\t')
    val.to_csv(VAL_FILE, index=False, header=False, sep='\t')
    
    # Save test set separately just in case
    test.to_csv(os.path.join(OUTPUT_DIR, "test.txt"), index=False, header=False, sep='\t')
    
    print(f"\nSuccess! FastText files created:")
    print(f" - Train: {len(train)} rows -> {TRAIN_FILE}")
    print(f" - Val:   {len(val)} rows -> {VAL_FILE}")
    print(f" - Test:  {len(test)} rows")

if __name__ == "__main__":
    main()

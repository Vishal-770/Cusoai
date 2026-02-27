import fasttext
import os
import time

# Paths
TRAIN_FILE = "data/fasttext_data/train.txt"
VAL_FILE = "data/fasttext_data/val.txt"
MODEL_PATH = "models/fasttext_category.bin"

def main():
    print("Starting FastText training...")
    start_time = time.time()
    
    # Ensure models directory exists
    os.makedirs("models", exist_ok=True)
    
    # Training
    # lr: Learning rate
    # epoch: Number of passes over data
    # wordNgrams: Max length of word n-gram (2 helps capture context)
    # bucket: Number of buckets for hashing
    # dim: Dimension of word vectors
    model = fasttext.train_supervised(
        input=TRAIN_FILE,
        lr=1.0,
        epoch=25,
        wordNgrams=2,
        bucket=200000,
        dim=50,
        loss='softmax'
    )
    
    end_time = time.time()
    print(f"Training complete in {end_time - start_time:.2f} seconds.")
    
    # Save the model
    model.save_model(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    
    # Evaluation
    print("\nEvaluating on Validation set...")
    n, p, r = model.test(VAL_FILE)
    
    print(f"Number of samples: {n}")
    print(f"Precision @ 1:     {p:.4f}")
    print(f"Recall @ 1:        {r:.4f}")
    
    # Quick sanity check with a sample
    sample_text = "i cannot access my account because i forgot my password"
    pred = model.predict(sample_text)
    print(f"\nSanity check prediction:")
    print(f"Text: '{sample_text}'")
    print(f"Prediction: {pred[0][0]} with confidence {pred[1][0]:.4f}")

if __name__ == "__main__":
    main()

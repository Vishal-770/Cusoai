import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Configuration
KB_DIR = "data/kb"
INDEX_PATH = "embeddings/kb_index.faiss"
METADATA_PATH = "embeddings/kb_metadata.txt"
MODEL_NAME = "all-MiniLM-L6-v2"

def main():
    print(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    # Ensure embeddings directory exists
    os.makedirs("embeddings", exist_ok=True)
    
    # 1. Read all files in data/kb
    print(f"Reading policies from {KB_DIR}...")
    texts = []
    metadata = []
    
    for filename in os.listdir(KB_DIR):
        if filename.endswith(".txt"):
            with open(os.path.join(KB_DIR, filename), "r", encoding="utf-8") as f:
                content = f.read().strip()
                # For this hackathon, we treat each file as a single policy chunk
                # In a larger system, we would split by paragraph
                texts.append(content)
                metadata.append(filename)
    
    if not texts:
        print("Error: No policy files found in data/kb!")
        return

    # 2. Generate Embeddings
    print(f"Generating embeddings for {len(texts)} policy chunks...")
    embeddings = model.encode(texts)
    
    # 3. Create FAISS Index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    
    # 4. Save Index and Metadata
    print(f"Saving FAISS index to {INDEX_PATH}...")
    faiss.write_index(index, INDEX_PATH)
    
    # Save the raw text/filenames as metadata so we can retrieve them later
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        # We store them in order: INDEX_ID | FILENAME | CONTENT
        for i, (fname, content) in enumerate(zip(metadata, texts)):
            # Replace newlines in content with a placeholder to keep it one line per entry
            safe_content = content.replace("\n", "[NEWLINE]")
            f.write(f"{i}|{fname}|{safe_content}\n")
            
    print("\nSuccess! RAG Vector Database created.")
    print(f" - Chunks indexed: {len(texts)}")
    print(f" - Files saved: {INDEX_PATH}, {METADATA_PATH}")

if __name__ == "__main__":
    main()

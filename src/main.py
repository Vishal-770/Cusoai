import os
import fasttext
import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import google.generativeai as genai
from dotenv import load_dotenv
import re

# 1. Load Environment Variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in .env file. RAG generation will be disabled.")

# 2. Load Models & Data
print("Initializing Backend Engine...")
ft_model = fasttext.load_model("models/fasttext_category.bin")
vader_analyzer = SentimentIntensityAnalyzer()
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load FAISS Index
faiss_index = faiss.read_index("embeddings/kb_index.faiss")

# Load Metadata (Policies)
policies = {}
with open("embeddings/kb_metadata.txt", "r", encoding="utf-8") as f:
    for line in f:
        idx, fname, content = line.strip().split("|")
        # Restore newlines
        clean_content = content.replace("[NEWLINE]", "\n")
        policies[int(idx)] = {"file": fname, "text": clean_content}

# 3. FastAPI Setup
app = FastAPI(title="Support Ticket AI Engine")

class TicketRequest(BaseModel):
    description: str

class PredictionResponse(BaseModel):
    category: str
    category_confidence: float
    urgency: str
    urgency_score: float
    retrieved_policy: str
    ai_draft_reply: str

def get_urgency(text):
    scores = vader_analyzer.polarity_scores(text)
    compound = scores['compound']
    power_keywords = r'\b(asap|urgent|emergency|directly|now|broken|lost|stolen|hacked|immediately|threat)\b'
    has_power_word = bool(re.search(power_keywords, text.lower()))
    
    if compound < -0.5 or has_power_word:
        return "High", compound
    elif compound > 0.5:
        return "Low", compound
    return "Medium", compound

@app.post("/process_ticket", response_model=PredictionResponse)
async def process_ticket(request: TicketRequest):
    try:
        # Step 1: Category Prediction (FastText)
        desc_clean = request.description.lower().replace("\n", " ")
        labels, probs = ft_model.predict(desc_clean)
        category = labels[0].replace("__label__", "").replace("_", " ")
        confidence = probs[0]
        
        # Step 2: Urgency Prediction (VADER)
        urgency, urg_score = get_urgency(request.description)
        
        # Step 3: RAG Retrieval (FAISS)
        query_vector = embed_model.encode([request.description])
        distances, indices = faiss_index.search(np.array(query_vector).astype('float32'), k=1)
        best_idx = indices[0][0]
        policy_context = policies[best_idx]['text']
        
        # Step 4: AI Generation (Gemini)
        ai_reply = "Gemini API Key missing - could not generate draft."
        if GEMINI_API_KEY:
            prompt = f"""
            You are a helpful customer support agent. 
            A customer sent this ticket: "{request.description}"
            Our internal policy for this issue is: "{policy_context}"
            
            TASK:
            1. Analyze the customer's language.
            2. Draft a polite, helpful response that solves their problem using ONLY the policy provided.
            3. OUTPUT THE RESPONSE IN THE CUSTOMER'S NATIVE LANGUAGE.
            """
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            ai_reply = response.text
            
        return PredictionResponse(
            category=category,
            category_confidence=float(confidence),
            urgency=urgency,
            urgency_score=float(urg_score),
            retrieved_policy=policy_context,
            ai_draft_reply=ai_reply
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import re
import os

# Initialize VADER
analyzer = SentimentIntensityAnalyzer()

def get_urgency_score(text):
    """
    Combines VADER sentiment with custom urgency keywords to determine 
    ticket urgency.
    """
    if not isinstance(text, str):
        return "Medium", 0.0
    
    # 1. Get VADER sentiment scores
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    # 2. Check for "Power Keywords" that automatically boost urgency
    power_keywords = r'\b(asap|urgent|emergency|directly|now|broken|lost|stolen|hacked|immediately|threat)\b'
    has_power_word = bool(re.search(power_keywords, text.lower()))
    
    # 3. Decision Logic
    # High: Very negative sentiment OR power keywords
    if compound < -0.5 or has_power_word:
        urgency = "High"
    # Low: Positive or very polite sentiment
    elif compound > 0.5:
        urgency = "Low"
    # Medium: Neutral or slightly negative
    else:
        urgency = "Medium"
        
    return urgency, compound

def validate_vader():
    print("Validating VADER + Rules Urgency Engine...")
    
    test_cases = [
        "I need a refund NOW my account was hacked and I am very angry",
        "How do I change my profile picture? Thanks in advance.",
        "The app is slightly slow today, maybe just a small bug.",
        "URGENT: I lost my credit card and need to cancel my subscription immediately!"
    ]
    
    for text in test_cases:
        urgency, score = get_urgency_score(text)
        print(f"\nText: {text}")
        print(f"Urgency: {urgency} (Sentiment Score: {score:.4f})")

if __name__ == "__main__":
    validate_vader()
    
    # Optionally run on the 50K validation set to check accuracy
    VALIDATION_CSV = "data/processed_50k/val.csv"
    if os.path.exists(VALIDATION_CSV):
        print(f"\nRunning on {VALIDATION_CSV} for accuracy check...")
        df = pd.read_csv(VALIDATION_CSV)
        
        # Apply logic
        df[['predicted_urgency', 'sentiment_score']] = df['issue_description'].apply(
            lambda x: pd.Series(get_urgency_score(x))
        )
        
        # Calculate accuracy
        correct = (df['predicted_urgency'] == df['urgency']).sum()
        accuracy = correct / len(df)
        print(f"Total Val Samples: {len(df)}")
        print(f"Urgency Accuracy:  {accuracy:.4f}")

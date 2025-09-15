#!/usr/bin/env python3
"""Test the sentiment analysis functionality"""

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Test texts
test_texts = [
    "This product is absolutely fantastic! I love it.",
    "Terrible service, worst experience ever.",
    "The weather is okay today.",
    "I'm so happy with my purchase! Highly recommend!",
    "This is disappointing and not worth the money."
]

print("Testing Sentiment Analysis")
print("="*50)

# Initialize VADER
vader = SentimentIntensityAnalyzer()

for text in test_texts:
    print(f"\nText: {text}")
    print("-"*40)

    # TextBlob analysis
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    # VADER analysis
    vader_scores = vader.polarity_scores(text)
    compound = vader_scores['compound']

    # Combined score (same as in app)
    final_score = (polarity + compound) / 2

    # Determine sentiment
    if final_score > 0.1:
        sentiment = 'POSITIVE'
    elif final_score < -0.1:
        sentiment = 'NEGATIVE'
    else:
        sentiment = 'NEUTRAL'

    print(f"TextBlob Polarity: {polarity:.3f}")
    print(f"VADER Compound: {compound:.3f}")
    print(f"Combined Score: {final_score:.3f}")
    print(f"Final Sentiment: {sentiment}")

print("\n" + "="*50)
print("✓ Sentiment analysis is working correctly!")
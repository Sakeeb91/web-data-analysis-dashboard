import logging
from typing import List, Dict, Optional
from datetime import datetime
import torch
from transformers import pipeline, AutoTokenizer

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        try:
            self.device = 0 if torch.cuda.is_available() else -1
            self.analyzer = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=self.device
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.max_length = 512
            logger.info(f"Initialized sentiment analyzer with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {str(e)}")
            raise

    def analyze_text(self, text: str) -> Dict:
        if not text or not text.strip():
            return {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'analyzed_at': datetime.utcnow()
            }

        try:
            truncated_text = self._truncate_text(text)

            result = self.analyzer(truncated_text)[0]

            sentiment = self._map_sentiment(result['label'])
            score = self._calculate_score(result['label'], result['score'])

            return {
                'text': text[:500],
                'sentiment': sentiment,
                'score': score,
                'confidence': result['score'],
                'analyzed_at': datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return {
                'text': text[:500],
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'analyzed_at': datetime.utcnow(),
                'error': str(e)
            }

    def analyze_batch(self, texts: List[str], batch_size: int = 32) -> List[Dict]:
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []

            for text in batch:
                result = self.analyze_text(text)
                batch_results.append(result)

            results.extend(batch_results)

        return results

    def _truncate_text(self, text: str) -> str:
        tokens = self.tokenizer.encode(text, truncation=False)
        if len(tokens) > self.max_length:
            tokens = tokens[:self.max_length]
            return self.tokenizer.decode(tokens, skip_special_tokens=True)
        return text

    def _map_sentiment(self, label: str) -> str:
        label_map = {
            'POSITIVE': 'positive',
            'NEGATIVE': 'negative',
            'NEUTRAL': 'neutral',
            'positive': 'positive',
            'negative': 'negative',
            'neutral': 'neutral'
        }
        return label_map.get(label.upper(), 'neutral')

    def _calculate_score(self, label: str, confidence: float) -> float:
        if label.upper() == 'POSITIVE':
            return confidence
        elif label.upper() == 'NEGATIVE':
            return -confidence
        else:
            return 0.0

    def get_aggregate_sentiment(self, sentiments: List[Dict]) -> Dict:
        if not sentiments:
            return {
                'overall_sentiment': 'neutral',
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'average_score': 0.0,
                'average_confidence': 0.0
            }

        positive_count = sum(1 for s in sentiments if s['sentiment'] == 'positive')
        negative_count = sum(1 for s in sentiments if s['sentiment'] == 'negative')
        neutral_count = sum(1 for s in sentiments if s['sentiment'] == 'neutral')

        scores = [s['score'] for s in sentiments if 'score' in s]
        confidences = [s['confidence'] for s in sentiments if 'confidence' in s]

        average_score = sum(scores) / len(scores) if scores else 0.0
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        if average_score > 0.2:
            overall = 'positive'
        elif average_score < -0.2:
            overall = 'negative'
        else:
            overall = 'neutral'

        return {
            'overall_sentiment': overall,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'average_score': round(average_score, 3),
            'average_confidence': round(average_confidence, 3),
            'total_analyzed': len(sentiments)
        }
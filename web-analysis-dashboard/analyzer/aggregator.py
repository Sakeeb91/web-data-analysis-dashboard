import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)

class DataAggregator:
    def __init__(self):
        self.aggregation_functions = {
            'count': lambda x: len(x),
            'mean': lambda x: sum(x) / len(x) if x else 0,
            'sum': lambda x: sum(x),
            'min': lambda x: min(x) if x else None,
            'max': lambda x: max(x) if x else None
        }

    def aggregate_by_period(
        self,
        data: List[Dict],
        period: str = 'daily',
        date_field: str = 'analyzed_at'
    ) -> List[Dict]:
        if not data:
            return []

        df = pd.DataFrame(data)

        if date_field not in df.columns:
            logger.warning(f"Date field '{date_field}' not found in data")
            return []

        df[date_field] = pd.to_datetime(df[date_field])

        if period == 'daily':
            df['period'] = df[date_field].dt.date
        elif period == 'weekly':
            df['period'] = df[date_field].dt.to_period('W').dt.start_time
        elif period == 'hourly':
            df['period'] = df[date_field].dt.floor('H')
        else:
            df['period'] = df[date_field].dt.date

        aggregated = []
        for period_value, group in df.groupby('period'):
            period_data = self._aggregate_group(group, period_value)
            aggregated.append(period_data)

        return sorted(aggregated, key=lambda x: x['period'])

    def _aggregate_group(self, group: pd.DataFrame, period: datetime) -> Dict:
        sentiment_counts = group['sentiment'].value_counts().to_dict() if 'sentiment' in group.columns else {}

        scores = group['score'].tolist() if 'score' in group.columns else []
        confidences = group['confidence'].tolist() if 'confidence' in group.columns else []

        return {
            'period': period,
            'total_items': len(group),
            'sentiment_distribution': {
                'positive': sentiment_counts.get('positive', 0),
                'negative': sentiment_counts.get('negative', 0),
                'neutral': sentiment_counts.get('neutral', 0)
            },
            'average_score': sum(scores) / len(scores) if scores else 0,
            'average_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'min_score': min(scores) if scores else None,
            'max_score': max(scores) if scores else None
        }

    def aggregate_by_source(self, data: List[Dict]) -> Dict:
        by_source = defaultdict(list)

        for item in data:
            source = item.get('source', 'unknown')
            by_source[source].append(item)

        aggregated = {}
        for source, items in by_source.items():
            sentiments = [item for item in items if 'sentiment' in item]
            sentiment_summary = self._get_sentiment_summary(sentiments)

            aggregated[source] = {
                'total_items': len(items),
                'sentiment_summary': sentiment_summary,
                'last_updated': max(
                    (item.get('analyzed_at', datetime.min) for item in items),
                    default=None
                )
            }

        return aggregated

    def _get_sentiment_summary(self, sentiments: List[Dict]) -> Dict:
        if not sentiments:
            return {
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'dominant': 'neutral'
            }

        counts = defaultdict(int)
        for item in sentiments:
            sentiment = item.get('sentiment', 'neutral')
            counts[sentiment] += 1

        total = sum(counts.values())
        percentages = {k: (v / total * 100) for k, v in counts.items()}

        dominant = max(counts.items(), key=lambda x: x[1])[0] if counts else 'neutral'

        return {
            'positive': counts.get('positive', 0),
            'negative': counts.get('negative', 0),
            'neutral': counts.get('neutral', 0),
            'positive_pct': round(percentages.get('positive', 0), 1),
            'negative_pct': round(percentages.get('negative', 0), 1),
            'neutral_pct': round(percentages.get('neutral', 0), 1),
            'dominant': dominant
        }

    def calculate_trends(
        self,
        data: List[Dict],
        window_size: int = 7
    ) -> Dict:
        if len(data) < window_size:
            return {
                'trend': 'insufficient_data',
                'change_rate': 0,
                'direction': 'neutral'
            }

        df = pd.DataFrame(data)
        if 'average_score' not in df.columns:
            return {
                'trend': 'no_scores',
                'change_rate': 0,
                'direction': 'neutral'
            }

        df['ma'] = df['average_score'].rolling(window=window_size, min_periods=1).mean()

        recent_avg = df['ma'].iloc[-window_size:].mean() if len(df) >= window_size else df['ma'].mean()
        previous_avg = df['ma'].iloc[-window_size*2:-window_size].mean() if len(df) >= window_size*2 else df['ma'].iloc[0]

        if previous_avg != 0:
            change_rate = ((recent_avg - previous_avg) / abs(previous_avg)) * 100
        else:
            change_rate = 0

        if change_rate > 10:
            direction = 'improving'
        elif change_rate < -10:
            direction = 'declining'
        else:
            direction = 'stable'

        return {
            'trend': 'calculated',
            'change_rate': round(change_rate, 2),
            'direction': direction,
            'recent_average': round(recent_avg, 3),
            'previous_average': round(previous_avg, 3)
        }

    def get_summary_statistics(self, data: List[Dict]) -> Dict:
        if not data:
            return {
                'total_items': 0,
                'date_range': {'start': None, 'end': None},
                'sentiment_totals': {'positive': 0, 'negative': 0, 'neutral': 0},
                'score_stats': {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
            }

        df = pd.DataFrame(data)

        date_range = {
            'start': df['analyzed_at'].min() if 'analyzed_at' in df.columns else None,
            'end': df['analyzed_at'].max() if 'analyzed_at' in df.columns else None
        }

        sentiment_totals = (
            df['sentiment'].value_counts().to_dict()
            if 'sentiment' in df.columns
            else {'positive': 0, 'negative': 0, 'neutral': 0}
        )

        if 'score' in df.columns:
            score_stats = {
                'mean': round(df['score'].mean(), 3),
                'std': round(df['score'].std(), 3),
                'min': round(df['score'].min(), 3),
                'max': round(df['score'].max(), 3)
            }
        else:
            score_stats = {'mean': 0, 'std': 0, 'min': 0, 'max': 0}

        return {
            'total_items': len(df),
            'date_range': date_range,
            'sentiment_totals': sentiment_totals,
            'score_stats': score_stats
        }
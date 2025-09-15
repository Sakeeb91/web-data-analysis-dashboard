import os
from datetime import datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

import bcrypt  # noqa: E402

from database import db, APIKey  # noqa: E402
from database.models import ScrapedData, SentimentResult  # noqa: E402
import app_production as mod  # noqa: E402


def seed_db(app):
    with app.app_context():
        db.create_all()

        # API key (bcrypt hashed)
        token = "pytest-token"
        salt = bcrypt.gensalt(rounds=12)
        key_hash = bcrypt.hashpw(token.encode("utf-8"), salt).decode("utf-8")
        existing = APIKey.query.first()
        if not existing:
            k = APIKey(key=key_hash, is_active=True, label="pytest")
            db.session.add(k)
        else:
            existing.key = key_hash
            existing.is_active = True
        
        # Seed scraped + sentiments
        s = ScrapedData(url="https://example.com", content="Hello world", metadata={}, success=True)
        db.session.add(s)
        db.session.commit()

        for i in range(3):
            sr = SentimentResult(
                scraped_data_id=s.id,
                text_snippet=f"snippet {i}",
                sentiment="positive" if i % 2 == 0 else "neutral",
                score=0.6 if i % 2 == 0 else 0.0,
                confidence=0.9,
                analyzed_at=datetime.utcnow() - timedelta(hours=i),
            )
            db.session.add(sr)
        db.session.commit()

    return token


def test_export_and_aggregated_endpoints():
    app = mod.app
    token = seed_db(app)
    client = app.test_client()
    headers = {"X-API-Key": token}

    # Aggregated (should return either persisted aggregates or on-the-fly results)
    r1 = client.get("/api/aggregated/daily?days=7", headers=headers)
    assert r1.status_code == 200
    assert r1.is_json
    data = r1.get_json()
    assert data.get("success") is True
    assert isinstance(data.get("data"), list)

    # Export JSON
    r2 = client.get("/api/export/json?days=7", headers=headers)
    assert r2.status_code == 200
    assert r2.is_json
    data2 = r2.get_json()
    assert data2.get("success") is True
    assert data2.get("count") >= 1

    # Export CSV
    r3 = client.get("/api/export/csv?days=7", headers=headers)
    assert r3.status_code == 200
    assert r3.mimetype == "text/csv"
    assert len(r3.data) >= 1


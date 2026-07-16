"""Sanity tests for the prediction engine.

Run with:  cd backend && PYTHONPATH=. pytest -q
"""
from app.services.prediction_engine import dataset, predict


def test_dataset_loads():
    stats = dataset.stats()
    assert stats["valid_rows"] > 0
    assert stats["colleges"] > 0


def test_score_prediction_returns_bands():
    results = predict(
        mode="score", score=580, air=None, degrees=["MBBS"], gender="Male", category="OPEN"
    )
    assert results, "expected at least one college for a strong OPEN score"
    assert all(r["chance"] in {"High", "Moderate", "Low"} for r in results)
    # OPEN category must not expose a category rank.
    assert all(r["category_rank"] is None for r in results)
    # Sorted best-first by serial number.
    assert results[0]["sr_no"] == 1


def test_air_prediction_shows_category_rank():
    results = predict(
        mode="air", score=None, air=15000, degrees=["All"], gender="Female", category="OBC"
    )
    assert results
    # At least some non-OPEN rows should carry a category rank string.
    assert any(r["category_rank"] for r in results)


def test_all_degrees_expands():
    results = predict(
        mode="air", score=None, air=50000, degrees=["All"], gender="Male", category="OPEN"
    )
    degrees = {r["degree"] for r in results}
    assert len(degrees) >= 2

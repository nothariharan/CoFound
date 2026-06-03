"""Historical snapshot writer for Decision Journal."""

from datetime import datetime

from graph.schema import HistoricalSnapshot


def create_snapshot(confidence: int, delta: str) -> HistoricalSnapshot:
    return HistoricalSnapshot(
        timestamp=datetime.utcnow(),
        confidence=confidence,
        delta=delta,
    )

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def datetime_utc_from_str(datetime_str: str) -> datetime:
    return datetime.fromisoformat(datetime_str).astimezone(timezone.utc)


def ts_to_datetime_str(ts: float | int, dt_format: str = '%Y-%m-%dT%H:%M:%SZ'):
    return datetime.fromtimestamp(int(ts)).strftime(dt_format)

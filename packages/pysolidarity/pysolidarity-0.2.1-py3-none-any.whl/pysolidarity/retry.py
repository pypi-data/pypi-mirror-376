# pysolidarity/retry.py
from __future__ import annotations
import datetime
import email.utils
import random
from dataclasses import dataclass
from typing import Tuple, Optional, Type

import requests


@dataclass(frozen=True)
class RetryPolicy:
    """Exponential backoff with full jitter.

    - Applies to HTTP {429, 500, 502, 503, 504} and to common network exceptions.
    - Honors HTTP `Retry-After` when present (seconds or HTTP-date).
    - This is additive to any Redis RateLimitedSession gate you already use.
    """
    max_retries: int = 4              # total retry attempts (0 = disabled)
    backoff_initial: float = 0.5      # seconds
    backoff_max: float = 20.0         # cap in seconds
    jitter: bool = True
    retry_on_statuses: Tuple[int, ...] = (429, 500, 502, 503, 504)
    retry_on_exceptions: Tuple[Type[Exception], ...] = (
        requests.Timeout, requests.ConnectionError
    )


def parse_retry_after(value: Optional[str]) -> Optional[float]:
    """Parse Retry-After header to seconds (int or HTTP-date)."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return max(0.0, float(value))
    try:
        dt = email.utils.parsedate_to_datetime(value)
        now = datetime.datetime.now(tz=dt.tzinfo)
        return max(0.0, (dt - now).total_seconds())
    except Exception:
        return None


def compute_backoff(attempt: int, base: float, cap: float, jitter: bool) -> float:
    """Exponential backoff (attempt is 0-based) with optional full jitter."""
    delay = min(cap, base * (2 ** attempt))
    if jitter:
        delay = random.uniform(0, delay)
    return max(0.0, delay)


DEFAULT_RETRY = RetryPolicy()

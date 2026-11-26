"""Shared-demonstration lock. Local runs leave DEMO_ACCESS_TOKEN unset."""

import hmac
import os
import threading
import time


def enabled() -> bool:
    return bool(os.environ.get("DEMO_ACCESS_TOKEN", "").strip())


def token_ok(presented: str | None) -> bool:
    expected = os.environ.get("DEMO_ACCESS_TOKEN", "").strip()
    if not expected:
        return True
    if not presented:
        return False
    try:
        return hmac.compare_digest(presented, expected)
    except (TypeError, ValueError):
        return False


class ModelBudget:
    """Counts model starts for one process. A replay that does not start a model is free."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started: list[float] = []

    def allow(self) -> bool:
        if not enabled():
            return True
        raw = os.environ.get("DEMO_MODEL_CALLS_PER_HOUR", "8").strip() or "8"
        try:
            limit = int(raw)
        except ValueError:
            limit = 8
        now = time.monotonic()
        with self._lock:
            self._started = [stamp for stamp in self._started if now - stamp < 3600]
            if len(self._started) >= limit:
                return False
            self._started.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._started.clear()


budget = ModelBudget()


def allow_model_call() -> bool:
    return budget.allow()

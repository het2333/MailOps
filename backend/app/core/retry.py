import time
from collections.abc import Callable
from typing import TypeVar


Result = TypeVar("Result")


def with_retry(
    operation: Callable[[], Result],
    *,
    attempts: int = 3,
    base_delay: float = 0.05,
    sleep: Callable[[float], None] = time.sleep,
) -> Result:
    """Retry a safe operation with bounded exponential backoff."""
    if attempts < 1:
        raise ValueError("attempts must be at least one")
    for attempt in range(attempts):
        try:
            return operation()
        except Exception:
            if attempt == attempts - 1:
                raise
            sleep(base_delay * (2**attempt))
    raise RuntimeError("retry loop exhausted")

import pytest

from app.core.retry import with_retry


def test_retry_returns_third_attempt_after_two_transient_failures():
    attempts = 0
    delays: list[float] = []

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError("temporary")
        return "ok"

    assert with_retry(operation, base_delay=0.1, sleep=delays.append) == "ok"
    assert attempts == 3
    assert delays == [0.1, 0.2]


def test_retry_raises_final_error_after_three_attempts():
    attempts = 0

    def operation() -> None:
        nonlocal attempts
        attempts += 1
        raise TimeoutError(f"failure-{attempts}")

    with pytest.raises(TimeoutError, match="failure-3"):
        with_retry(operation, sleep=lambda _delay: None)

    assert attempts == 3

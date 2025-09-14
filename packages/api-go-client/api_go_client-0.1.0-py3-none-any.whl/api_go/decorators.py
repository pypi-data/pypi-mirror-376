import time
from functools import wraps
from typing import Callable


def retry(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток запроса"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
            raise last_exception

        return wrapper

    return decorator


def rate_limit(requests_per_minute: int = 60):
    """Декоратор для ограничения частоты запросов"""
    min_interval = 60.0 / requests_per_minute
    last_call = 0.0

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call
            elapsed = time.time() - last_call

            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                time.sleep(sleep_time)

            last_call = time.time()
            return func(*args, **kwargs)

        return wrapper

    return decorator
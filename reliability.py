"""
Retry-with-backoff wrapper for external API calls (Groq, Voyage).
Retries transient failures a limited number of times before giving up
and returning a safe fallback instead of crashing the caller.
"""

import time


def call_with_retry(func, *args, max_retries=3, base_delay=2, fallback=None, **kwargs):
    """
    Calls func(*args, **kwargs). On failure, retries up to max_retries
    times with exponential backoff (delay doubles each attempt).
    If all retries fail, returns `fallback` instead of raising.
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            wait = base_delay * (2 ** attempt)
            print(f"[retry] attempt {attempt + 1}/{max_retries} failed: {e}. Waiting {wait}s...")
            time.sleep(wait)

    print(f"[retry] all {max_retries} attempts failed, using fallback.")
    return fallback
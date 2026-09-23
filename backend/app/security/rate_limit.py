from collections import defaultdict, deque
from functools import wraps
from threading import Lock
from time import monotonic

from flask import current_app, g, request


_requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = Lock()


def reset_rate_limits() -> None:
    with _lock:
        _requests.clear()


def rate_limit(config_key: str):
    def apply(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            limit = int(current_app.config[config_key])
            window = int(current_app.config["RATE_LIMIT_WINDOW_SECONDS"])
            identity = request.remote_addr or "unknown"
            key = (identity, request.endpoint or view.__name__)
            now = monotonic()
            with _lock:
                timestamps = _requests[key]
                while timestamps and now - timestamps[0] >= window:
                    timestamps.popleft()
                if len(timestamps) >= limit:
                    from backend.app.errors import ApiError
                    raise ApiError("Too many requests", 429, "rate_limited")
                timestamps.append(now)
            g.rate_limit_key = key
            return view(*args, **kwargs)

        return wrapped

    return apply

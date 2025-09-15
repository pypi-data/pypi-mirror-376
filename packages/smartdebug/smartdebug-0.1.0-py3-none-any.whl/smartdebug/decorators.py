"""decorators — function I/O logging and simple benchmarking"""
from functools import wraps
import time
from typing import Callable

def log_io(show_time: bool = True) -> Callable:
    """Decorator to log function inputs and outputs.

    Usage:
        @log_io()
        def f(a, b=1):
            return a + b
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                arg_repr = tuple(repr(a) for a in args)
                kw_repr = {k: repr(v) for k, v in kwargs.items()}
            except Exception:
                arg_repr = "<unrepr-able>"
                kw_repr = "<unrepr-able>"

            print(f"⚡ Calling {func.__name__} with args={arg_repr}, kwargs={kw_repr}")
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            if show_time:
                print(f"✅ {func.__name__} returned {repr(result)} (in {elapsed:.6f}s)")
            else:
                print(f"✅ {func.__name__} returned {repr(result)}")
            return result

        return wrapper

    return decorator


# Time travel decorator functionality
from typing import Any, Dict, List
import datetime

class TimeTravel:
    """Store history of calls (args, kwargs, result, timestamp).

    Usage:
        tt = TimeTravel()
        @tt.track
        def f(...):
            ...
        tt.history('f')  # get history for function name
    """

    def __init__(self):
        # key: func qualname -> list of records
        self._hist: Dict[str, List[Dict[str, Any]]] = {}

    def record(self, func_name: str, record: Dict[str, Any]):
        self._hist.setdefault(func_name, []).append(record)

    def history(self, func_name: str):
        return list(self._hist.get(func_name, []))

    def clear(self, func_name: str = None):
        if func_name:
            self._hist.pop(func_name, None)
        else:
            self._hist.clear()

    def track(self, func: Callable):
        """Decorator to record calls to the function (args, kwargs, result, timestamp)."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            ts = datetime.datetime.utcnow().isoformat() + "Z"
            try:
                result = func(*args, **kwargs)
                ok = True
            except Exception as e:
                result = repr(e)
                ok = False
                raise
            finally:
                # record after call completes (or raises)
                rec = {
                    "ts": ts,
                    "args": [repr(a) for a in args],
                    "kwargs": {k: repr(v) for k, v in kwargs.items()},
                    "result": repr(result) if ok else repr(result),
                    "ok": ok,
                }
                self.record(func.__qualname__, rec)
            return result

        return wrapper

# global helper
_global_tt = TimeTravel()

def time_travel_decorator(func: Callable):
    return _global_tt.track(func)

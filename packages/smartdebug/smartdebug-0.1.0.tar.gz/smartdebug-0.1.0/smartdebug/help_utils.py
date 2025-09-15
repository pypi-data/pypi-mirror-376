"""help_utils — why_none heuristic and TimeTravel improved wrapper"""
import inspect
import linecache
from typing import List

def why_none(var_name: str, frame=None, max_candidates: int = 5) -> List[str]:
    """Heuristic helper: try to locate likely assignments to var_name in source nearby."""
    if frame is None:
        frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    lineno = frame.f_lineno
    results = []
    try:
        start = max(1, lineno - 200)
        end = lineno + 200
        for i in range(start, end + 1):
            line = linecache.getline(filename, i)
            if not line:
                continue
            if var_name in line and "#" not in line.split(var_name)[-1]:
                snippet = line.strip()
                results.append(f"{i}: {snippet}")
            if len(results) >= max_candidates:
                break
    except Exception:
        pass
    return results

class TimeTravel:
    """Improved TimeTravel: record calls and optionally snapshots via a helper."""
    def __init__(self):
        self._hist = {}

    def record(self, func_name: str, rec: dict):
        self._hist.setdefault(func_name, []).append(rec)

    def history(self, func_name: str):
        return list(self._hist.get(func_name, []))

    def clear(self, func_name: str = None):
        if func_name:
            self._hist.pop(func_name, None)
        else:
            self._hist.clear()

    def track(self, func):
        import datetime
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            ts = datetime.datetime.utcnow().isoformat() + "Z"
            local_snap = None
            try:
                result = func(*args, **kwargs)
                ok = True
            except Exception as e:
                result = repr(e)
                ok = False
                raise
            finally:
                rec = {
                    "ts": ts,
                    "args": [repr(a) for a in args],
                    "kwargs": {k: repr(v) for k, v in kwargs.items()},
                    "result": repr(result) if ok else repr(result),
                    "ok": ok,
                    "locals": local_snap,
                }
                self.record(func.__qualname__, rec)
            return result

        return wrapper

    def snapshot_locals(self, func_name: str, locals_dict: dict):
        try:
            small = {k: repr(v) for k, v in locals_dict.items()}
        except Exception:
            small = {k: '<unrepr-able>' for k in locals_dict.keys()}
        lst = self._hist.get(func_name, [])
        if lst:
            lst[-1]['locals'] = small
        else:
            self._hist.setdefault(func_name, []).append({
                'ts': 'snapshot', 'locals': small
            })

# global instance for convenience
_GLOBAL_TT = TimeTravel()

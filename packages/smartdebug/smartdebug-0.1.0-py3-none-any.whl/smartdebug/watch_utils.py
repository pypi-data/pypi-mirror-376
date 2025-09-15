"""watch_utils — simple variable watcher and snapshot helper"""

from typing import Any
import time

class Watch:
    """Simple watched container for a value.

    Example:
        w = Watch('counter', 0)
        w.value = 3
    """

    def __init__(self, name: str, value: Any):
        self.name = name
        self._value = value
        self.history = [(time.time(), value)]

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new: Any) -> None:
        old = self._value
        print(f"👀 {self.name} changed: {old!r} -> {new!r}")
        self._value = new
        self.history.append((time.time(), new))

    def snapshot(self):
        """Return a copy of current value (best-effort shallow copy)."""
        try:
            import copy
            return copy.copy(self._value)
        except Exception:
            return self._value

    def history_str(self):
        import datetime
        return [
            (datetime.datetime.fromtimestamp(ts).isoformat(), val)
            for ts, val in self.history
        ]

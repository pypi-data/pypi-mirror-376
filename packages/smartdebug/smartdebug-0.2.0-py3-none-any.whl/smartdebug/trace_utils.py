"""trace_utils — enhanced traceback inspector with diffs, filters, source context, and colorized output"""
import linecache
from typing import Optional, List, Dict, Any
import os
import sys

_prev_locals: Dict[str, Dict[str, Any]] = {}

# Color helpers
def _supports_color() -> bool:
    """Detect whether the current environment supports ANSI colors."""
    if "NO_COLOR" in os.environ:
        return False
    if sys.stdout is None:
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False

_COLOR_CODES = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "grey": "\033[90m",
}

def _color(text: str, name: str, use_color: bool) -> str:
    if not use_color or name not in _COLOR_CODES:
        return text
    return f"{_COLOR_CODES[name]}{text}{_COLOR_CODES['reset']}"

def _safe_repr(value):
    try:
        text = repr(value)
        if len(text) > 120:
            text = text[:117] + "..."
        return text
    except Exception:
        return f"<unrepr-able {type(value).__name__}>"

def smart_trace(
    exc: Exception,
    max_frames: int = 10,
    context: int = 2,
    include_vars: Optional[List[str]] = None,
    exclude_vars: Optional[List[str]] = None,
    show_diffs: bool = True,
    use_color: Optional[bool] = None,
) -> None:
    """Pretty-print traceback for an exception, including local variables."""
    if use_color is None:
        use_color = _supports_color()

    tb = exc.__traceback__
    frames = []
    while tb is not None and len(frames) < max_frames:
        frames.append(tb.tb_frame)
        tb = tb.tb_next

    header = _color("=== SMART TRACE ===", "cyan", use_color)
    footer = _color("=== END SMART TRACE ===", "cyan", use_color)
    print("\n" + header)

    for frame in reversed(frames):
        code = frame.f_code
        lineno = frame.f_lineno
        func = code.co_name
        filename = code.co_filename
        location = f"File \"{filename}\", line {lineno}, in {func}"
        print(_color(f"\n📍 {location}", "magenta", use_color))

        # show context lines
        try:
            start = max(1, lineno - context)
            end = lineno + context
            for i in range(start, end + 1):
                line = linecache.getline(filename, i)
                if not line:
                    continue
                prefix = _color("▶", "yellow", use_color) if i == lineno else " "
                line_str = line.rstrip("\n")
                if i == lineno:
                    # highlight the error line
                    print(f" {prefix} {_color(f'{i:4}: {line_str}', 'red', use_color)}")
                else:
                    print(f" {prefix} {i:4}: {line_str}")
        except Exception:
            pass

        # print local variables
        local_items = list(frame.f_locals.items())
        if not local_items:
            print(_color("    (no local variables)", "grey", use_color))
            continue

        print(_color("    Local variables:", "blue", use_color))
        prev = _prev_locals.get(filename + ":" + func, {}) if show_diffs else {}
        current: Dict[str, Any] = {}
        for name, val in local_items:
            if include_vars and name not in include_vars:
                continue
            if exclude_vars and name in exclude_vars:
                continue
            val_repr = _safe_repr(val)
            current[name] = val_repr

            name_colored = _color(name, "bold", use_color)
            if show_diffs and name in prev and prev[name] != val_repr:
                changed_from = _color(prev[name], "yellow", use_color)
                print(f"      - {name_colored} = {val_repr}  {_color('(changed from', 'grey', use_color)} {changed_from})")
            else:
                print(f"      - {name_colored} = {val_repr}")

        _prev_locals[filename + ":" + func] = current

    print(footer + "\n")

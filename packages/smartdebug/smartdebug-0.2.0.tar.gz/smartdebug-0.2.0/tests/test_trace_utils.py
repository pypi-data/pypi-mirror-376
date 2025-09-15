from smartdebug.trace_utils import smart_trace
def test_smart_trace_runs_with_context():
    try:
        def inner():
            a = 1
            b = 2
            raise ValueError("boom")
        def outer():
            inner()
        outer()
    except Exception as e:
        smart_trace(e, context=1, exclude_vars=["__builtins__"], use_color=False)

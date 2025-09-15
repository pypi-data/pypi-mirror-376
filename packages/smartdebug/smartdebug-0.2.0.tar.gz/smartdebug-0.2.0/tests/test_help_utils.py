from smartdebug.help_utils import why_none, TimeTravel
def test_why_none_returns_candidates():
    def f():
        x = None
        return why_none('x', frame=None)
    res = f()
    assert isinstance(res, list)

def test_timetravel_snapshot_and_history():
    tt = TimeTravel()
    @tt.track
    def g(n):
        tt.snapshot_locals(g.__qualname__, locals())
        return n + 1
    assert g(4) == 5
    h = tt.history(g.__qualname__)
    assert len(h) >= 1
    assert 'locals' in h[-1]

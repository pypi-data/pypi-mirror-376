from smartdebug.decorators import log_io, TimeTravel, time_travel_decorator
def test_log_io_basic():
    @log_io()
    def add(a, b):
        return a + b
    assert add(2, 3) == 5

def test_time_travel_records():
    tt = TimeTravel()
    @tt.track
    def mul(a, b):
        return a * b
    assert mul(2, 3) == 6
    hist = tt.history(mul.__qualname__)
    assert len(hist) >= 1
    last = hist[-1]
    assert 'args' in last and 'result' in last

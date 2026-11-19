from collections.abc import Callable

import pytest
from toolbox.functions.threads import ProgressExecutor


ExcInit = Callable[[int, int], ProgressExecutor[int]]


@pytest.fixture
def exc():
    def _func(idx: int):
        return idx

    def init(max_workers: int, range_: int):
        with ProgressExecutor[int](max_workers=max_workers) as exc:
            for i in range(range_):
                exc.submit(_func, i)
            return exc
            
    yield init


def test_progress_executor_init(exc: ExcInit):
    e = exc(5, 10)
    assert len(getattr(e, "_futures")) == 10, "Incorrect number of futures"


def test_progress_executor_as_completed(exc: ExcInit):
    for range_ in [1, 5, 100]:
        expected = sum(range(range_))
        for workers_ in [1, 20, 50]:
            assert sum(exc(workers_, range_).as_completed()) == expected
            assert sum(exc(workers_, range_).as_completed_progress("Test")) == expected
            assert exc(workers_, range_).live("Test", limit=5) is None


def test_progress_executor_filter(exc: ExcInit):
    filter_ = 10

    for range_ in [1, 5, 100]:
        e = exc(1, range_).filter(lambda n: n < filter_)
        expected = sum(range(min(filter_, range_)))

        assert sum(e.as_completed()) == expected
        assert sum(e.as_completed_progress("Test")) == expected
        assert e.live("Test", limit=5) is None

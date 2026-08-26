from toolbox.functions.threads import ProgressExecutor


def test_progress_executor():
    def _func(idx: int):
        return idx * 2

    with ProgressExecutor(max_workers=5) as exc:
        for i in range(10):
            exc.submit(_func, i)
        res = sum(exc.as_completed())
    assert res == sum(range(10)) * 2, "Incorrect return values"

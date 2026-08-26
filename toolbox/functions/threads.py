from types import TracebackType
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import TypeVar, ParamSpec, Callable
from rich.live import Live
from rich.panel import Panel
from rich.progress import track

from toolbox.logger import console
from toolbox.types import with_signature


T = TypeVar("T")
P = ParamSpec("P")


FutureFunc = Callable[[Future[T]], bool]

noop: FutureFunc = lambda val: True


class ProgressExecutor[T](ThreadPoolExecutor):
    _futures: list[Future[T]]
    _filter: FutureFunc[T]

    @with_signature(ThreadPoolExecutor.__init__)
    # pyrefly: ignore [invalid-overload]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._futures = []
        self._filter = noop

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        if exc_type in [InterruptedError, KeyboardInterrupt]:
            self.shutdown(wait=False, cancel_futures=True)

    def filter(self, func: Callable[[T], bool]):
        def _filter(val: Future[T]):
            return func(val.result())
        self._filter = lambda val: func(val.result())
        return self

    @with_signature(ThreadPoolExecutor.submit)
    def submit(self, *args, **kwargs):
        future: Future[T] = super().submit(*args, **kwargs)
        self._futures.append(future)
        return future

    def as_completed_progress(self, title: str):
        for future in track(as_completed(self._futures), total=len(self._futures), description=title):
            if self._filter(future):
                yield future.result()

    def as_completed(self):
        for future in as_completed(self._futures):
            if self._filter(future):
                yield future.result()

    def live(self, title: str, limit: int=10):
        lines: list[str] = []

        def generate(lines: list[str], clr: str="#444444"):
            content = "\n".join(lines).strip("\n")
            return Panel(
                f"[{clr}]{content}[/]",
                title=title,
                border_style=clr,
                title_align="left",
            )

        idx = 0
        with Live(generate(lines), console=console, transient=True) as live:
            for future in as_completed(self._futures):
                idx += 1

                if not self._filter(future):
                    continue
                
                result = future.result()
                lines.append("[#444444]{idx}[/]: {result}".format(idx=idx, result=result))
                if len(lines) > limit:
                    lines.pop(0)

                live.update(generate(lines))
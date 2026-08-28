import threading
import time

from core.background import BackgroundExecutor


class FakeRoot:
    def __init__(self): self.scheduled = None
    def after(self, _delay, callback): self.scheduled = callback; return "poll"
    def after_cancel(self, _identifier): self.scheduled = None


def test_bounded_executor_marshals_results_through_ui_queue():
    root = FakeRoot(); executor = BackgroundExecutor(max_workers=2); executor.bind(root)
    worker_id = []; results = []
    def work(): worker_id.append(threading.get_ident()); return 42
    future = executor.submit_ui(work, results.append)
    assert future.result(timeout=1) == 42
    deadline = time.monotonic() + 1
    while not results and time.monotonic() < deadline:
        root.scheduled()
    assert results == [42]
    assert worker_id[0] != threading.get_ident()
    executor.shutdown()

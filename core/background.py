"""Bounded background work shared by GUI pages."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from queue import Empty, SimpleQueue
from typing import Any, Callable
import logging

LOGGER = logging.getLogger(__name__)


class BackgroundExecutor:
    """Small bounded pool that prevents unbounded per-action threads."""

    def __init__(self, max_workers: int = 4) -> None:
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="app-manager")
        self._ui_queue: SimpleQueue[Callable[[], None]] = SimpleQueue()
        self._root: Any = None
        self._poll_id: Any = None

    def bind(self, root: Any) -> None:
        """Start a lightweight main-thread queue pump for Tk-safe callbacks."""
        self._root = root
        self._poll_id = root.after(16, self._drain_ui_queue)

    def submit(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> Future[Any]:
        return self._pool.submit(function, *args, **kwargs)

    def submit_ui(
        self,
        function: Callable[..., Any],
        callback: Callable[[Any], None],
        *args: Any,
        on_error: Callable[[BaseException], None] | None = None,
        **kwargs: Any,
    ) -> Future[Any]:
        future = self.submit(function, *args, **kwargs)
        def completed(result: Future[Any]) -> None:
            try:
                value = result.result()
                self._ui_queue.put(lambda value=value: callback(value))
            except BaseException as exc:
                if on_error:
                    self._ui_queue.put(lambda exc=exc: on_error(exc))
        future.add_done_callback(completed)
        return future

    def post_ui(self, callback: Callable[[], None]) -> None:
        self._ui_queue.put(callback)

    def _drain_ui_queue(self) -> None:
        for _ in range(100):
            try:
                callback = self._ui_queue.get_nowait()
            except Empty:
                break
            try:
                callback()
            except Exception:
                LOGGER.exception("Background UI callback failed")
        if self._root is not None:
            self._poll_id = self._root.after(16, self._drain_ui_queue)

    def shutdown(self) -> None:
        if self._root is not None and self._poll_id is not None:
            try:
                self._root.after_cancel(self._poll_id)
            except Exception:
                pass
        self._root = None
        self._pool.shutdown(wait=False, cancel_futures=True)

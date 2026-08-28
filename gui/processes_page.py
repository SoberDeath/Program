"""Responsive, progressively populated process browser."""
from __future__ import annotations

import logging
import time
from typing import Any

import customtkinter as ctk

from core.background import BackgroundExecutor
from .components import PageHeader, Surface
from .theme import COLORS, FONT

LOGGER = logging.getLogger(__name__)
BATCH_SIZE = 35


class ProcessesPage(ctk.CTkFrame):
    """Loads lightweight process snapshots first and paths in background batches."""

    def __init__(self, master, manager, executor: BackgroundExecutor) -> None:
        super().__init__(master, fg_color="transparent")
        self.manager = manager
        self.executor = executor
        self.process_refresh_in_progress = False
        self.refresh_pending = False
        self._generation = 0
        self._last_refresh = 0.0
        self._path_labels: dict[int, ctk.CTkLabel] = {}
        self._icon_labels: dict[int, ctk.CTkLabel] = {}
        self._snapshot: list[dict[str, Any]] = []
        PageHeader(
            self,
            "Running Processes",
            "Application names appear first; executable details load progressively.",
            "↻  Refresh",
            self.refresh,
        ).pack(fill="x", pady=(0, 18))
        self.system = ctk.CTkSwitch(self, text="Show system processes", command=self.refresh)
        self.system.pack(anchor="w", pady=(0, 10))
        self.list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list.pack(fill="both", expand=True)
        self._show_loading()

    def on_show(self) -> None:
        if not self._snapshot or time.monotonic() - self._last_refresh > 8:
            self.refresh()

    def refresh(self) -> None:
        """Start at most one scan; coalesce repeated refresh requests."""
        if self.process_refresh_in_progress:
            self.refresh_pending = True
            return
        self.process_refresh_in_progress = True
        self.refresh_pending = False
        self._generation += 1
        generation = self._generation
        self._show_loading()
        include_system = bool(self.system.get())
        started = time.perf_counter()
        self.executor.submit_ui(
            self.manager.process_snapshot,
            lambda items: self._snapshot_ready(generation, started, items),
            include_system,
            on_error=lambda error: self._snapshot_failed(generation, error),
        )

    def _show_loading(self) -> None:
        self._clear_rows()
        for width in (0.72, 0.58, 0.66):
            row = Surface(self.list, height=58)
            row.pack(fill="x", pady=4)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text="Loading process information…", text_color=COLORS["muted"], anchor="w").pack(fill="x", padx=18, pady=18)

    def _snapshot_ready(self, generation: int, started: float, items: list[dict[str, Any]]) -> None:
        if generation != self._generation or not self.winfo_exists():
            return
        self._snapshot = items
        self._last_refresh = time.monotonic()
        self._clear_rows()
        if not self._snapshot:
            ctk.CTkLabel(self.list, text="No user applications found.", text_color=COLORS["muted"]).pack(pady=50)
            self._refresh_finished()
            return
        self._render_batch(generation, 0, started)

    def _snapshot_failed(self, generation: int, error: BaseException) -> None:
        if generation != self._generation:
            return
        LOGGER.error("Process refresh failed: %s", error)
        self._snapshot = []
        self._clear_rows()
        ctk.CTkLabel(self.list, text="Processes could not be loaded.", text_color=COLORS["danger"]).pack(pady=50)
        self._refresh_finished()

    def _render_batch(self, generation: int, offset: int, started: float) -> None:
        if generation != self._generation:
            return
        end = min(offset + BATCH_SIZE, len(self._snapshot))
        for item in self._snapshot[offset:end]:
            self._create_row(item)
        if end < len(self._snapshot):
            self.after(1, self._render_batch, generation, end, started)
            return
        LOGGER.debug("Process page rendered %d rows in %.3f seconds", len(self._snapshot), time.perf_counter() - started)
        self._refresh_finished()
        self._load_paths(generation)

    def _create_row(self, item: dict[str, Any]) -> None:
        row = Surface(self.list)
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(1, weight=1)
        icon_label = ctk.CTkLabel(row, text="▣", font=(FONT, 20, "bold"), text_color=COLORS["accent"])
        icon_label.grid(row=0, column=0, rowspan=2, padx=16)
        ctk.CTkLabel(row, text=f"{item['name']}   ·   PID {item['pid']}", font=(FONT, 13, "bold")).grid(row=0, column=1, sticky="w", pady=(10, 0))
        path_label = ctk.CTkLabel(row, text="Resolving executable path…", text_color=COLORS["muted"], font=(FONT, 11), anchor="w")
        path_label.grid(row=1, column=1, sticky="ew", pady=(1, 10), padx=(0, 12))
        self._path_labels[item["pid"]] = path_label
        self._icon_labels[item["pid"]] = icon_label

    def _load_paths(self, generation: int) -> None:
        snapshot = tuple(self._snapshot)
        def resolve() -> list[tuple[int, str]]:
            return [(item["pid"], self.manager.process_executable(item["pid"])) for item in snapshot]
        self.executor.submit_ui(resolve, lambda paths: self._paths_ready(generation, paths))

    def _paths_ready(self, generation: int, paths: list[tuple[int, str]]) -> None:
        if generation != self._generation or not self.winfo_exists():
            return
        for offset in range(0, len(paths), BATCH_SIZE):
            self.after(offset // BATCH_SIZE, self._update_path_batch, generation, paths[offset:offset + BATCH_SIZE])

    def _update_path_batch(self, generation: int, paths: list[tuple[int, str]]) -> None:
        if generation != self._generation:
            return
        for pid, path in paths:
            label = self._path_labels.get(pid)
            if label and label.winfo_exists():
                label.configure(text=path or "Path unavailable")


    def _refresh_finished(self) -> None:
        self.process_refresh_in_progress = False
        if self.refresh_pending:
            self.after_idle(self.refresh)

    def _clear_rows(self) -> None:
        self._path_labels.clear()
        self._icon_labels.clear()
        for child in self.list.winfo_children():
            child.destroy()

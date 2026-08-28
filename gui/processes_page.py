"""Responsive process browser with search and bounded rendering."""
from __future__ import annotations

import logging
import time
from typing import Any

import customtkinter as ctk

from core.background import BackgroundExecutor
from .components import PageHeader, Surface
from .theme import COLORS, FONT

LOGGER = logging.getLogger(__name__)
BATCH_SIZE = 25
INITIAL_VISIBLE_ROWS = 80
LOAD_MORE_ROWS = 80
SEARCH_DEBOUNCE_MS = 160


class ProcessesPage(ctk.CTkFrame):
    """Browse running processes without flooding Tk with hundreds of widgets."""

    def __init__(self, master, manager, executor: BackgroundExecutor) -> None:
        super().__init__(master, fg_color="transparent")
        self.manager = manager
        self.executor = executor
        self.process_refresh_in_progress = False
        self.refresh_pending = False
        self._generation = 0
        self._last_refresh = 0.0
        self._snapshot: list[dict[str, Any]] = []
        self._filtered_snapshot: list[dict[str, Any]] = []
        self._path_labels: dict[int, ctk.CTkLabel] = {}
        self._icon_labels: dict[int, ctk.CTkLabel] = {}
        self._visible_limit = INITIAL_VISIBLE_ROWS
        self._search_job: str | None = None

        PageHeader(
            self,
            "Running Processes",
            "Search running applications. System processes are loaded only when enabled.",
            "↻  Refresh",
            self.refresh,
        ).pack(fill="x", pady=(0, 14))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 12))
        toolbar.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            placeholder_text="Search by process name, PID or executable path…",
            height=38,
        )
        self.search.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        self.search_var.trace_add("write", self._on_search_changed)

        self.system = ctk.CTkSwitch(
            toolbar,
            text="Show system processes",
            command=self._system_processes_changed,
        )
        self.system.grid(row=0, column=1, sticky="e")

        self.result_info = ctk.CTkLabel(
            self,
            text="",
            text_color=COLORS["muted"],
            font=(FONT, 11),
            anchor="w",
        )
        self.result_info.pack(fill="x", pady=(0, 6))

        self.list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list.pack(fill="both", expand=True)

        self.more_button = ctk.CTkButton(
            self,
            text="Load more processes",
            command=self._load_more,
            height=34,
        )

        # Deliberately do not enumerate system processes until the user enables
        # the switch. Normal user applications can still be shown immediately.
        self._show_loading()

    def on_show(self) -> None:
        if not self._snapshot or time.monotonic() - self._last_refresh > 8:
            self.refresh()

    def _system_processes_changed(self) -> None:
        """Refresh only after the user explicitly changes the system-process switch."""
        self._visible_limit = INITIAL_VISIBLE_ROWS
        self.refresh()

    def refresh(self) -> None:
        """Start at most one process scan; coalesce repeated refresh requests."""
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
        self.more_button.pack_forget()
        self._clear_rows()
        self.result_info.configure(text="Loading processes…")
        for _ in range(3):
            row = Surface(self.list, height=58)
            row.pack(fill="x", pady=4)
            row.pack_propagate(False)
            ctk.CTkLabel(
                row,
                text="Loading process information…",
                text_color=COLORS["muted"],
                anchor="w",
            ).pack(fill="x", padx=18, pady=18)

    def _snapshot_ready(
        self,
        generation: int,
        started: float,
        items: list[dict[str, Any]],
    ) -> None:
        if generation != self._generation or not self.winfo_exists():
            return

        self._snapshot = items
        self._last_refresh = time.monotonic()
        self._visible_limit = INITIAL_VISIBLE_ROWS
        self._apply_filter(generation, started)

    def _snapshot_failed(self, generation: int, error: BaseException) -> None:
        if generation != self._generation:
            return

        LOGGER.error("Process refresh failed: %s", error)
        self._snapshot = []
        self._filtered_snapshot = []
        self.more_button.pack_forget()
        self._clear_rows()
        self.result_info.configure(text="")
        ctk.CTkLabel(
            self.list,
            text="Processes could not be loaded.",
            text_color=COLORS["danger"],
        ).pack(pady=50)
        self._refresh_finished()

    def _on_search_changed(self, *_: object) -> None:
        if self._search_job is not None:
            try:
                self.after_cancel(self._search_job)
            except ValueError:
                pass
        self._search_job = self.after(SEARCH_DEBOUNCE_MS, self._run_search)

    def _run_search(self) -> None:
        self._search_job = None
        self._visible_limit = INITIAL_VISIBLE_ROWS
        self._generation += 1
        generation = self._generation
        self._apply_filter(generation, time.perf_counter(), resolve_missing_paths=False)

    def _matches_search(self, item: dict[str, Any], query: str) -> bool:
        if not query:
            return True
        name = str(item.get("name", ""))
        pid = str(item.get("pid", ""))
        path = str(item.get("exe", ""))
        haystack = f"{name} {pid} {path}".casefold()
        return query in haystack

    def _apply_filter(
        self,
        generation: int,
        started: float,
        *,
        resolve_missing_paths: bool = True,
    ) -> None:
        query = self.search_var.get().strip().casefold()
        self._filtered_snapshot = [
            item for item in self._snapshot if self._matches_search(item, query)
        ]
        self._render_filtered(generation, started, resolve_missing_paths=resolve_missing_paths)

    def _render_filtered(
        self,
        generation: int,
        started: float,
        *,
        resolve_missing_paths: bool,
    ) -> None:
        if generation != self._generation:
            return

        self.more_button.pack_forget()
        self._clear_rows()

        if not self._filtered_snapshot:
            self.result_info.configure(text="No matching processes")
            ctk.CTkLabel(
                self.list,
                text="No processes match your search.",
                text_color=COLORS["muted"],
            ).pack(pady=50)
            self._refresh_finished()
            return

        visible = self._filtered_snapshot[: self._visible_limit]
        total = len(self._filtered_snapshot)
        self.result_info.configure(
            text=f"Showing {len(visible)} of {total} process{'es' if total != 1 else ''}"
        )
        self._render_batch(generation, visible, 0, started, resolve_missing_paths)

    def _render_batch(
        self,
        generation: int,
        visible: list[dict[str, Any]],
        offset: int,
        started: float,
        resolve_missing_paths: bool,
    ) -> None:
        if generation != self._generation:
            return

        end = min(offset + BATCH_SIZE, len(visible))
        for item in visible[offset:end]:
            self._create_row(item)

        if end < len(visible):
            self.after(
                1,
                self._render_batch,
                generation,
                visible,
                end,
                started,
                resolve_missing_paths,
            )
            return

        LOGGER.debug(
            "Process page rendered %d rows in %.3f seconds",
            len(visible),
            time.perf_counter() - started,
        )
        self._refresh_finished()

        if len(self._filtered_snapshot) > len(visible):
            self.more_button.pack(fill="x", pady=(8, 0))

        if resolve_missing_paths:
            self._load_paths(generation, visible)
        else:
            missing = [item for item in visible if "exe" not in item]
            if missing:
                self._load_paths(generation, missing)

    def _create_row(self, item: dict[str, Any]) -> None:
        row = Surface(self.list)
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(1, weight=1)

        icon_label = ctk.CTkLabel(
            row,
            text="▣",
            font=(FONT, 20, "bold"),
            text_color=COLORS["accent"],
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=16)

        ctk.CTkLabel(
            row,
            text=f"{item['name']}   ·   PID {item['pid']}",
            font=(FONT, 13, "bold"),
        ).grid(row=0, column=1, sticky="w", pady=(10, 0))

        path_label = ctk.CTkLabel(
            row,
            text=item.get("exe") or "Resolving executable path…",
            text_color=COLORS["muted"],
            font=(FONT, 11),
            anchor="w",
        )
        path_label.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=(1, 10),
            padx=(0, 12),
        )
        self._path_labels[item["pid"]] = path_label
        self._icon_labels[item["pid"]] = icon_label

    def _load_paths(self, generation: int, items: list[dict[str, Any]]) -> None:
        snapshot = tuple(items)

        def resolve() -> list[tuple[int, str]]:
            return [
                (item["pid"], self.manager.process_executable(item["pid"]))
                for item in snapshot
            ]

        self.executor.submit_ui(
            resolve,
            lambda paths: self._paths_ready(generation, paths),
        )

    def _paths_ready(self, generation: int, paths: list[tuple[int, str]]) -> None:
        if generation != self._generation or not self.winfo_exists():
            return

        by_pid = {item["pid"]: item for item in self._snapshot}
        for pid, path in paths:
            item = by_pid.get(pid)
            if item is not None:
                item["exe"] = path

        for offset in range(0, len(paths), BATCH_SIZE):
            self.after(
                offset // BATCH_SIZE,
                self._update_path_batch,
                generation,
                paths[offset : offset + BATCH_SIZE],
            )

    def _update_path_batch(
        self,
        generation: int,
        paths: list[tuple[int, str]],
    ) -> None:
        if generation != self._generation:
            return

        for pid, path in paths:
            label = self._path_labels.get(pid)
            if label and label.winfo_exists():
                label.configure(text=path or "Path unavailable")

    def _load_more(self) -> None:
        self._visible_limit += LOAD_MORE_ROWS
        self._generation += 1
        generation = self._generation
        self._render_filtered(
            generation,
            time.perf_counter(),
            resolve_missing_paths=False,
        )

    def _refresh_finished(self) -> None:
        self.process_refresh_in_progress = False
        if self.refresh_pending:
            self.after_idle(self.refresh)

    def _clear_rows(self) -> None:
        self._path_labels.clear()
        self._icon_labels.clear()
        for child in self.list.winfo_children():
            child.destroy()

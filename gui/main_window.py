"""Application shell with cached pages and deferred integrations."""
from __future__ import annotations

import logging
import time
from typing import Any

import customtkinter as ctk

from core.background import BackgroundExecutor
from core.shortcut_manager import ShortcutManager
from core.startup_manager import StartupManager
from .components import ActivityPanel
from .dashboard import DashboardPage
from .theme import COLORS, FONT

LOGGER = logging.getLogger(__name__)
APP_VERSION = "1.0.0"


class MainWindow(ctk.CTk):
    """Creates the dashboard immediately and lazily caches secondary pages."""

    def __init__(self, config, profiles, processes) -> None:
        started = time.perf_counter()
        super().__init__()
        self.config, self.profiles, self.processes = config, profiles, processes
        self.tray: Any = None
        self.exiting = False
        self.executor = BackgroundExecutor(max_workers=4)
        self.executor.bind(self)
        self.pages: dict[str, ctk.CTkFrame] = {}
        self.current: ctk.CTkFrame | None = None
        self.editor: Any = None
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        ctk.set_widget_scaling(float(config.data["settings"]["ui_scaling"]))
        self.title(f"App Manager {APP_VERSION}")
        self.geometry("1180x780")
        self.minsize(940, 650)
        self.configure(fg_color=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.grid(row=0, column=1, sticky="nsew", padx=28, pady=25)
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)
        self.content = ctk.CTkFrame(shell, fg_color="transparent")
        self.content.grid(row=0, column=0, sticky="nsew")
        self.activity = ActivityPanel(shell)
        self.activity.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        self.activity.grid_remove()
        self.show("Dashboard")
        if config.warning:
            self.show_status("warning", config.warning)
        # Let Tk paint the dashboard before Pillow/pystray startup work begins.
        self.after_idle(self._start_tray)
        LOGGER.info("Main window constructed in %.3f seconds", time.perf_counter() - started)

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="◆  APP MANAGER",
            font=(FONT, 17, "bold"),
        ).pack(anchor="w", padx=24, pady=(30, 35))

        self.nav: dict[str, ctk.CTkButton] = {}
        for glyph, label in (("▦", "Dashboard"), ("≡", "Profiles"), ("◉", "Processes"), ("⚙", "Settings")):
            button = ctk.CTkButton(
                self.sidebar,
                text=f"{glyph}   {label}",
                anchor="w",
                height=45,
                corner_radius=9,
                fg_color="transparent",
                hover_color=COLORS["surface_hover"],
                font=(FONT, 13),
                command=lambda page=label: self.show(page),
            )
            button.pack(fill="x", padx=12, pady=3)
            self.nav[label] = button

        info = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info.pack(side="bottom", fill="x", padx=20, pady=(10, 22))

        ctk.CTkFrame(info, height=1, fg_color=COLORS["surface_hover"]).pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            info,
            text=f"App Manager  v{APP_VERSION}",
            text_color=COLORS["text"],
            font=(FONT, 10, "bold"),
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            info,
            text="Offline workspace launcher",
            text_color=COLORS["muted"],
            font=(FONT, 9),
            anchor="w",
        ).pack(fill="x", pady=(3, 0))
        ctk.CTkLabel(
            info,
            text="LOCAL  •  PRIVATE",
            text_color=COLORS["muted"],
            font=(FONT, 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(8, 0))

    def _create_page(self, name: str) -> ctk.CTkFrame:
        if name == "Dashboard":
            return DashboardPage(self.content, lambda: self.profiles.profiles, self.run_profile, lambda: self.edit_profile(None), self.edit_profile)
        if name == "Profiles":
            from .profiles_page import ProfilesPage
            return ProfilesPage(self.content, lambda: self.profiles.profiles, lambda: self.edit_profile(None), self.edit_profile, self._duplicate_profile, self._delete_profile, self._shortcut)
        if name == "Processes":
            from .processes_page import ProcessesPage
            return ProcessesPage(self.content, self.processes, self.executor)
        from .settings_page import SettingsPage
        return SettingsPage(self.content, self.config, StartupManager(), self.show_status)

    def show(self, page: str) -> None:
        started = time.perf_counter()
        if self.editor is not None:
            self.editor.destroy()
            self.editor = None
        if self.current is not None:
            self.current.pack_forget()
        frame = self.pages.get(page)
        if frame is None:
            frame = self._create_page(page)
            self.pages[page] = frame
        self.current = frame
        frame.pack(fill="both", expand=True)
        frame.tkraise()
        on_show = getattr(frame, "on_show", None)
        if on_show:
            on_show()
        for name, button in self.nav.items():
            button.configure(fg_color=COLORS["surface_hover"] if name == page else "transparent", text_color=COLORS["text"] if name == page else COLORS["muted"])
        LOGGER.debug("Navigation to %s took %.3f seconds", page, time.perf_counter() - started)

    def edit_profile(self, profile: dict[str, Any] | None) -> None:
        started = time.perf_counter()
        if self.current is not None:
            self.current.pack_forget()
        if self.editor is not None:
            self.editor.destroy()
        from .profile_editor import ProfileEditor
        self.editor = ProfileEditor(
            self.content, profile, self._save_profile, lambda: self.show("Dashboard"),
            self._delete_profile, self._duplicate_profile, self._shortcut, self.processes, self.executor,
        )
        self.editor.pack(fill="both", expand=True)
        LOGGER.debug("Profile editor opened in %.3f seconds", time.perf_counter() - started)

    def _profiles_changed(self) -> None:
        for page in self.pages.values():
            callback = getattr(page, "profiles_changed", None)
            if callback:
                callback()
        self._refresh_tray()

    def _save_profile(self, item: dict[str, Any]) -> None:
        self.profiles.save_profile(item)
        self._profiles_changed()
        self.show("Dashboard")
        self.show_status("success", f"{item['name']} saved")

    def _delete_profile(self, item: dict[str, Any]) -> None:
        self.profiles.delete(item["id"])
        self._profiles_changed()
        self.show("Dashboard")
        self.show_status("success", "Profile deleted")

    def _duplicate_profile(self, item: dict[str, Any]) -> None:
        duplicate = self.profiles.duplicate(item["id"])
        self._profiles_changed()
        self.edit_profile(duplicate)

    def _shortcut(self, item: dict[str, Any]) -> None:
        self.show_status("info", "Creating desktop shortcut…")
        self.executor.submit_ui(
            ShortcutManager().create,
            lambda result: self.show_status("success" if result[0] else "warning", result[1]),
            item["name"],
        )

    def _start_tray(self) -> None:
        if self.exiting:
            return

        def create_tray():
            from core.tray_manager import TrayManager
            tray = TrayManager(
                lambda: self.executor.post_ui(self.restore),
                lambda profile: self.executor.post_ui(lambda: self.run_profile(profile)),
                lambda: self.executor.post_ui(self.exit_app),
            )
            tray.start(list(self.profiles.profiles))
            return tray

        self.executor.submit_ui(
            create_tray,
            lambda tray: setattr(self, "tray", tray),
            on_error=lambda error: self.show_status("warning", f"System tray unavailable: {error}"),
        )

    def _refresh_tray(self) -> None:
        if self.tray:
            self.executor.submit(self.tray.start, list(self.profiles.profiles))

    def run_profile(self, profile: dict[str, Any]) -> None:
        if getattr(self, "_running_thread", None) and self._running_thread.is_alive():
            self.show_status("warning", "A profile is already running. Please wait for it to finish.")
            return
        self.activity.grid()
        self.activity.reset(str(profile.get("name", "Profile")))

        def event(status, message, completed, total):
            self.executor.post_ui(lambda: self.activity.add(status, message, completed, total))

        def done(warnings, errors):
            self.executor.post_ui(lambda: self.activity.finish(warnings, errors))

        self._running_thread = self.profiles.run_async(profile, event, done)

    def show_status(self, status: str, message: str) -> None:
        self.activity.grid()
        self.activity.reset("App Manager")
        self.activity.add(status, message, 1, 1)
        self.activity.finish(1 if status == "warning" else 0, 1 if status == "error" else 0)

    def restore(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_close(self) -> None:
        if self.config.data["settings"].get("minimize_to_tray") and self.tray:
            self.withdraw()
        else:
            self.exit_app()

    def exit_app(self) -> None:
        self.exiting = True
        if self.tray:
            self.tray.stop()
        self.executor.shutdown()
        self.destroy()

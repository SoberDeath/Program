from __future__ import annotations
import customtkinter as ctk
from core.shortcut_manager import ShortcutManager
from core.startup_manager import StartupManager
from core.tray_manager import TrayManager
from .components import ActivityPanel
from .dashboard import DashboardPage
from .processes_page import ProcessesPage
from .profile_editor import ProfileEditor
from .settings_page import SettingsPage
from .theme import COLORS, FONT

class MainWindow(ctk.CTk):
    def __init__(self, config, profiles, processes):
        super().__init__(); self.config, self.profiles, self.processes = config, profiles, processes; self.tray = None; self.exiting = False
        ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue"); ctk.set_widget_scaling(float(config.data["settings"]["ui_scaling"]))
        self.title("App Manager"); self.geometry("1180x780"); self.minsize(940, 650); self.configure(fg_color=COLORS["bg"]); self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["sidebar"], border_width=0); self.sidebar.grid(row=0, column=0, sticky="nsew"); self.sidebar.grid_propagate(False)
        ctk.CTkLabel(self.sidebar, text="◈  APP MANAGER", font=(FONT, 17, "bold"), text_color=COLORS["text"]).pack(anchor="w", padx=24, pady=(30, 35))
        self.nav = {}
        for icon, label in (("⌂", "Dashboard"), ("▦", "Profiles"), ("◉", "Processes"), ("⚙", "Settings")):
            button = ctk.CTkButton(self.sidebar, text=f"{icon}    {label}", anchor="w", height=45, corner_radius=9, fg_color="transparent", hover_color=COLORS["surface_hover"], font=(FONT, 13), command=lambda page=label: self.show(page)); button.pack(fill="x", padx=12, pady=3); self.nav[label] = button
        ctk.CTkLabel(self.sidebar, text="LOCAL • PRIVATE", text_color=COLORS["muted"], font=(FONT, 9, "bold")).pack(side="bottom", anchor="w", padx=24, pady=24)
        shell = ctk.CTkFrame(self, fg_color="transparent"); shell.grid(row=0, column=1, sticky="nsew", padx=28, pady=25); shell.grid_rowconfigure(0, weight=1); shell.grid_columnconfigure(0, weight=1)
        self.content = ctk.CTkFrame(shell, fg_color="transparent"); self.content.grid(row=0, column=0, sticky="nsew")
        self.activity = ActivityPanel(shell); self.activity.grid(row=1, column=0, sticky="ew", pady=(14, 0)); self.activity.grid_remove()
        self.current = None; self.show("Dashboard")
        if config.warning: self.show_status("warning", config.warning)
        try:
            self.tray = TrayManager(lambda: self.after(0, self.restore), lambda p: self.after(0, lambda: self.run_profile(p)), lambda: self.after(0, self.exit_app)); self.tray.start(self.profiles.profiles)
        except Exception as exc: self.show_status("warning", f"System tray unavailable: {exc}")
    def _clear(self):
        if self.current: self.current.destroy()
    def show(self, page):
        self._clear()
        for name, button in self.nav.items(): button.configure(fg_color=COLORS["surface_hover"] if name == page else "transparent", text_color=COLORS["text"] if name == page else COLORS["muted"])
        if page in ("Dashboard", "Profiles"):
            self.current = DashboardPage(self.content, lambda: self.profiles.profiles, self.run_profile, lambda: self.edit_profile(None), self.edit_profile)
        elif page == "Processes": self.current = ProcessesPage(self.content, self.processes)
        else: self.current = SettingsPage(self.content, self.config, StartupManager(), self.show_status)
        self.current.pack(fill="both", expand=True)
    def edit_profile(self, profile):
        self._clear(); self.current = ProfileEditor(self.content, profile, self._save_profile, lambda: self.show("Dashboard"), self._delete_profile, self._duplicate_profile, self._shortcut, self.processes); self.current.pack(fill="both", expand=True)
    def _save_profile(self, item): self.profiles.save_profile(item); self._refresh_tray(); self.show("Dashboard"); self.show_status("success", f"{item['name']} saved")
    def _delete_profile(self, item): self.profiles.delete(item["id"]); self._refresh_tray(); self.show("Dashboard"); self.show_status("success", "Profile deleted")
    def _duplicate_profile(self, item): duplicate = self.profiles.duplicate(item["id"]); self._refresh_tray(); self.edit_profile(duplicate)
    def _shortcut(self, item): status, message = ShortcutManager().create(item["name"]); self.show_status("success" if status else "warning", message)
    def _refresh_tray(self):
        if self.tray: self.tray.start(self.profiles.profiles)
    def run_profile(self, profile):
        self.activity.grid(); self.activity.reset(str(profile.get("name", "Profile")))
        def event(status, message, completed, total): self.after(0, lambda: self.activity.add(status, message, completed, total))
        def done(warnings, errors): self.after(0, lambda: self.activity.finish(warnings, errors))
        self.profiles.run_async(profile, event, done)
    def show_status(self, status, message):
        self.activity.grid(); self.activity.reset("App Manager"); self.activity.add(status, message, 1, 1); self.activity.finish(1 if status == "warning" else 0, 1 if status == "error" else 0)
    def restore(self): self.deiconify(); self.lift(); self.focus_force()
    def on_close(self):
        if self.config.data["settings"].get("minimize_to_tray") and self.tray: self.withdraw()
        else: self.exit_app()
    def exit_app(self):
        self.exiting = True
        if self.tray: self.tray.stop()
        self.destroy()

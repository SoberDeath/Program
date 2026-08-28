import customtkinter as ctk
from .components import PageHeader, Surface
from .theme import COLORS, FONT

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, config, startup, status):
        super().__init__(master, fg_color="transparent"); self.config, self.startup, self.status = config, startup, status; self.controls = {}
        PageHeader(self, "Settings", "Personalize how App Manager behaves.").pack(fill="x", pady=(0, 18)); settings = config.data["settings"]
        general = self._section("General", "Windows integration and launch behavior.")
        self._switch(general, "Start App Manager automatically with Windows", "start_with_windows", settings)
        self._switch(general, "Minimize to system tray when closing", "minimize_to_tray", settings)
        self._switch(general, "Do not launch applications that are already running", "skip_running_apps", settings)
        behavior = self._section("Behaviour", "Timing used while switching profiles.")
        self._slider(behavior, "Delay between closing and launching", "close_launch_delay", 0, 3, settings, "seconds")
        self._slider(behavior, "Graceful close timeout", "graceful_close_timeout", 1, 10, settings, "seconds")
        appearance = self._section("Appearance", "A focused dark interface designed for Windows.")
        self._slider(appearance, "UI scaling", "ui_scaling", .8, 1.4, settings, "×")
    def _section(self, title, subtitle):
        box = Surface(self); box.pack(fill="x", pady=7); ctk.CTkLabel(box, text=title, font=(FONT, 16, "bold")).pack(anchor="w", padx=20, pady=(16, 2)); ctk.CTkLabel(box, text=subtitle, font=(FONT, 11), text_color=COLORS["muted"]).pack(anchor="w", padx=20, pady=(0, 10)); return box
    def _switch(self, parent, label, key, settings):
        def toggle():
            requested = bool(switch.get())
            if not self._changed(key, requested):
                switch.select() if not requested else switch.deselect()
        switch = ctk.CTkSwitch(parent, text=label, command=toggle, font=(FONT, 12)); switch.pack(fill="x", padx=20, pady=9)
        if settings.get(key): switch.select()
    def _slider(self, parent, label, key, low, high, settings, suffix):
        row = ctk.CTkFrame(parent, fg_color="transparent"); row.pack(fill="x", padx=20, pady=9); row.grid_columnconfigure(0, weight=1)
        text = ctk.CTkLabel(row, text=f"{label}   {float(settings[key]):.1f}{suffix}", font=(FONT, 12)); text.grid(row=0, column=0, sticky="w")
        def change(value): text.configure(text=f"{label}   {value:.1f}{suffix}"); self._changed(key, round(value, 2))
        slider = ctk.CTkSlider(row, from_=low, to=high, command=change, progress_color=COLORS["accent"]); slider.set(float(settings[key])); slider.grid(row=0, column=1, padx=(20, 0)); parent.configure(height=100)
    def _changed(self, key, value):
        old = self.config.data["settings"].get(key); self.config.data["settings"][key] = value
        if old == value:
            return True
        if key == "start_with_windows":
            ok, message = self.startup.set_enabled(value)
            if not ok: self.config.data["settings"][key] = old
            self.status("success" if ok else "warning", message)
        elif key == "ui_scaling": ctk.set_widget_scaling(value)
        self.config.save()
        return self.config.data["settings"].get(key) == value

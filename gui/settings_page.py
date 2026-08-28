from __future__ import annotations

import customtkinter as ctk

from .components import PageHeader, Surface
from .theme import COLORS, FONT


class SettingsPage(ctk.CTkFrame):
    """Professional settings page with stable, non-blocking scale changes."""

    def __init__(self, master, config, startup, status):
        super().__init__(master, fg_color="transparent")
        self.config = config
        self.startup = startup
        self.status = status
        self.controls = {}
        self._scale_apply_job = None

        PageHeader(self, "Settings", "Personalize how App Manager behaves.").pack(
            fill="x", pady=(0, 18)
        )
        settings = config.data["settings"]

        general = self._section("General", "Windows integration and launch behaviour.")
        self._switch(general, "Start App Manager automatically with Windows", "start_with_windows", settings)
        self._switch(general, "Minimize to system tray when closing", "minimize_to_tray", settings)
        self._switch(general, "Do not launch applications that are already running", "skip_running_apps", settings)

        behaviour = self._section("Behaviour", "Timing used while switching profiles.")
        self._slider(
            behaviour,
            "Delay between closing and launching",
            "close_launch_delay",
            0,
            3,
            settings,
            "seconds",
        )
        self._slider(
            behaviour,
            "Graceful close timeout",
            "graceful_close_timeout",
            1,
            10,
            settings,
            "seconds",
        )

        appearance = self._section("Appearance", "A focused dark interface designed for Windows.")
        self._slider(
            appearance,
            "UI scaling",
            "ui_scaling",
            0.8,
            1.4,
            settings,
            "×",
            scaling=True,
        )

    def _section(self, title: str, subtitle: str):
        box = Surface(self)
        box.pack(fill="x", pady=7)

        header = ctk.CTkFrame(box, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(header, text=title, font=(FONT, 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=subtitle,
            font=(FONT, 11),
            text_color=COLORS["muted"],
        ).pack(anchor="w", pady=(3, 0))

        body = ctk.CTkFrame(box, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=(0, 14))
        return body

    def _switch(self, parent, label: str, key: str, settings: dict):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=42)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)

        switch = ctk.CTkSwitch(
            row,
            text=label,
            command=lambda: self._toggle_switch(key, switch),
            font=(FONT, 12),
            progress_color=COLORS["accent"],
        )
        switch.pack(fill="x", expand=True)
        if settings.get(key):
            switch.select()
        self.controls[key] = switch

    def _toggle_switch(self, key: str, switch) -> None:
        requested = bool(switch.get())
        if not self._changed(key, requested):
            switch.select() if not requested else switch.deselect()

    def _slider(
        self,
        parent,
        label: str,
        key: str,
        low: float,
        high: float,
        settings: dict,
        suffix: str,
        scaling: bool = False,
    ) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(6, 10))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)

        current = float(settings[key])
        value_label = ctk.CTkLabel(
            row,
            text=self._format_value(current, suffix),
            width=70,
            anchor="e",
            font=(FONT, 12, "bold"),
            text_color=COLORS["text"],
        )
        title_label = ctk.CTkLabel(row, text=label, font=(FONT, 12), anchor="w")
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 7))
        value_label.grid(row=0, column=1, sticky="e", pady=(0, 7))

        slider = ctk.CTkSlider(
            row,
            from_=low,
            to=high,
            command=lambda value: self._slider_preview(key, value, value_label, suffix, scaling),
            progress_color=COLORS["accent"],
            height=18,
        )
        slider.set(current)
        slider.grid(row=1, column=0, columnspan=2, sticky="ew")

        if scaling:
            # Apply the expensive global scale change only after the user stops dragging.
            slider.bind(
                "<ButtonRelease-1>",
                lambda _event: self._commit_scaling(float(slider.get())),
                add="+",
            )

        self.controls[key] = slider

    @staticmethod
    def _format_value(value: float, suffix: str) -> str:
        if suffix == "×":
            return f"{value:.1f}×"
        return f"{value:.1f} {suffix}"

    def _slider_preview(self, key: str, value: float, label, suffix: str, scaling: bool) -> None:
        rounded = round(float(value), 2)
        label.configure(text=self._format_value(rounded, suffix))

        if scaling:
            # Preview text only while dragging. Live global scaling causes Tk to briefly
            # reflow widgets at mixed old/new dimensions, which looks broken.
            return

        self._changed(key, rounded)

    def _commit_scaling(self, value: float) -> None:
        value = round(float(value), 2)
        old = float(self.config.data["settings"].get("ui_scaling", 1.0))
        if old == value:
            return

        self.config.data["settings"]["ui_scaling"] = value
        self.config.save()

        # Apply once after the pointer event has finished, then let Tk finish one
        # complete layout pass before accepting more interaction.
        if self._scale_apply_job is not None:
            try:
                self.after_cancel(self._scale_apply_job)
            except Exception:
                pass
        self._scale_apply_job = self.after(80, lambda: self._apply_scaling(value))

    def _apply_scaling(self, value: float) -> None:
        self._scale_apply_job = None
        ctk.set_widget_scaling(value)
        self.update_idletasks()
        self.status("success", f"UI scaling set to {value:.1f}×")

    def _changed(self, key: str, value) -> bool:
        old = self.config.data["settings"].get(key)
        self.config.data["settings"][key] = value
        if old == value:
            return True

        if key == "start_with_windows":
            ok, message = self.startup.set_enabled(value)
            if not ok:
                self.config.data["settings"][key] = old
            self.status("success" if ok else "warning", message)

        self.config.save()
        return self.config.data["settings"].get(key) == value

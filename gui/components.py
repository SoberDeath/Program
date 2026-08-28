from __future__ import annotations
from typing import Callable
import customtkinter as ctk
from .theme import COLORS, FONT

class PageHeader(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str, action_text: str | None = None, command: Callable[[], None] | None = None, action_image=None):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, font=(FONT, 28, "bold"), text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(self, text=subtitle, font=(FONT, 13), text_color=COLORS["muted"]).grid(row=1, column=0, sticky="w", pady=(4, 0))
        if action_text:
            ctk.CTkButton(self, text=action_text, image=action_image, compound="left", command=command, height=42, corner_radius=10, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], font=(FONT, 13, "bold")).grid(row=0, column=1, rowspan=2)

class Surface(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["surface"], border_color=COLORS["border"], border_width=1, corner_radius=14, **kwargs)

class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, message: str, confirm: Callable[[], None]):
        super().__init__(master); self.title(title); self.geometry("420x220"); self.resizable(False, False); self.configure(fg_color=COLORS["bg"]); self.transient(master); self.grab_set()
        ctk.CTkLabel(self, text=title, font=(FONT, 20, "bold")).pack(anchor="w", padx=28, pady=(28, 8))
        ctk.CTkLabel(self, text=message, text_color=COLORS["muted"], wraplength=350, justify="left").pack(anchor="w", padx=28)
        row = ctk.CTkFrame(self, fg_color="transparent"); row.pack(fill="x", side="bottom", padx=28, pady=24)
        ctk.CTkButton(row, text="Cancel", fg_color=COLORS["surface"], hover_color=COLORS["surface_hover"], command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 6))
        def proceed(): self.destroy(); confirm()
        ctk.CTkButton(row, text="Delete", fg_color=COLORS["danger"], hover_color="#d95862", command=proceed).pack(side="left", expand=True, fill="x", padx=(6, 0))

class ActivityPanel(Surface):
    symbols = {"success": "✓", "warning": "!", "error": "×", "info": "i"}
    colors = {"success": COLORS["success"], "warning": COLORS["warning"], "error": COLORS["danger"], "info": COLORS["accent"]}
    def __init__(self, master):
        super().__init__(master); self.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(self, text="Activity", font=(FONT, 15, "bold")); self.title_label.grid(row=0, column=0, sticky="w", padx=18, pady=(15, 5))
        self.progress = ctk.CTkProgressBar(self, progress_color=COLORS["accent"], height=5); self.progress.grid(row=1, column=0, sticky="ew", padx=18); self.progress.set(0)
        self.body = ctk.CTkScrollableFrame(self, height=90, fg_color="transparent"); self.body.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
    def reset(self, name: str):
        for child in self.body.winfo_children(): child.destroy()
        self.title_label.configure(text=f"Running {name}… 0 / 0"); self.progress.set(0)
    def add(self, status: str, message: str, completed: int, total: int):
        self.title_label.configure(text=f"Running profile… {completed} / {total}"); self.progress.set(completed / max(total, 1))
        ctk.CTkLabel(self.body, text=f"{self.symbols.get(status, '•')}  {message}", text_color=self.colors.get(status, COLORS["text"]), anchor="w", font=(FONT, 12)).pack(fill="x", padx=8, pady=2)
    def finish(self, warnings: int, errors: int):
        if errors: text = f"Profile completed with {errors} error(s) and {warnings} warning(s)"
        elif warnings: text = f"Profile completed with {warnings} warning(s)"
        else: text = "Profile completed successfully"
        self.title_label.configure(text=text); self.progress.set(1)

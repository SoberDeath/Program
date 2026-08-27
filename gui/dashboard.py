from __future__ import annotations
from typing import Any, Callable
import customtkinter as ctk
from .components import PageHeader, Surface
from .theme import COLORS, FONT

class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, profiles: Callable[[], list[dict[str, Any]]], run, create, edit):
        super().__init__(master, fg_color="transparent"); self.profiles, self.run_profile, self.create, self.edit = profiles, run, create, edit
        PageHeader(self, "Your Profiles", "Launch a complete workspace with one click.", "+  Create Profile", create).pack(fill="x", pady=(0, 20))
        self.search = ctk.CTkEntry(self, placeholder_text="Search profiles…", height=42, corner_radius=10, border_color=COLORS["border"], fg_color=COLORS["surface"]); self.search.pack(fill="x", pady=(0, 16)); self.search.bind("<KeyRelease>", lambda _: self.refresh())
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent"); self.grid_frame.pack(fill="both", expand=True)
        for col in range(3): self.grid_frame.grid_columnconfigure(col, weight=1, uniform="cards")
        self.refresh()
    def refresh(self):
        for child in self.grid_frame.winfo_children(): child.destroy()
        query = self.search.get().casefold() if hasattr(self, "search") else ""
        profiles = [p for p in self.profiles() if query in str(p.get("name", "")).casefold() or query in str(p.get("description", "")).casefold()]
        if not profiles:
            ctk.CTkLabel(self.grid_frame, text="No profiles found\nCreate a profile to build your first workspace.", text_color=COLORS["muted"], font=(FONT, 15), justify="center").grid(row=0, column=0, columnspan=3, pady=80)
        for index, profile in enumerate(profiles): self._card(profile).grid(row=index // 3, column=index % 3, sticky="nsew", padx=7, pady=7)
    def _card(self, profile):
        card = Surface(self.grid_frame, height=210); card.grid_propagate(False); card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=str(profile.get("icon", "◆")), font=(FONT, 25), text_color=COLORS["accent"]).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 6))
        ctk.CTkButton(card, text="•••", width=36, fg_color="transparent", hover_color=COLORS["surface_hover"], command=lambda: self.edit(profile)).grid(row=0, column=1, padx=12)
        ctk.CTkLabel(card, text=profile.get("name", "Untitled"), font=(FONT, 17, "bold"), anchor="w").grid(row=1, column=0, columnspan=2, sticky="ew", padx=20)
        counts = f"↑  {len(profile.get('open_apps', []))} to open     ↓  {len(profile.get('close_apps', []))} to close"
        ctk.CTkLabel(card, text=counts, font=(FONT, 12), text_color=COLORS["muted"]).grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=(8, 18))
        ctk.CTkButton(card, text="Run Profile", height=38, corner_radius=9, command=lambda: self.run_profile(profile), fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"]).grid(row=3, column=0, columnspan=2, sticky="ew", padx=20)
        return card

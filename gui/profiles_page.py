"""Profile administration page."""
from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from .components import ConfirmDialog, PageHeader, Surface
from .theme import COLORS, FONT


class ProfilesPage(ctk.CTkFrame):
    """Displays every saved profile with explicit management actions."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        profiles: Callable[[], list[dict[str, Any]]],
        create: Callable[[], None],
        edit: Callable[[dict[str, Any]], None],
        duplicate: Callable[[dict[str, Any]], None],
        delete: Callable[[dict[str, Any]], None],
        shortcut: Callable[[dict[str, Any]], None],
    ) -> None:
        super().__init__(master, fg_color="transparent")
        PageHeader(
            self,
            "Manage Profiles",
            "Create, organize, and share shortcuts to your workspaces.",
            "+  New Profile",
            create,
        ).pack(fill="x", pady=(0, 20))
        self.list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list.pack(fill="both", expand=True)
        self._profiles = profiles
        self._create = create
        self._edit = edit
        self._duplicate = duplicate
        self._delete = delete
        self._shortcut = shortcut
        self._render_key = None
        self.refresh(force=True)

    def on_show(self) -> None:
        self.refresh()

    def profiles_changed(self) -> None:
        self._render_key = None

    def refresh(self, force: bool = False) -> None:
        items = self._profiles()
        render_key = tuple((p.get("id"), p.get("name"), len(p.get("open_apps", [])), len(p.get("close_apps", []))) for p in items)
        if not force and render_key == self._render_key:
            return
        self._render_key = render_key
        for child in self.list.winfo_children():
            child.destroy()
        if not items:
            ctk.CTkLabel(
                self.list,
                text="No profiles yet\nCreate a profile to get started.",
                justify="center",
                text_color=COLORS["muted"],
                font=(FONT, 15),
            ).pack(pady=90)
            return
        for profile in items:
            row = Surface(self.list)
            row.pack(fill="x", pady=5)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row,
                text="◇",
                font=(FONT, 22, "bold"),
                text_color=COLORS["accent"],
                width=44,
            ).grid(row=0, column=0, rowspan=2, padx=(16, 8), pady=15)
            ctk.CTkLabel(
                row,
                text=str(profile.get("name", "Untitled")),
                anchor="w",
                font=(FONT, 14, "bold"),
            ).grid(row=0, column=1, sticky="ew", pady=(14, 0))
            summary = f"{len(profile.get('open_apps', []))} open  •  {len(profile.get('close_apps', []))} close"
            ctk.CTkLabel(row, text=summary, anchor="w", font=(FONT, 11), text_color=COLORS["muted"]).grid(row=1, column=1, sticky="ew", pady=(0, 14))
            self._action(row, "Shortcut", lambda item=profile: self._shortcut(item), 2)
            self._action(row, "Duplicate", lambda item=profile: self._duplicate(item), 3)
            self._action(row, "Edit", lambda item=profile: self._edit(item), 4, accent=True)
            ctk.CTkButton(
                row,
                text="Delete",
                width=70,
                fg_color="transparent",
                hover_color=COLORS["surface_hover"],
                text_color=COLORS["danger"],
                command=lambda item=profile: ConfirmDialog(
                    self,
                    "Delete profile?",
                    f"Delete {item.get('name', 'this profile')} permanently?",
                    lambda: self._delete(item),
                ),
            ).grid(row=0, column=5, rowspan=2, padx=(4, 14))

    @staticmethod
    def _action(parent, text: str, command: Callable[[], None], column: int, accent: bool = False) -> None:
        ctk.CTkButton(
            parent,
            text=text,
            width=78,
            height=34,
            corner_radius=8,
            fg_color=COLORS["accent"] if accent else COLORS["surface_hover"],
            hover_color=COLORS["accent_hover"] if accent else COLORS["border"],
            command=command,
        ).grid(row=0, column=column, rowspan=2, padx=4)

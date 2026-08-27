from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from .components import PageHeader, Surface, ConfirmDialog
from .theme import COLORS, FONT

class ProfileEditor(ctk.CTkFrame):
    def __init__(self, master, profile, save, cancel, delete, duplicate, shortcut, process_manager):
        super().__init__(master, fg_color="transparent"); self.item = deepcopy(profile or {"name": "", "description": "", "icon": "◆", "open_apps": [], "close_apps": []}); self.save_cb, self.cancel_cb = save, cancel; self.process_manager = process_manager
        PageHeader(self, "Profile Editor", "Configure the apps that shape this workspace.", "Save Profile", self._save).pack(fill="x", pady=(0, 16))
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent"); self.scroll.pack(fill="both", expand=True)
        general = self._section("General", "Name and describe this profile.")
        self.name = ctk.CTkEntry(general, placeholder_text="Profile name", height=42); self.name.pack(fill="x", padx=18, pady=(4, 8)); self.name.insert(0, self.item.get("name", ""))
        self.description = ctk.CTkEntry(general, placeholder_text="Optional description", height=42); self.description.pack(fill="x", padx=18, pady=(0, 18)); self.description.insert(0, self.item.get("description", ""))
        opens = self._section("Applications to Open", "Selected executables launch in order.")
        ctk.CTkButton(opens, text="+  Add Application", command=self._add_exe, fg_color=COLORS["accent"], width=160).pack(anchor="w", padx=18, pady=(2, 10))
        self.open_list = ctk.CTkFrame(opens, fg_color="transparent"); self.open_list.pack(fill="x", padx=12, pady=(0, 10))
        closes = self._section("Applications to Close", "Select a running app or enter an executable process name.")
        controls = ctk.CTkFrame(closes, fg_color="transparent"); controls.pack(fill="x", padx=18, pady=(2, 10)); controls.grid_columnconfigure(0, weight=1)
        self.process_name = ctk.CTkEntry(controls, placeholder_text="Process name, e.g. OUTLOOK.EXE", height=40); self.process_name.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(controls, text="Add", width=72, command=self._add_process).grid(row=0, column=1)
        ctk.CTkButton(controls, text="Choose Running", width=120, fg_color=COLORS["surface_hover"], command=self._choose_running).grid(row=0, column=2, padx=(8, 0))
        self.close_list = ctk.CTkFrame(closes, fg_color="transparent"); self.close_list.pack(fill="x", padx=12, pady=(0, 10)); self._render_lists()
        if profile:
            actions = ctk.CTkFrame(self.scroll, fg_color="transparent"); actions.pack(fill="x", pady=14)
            ctk.CTkButton(actions, text="Create Desktop Shortcut", fg_color=COLORS["surface"], hover_color=COLORS["surface_hover"], command=lambda: shortcut(self.item)).pack(side="left")
            ctk.CTkButton(actions, text="Duplicate", fg_color=COLORS["surface"], hover_color=COLORS["surface_hover"], command=lambda: duplicate(self.item)).pack(side="left", padx=8)
            ctk.CTkButton(actions, text="Delete Profile", fg_color=COLORS["danger"], command=lambda: ConfirmDialog(self, "Delete profile?", f"Delete {self.item.get('name')} permanently?", lambda: delete(self.item))).pack(side="right")
        ctk.CTkButton(self.scroll, text="Cancel", fg_color="transparent", hover_color=COLORS["surface_hover"], command=cancel).pack(anchor="w")
    def _section(self, title, subtitle):
        box = Surface(self.scroll); box.pack(fill="x", pady=7)
        ctk.CTkLabel(box, text=title, font=(FONT, 16, "bold")).pack(anchor="w", padx=18, pady=(16, 2)); ctk.CTkLabel(box, text=subtitle, text_color=COLORS["muted"], font=(FONT, 11)).pack(anchor="w", padx=18, pady=(0, 12)); return box
    def _save(self):
        name = self.name.get().strip()
        if not name: self.name.configure(border_color=COLORS["danger"]); return
        self.item["name"], self.item["description"] = name, self.description.get().strip(); self.save_cb(self.item)
    def _add_exe(self):
        path = filedialog.askopenfilename(title="Select an application", filetypes=[("Windows applications", "*.exe"), ("All files", "*.*")])
        if path and not any(a.get("path", "").casefold() == path.casefold() for a in self.item["open_apps"]): self.item["open_apps"].append({"name": Path(path).stem, "path": path}); self._render_lists()
    def _add_process(self):
        name = Path(self.process_name.get().strip()).name
        if name and name.casefold() not in [str(x).casefold() for x in self.item["close_apps"]]: self.item["close_apps"].append(name); self.process_name.delete(0, "end"); self._render_lists()
    def _choose_running(self):
        dialog = ctk.CTkToplevel(self); dialog.title("Choose a running process"); dialog.geometry("600x500"); dialog.configure(fg_color=COLORS["bg"]); dialog.transient(self); dialog.grab_set()
        ctk.CTkLabel(dialog, text="Choose a running application", font=(FONT, 19, "bold")).pack(anchor="w", padx=22, pady=18)
        area = ctk.CTkScrollableFrame(dialog, fg_color="transparent"); area.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        for info in self.process_manager.running_processes(False):
            def choose(name=info["name"]): self.process_name.delete(0, "end"); self.process_name.insert(0, name); dialog.destroy(); self._add_process()
            ctk.CTkButton(area, text=f"{info['name']}   ·   PID {info['pid']}", anchor="w", fg_color=COLORS["surface"], hover_color=COLORS["surface_hover"], command=choose).pack(fill="x", pady=3)
    def _render_lists(self):
        for parent in (self.open_list, self.close_list):
            for child in parent.winfo_children(): child.destroy()
        for index, app in enumerate(self.item["open_apps"]): self._list_row(self.open_list, app.get("name", "Application"), app.get("path", ""), lambda i=index: (self.item["open_apps"].pop(i), self._render_lists()))
        for index, name in enumerate(self.item["close_apps"]): self._list_row(self.close_list, str(name), "Process name", lambda i=index: (self.item["close_apps"].pop(i), self._render_lists()))
    def _list_row(self, parent, title, subtitle, remove):
        row = ctk.CTkFrame(parent, fg_color=COLORS["surface_hover"], corner_radius=9); row.pack(fill="x", pady=3); row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(row, text=title, font=(FONT, 12, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 0)); ctk.CTkLabel(row, text=subtitle, text_color=COLORS["muted"], font=(FONT, 10), anchor="w").grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8)); ctk.CTkButton(row, text="Remove", width=70, fg_color="transparent", text_color=COLORS["danger"], hover_color=COLORS["surface"], command=remove).grid(row=0, column=1, rowspan=2, padx=8)

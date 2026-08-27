import threading
import customtkinter as ctk
from .components import PageHeader, Surface
from .theme import COLORS, FONT

class ProcessesPage(ctk.CTkFrame):
    def __init__(self, master, manager):
        super().__init__(master, fg_color="transparent"); self.manager = manager
        PageHeader(self, "Running Processes", "Inspect active desktop applications.", "↻  Refresh", self.refresh).pack(fill="x", pady=(0, 18))
        self.system = ctk.CTkSwitch(self, text="Show system processes", command=self.refresh); self.system.pack(anchor="w", pady=(0, 10))
        self.list = ctk.CTkScrollableFrame(self, fg_color="transparent"); self.list.pack(fill="both", expand=True); self.refresh()
    def refresh(self):
        for child in self.list.winfo_children(): child.destroy()
        ctk.CTkLabel(self.list, text="Loading processes…", text_color=COLORS["muted"]).pack(pady=30)
        def load():
            items = self.manager.running_processes(bool(self.system.get())); self.after(0, lambda: self.render(items))
        threading.Thread(target=load, daemon=True).start()
    def render(self, items):
        for child in self.list.winfo_children(): child.destroy()
        for item in items:
            row = Surface(self.list); row.pack(fill="x", pady=4); row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text="●", text_color=COLORS["success"]).grid(row=0, column=0, rowspan=2, padx=16)
            ctk.CTkLabel(row, text=f"{item['name']}   ·   PID {item['pid']}", font=(FONT, 13, "bold")).grid(row=0, column=1, sticky="w", pady=(10, 0))
            ctk.CTkLabel(row, text=item.get("exe") or "Path unavailable", text_color=COLORS["muted"], font=(FONT, 11), anchor="w").grid(row=1, column=1, sticky="ew", pady=(1, 10), padx=(0, 12))

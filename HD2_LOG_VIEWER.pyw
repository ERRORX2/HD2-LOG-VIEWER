import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import numpy as np
import csv
import json
import os

GROUPS_FILE = "groups.json"

def save_config(groups_dict: Dict, is_dark: bool, multi_mode: bool = False, delta_mode: bool = False):
    config = {
        "groups": groups_dict, 
        "settings": {
            "dark_mode": is_dark, 
            "multi_mode": multi_mode,
            "delta_mode": delta_mode
        }
    }
    try:
        with open(GROUPS_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except: pass

def load_config() -> Tuple[Dict, bool, bool, bool]:
    if not Path(GROUPS_FILE).exists(): return {}, False, False, False
    try:
        with open(GROUPS_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and "groups" in data and "settings" in data:
                sets = data["settings"]
                return (data["groups"], 
                        sets.get("dark_mode", False), 
                        sets.get("multi_mode", False),
                        sets.get("delta_mode", False))
            return data if isinstance(data, dict) else {}, False, False, False
    except: return {}, False, False, False

class TelemetryAnalyzer:
    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self.df: pd.DataFrame = pd.DataFrame()

    def load(self) -> None:
        success = False
        try:
            with open(self.path, 'r', encoding='latin-1', errors='ignore') as f:
                sample = f.readline() + f.readline()
                dialect = csv.Sniffer().sniff(sample)
                sep = dialect.delimiter
        except: sep = None 

        for enc in ['utf-8-sig', 'latin-1', 'cp1252']:
            try:
                self.df = pd.read_csv(self.path, encoding=enc, sep=sep, on_bad_lines='skip', engine='python')
                if not self.df.empty:
                    success = True; break
            except: continue
        
        if not success: raise ValueError("File Load Failed")
        self.df.columns = [str(c).strip().replace('\ufeff', '') for c in self.df.columns]
        
        for col in self.df.columns:
            try:
                s = self.df[col].astype(str).str.replace(',', '.', regex=False)
                cleaned = s.str.replace(r'[^\d\.\-eE]', '', regex=True)
                self.df[col] = pd.to_numeric(cleaned, errors='coerce')
            except: continue

        while len(self.df) > 1:
            last_row = self.df.iloc[-1]
            if (last_row == 0).sum() + last_row.isna().sum() > (len(self.df.columns) / 2):
                self.df = self.df.iloc[:-1]
            else: break
        self.df.ffill(inplace=True)

class TelemetryApp:
    def __init__(self, root: tk.Tk, analyzer: TelemetryAnalyzer):
        self.root = root
        self.analyzer = analyzer
        self.df = analyzer.df
        self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode = load_config()
        
        self.vars = {}
        self.cb_widgets = {}
        self.header_widgets = {}
        self.group_map = {}
        self.cursor_lines = []
        self.cursor_text = None
        self.filter_active = False 
        
        self.temp_limits = {'HOTSPOT': 95.0, 'CORE': 100.0, 'GPU': 88.0, 'MEMORY': 105.0, 'VRM': 110.0, 'SSD': 80.0}
        self.volt_rails = {'+12V': (11.4, 12.6), '+5V': (4.75, 5.25), '+3.3V': (3.13, 3.46)}

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._setup_ui()
        self._apply_theme_colors()
        self.update_plot()

    def _on_close(self):
        plt.close('all'); self.root.quit(); self.root.destroy(); os._exit(0)

    def show_toast(self, message: str, duration: int = 2000):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        bg = "#333333" if self.is_dark else "#eeeeee"
        fg = "white" if self.is_dark else "black"
        label = tk.Label(toast, text=message, bg=bg, fg=fg, padx=20, pady=10, 
                         font=('Segoe UI', 10, 'bold'), relief='flat')
        label.pack()
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (toast.winfo_width() // 2)
        y = self.root.winfo_y() + self.root.winfo_height() - 100
        toast.geometry(f"+{x}+{y}")
        self.root.after(duration, toast.destroy)

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self._apply_theme_colors()
        self.update_plot()
        save_config(self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode)

    def _toggle_multi(self):
        self.multi_mode = not self.multi_mode
        self.multi_btn.config(text="📊 Multiplot: ON" if self.multi_mode else "📊 Multiplot: OFF")
        self.update_plot()
        save_config(self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode)

    def _toggle_delta(self):
        self.delta_mode = not self.delta_mode
        self.delta_btn.config(text="Δ Delta Mode: ON" if self.delta_mode else "Δ Delta Mode: OFF")
        self.update_plot()
        save_config(self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode)

    def _apply_theme_colors(self):
        bg, fg = ("#1e1e1e", "#ffffff") if self.is_dark else ("#f0f0f0", "#000000")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background=bg, foreground=fg, fieldbackground=bg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabelframe", background=bg, foreground=fg)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.configure("Alert.TCheckbutton", background=bg, foreground="#ff4d4d", font=('Segoe UI', 9, 'bold'))
        self.style.configure("Delete.TButton", foreground="#ff4d4d")
        self.style.map("TCheckbutton", background=[('active', bg)])
        self.root.configure(bg=bg)
        self.canvas_checklist.configure(bg=bg)
        self.scroll_frame.configure(bg=bg)
        for hdr in self.header_widgets.values():
            hdr.configure(bg=bg, fg="#62a1ff" if self.is_dark else "#2c3e50")

    def _is_critical(self, col: str) -> bool:
        name = col.upper()
        series = self.df[col].dropna()
        if series.empty: return False
        if "FREQUENCY LIMIT" in name: return False
        if "[%]" in name and "LIMIT" in name: return series.max() >= 99.0
        for rail, (low, high) in self.volt_rails.items():
            if rail in name:
                if series.min() < low or series.max() > high: return True
        limit_keywords = ['THROTTLING', 'RELIABILITY', 'PERFCAP']
        if any(x in name for x in limit_keywords):
            if series.max() >= 0.9: return True
        if any(x in name for x in ['TEMP', '°C']):
            for key, limit in self.temp_limits.items():
                if key in name:
                    if series.max() >= limit: return True
            if series.max() >= 95.0: return True
        return False

    def _setup_ui(self):
        self.root.title(f"HD2 LOG VIEWER - {self.analyzer.path.name}")
        self.root.geometry("1550x900")
        for widget in self.root.winfo_children(): widget.destroy()

        self.left = ttk.Frame(self.root, width=420, padding="10")
        self.left.pack(side=tk.LEFT, fill=tk.Y)
        self.right = ttk.Frame(self.root, padding="10")
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        top = ttk.Frame(self.left)
        top.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(top, text="Telemetry Controls", font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)
        ttk.Button(top, text="◐ Theme", command=self._toggle_theme, width=10).pack(side=tk.RIGHT, padx=5)
        
        self.multi_btn = ttk.Button(self.left, text="📊 Multiplot: ON" if self.multi_mode else "📊 Multiplot: OFF", command=self._toggle_multi)
        self.multi_btn.pack(fill=tk.X, pady=2)

        self.delta_btn = ttk.Button(self.left, text="Δ Delta Mode: ON" if self.delta_mode else "Δ Delta Mode: OFF", command=self._toggle_delta)
        self.delta_btn.pack(fill=tk.X, pady=2)

        self.grp_f = ttk.LabelFrame(self.left, text=" Saved Groups ", padding=10)
        self.grp_f.pack(fill=tk.X, pady=5); self._refresh_group_buttons()

        ent_f = ttk.Frame(self.left)
        ent_f.pack(fill=tk.X, pady=5)
        ttk.Label(ent_f, text="Group Name:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0,5))
        self.name_var = tk.StringVar(value="")
        ttk.Entry(ent_f, textvariable=self.name_var).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(ent_f, text="Save", command=self._save_group).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.left, text="📋 Import Group from Clipboard", command=self._import_from_clipboard).pack(fill=tk.X, pady=2)

        self.filter_btn = ttk.Button(self.left, text="🚨 Filter Out-of-Spec", command=self._toggle_filter)
        self.filter_btn.pack(fill=tk.X, pady=2)

        ttk.Label(self.left, text="Search Sensors:").pack(fill=tk.X, pady=(5,0))
        self.search_var = tk.StringVar(); self.search_var.trace_add("write", lambda *a: self._filter_sensors())
        ttk.Entry(self.left, textvariable=self.search_var).pack(fill=tk.X, pady=(2, 10))

        self.canv_f = ttk.Frame(self.left); self.canv_f.pack(fill=tk.BOTH, expand=True)
        self.canvas_checklist = tk.Canvas(self.canv_f, highlightthickness=0)
        sc = ttk.Scrollbar(self.canv_f, orient="vertical", command=self.canvas_checklist.yview)
        self.scroll_frame = tk.Frame(self.canvas_checklist)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas_checklist.configure(scrollregion=self.canvas_checklist.bbox("all")))
        self.canvas_checklist.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.canvas_checklist.configure(yscrollcommand=sc.set)
        self.canvas_checklist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); sc.pack(side=tk.RIGHT, fill=tk.Y)
        self._build_checklist()

        btn_frame = ttk.Frame(self.left); btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Import CSV", command=self._import_new_csv).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_frame, text="Clear", command=self._clear_all).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_frame, text="Export PNG", command=self._export).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.fig = plt.figure(figsize=(10, 6))
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self.right)
        self.canvas_widget.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas_widget.mpl_connect('axes_leave_event', self._on_mouse_leave)
        NavigationToolbar2Tk(self.canvas_widget, self.right, pack_toolbar=True)
        self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _build_checklist(self):
        self.group_map = {}
        for col in self.df.columns:
            cat = self._get_category(col)
            if cat not in self.group_map: self.group_map[cat] = []
            self.group_map[cat].append(col)
        self.sorted_cats = ["Processor (CPU)", "Graphics Card (GPU)", "Thermal / Temperatures"] + \
                          sorted([c for c in self.group_map.keys() if c not in ["Processor (CPU)", "Graphics Card (GPU)", "Thermal / Temperatures"]])
        for cat in self.sorted_cats:
            if cat not in self.group_map: continue
            h = tk.Label(self.scroll_frame, text=f"--- {cat} ---", font=('Arial', 9, 'bold'), anchor="w")
            h.pack(fill=tk.X, pady=(10,0)); self.header_widgets[cat] = h
            for col in sorted(self.group_map[cat]):
                v = self.vars.get(col, tk.BooleanVar(value=False))
                self.vars[col] = v
                cb = ttk.Checkbutton(self.scroll_frame, text=col, variable=v, command=self.update_plot,
                                     style="Alert.TCheckbutton" if self._is_critical(col) else "TCheckbutton")
                cb.pack(anchor=tk.W, padx=15); self.cb_widgets[col] = cb

    def _get_category(self, n: str) -> str:
        u = n.upper()
        if any(x in u for x in ['GPU', 'NVIDIA', 'GEFORCE', 'AMD', 'RTX', 'GTX']): return "Graphics Card (GPU)"
        if any(x in u for x in ['CPU', 'CORE ', 'VCORE', 'AMD RYZEN', 'INTEL']): return "Processor (CPU)"
        if any(x in u for x in ['TEMP', '°C', 'HOTSPOT']): return "Thermal / Temperatures"
        return "Other Sensors"

    def _toggle_filter(self):
        self.filter_active = not self.filter_active
        self.filter_btn.config(text="🚨 Show All Sensors" if self.filter_active else "🚨 Filter Out-of-Spec")
        if self.filter_active: self._apply_issue_filter()
        else: self._filter_sensors()

    def _apply_issue_filter(self):
        for h in self.header_widgets.values(): h.pack_forget()
        for cb in self.cb_widgets.values(): cb.pack_forget()
        for cat in self.sorted_cats:
            if cat not in self.group_map: continue
            issues = [col for col in self.group_map[cat] if self._is_critical(col)]
            if issues:
                self.header_widgets[cat].pack(fill=tk.X, pady=(10,0))
                for col in sorted(issues): self.cb_widgets[col].pack(anchor=tk.W, padx=15)

    def _refresh_group_buttons(self):
        for w in self.grp_f.winfo_children(): w.destroy()
        self.grp_f.columnconfigure(0, weight=1)
        for i, g in enumerate(sorted(self.custom_groups.keys())):
            btn = ttk.Button(self.grp_f, text=g, command=lambda n=g: self._apply_group(n))
            btn.grid(row=i, column=0, sticky='ew', pady=1, padx=(0,2))
            sh_btn = ttk.Button(self.grp_f, text="📋", width=3, command=lambda n=g: self._share_group(n))
            sh_btn.grid(row=i, column=1, pady=1, padx=1)
            del_btn = ttk.Button(self.grp_f, text="✕", width=3, command=lambda n=g: self._delete_group(n), style="Delete.TButton")
            del_btn.grid(row=i, column=2, pady=1)

    def _share_group(self, n):
        data = {"name": n, "sensors": self.custom_groups[n]}
        self.root.clipboard_clear()
        self.root.clipboard_append(json.dumps(data))
        self.show_toast(f"Copied '{n}' to Clipboard")

    def _import_from_clipboard(self):
        try:
            data = json.loads(self.root.clipboard_get())
            if "name" in data and "sensors" in data:
                self.custom_groups[data["name"]] = data["sensors"]
                save_config(self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode)
                self._refresh_group_buttons()
                self.show_toast(f"Imported Group: {data['name']}")
        except: messagebox.showerror("Error", "Clipboard does not contain a valid group configuration.")

    def _delete_group(self, n):
        if messagebox.askyesno("Delete Group", f"Are you sure you want to delete '{n}'?"):
            if n in self.custom_groups:
                del self.custom_groups[n]
                save_config(self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode)
                self._refresh_group_buttons()

    def _apply_group(self, n):
        for v in self.vars.values(): v.set(False)
        for s in self.custom_groups.get(n, []):
            if s in self.vars: self.vars[s].set(True)
        self.update_plot()

    def _save_group(self):
        name = self.name_var.get().strip()
        sel = [c for c, v in self.vars.items() if v.get()]
        if sel and name:
            self.custom_groups[name] = sel
            save_config(self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode)
            self._refresh_group_buttons(); self.name_var.set("") 
            self.show_toast(f"Saved Group: {name}")

    def _filter_sensors(self):
        if self.filter_active: return 
        q = self.search_var.get().upper()
        for h in self.header_widgets.values(): h.pack_forget()
        for cb in self.cb_widgets.values(): cb.pack_forget()
        for cat in self.sorted_cats:
            if cat not in self.group_map: continue
            m = [col for col in self.group_map[cat] if q in col.upper()]
            if m:
                self.header_widgets[cat].pack(fill=tk.X, pady=(10,0))
                for col in sorted(m): self.cb_widgets[col].pack(anchor=tk.W, padx=15)

    def _import_new_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            try:
                new_analyzer = TelemetryAnalyzer(path); new_analyzer.load()
                self.analyzer = new_analyzer; self.df = self.analyzer.df
                new_cols = set(self.df.columns)
                for col, var in list(self.vars.items()):
                    if col not in new_cols: var.set(False)
                self.filter_active = False 
                self._setup_ui(); self._apply_theme_colors(); self.update_plot()
            except Exception as e: messagebox.showerror("Error", str(e))

    def _clear_all(self):
        for v in self.vars.values(): v.set(False)
        self.update_plot()

    def _export(self):
        f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if f: self.fig.savefig(f, dpi=300, bbox_inches='tight', facecolor=self.fig.get_facecolor())

    def _clear_cursors(self):
        for line in self.cursor_lines: 
            try: line.remove()
            except: pass
        self.cursor_lines = []
        if self.cursor_text:
            try: self.cursor_text.remove()
            except: pass
            self.cursor_text = None

    def _on_mouse_leave(self, event):
        self._clear_cursors()
        self.canvas_widget.draw_idle()

    def _on_mouse_move(self, event):
        if event.inaxes is None:
            self._on_mouse_leave(event)
            return
        try:
            x = int(round(event.xdata))
            if x < 0 or x >= len(self.df):
                self._on_mouse_leave(event)
                return
            self._clear_cursors()
            for ax in self.fig.axes:
                l = ax.axvline(x=x, color='white' if self.is_dark else 'gray', ls='--', alpha=0.5)
                self.cursor_lines.append(l)
            sel = [c for c, v in self.vars.items() if v.get() and c in self.df.columns]
            txt = f"Rec: {x}\n"
            if self.delta_mode and len(sel) >= 2:
                d_val = abs(self.df.iloc[x][sel[0]] - self.df.iloc[x][sel[1]])
                txt += f"Δ Delta: {d_val:.2f}\n---\n"
            txt += "\n".join([f"{c}: {self.df.iloc[x][c]:.2f}" for c in sel])
            self.cursor_text = self.fig.text(0.01, 0.99, txt, va='top', ha='left',
                bbox=dict(boxstyle='round', facecolor='#252525' if self.is_dark else 'white', alpha=0.8),
                fontsize=8, color='white' if self.is_dark else 'black')
            self.canvas_widget.draw_idle()
        except: pass

    def update_plot(self):
        self.fig.clear()
        self.cursor_lines = []
        self.cursor_text = None
        is_dark = self.is_dark
        bg_color, text_color, grid_color = ("#1e1e1e", "white", "#444444") if is_dark else ("white", "black", "#b0b0b0")
        self.fig.patch.set_facecolor(bg_color)
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        sel = [c for c, v in self.vars.items() if v.get() and c in self.df.columns]
        
        if not sel:
            ax = self.fig.add_subplot(111); ax.set_facecolor("#252525" if is_dark else "#fdfdfd")
            ax.text(0.5, 0.5, "No Sensors Selected", ha='center', va='center', color='gray')
        elif self.delta_mode and len(sel) >= 2:
            ax = self.fig.add_subplot(111); ax.set_facecolor("#252525" if is_dark else "#fdfdfd")
            s1, s2 = self.df[sel[0]], self.df[sel[1]]
            delta = (s1 - s2).abs()
            ax.plot(self.df.index, s1, label=sel[0], alpha=0.4, ls='--')
            ax.plot(self.df.index, s2, label=sel[1], alpha=0.4, ls='--')
            ax.plot(self.df.index, delta, label=f"Δ Delta ({sel[0]} - {sel[1]})", color="#ffcc00", lw=2)
            ax.grid(True, linestyle=':', alpha=0.4, color=grid_color)
            ax.tick_params(colors=text_color, labelsize=8)
            l = ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize='x-small', frameon=False)
            for t in l.get_texts(): t.set_color(text_color)
        else:
            num_plots = len(sel) if self.multi_mode else 1
            axes = []
            for i, col_name in enumerate(sel):
                color = colors[i % len(colors)]
                series = self.df[col_name].dropna()
                stats_str = f"Min: {series.min():.1f} | Max: {series.max():.1f} | Avg: {series.mean():.1f}"
                if self.multi_mode:
                    ax = self.fig.add_subplot(num_plots, 1, i+1, sharex=axes[0] if axes else None)
                    axes.append(ax)
                    ax.set_title(f"{col_name}  [{stats_str}]", color=color, fontsize=8, fontweight='bold', loc='left', pad=4)
                else:
                    if not axes: ax = self.fig.add_subplot(111); axes.append(ax)
                    ax = axes[0]
                ax.set_facecolor("#252525" if is_dark else "#fdfdfd")
                ax.plot(self.df.index, self.df[col_name], label=f"{col_name}\n({stats_str})", lw=1.5, color=color)
                ax.grid(True, linestyle=':', alpha=0.4, color=grid_color)
                ax.tick_params(colors=text_color, labelsize=8)
                if not self.multi_mode:
                    l = ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize='x-small', frameon=False)
                    for t in l.get_texts(): t.set_color(text_color)
            if self.multi_mode:
                for ax in axes[:-1]: plt.setp(ax.get_xticklabels(), visible=False)
        self.fig.tight_layout(); self.fig.subplots_adjust(hspace=0.5 if self.multi_mode else 0.2)
        self.canvas_widget.draw_idle()

if __name__ == "__main__":
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if path:
        try:
            a = TelemetryAnalyzer(path); a.load()
            root.deiconify(); TelemetryApp(root, a); root.mainloop()
        except Exception as e: messagebox.showerror("Error", str(e)); root.destroy()
    else: root.destroy()
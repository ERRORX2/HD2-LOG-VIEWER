import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import seaborn as sns
from pathlib import Path
from typing import List, Optional, Dict, Set
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import numpy as np
import csv
import re
import json
import sys
import os

GROUPS_FILE = "groups.json"

def save_custom_groups(groups_dict):
    with open(GROUPS_FILE, 'w') as f:
        json.dump(groups_dict, f)

def load_custom_groups():
    if Path(GROUPS_FILE).exists():
        try:
            with open(GROUPS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

class TelemetryAnalyzer:
    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self.df: pd.DataFrame = pd.DataFrame()
        self.hardware_list: Set[str] = set()

    def load(self) -> None:
        success = False
        try:
            with open(self.path, 'r', encoding='latin-1', errors='ignore') as f:
                sample = f.readline() + f.readline()
                dialect = csv.Sniffer().sniff(sample)
                sep = dialect.delimiter
        except:
            sep = None 

        encodings = ['utf-8-sig', 'latin-1', 'cp1252', 'utf-8']
        for enc in encodings:
            try:
                self.df = pd.read_csv(self.path, encoding=enc, sep=sep, on_bad_lines='skip', engine='python')
                if not self.df.empty:
                    success = True
                    break
            except: continue
        
        if not success: raise ValueError("Could not read file.")

        self.df.columns = [str(c).strip().replace('\ufeff', '') for c in self.df.columns]
        
        unit_ignore = {'GB/S', 'GT/S', 'KB/S', 'MB/S', 'YES/NO', 'V', 'W', '%', 'RPM', 'MHZ', 'GHZ', 'FPS', 'HZ', 'C', 'TEMP', 'OK'}

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
            else:
                break

        self.df.ffill(inplace=True)
        self.hardware_list.clear()
        
        for col in self.df.columns:
            matches = re.findall(r'\[(.*?)\]', col)
            for m in matches:
                m_clean = m.strip()
                if len(m_clean) > 2 and m_clean.upper() not in unit_ignore and not m_clean.isdigit():
                    self.hardware_list.add(m_clean)

class TelemetryApp:
    def __init__(self, root: tk.Tk, analyzer: TelemetryAnalyzer):
        self.root = root
        self.analyzer = analyzer
        self.df = analyzer.df
        self.vars = {}
        self.cb_widgets = {}
        self.header_widgets = {}
        self.group_map = {}
        self.custom_groups = load_custom_groups()
        
        self.rail_specs = {'12': (11.2, 12.8), '5': (4.7, 5.3), '3.3': (3.1, 3.5), 'VCORE': (0.6, 1.52)}
        self.temp_limits = {'HOTSPOT': 95.0, 'CORE': 100.0, 'GPU': 88.0, 'MEMORY': 105.0, 'VRM': 110.0, 'SSD': 80.0}
        
        self.cursor_line = None
        self.cursor_text = None

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._setup_ui()

    def _on_close(self):
        """Standard clean exit."""
        plt.close('all')
        self.root.quit()
        self.root.destroy()
        os._exit(0)

    def _get_rail_type(self, col: str) -> Optional[str]:
        name = col.upper()
        if 'VCORE' in name: return 'VCORE'
        if not any(x in name for x in ['+12V', '+5V', '+3.3V']): return None
        series = self.df[col].dropna()
        if series.empty: return None
        med = series.median()
        for rid, (low, high) in self.rail_specs.items():
            if rid == 'VCORE': continue
            if low <= med <= high: return rid
        return None

    def _is_critical(self, col: str) -> bool:
        name = col.upper()
        series = self.df[col].dropna()
        if series.empty: return False
        if any(x in name for x in ['THROTTLING', 'RELIABILITY', 'PERFCAP']):
            if series.max() >= 1.0: return True
        if 'LIMIT' in name and '%' in name:
            if series.max() >= 100.0: return True
        if any(x in name for x in ['TEMP', '\u00b0C', 'TEMPERATURE', 'TEMP\u00c9RATURE']):
            for key, limit in self.temp_limits.items():
                if key in name and series.max() >= limit: return True
        rid = self._get_rail_type(col)
        if rid:
            low, high = self.rail_specs[rid]
            if series.min() < low or series.max() > high: return True
        return False

    def _get_category(self, name: str) -> str:
        n = name.upper()
        if any(x in n for x in ['GPU', 'NVIDIA', 'AMD']): return "Graphics Card (GPU)"
        if any(x in n for x in ['CPU', 'CORE ', 'VCORE']): return "Processor (CPU)"
        if any(x in n for x in ['TEMP', '\u00b0C', 'TEMPERATURE', 'TEMP\u00c9RATURE']): return "Thermal / Temperatures"
        if any(x in n for x in ['VOLT', 'VIN', 'VCC']): return "Mainboard Voltages"
        if any(x in n for x in ['POWER', '[W]', 'WATT']): return "Power Consumption"
        if any(x in n for x in ['CLOCK', 'MHZ', 'GHZ']): return "Clocks / Frequencies"
        if any(x in n for x in ['USAGE', 'LOAD', 'PERCENT', '%', 'UTILISATION']): return "System Load / Usage"
        return "Other Sensors"

    def _setup_ui(self):
        self.root.title(f"HD2 LOG VIEWER - {self.analyzer.path.name}")
        self.root.geometry("1550x900")
        sns.set_theme(style="darkgrid")
        
        self.style = ttk.Style()
        self.style.configure("Alert.TCheckbutton", foreground="#cc0000", font=('Segoe UI', 9, 'bold'))

        for widget in self.root.winfo_children(): widget.destroy()

        self.left = ttk.Frame(self.root, width=420, padding="10")
        self.left.pack(side=tk.LEFT, fill=tk.Y)
        self.right = ttk.Frame(self.root, padding="10")
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        hw_frame = ttk.LabelFrame(self.left, text=" Detected Hardware ", padding=10)
        hw_frame.pack(fill=tk.X, pady=(0, 10))
        valid_hw = sorted(list(self.analyzer.hardware_list))
        hw_text = " \u2022 " + "\n \u2022 ".join(valid_hw) if valid_hw else "No specific hardware tags found"
        ttk.Label(hw_frame, text=hw_text, font=('Consolas', 9), foreground="#005fb8").pack(anchor=tk.W)

        self.group_btn_frame = ttk.LabelFrame(self.left, text=" Saved Groups ", padding=10)
        self.group_btn_frame.pack(fill=tk.X, pady=(0, 10))
        self._refresh_group_buttons()

        tool_frame = ttk.Frame(self.left); tool_frame.pack(fill=tk.X, pady=(0, 10))
        self.group_name_var = tk.StringVar(value="New Group")
        entry_f = ttk.Frame(tool_frame); entry_f.pack(fill=tk.X)
        ttk.Entry(entry_f, textvariable=self.group_name_var).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(entry_f, text="Save", command=self._save_group).pack(side=tk.LEFT, padx=5)
        ttk.Button(tool_frame, text="\U0001F6A8 Filter Out-of-Spec", command=self._filter_to_issues).pack(fill=tk.X, pady=(10, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_sensors())
        ttk.Entry(self.left, textvariable=self.search_var).pack(fill=tk.X, pady=(0, 10))

        self.container = ttk.Frame(self.left); self.container.pack(fill=tk.BOTH, expand=True)
        self._build_checklist()

        btn_frame = ttk.Frame(self.left); btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Import CSV", command=self._import_new_csv).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self._clear_all).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_frame, text="Export PNG", command=self._export).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self.right)
        self.canvas_widget.mpl_connect('motion_notify_event', self._on_mouse_move)
        NavigationToolbar2Tk(self.canvas_widget, self.right, pack_toolbar=True)
        self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.update_plot()

    def _on_mouse_move(self, event):
        if event.inaxes != self.ax:
            if self.cursor_line: self.cursor_line.remove(); self.cursor_line = None
            if self.cursor_text: self.cursor_text.remove(); self.cursor_text = None
            self.canvas_widget.draw_idle(); return
        x = int(round(event.xdata))
        if x < 0 or x >= len(self.df): return
        if self.cursor_line: self.cursor_line.remove()
        self.cursor_line = self.ax.axvline(x=x, color='gray', linestyle='--', alpha=0.5)
        selected = [c for c, v in self.vars.items() if v.get()]
        if not selected: return
        txt_lines = [f"Record: {x}"]
        for col in selected:
            txt_lines.append(f"{col}: {self.df.iloc[x][col]:.2f}")
        if self.cursor_text: self.cursor_text.remove()
        self.cursor_text = self.ax.text(0.02, 0.98, "\n".join(txt_lines), transform=self.ax.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'),
            fontsize=8, family='monospace')
        self.canvas_widget.draw_idle()

    def _filter_to_issues(self):
        for hdr in self.header_widgets.values(): hdr.pack_forget()
        for cb in self.cb_widgets.values(): cb.pack_forget()
        found = False
        for cat in self.sorted_cats:
            if cat not in self.group_map: continue
            issues = [col for col in self.group_map[cat] if self._is_critical(col)]
            if issues:
                self.header_widgets[cat].pack(anchor=tk.W, pady=(10, 0))
                for col in sorted(issues):
                    self.cb_widgets[col].pack(anchor=tk.W, padx=15); found = True
        if not found:
            messagebox.showinfo("Hardware Health", "System within operating specs.")
            self._filter_sensors()
        else: self.canvas_checklist.yview_moveto(0)

    def _refresh_group_buttons(self):
        for widget in self.group_btn_frame.winfo_children(): widget.destroy()
        if not self.custom_groups: return
        row, col = 0, 0
        for g_name in sorted(self.custom_groups.keys()):
            ttk.Button(self.group_btn_frame, text=g_name, width=15, 
                       command=lambda n=g_name: self._apply_group(n)).grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 1: col = 0; row += 1

    def _apply_group(self, group_name):
        self.root.config(cursor="watch")
        for v in self.vars.values():
            v.set(False)
        for s in self.custom_groups.get(group_name, []):
            if s in self.vars: 
                self.vars[s].set(True)
        self.update_plot()
        self.root.config(cursor="")

    def _save_group(self):
        name = self.group_name_var.get().strip()
        selected = [c for c, v in self.vars.items() if v.get()]
        if selected:
            self.custom_groups[name] = selected
            save_custom_groups(self.custom_groups); self._refresh_group_buttons()

    def _build_checklist(self):
        self.canvas_checklist = tk.Canvas(self.container, width=380, highlightthickness=0)
        scroll = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas_checklist.yview)
        self.scroll_frame = ttk.Frame(self.canvas_checklist)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas_checklist.configure(scrollregion=self.canvas_checklist.bbox("all")))
        self.canvas_checklist.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas_checklist.configure(yscrollcommand=scroll.set)
        self.canvas_checklist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.group_map = {}
        for col in self.df.columns:
            cat = self._get_category(col)
            if cat not in self.group_map: self.group_map[cat] = []
            self.group_map[cat].append(col)

        self.vars = {}; self.cb_widgets = {}; self.header_widgets = {}
        priority = ["Processor (CPU)", "Graphics Card (GPU)", "Thermal / Temperatures"]
        self.sorted_cats = priority + sorted([c for c in self.group_map.keys() if c not in priority])

        for cat in self.sorted_cats:
            if cat not in self.group_map: continue
            cat_crit = any(self._is_critical(col) for col in self.group_map[cat])
            hdr = ttk.Label(self.scroll_frame, text=f"--- {cat} ---" + (" (!)" if cat_crit else ""), 
                            font=('Arial', 9, 'bold'), foreground="#cc0000" if cat_crit else "#2c3e50")
            hdr.pack(anchor=tk.W, pady=(10, 0)); self.header_widgets[cat] = hdr
            for col in sorted(self.group_map[cat]):
                var = tk.BooleanVar(value=False); self.vars[col] = var
                is_crit = self._is_critical(col)
                cb = ttk.Checkbutton(self.scroll_frame, text=col, variable=var, 
                                     command=self.update_plot, style="Alert.TCheckbutton" if is_crit else "TCheckbutton")
                cb.pack(anchor=tk.W, padx=15); self.cb_widgets[col] = cb

    def _filter_sensors(self):
        query = self.search_var.get().upper()
        for hdr in self.header_widgets.values(): hdr.pack_forget()
        for cb in self.cb_widgets.values(): cb.pack_forget()
        for cat in self.sorted_cats:
            if cat not in self.group_map: continue
            matches = [col for col in self.group_map[cat] if query in col.upper()]
            if matches:
                self.header_widgets[cat].pack(anchor=tk.W, pady=(10, 0))
                for col in sorted(matches): self.cb_widgets[col].pack(anchor=tk.W, padx=15)

    def _import_new_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            try:
                self.analyzer = TelemetryAnalyzer(path); self.analyzer.load()
                self.df = self.analyzer.df; self._setup_ui()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def _clear_all(self):
        for v in self.vars.values():
            v.set(False)
        self.update_plot()

    def _export(self):
        f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if f: self.fig.savefig(f, dpi=300, bbox_inches='tight')

    def update_plot(self):
        self.ax.clear()
        self.cursor_line = self.cursor_text = None
        selected = [c for c, v in self.vars.items() if v.get()]
        
        if not selected:
            self.ax.text(0.5, 0.5, "No Sensors Selected", ha='center', va='center', color='gray')
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.canvas_widget.draw_idle()
            return

        palette = sns.color_palette("husl", n_colors=len(selected))
        for i, col in enumerate(selected):
            color = palette[i]
            self.ax.plot(self.df.index, self.df[col], label=col, color=color, linewidth=1.2)
            rid = self._get_rail_type(col)
            if rid:
                low, high = self.rail_specs[rid]
                self.ax.axhline(y=low, color=color, ls='--', alpha=0.3)
                self.ax.axhline(y=high, color=color, ls='--', alpha=0.3)
        
        self.ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize='x-small')
        self.fig.tight_layout()
        self.canvas_widget.draw_idle()

if __name__ == "__main__":
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if path:
        try:
            a = TelemetryAnalyzer(path); a.load()
            root.deiconify(); TelemetryApp(root, a); root.mainloop()
        except Exception as e:
            messagebox.showerror("Launch Error", f"Could not open file: {e}")
            root.destroy()
            os._exit(1)
    else: 
        root.destroy()
        os._exit(0)
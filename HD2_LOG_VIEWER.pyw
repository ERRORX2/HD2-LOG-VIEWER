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
import threading
import urllib.request
import urllib.error
import webbrowser

import re

GROUPS_FILE = "groups.json"
CURRENT_VERSION = "1.3.3"  # BUMP
GITHUB_REPO = "ERRORX2/HD2-LOG-VIEWER"


def save_config(groups_dict: Dict, is_dark: bool, multi_mode: bool = False, delta_mode: bool = False,
                ignored_version: str = "", updates_disabled: bool = False, time_mode: bool = False,
                thresholds: Dict = None, heatmap_mode: bool = False):
    config = {
        "groups": groups_dict,
        "settings": {
            "dark_mode": is_dark,
            "multi_mode": multi_mode,
            "delta_mode": delta_mode,
            "ignored_version": ignored_version,
            "updates_disabled": updates_disabled,
            "time_mode": time_mode,
            "heatmap_mode": heatmap_mode,
            "thresholds": thresholds or {}
        }
    }
    try:
        with open(GROUPS_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except:
        pass

def load_config() -> Tuple[Dict, bool, bool, bool, str, bool, bool, Dict, bool]:
    if not Path(GROUPS_FILE).exists():
        return {}, False, False, False, "", False, False, {}, False
    try:
        with open(GROUPS_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and "groups" in data and "settings" in data:
                sets = data["settings"]
                return (data["groups"],
                        sets.get("dark_mode", False),
                        sets.get("multi_mode", False),
                        sets.get("delta_mode", False),
                        sets.get("ignored_version", ""),
                        sets.get("updates_disabled", False),
                        sets.get("time_mode", False),
                        sets.get("thresholds", {}),
                        sets.get("heatmap_mode", False))
            return data if isinstance(data, dict) else {}, False, False, False, "", False, False, {}, False
    except:
        return {}, False, False, False, "", False, False, {}, False


def check_for_updates(root: tk.Tk, ignored_version: str = "", updates_disabled: bool = False,
                      on_ignore=None, on_disable=None, silent: bool = True):
    """
    silent=True  -> startup check, skips notification if version is ignored or updates are disabled.
    silent=False -> manual ⟳ check, always gives feedback.
    """
    def _check():
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "HD2-LOG-VIEWER"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            latest = data.get("tag_name", "").lstrip("v")
            current = CURRENT_VERSION.lstrip("v")

            if not latest:
                if not silent:
                    root.after(0, lambda: _toast("⚠️ Could not read release info"))
                return

            if latest == current:
                if not silent:
                    root.after(0, lambda: _toast("✅ You're on the latest version!"))
                return

            # A newer version exists — check if we should suppress
            if silent:
                if updates_disabled:
                    return
                if latest == ignored_version.lstrip("v"):
                    return

            release_url = data.get("html_url", "")
            root.after(0, lambda: _notify(latest, release_url))

        except Exception:
            if not silent:
                root.after(0, lambda: _toast("⚠️ Could not reach GitHub"))

    def _toast(msg: str):
        try:
            root._app_ref.show_toast(msg)
        except Exception:
            pass

    def _notify(latest_version: str, release_url: str):
        dialog = tk.Toplevel(root)
        dialog.title("Update Available")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        # Pull theme from app reference
        try:
            is_dark = root._app_ref.is_dark
        except Exception:
            is_dark = False
        bg     = "#121212" if is_dark else "#f8f9fa"
        fg     = "#e0e0e0" if is_dark else "#212529"
        accent = "#1f6aa5" if is_dark else "#3498db"

        dialog.configure(bg=bg)

        root.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() // 2) - 200
        y = root.winfo_y() + (root.winfo_height() // 2) - 105
        dialog.geometry(f"400x210+{x}+{y}")

        tk.Label(dialog, text="🆕 Update Available",
                 font=('Segoe UI', 12, 'bold'), bg=bg, fg=accent).pack(pady=(18, 4))
        tk.Label(dialog, text=f"Current: v{CURRENT_VERSION}   →   Latest: v{latest_version}",
                 font=('Segoe UI', 10), bg=bg, fg=fg).pack(pady=(0, 14))

        btn_f = tk.Frame(dialog, bg=bg)
        btn_f.pack(pady=4)

        def _open():
            webbrowser.open(release_url)
            dialog.destroy()

        def _ignore():
            if on_ignore:
                on_ignore(latest_version)
            dialog.destroy()

        def _disable():
            if on_disable:
                on_disable()
            dialog.destroy()

        ttk.Button(btn_f, text="View Release Page", command=_open,
                   style="Action.TButton").grid(row=0, column=0, padx=6, pady=4, sticky='ew')
        ttk.Button(btn_f, text=f"Ignore v{latest_version}",
                   command=_ignore).grid(row=0, column=1, padx=6, pady=4, sticky='ew')
        ttk.Button(btn_f, text="Never Notify Me", command=_disable
                   ).grid(row=1, column=0, columnspan=2, padx=6, pady=2, sticky='ew')

        tk.Label(dialog,
                 text='"Ignore" skips this version only. "Never Notify" disables all future checks.',
                 font=('Segoe UI', 8), bg=bg, fg="gray").pack(pady=(8, 0))

    threading.Thread(target=_check, daemon=True).start()


class TelemetryAnalyzer:
    # Candidate column names to check for time data, in priority order
    TIME_COLUMN_CANDIDATES = ['time', 'date', 'timestamp', 'elapsed', 'clock', '#']
    # Common time formats to attempt parsing
    TIME_FORMATS = ['%H:%M:%S', '%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%H:%M']

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self.df: pd.DataFrame = pd.DataFrame()
        self.time_col: str = ""           # Name of detected time column, "" if none
        self.time_series = None           # Parsed datetime/timedelta Series, None if unavailable

    def load(self) -> None:
        success = False
        try:
            with open(self.path, 'r', encoding='latin-1', errors='ignore') as f:
                sample = f.readline() + f.readline()
                dialect = csv.Sniffer().sniff(sample)
                sep = dialect.delimiter
        except:
            sep = None

        for enc in ['utf-8-sig', 'latin-1', 'cp1252']:
            try:
                self.df = pd.read_csv(self.path, encoding=enc, sep=sep, on_bad_lines='skip',
                                      engine='python')
                if not self.df.empty:
                    success = True
                    break
            except:
                continue

        if not success:
            raise ValueError("File Load Failed")
        self.df.columns = [str(c).strip().replace('\ufeff', '') for c in self.df.columns]

        # Detect time column BEFORE numeric conversion so raw strings are still intact
        self._detect_time_column()

        for col in self.df.columns:
            if col == self.time_col:
                continue  # Keep time column as-is
            try:
                s = self.df[col].astype(str).str.replace(',', '.', regex=False)
                cleaned = s.str.replace(r'[^\d\.\-eE]', '', regex=True)
                self.df[col] = pd.to_numeric(cleaned, errors='coerce')
            except:
                continue

        while len(self.df) > 1:
            last_row = self.df.iloc[-1]
            numeric_cols = [c for c in self.df.columns if c != self.time_col]
            check = self.df.iloc[-1][numeric_cols]
            if (check == 0).sum() + check.isna().sum() > (len(numeric_cols) / 2):
                self.df = self.df.iloc[:-1]
            else:
                break
        self.df.ffill(inplace=True)

        # Keep time_series in sync with df after row trimming
        if self.time_series is not None:
            self.time_series = self.time_series.iloc[:len(self.df)].reset_index(drop=True)
        self.df = self.df.reset_index(drop=True)

    def _detect_time_column(self):
        """Find the best time column and parse it into self.time_series."""
        cols_lower = {c.lower().strip(): c for c in self.df.columns}

        # Find the first candidate column that exists
        found_col = None
        for candidate in self.TIME_COLUMN_CANDIDATES:
            if candidate in cols_lower:
                found_col = cols_lower[candidate]
                break

        if not found_col:
            return

        raw = self.df[found_col].astype(str).str.strip()

        # Try each known format
        for fmt in self.TIME_FORMATS:
            try:
                parsed = pd.to_datetime(raw, format=fmt, errors='coerce')
                if parsed.notna().sum() > len(parsed) * 0.8:  # 80%+ parsed successfully
                    self.time_col = found_col
                    # Convert to elapsed timedelta from first valid entry
                    first = parsed.dropna().iloc[0]
                    self.time_series = parsed - first
                    return
            except Exception:
                continue

        # Last resort: try pandas auto-inference
        try:
            parsed = pd.to_datetime(raw, errors='coerce')
            if parsed.notna().sum() > len(parsed) * 0.8:
                self.time_col = found_col
                first = parsed.dropna().iloc[0]
                self.time_series = parsed - first
        except Exception:
            pass


class TelemetryApp:
    def __init__(self, root: tk.Tk, analyzer: TelemetryAnalyzer):
        self.root = root
        self.analyzer = analyzer
        self.df = analyzer.df

        self.ref_df = None
        self.compare_mode = False

        (self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode,
         self.ignored_version, self.updates_disabled, self.time_mode,
         saved_thresholds, self.heatmap_mode) = load_config()

        self.vars = {}
        self.cb_widgets = {}
        self.header_widgets = {}
        self.group_map = {}
        self.cursor_lines = []
        self.cursor_text = None
        self.filter_active = False

        # Default thresholds — these are the fallback values
        self._default_temp_limits = {
            'HOTSPOT': 95.0, 'HOT SPOT': 95.0,
            'GPU': 88.0,
            'VRAM': 95.0, 'MEMORY': 95.0,
            'VRM': 110.0,
            'CORE': 95.0,
            'TDIE': 95.0, 'TCTL': 95.0,
            'CCD': 90.0, 'CCX': 90.0,
            'IOD': 95.0,
            'SOCKET': 95.0,
            'COOLANT': 45.0, 'LIQUID': 45.0, 'WATER': 45.0,
            'SSD': 65.0, 'NVME': 65.0, 'HDD': 55.0,
            'CHIPSET': 90.0, 'PCH': 90.0,
            'MOSFET': 110.0, 'CHOKE': 110.0,
        }
        self._default_volt_rails = {
            '+12V': (11.4, 12.6),
            '+5V':  (4.75, 5.25),
            '+3.3V': (3.13, 3.46),
        }
        self._default_misc = {
            'cpu_volt_lo': 0.8,  'cpu_volt_hi': 1.55,
            'gpu_volt_max': 1.1,
            'dram_volt_lo': 1.1, 'dram_volt_hi': 1.55,
            'fan_min_rpm': 400.0,
            'cpu_power_max': 300.0,
            'gpu_power_max': 500.0,
            'total_power_max': 600.0,
            'latency_max_ms': 50.0,
            'frametime_max_ms': 100.0,
            'fps_min': 10.0,
            'coolant_max': 45.0,
        }

        # Apply saved overrides on top of defaults
        self.temp_limits  = {**self._default_temp_limits,
                             **saved_thresholds.get('temp_limits', {})}
        self.volt_rails   = {k: tuple(v) for k, v in
                             {**self._default_volt_rails,
                              **saved_thresholds.get('volt_rails', {})}.items()}
        misc              = {**self._default_misc,
                             **saved_thresholds.get('misc', {})}
        self.cpu_volt_range  = (misc['cpu_volt_lo'],  misc['cpu_volt_hi'])
        self.gpu_volt_max    = misc['gpu_volt_max']
        self.dram_volt_range = (misc['dram_volt_lo'], misc['dram_volt_hi'])
        self.fan_min_rpm     = misc['fan_min_rpm']
        self.cpu_power_max   = misc['cpu_power_max']
        self.gpu_power_max   = misc['gpu_power_max']
        self.total_power_max = misc['total_power_max']
        self.latency_max_ms  = misc['latency_max_ms']
        self.frametime_max_ms = misc['frametime_max_ms']
        self.fps_min         = misc['fps_min']

        # Expose app reference so check_for_updates can call show_toast
        self.root._app_ref = self

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._setup_ui()
        self._apply_theme_colors()
        self.update_plot()

        # Silent startup update check
        check_for_updates(
            self.root,
            ignored_version=self.ignored_version,
            updates_disabled=self.updates_disabled,
            on_ignore=self._on_ignore_version,
            on_disable=self._on_disable_updates,
            silent=True
        )

    def _on_close(self):
        plt.close('all')
        self.root.quit()
        self.root.destroy()
        os._exit(0)

    def _open_limits_editor(self):
        """Open a scrollable dialog to view and edit all detection thresholds."""
        is_dark = self.is_dark
        bg  = "#121212" if is_dark else "#f8f9fa"
        fg  = "#e0e0e0" if is_dark else "#212529"
        bg2 = "#1e1e1e" if is_dark else "#ffffff"
        accent = "#1f6aa5" if is_dark else "#3498db"

        dialog = tk.Toplevel(self.root)
        dialog.title("Detection Limits Editor")
        dialog.geometry("560x680")
        dialog.minsize(480, 500)
        dialog.grab_set()
        dialog.configure(bg=bg)
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 280
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 340
        dialog.geometry(f"560x680+{x}+{y}")

        # Scrollable body
        outer = tk.Frame(dialog, bg=bg)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg=bg)
        win_id = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units")))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        entries = {}  # key -> StringVar

        def section(text):
            tk.Label(body, text=text, bg=bg, fg=accent,
                     font=('Segoe UI', 9, 'bold')).pack(fill=tk.X, pady=(14, 2), padx=4)
            tk.Frame(body, bg=accent, height=1).pack(fill=tk.X, padx=4)

        def row(label, key, value, unit=""):
            f = tk.Frame(body, bg=bg)
            f.pack(fill=tk.X, pady=2, padx=8)
            tk.Label(f, text=label, bg=bg, fg=fg, font=('Segoe UI', 9),
                     width=30, anchor='w').pack(side=tk.LEFT)
            var = tk.StringVar(value=str(value))
            entries[key] = var
            tk.Entry(f, textvariable=var, width=8, bg=bg2, fg=fg,
                     insertbackground=fg, relief='flat',
                     highlightthickness=1, highlightbackground="#444").pack(side=tk.LEFT, padx=4)
            if unit:
                tk.Label(f, text=unit, bg=bg, fg="#888",
                         font=('Segoe UI', 8)).pack(side=tk.LEFT)

        def range_row(label, key_lo, key_hi, val_lo, val_hi, unit=""):
            f = tk.Frame(body, bg=bg)
            f.pack(fill=tk.X, pady=2, padx=8)
            tk.Label(f, text=label, bg=bg, fg=fg, font=('Segoe UI', 9),
                     width=30, anchor='w').pack(side=tk.LEFT)
            var_lo = tk.StringVar(value=str(val_lo))
            var_hi = tk.StringVar(value=str(val_hi))
            entries[key_lo] = var_lo
            entries[key_hi] = var_hi
            tk.Entry(f, textvariable=var_lo, width=6, bg=bg2, fg=fg,
                     insertbackground=fg, relief='flat',
                     highlightthickness=1, highlightbackground="#444").pack(side=tk.LEFT, padx=(4,1))
            tk.Label(f, text="–", bg=bg, fg=fg).pack(side=tk.LEFT, padx=1)
            tk.Entry(f, textvariable=var_hi, width=6, bg=bg2, fg=fg,
                     insertbackground=fg, relief='flat',
                     highlightthickness=1, highlightbackground="#444").pack(side=tk.LEFT, padx=(1,4))
            if unit:
                tk.Label(f, text=unit, bg=bg, fg="#888",
                         font=('Segoe UI', 8)).pack(side=tk.LEFT)

        # Temperature limits ────────────────────────────────────────────────
        section("Temperature Limits (°C)")
        temp_display = [
            ("GPU Core",         "GPU"),
            ("GPU Hotspot",      "HOTSPOT"),
            ("GPU VRAM",         "VRAM"),
            ("GPU VRM",          "VRM"),
            ("CPU Core",         "CORE"),
            ("CPU Tdie/Tctl",    "TDIE"),
            ("CPU CCD/CCX",      "CCD"),
            ("CPU Socket",       "SOCKET"),
            ("Coolant/Liquid",   "COOLANT"),
            ("SSD/NVMe",         "SSD"),
            ("HDD",              "HDD"),
            ("Chipset/PCH",      "CHIPSET"),
            ("MOSFET/Choke",     "MOSFET"),
        ]
        for label, key in temp_display:
            if key in self.temp_limits:
                row(label, f"temp_{key}", self.temp_limits[key], "°C")

        # Voltage rails ─────────────────────────────────────────────────────
        section("Voltage Rails — Safe Range (V)")
        range_row("+12V Rail",   "rail_12v_lo",   "rail_12v_hi",   *self.volt_rails['+12V'],  "V")
        range_row("+5V Rail",    "rail_5v_lo",    "rail_5v_hi",    *self.volt_rails['+5V'],   "V")
        range_row("+3.3V Rail",  "rail_33v_lo",   "rail_33v_hi",   *self.volt_rails['+3.3V'], "V")

        # Component voltages ────────────────────────────────────────────────
        section("Component Voltages")
        range_row("CPU Vcore",   "cpu_volt_lo", "cpu_volt_hi", *self.cpu_volt_range,  "V")
        range_row("DRAM Voltage","dram_volt_lo","dram_volt_hi",*self.dram_volt_range, "V")
        row("GPU Core Voltage max", "gpu_volt_max", self.gpu_volt_max, "V")

        # Power limits ──────────────────────────────────────────────────────
        section("Power Draw Limits (W)")
        row("CPU max power",    "cpu_power_max",   self.cpu_power_max,   "W")
        row("GPU max power",    "gpu_power_max",   self.gpu_power_max,   "W")
        row("Total system max", "total_power_max", self.total_power_max, "W")

        # Frame / latency ───────────────────────────────────────────────────
        section("Frame Timing & Latency")
        row("Frame time spike (1% high)", "frametime_max_ms", self.frametime_max_ms, "ms")
        row("Min FPS (0.1% low)",         "fps_min",          self.fps_min,          "FPS")
        row("Latency max",                "latency_max_ms",   self.latency_max_ms,   "ms")

        # Misc ──────────────────────────────────────────────────────────────
        section("Miscellaneous")
        row("Fan stall threshold", "fan_min_rpm", self.fan_min_rpm, "RPM")

        # Buttons + live save ───────────────────────────────────────────────
        btn_f = tk.Frame(dialog, bg=bg)
        btn_f.pack(fill=tk.X, padx=10, pady=10)

        status_var = tk.StringVar(value="")
        status_lbl = tk.Label(dialog, textvariable=status_var, bg=bg,
                              font=('Segoe UI', 8), fg="#888")
        status_lbl.pack(pady=(0, 4))

        def _try_apply(show_toast=False, close=False):
            """Parse all fields and apply if all valid. Called on every keystroke."""
            try:
                # Temperatures
                for label, key in temp_display:
                    if f"temp_{key}" in entries:
                        val = float(entries[f"temp_{key}"].get())
                        self.temp_limits[key] = val
                        if key == 'HOTSPOT':  self.temp_limits['HOT SPOT'] = val
                        if key == 'TDIE':     self.temp_limits['TCTL'] = val
                        if key == 'CCD':      self.temp_limits['CCX'] = val
                        if key == 'COOLANT':
                            self.temp_limits['LIQUID'] = val
                            self.temp_limits['WATER']  = val
                        if key == 'SSD':      self.temp_limits['NVME'] = val
                        if key == 'CHIPSET':  self.temp_limits['PCH']  = val
                        if key == 'MOSFET':   self.temp_limits['CHOKE'] = val

                # Volt rails
                self.volt_rails['+12V']  = (float(entries['rail_12v_lo'].get()),
                                             float(entries['rail_12v_hi'].get()))
                self.volt_rails['+5V']   = (float(entries['rail_5v_lo'].get()),
                                             float(entries['rail_5v_hi'].get()))
                self.volt_rails['+3.3V'] = (float(entries['rail_33v_lo'].get()),
                                             float(entries['rail_33v_hi'].get()))

                # Component voltages
                self.cpu_volt_range  = (float(entries['cpu_volt_lo'].get()),
                                        float(entries['cpu_volt_hi'].get()))
                self.dram_volt_range = (float(entries['dram_volt_lo'].get()),
                                        float(entries['dram_volt_hi'].get()))
                self.gpu_volt_max    = float(entries['gpu_volt_max'].get())

                # Power
                self.cpu_power_max   = float(entries['cpu_power_max'].get())
                self.gpu_power_max   = float(entries['gpu_power_max'].get())
                self.total_power_max = float(entries['total_power_max'].get())

                # Frame / latency
                self.frametime_max_ms = float(entries['frametime_max_ms'].get())
                self.fps_min          = float(entries['fps_min'].get())
                self.latency_max_ms   = float(entries['latency_max_ms'].get())

                # Misc
                self.fan_min_rpm = float(entries['fan_min_rpm'].get())

                # All parsed OK — save and update
                self._save_config()
                self._build_checklist()
                self._apply_theme_colors()
                if self.filter_active:
                    self._apply_issue_filter()
                else:
                    self._filter_sensors()
                self.update_plot()
                status_var.set("✔ Saved")
                status_lbl.config(fg="#2ecc71")

                if show_toast:
                    self.show_toast("Limits saved")
                if close:
                    dialog.destroy()

            except ValueError:
                # Field mid-edit — silently ignore, just flag status
                status_var.set("⚠ Invalid value — fix before closing")
                status_lbl.config(fg="#e74c3c")

        # Bind live save to every entry var — fires on each keystroke
        def _on_trace(*_):
            _try_apply()

        for var in entries.values():
            var.trace_add("write", _on_trace)

        def _apply():
            _try_apply(show_toast=True, close=True)

        def _reset():
            if messagebox.askyesno("Reset to Defaults",
                    "Reset all limits to their default values?", parent=dialog):
                self.temp_limits  = dict(self._default_temp_limits)
                self.volt_rails   = dict(self._default_volt_rails)
                misc = self._default_misc
                self.cpu_volt_range   = (misc['cpu_volt_lo'],  misc['cpu_volt_hi'])
                self.gpu_volt_max     = misc['gpu_volt_max']
                self.dram_volt_range  = (misc['dram_volt_lo'], misc['dram_volt_hi'])
                self.fan_min_rpm      = misc['fan_min_rpm']
                self.cpu_power_max    = misc['cpu_power_max']
                self.gpu_power_max    = misc['gpu_power_max']
                self.total_power_max  = misc['total_power_max']
                self.latency_max_ms   = misc['latency_max_ms']
                self.frametime_max_ms = misc['frametime_max_ms']
                self.fps_min          = misc['fps_min']
                self._save_config()
                self._build_checklist()
                self._apply_theme_colors()
                self.update_plot()
                self.show_toast("Limits reset to defaults")
                dialog.destroy()

        ttk.Button(btn_f, text="Save & Apply", command=_apply,
                   style="Action.TButton").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,4))
        ttk.Button(btn_f, text="Reset to Defaults",
                   command=_reset).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4,4))
        ttk.Button(btn_f, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4,0))

    def _on_ignore_version(self, version: str):
        self.ignored_version = version
        self._save_config()
        self.show_toast(f"Ignored v{version} — you'll be notified about future versions")

    def _on_disable_updates(self):
        self.updates_disabled = True
        self._save_config()
        self.show_toast("Update notifications disabled")

    def _save_config(self):
        misc = {
            'cpu_volt_lo':     self.cpu_volt_range[0],
            'cpu_volt_hi':     self.cpu_volt_range[1],
            'gpu_volt_max':    self.gpu_volt_max,
            'dram_volt_lo':    self.dram_volt_range[0],
            'dram_volt_hi':    self.dram_volt_range[1],
            'fan_min_rpm':     self.fan_min_rpm,
            'cpu_power_max':   self.cpu_power_max,
            'gpu_power_max':   self.gpu_power_max,
            'total_power_max': self.total_power_max,
            'latency_max_ms':  self.latency_max_ms,
            'frametime_max_ms': self.frametime_max_ms,
            'fps_min':         self.fps_min,
            'coolant_max':     self.temp_limits.get('COOLANT', 45.0),
        }
        thresholds = {
            'temp_limits': self.temp_limits,
            'volt_rails':  {k: list(v) for k, v in self.volt_rails.items()},
            'misc':        misc,
        }
        save_config(self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode,
                    self.ignored_version, self.updates_disabled, self.time_mode, thresholds,
                    self.heatmap_mode)

    def show_toast(self, message: str, duration: int = 2000):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        bg = "#333333" if self.is_dark else "#2c3e50"
        fg = "white"
        label = tk.Label(toast, text=message, bg=bg, fg=fg, padx=20, pady=10,
                         font=('Segoe UI', 10, 'bold'), relief='flat')
        label.pack()
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (toast.winfo_width() // 2)
        y = self.root.winfo_y() + self.root.winfo_height() - 150
        toast.geometry(f"+{x}+{y}")
        self.root.after(duration, toast.destroy)

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self._apply_theme_colors()
        self.update_plot()
        self._save_config()

    def _toggle_multi(self):
        self.multi_mode = not self.multi_mode
        self.multi_btn.config(text="📊 Multi: ON" if self.multi_mode else "📊 Multi: OFF")
        self.update_plot()
        self._save_config()

    def _toggle_delta(self):
        self.delta_mode = not self.delta_mode
        self.delta_btn.config(text="Δ Delta: ON" if self.delta_mode else "Δ Delta: OFF")
        self.update_plot()
        self._save_config()

    def _toggle_time(self):
        if not self.analyzer.time_col:
            self.show_toast("No time column detected in this CSV")
            return
        self.time_mode = not self.time_mode
        self.time_btn.config(text="🕒 Time: ON" if self.time_mode else "🕒 Time: OFF")
        self.update_plot()
        self._save_config()

    def _toggle_heatmap(self):
        self.heatmap_mode = not self.heatmap_mode
        self.heatmap_btn.config(text="🌡 Heatmap: ON" if self.heatmap_mode else "🌡 Heatmap: OFF")
        self.update_plot()
        self._save_config()

    def _draw_heatmap(self, sel: list):
        """Draw a heatmap with absolute thresholds for known sensor types,
        per-sensor normalization as fallback, and discrete color bands."""
        is_dark = self.is_dark
        bg_color   = "#121212" if is_dark else "white"
        text_color = "white"   if is_dark else "black"
        grid_color = "#2a2a2a" if is_dark else "#cccccc"

        self.fig.clear()
        self._clear_cursors()
        self.fig.patch.set_facecolor(bg_color)

        if not sel:
            ax = self.fig.add_subplot(111)
            ax.set_facecolor("#1e1e1e" if is_dark else "#fdfdfd")
            ax.text(0.5, 0.5, "No Sensors Selected", ha='center', va='center', color='gray')
            self.canvas_widget.draw_idle()
            return

        import matplotlib.colors as mcolors
        import matplotlib.cm as mcm

        # Green covers 0.0–0.60 (safe zone), yellow 0.60–0.85 (warning), dark red 0.85–1.0 (critical)
        band_colors = [
            (0.00, '#1a7a3a'),   # deep green — safe
            (0.55, '#2ecc71'),   # bright green — still safe
            (0.60, '#f1c40f'),   # yellow — warning starts here
            (0.80, '#e67e22'),   # orange — approaching limit
            (0.85, '#922b21'),   # dark red — at limit
            (1.00, '#641e16'),   # very dark red — over limit
        ]
        cmap_discrete = mcolors.LinearSegmentedColormap.from_list(
            'threshold_map',
            [(pos, col) for pos, col in band_colors],
            N=512)

        def _get_limit(col: str):
            """Return the configured danger threshold for this sensor, or None."""
            raw  = col.upper()
            name = raw.replace(" ", "")

            # Temperature
            if any(x in name for x in ['TEMP', '°C', 'HOTSPOT', 'TDIE', 'TCTL']):
                matched_limit = None
                matched_len   = 0
                for key, limit in self.temp_limits.items():
                    key_norm = key.upper().replace(" ", "")
                    if key_norm in name and len(key_norm) > matched_len:
                        matched_limit = limit
                        matched_len   = len(key_norm)
                return matched_limit if matched_limit is not None else 90.0

            # Percentage load
            if '[%]' in raw and any(x in raw for x in ['USAGE', 'LOAD']):
                return 95.0

            # Power
            if '[W]' in raw and 'LIMIT' not in raw and 'STATIC' not in raw:
                if 'CPU' in raw: return self.cpu_power_max
                if 'GPU' in raw: return self.gpu_power_max
                if 'TOTAL' in raw: return self.total_power_max

            # Frame time
            if any(x in raw for x in ['FRAME TIME', 'FRAMETIME']):
                return self.frametime_max_ms

            # Latency
            if any(x in raw for x in ['LATENCY', 'GPU BUSY', 'CPU BUSY']):
                return self.latency_max_ms

            return None  # No known limit — fall back to relative

        def _normalize_row(col: str, data: np.ndarray) -> np.ndarray:
            """
            Map values to 0–1 where:
              0.00–0.60  = green  (well below limit)
              0.60–0.85  = yellow (approaching limit, ~75–100% of limit)
              0.85–1.00  = dark red (at or above limit)
            """
            limit = _get_limit(col)
            raw   = col.upper()

            if limit is not None and limit > 0:
                # Scale: 0 at 0, 0.85 at limit, 1.0 at limit * 1.15 (15% over)
                # This puts the yellow band from 75%–100% of limit,
                # and dark red kicks in at the limit itself
                warn_start = limit * 0.75   # yellow starts here
                # Piecewise: below warn_start → 0..0.60, warn_start..limit → 0.60..0.85, above limit → 0.85..1.0
                result = np.where(
                    data <= warn_start,
                    0.60 * (data / warn_start),                         # green zone
                    np.where(
                        data <= limit,
                        0.60 + 0.25 * ((data - warn_start) / (limit - warn_start)),  # yellow zone
                        np.clip(0.85 + 0.15 * ((data - limit) / (limit * 0.15)), 0.85, 1.0)  # red zone
                    )
                )
                return np.clip(result, 0.0, 1.0)

            # Voltage rails — green within tolerance, yellow approaching limits, red outside
            for rail, (lo, hi) in self.volt_rails.items():
                if rail in raw and not any(x in raw for x in ['GPU PCIE', 'PCIE', '12VHPWR', 'INPUT']):
                    centre   = (lo + hi) / 2
                    half_tol = (hi - lo) / 2
                    # Distance from centre, normalized: 0=perfect, 1=at limit edge
                    dist = np.abs(data - centre) / half_tol
                    return np.clip(dist * 0.85, 0.0, 1.0)  # red only if out of spec

            # Fan RPM — inverted: low is bad (stall = red)
            if 'RPM' in raw or 'FAN SPEED' in raw:
                mx = data.max()
                if mx > 0:
                    inv = 1.0 - np.clip(data / mx, 0.0, 1.0)
                    return inv * 0.85   # cap at yellow unless stalled
                return np.zeros_like(data)

            # FPS — inverted: low FPS = red, use fps_min as the danger floor
            if 'FPS' in raw or 'FRAMERATE' in raw:
                safe_fps = self.fps_min * 6   # e.g. 60 if fps_min=10
                return np.clip(1.0 - (data / max(safe_fps, 1.0)), 0.0, 0.95)

            # Fallback: relative per-sensor, capped at 0.85 (never full red)
            mn, mx = data.min(), data.max()
            if mx > mn:
                return np.clip((data - mn) / (mx - mn) * 0.85, 0.0, 0.85)
            return np.zeros_like(data)

        matrix = []
        labels = []
        raw_data_map = {}

        for col in sel:
            data = self.df[col].ffill().fillna(0).values.astype(float)
            raw_data_map[col] = data
            matrix.append(_normalize_row(col, data))
            # Strip unit brackets for cleaner labels
            short = col
            for bracket in ['[°C]', '[%]', '[MHz]', '[W]', '[V]', '[RPM]',
                            '[ms]', '[FPS]', '[A]', '[MB]', '[GB]']:
                short = short.replace(bracket, '').strip()
            labels.append(short[:45])

        matrix = np.array(matrix)  # (n_sensors, n_samples)

        x_vals, ts, use_time = self._get_x_axis()

        ax = self.fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        extent = [x_vals[0], x_vals[-1], len(sel) - 0.5, -0.5]
        ax.imshow(matrix, aspect='auto', cmap=cmap_discrete,
                  vmin=0, vmax=1, extent=extent,
                  interpolation='nearest', origin='upper')

        # Separator lines between rows — makes individual sensors easy to track
        for i in range(1, len(sel)):
            ax.axhline(i - 0.5, color=grid_color, lw=1.0)

        # Y axis labels
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, color=text_color, fontsize=7)
        ax.tick_params(axis='y', length=0)

        # X axis
        ax.tick_params(axis='x', colors=text_color, labelsize=8)
        if use_time:
            import matplotlib.ticker as ticker
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(
                lambda v, _: self._format_elapsed(v)))
            ax.tick_params(axis='x', labelrotation=30)

        # Colorbar with meaningful labels
        sm = plt.cm.ScalarMappable(cmap=cmap_discrete,
                                   norm=mcolors.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = self.fig.colorbar(sm, ax=ax, fraction=0.015, pad=0.01)
        cbar.set_ticks([0.0, 0.30, 0.60, 0.85, 1.0])
        cbar.set_ticklabels(['Safe', 'Normal', 'Warning', 'At Limit', 'Critical'])
        cbar.ax.yaxis.set_tick_params(color=text_color, labelsize=7)
        cbar.outline.set_edgecolor(text_color)
        for lbl in cbar.ax.get_yticklabels():
            lbl.set_color(text_color)

        ax.set_xlabel("Elapsed Time" if use_time else "Record Index",
                      color=text_color, fontsize=8)
        ax.set_title("Sensor Heatmap  —  Green: safe  |  Yellow: approaching limit  |  Red: at/above limit",
                     color=text_color, fontsize=8, pad=6)

        self.fig.tight_layout()
        self.canvas_widget.draw_idle()

        # Store for mouse hover
        self._heatmap_matrix_raw = raw_data_map
        self._heatmap_sel        = sel
        self._heatmap_x_vals     = x_vals

    def _get_ref_x_axis(self):
        """Returns x values for the reference df, independent of current df length."""
        if self.ref_df is not None:
            return self.ref_df.index.values
        return None

    def _get_x_axis(self):
        """Returns (x_values, x_labels, use_time) for plotting and tooltip use."""
        if self.time_mode and self.analyzer.time_series is not None:
            ts = self.analyzer.time_series
            # Guard: if lengths still differ for any reason, fall back to index
            if len(ts) != len(self.df):
                return self.df.index.values, None, False
            x_vals = ts.dt.total_seconds().values
            return x_vals, ts, True
        return self.df.index.values, None, False

    def _format_elapsed(self, seconds: float) -> str:
        """Format elapsed seconds as H:MM:SS."""
        try:
            s = int(seconds)
            h, rem = divmod(s, 3600)
            m, sec = divmod(rem, 60)
            return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
        except Exception:
            return str(seconds)

    def _toggle_compare(self):
        if self.ref_df is None:
            messagebox.showinfo("Comparison", "Please set a reference first by clicking 'Set Ref'")
            return
        self.compare_mode = not self.compare_mode
        self.compare_btn.config(text="🔍 Compare: ON" if self.compare_mode else "🔍 Compare: OFF")
        self.update_plot()

    def _set_reference(self):
        self.ref_df = self.df.copy()
        self.show_toast("Current log saved as Reference")
        self.compare_btn.config(state="normal")

    def _apply_theme_colors(self):
        bg, fg = ("#121212", "#e0e0e0") if self.is_dark else ("#f8f9fa", "#212529")
        accent = "#3498db" if not self.is_dark else "#1f6aa5"

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background=bg, foreground=fg, fieldbackground=bg, font=('Segoe UI', 9))
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabelframe", background=bg, foreground=fg, bordercolor="#444444")
        self.style.configure("TLabelframe.Label", background=bg, foreground=accent, font=('Segoe UI', 9, 'bold'))
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", padding=3)
        self.style.configure("Action.TButton", font=('Segoe UI', 9, 'bold'))
        self.style.configure("Delete.TButton", foreground="#ff4d4d", font=('Segoe UI', 9, 'bold'))
        self.style.configure("Issue.TButton", foreground="#ff9800", font=('Segoe UI', 9, 'bold'))
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.configure("Alert.TCheckbutton", background=bg, foreground="#ff4d4d", font=('Segoe UI', 9, 'bold'))
        self.style.map("TCheckbutton", background=[('active', bg)])

        self.root.configure(bg=bg)
        self.canvas_checklist.configure(bg=bg)
        self.scroll_frame.configure(bg=bg)
        self.preset_canvas.configure(bg=bg)
        self.grp_f.configure(bg=bg)

        for hdr in self.header_widgets.values():
            hdr.configure(bg=bg, fg="#3498db" if self.is_dark else "#2c3e50")

    def _is_critical(self, col: str) -> bool:
        name = col.upper().replace(" ", "")
        raw  = col.upper()
        series = self.df[col].dropna()
        if series.empty:
            return False

        # Exclusions ────────────────────────────────────────────────────────
        # Never flag configured limits, headroom values, control signals, or
        # unit-only columns that carry no diagnostic meaning on their own
        EXCLUDE_RAW = [
            '[MB]', '[GB]', '[A]', 'PWM', '(STATIC)',
            'THERMAL LIMIT', 'POWER LIMIT', 'TDC LIMIT', 'PPT LIMIT', 'EDC LIMIT',
            'FREQUENCY LIMIT', 'CLOCK LIMIT',
        ]
        EXCLUDE_NAME = [
            'FREQUENCYLIMIT', 'ACCUMULATED', 'EFFECTIVECLOCK', 'REQUESTEDCLOCK',
            'TARGETTEMP', 'LIMITTEMP', 'THERMALLIMIT', 'POWERLIMIT',
            'CURRENTLIMIT', 'TDCLIMIT', 'PPTLIMIT', 'EDCLIMIT',
        ]
        if any(x in raw for x in EXCLUDE_RAW) or any(x in name for x in EXCLUDE_NAME):
            return False

        # Frame timing / FPS ────────────────────────────────────────────────
        if any(x in raw for x in ['FRAME TIME', 'FRAMETIME']):
            if '1% HIGH' in raw and '0.1%' not in raw:
                return series.max() > self.frametime_max_ms
            return False

        if any(x in raw for x in ['FRAMERATE', ' FPS', 'FRAMES PER SECOND']):
            if '0.1%' in raw and 'LOW' in raw and 'PRESENTED' not in raw:
                return series.min() <= self.fps_min and series.max() > 0
            return False

        # Render pipeline latency
        if any(x in raw for x in ['LATENCY', 'RENDER TIME', 'PRESENT TIME',
                                   'GPU BUSY', 'CPU BUSY', 'DISPLAY LATENCY']):
            return series.max() > self.latency_max_ms

        # All other [ms] columns (animation error etc.) — skip
        if '[MS]' in raw:
            return False

        # Active throttling flags ───────────────────────────────────────────
        # HWinfo logs these as boolean-like 0/1 or 0/100 when throttling is active
        THROTTLE_KW = ['THROTTLING', 'RELIABILITY', 'PERFCAP']
        if any(x in raw for x in THROTTLE_KW):
            return series.max() >= 0.9

        # Performance Limit [Yes/No] — only flag thermal and power limiters
        # Skip utilization, SLI sync, voltage limiters (too noisy / system-specific)
        if 'YES/NO' in raw:
            if any(x in raw for x in ['THERMAL', 'POWER']) and 'PERFORMANCE LIMIT' in raw:
                return series.max() >= 1.0
            return False

        # [%] columns ───────────────────────────────────────────────────────
        if '[%]' in raw:
            if 'LIMIT' in raw:
                return False   # headroom values, not breach indicators
            # Memory load (system RAM or GPU VRAM)
            if any(x in raw for x in ['MEMORY', 'RAM']) and any(x in raw for x in ['USAGE', 'LOAD']):
                return series.max() >= 95.0
            # Skip video engine / decode / encode usage — not diagnostic
            if any(x in raw for x in ['DECODE', 'ENCODE', 'VIDEO', 'MEDIA']):
                return False

        # WHEA / hardware errors ────────────────────────────────────────────
        # Any nonzero WHEA count = system instability regardless of hardware type
        WHEA_KW = ['WHEA', 'MACHINE CHECK', 'MCE', 'MCA']
        if any(x in raw for x in WHEA_KW):
            return series.max() > 0

        # Drive / memory errors ─────────────────────────────────────────────
        ERROR_KW = ['ECC', 'BAD SECTOR', 'REALLOCATED', 'PENDING SECTOR',
                    'UNCORRECTABLE', 'CRC ERROR']
        if any(x in raw for x in ERROR_KW):
            return series.max() > 0

        # Power draw ────────────────────────────────────────────────────────
        # Only flag actual draw sensors, not configured limits or static values
        if '[W]' in raw and 'STATIC' not in raw and 'LIMIT' not in raw and 'PPT' not in raw:
            if 'CPU' in raw and series.max() > self.cpu_power_max:
                return True
            if 'GPU' in raw and series.max() > self.gpu_power_max:
                return True
            if 'TOTAL' in raw and series.max() > self.total_power_max:
                return True

        # CPU power limit saturation ────────────────────────────────────────
        # Flag if actual CPU power draw is consistently at or above its own PPT limit
        # This means the CPU is power-throttling regardless of temp
        if 'CPU PPT' in raw and '[W]' in raw and 'LIMIT' not in raw:
            ppt_limit_col = next(
                (c for c in self.df.columns if 'PPT' in c.upper() and 'LIMIT' in c.upper()
                 and '[W]' in c.upper() and 'CPU' in c.upper()), None)
            if ppt_limit_col is not None:
                limit_val = self.df[ppt_limit_col].dropna().mean()
                if limit_val > 0 and series.mean() >= limit_val * 0.98:
                    return True

        # Voltage rails (+12V, +5V, +3.3V) ────────────────────────────────
        RAIL_SKIP = ['GPU PCIE', 'PCIE', '12VHPWR', 'INPUT']
        for rail, (low, high) in self.volt_rails.items():
            if rail in raw:
                if any(x.upper() in raw for x in RAIL_SKIP):
                    continue
                after = raw.split(rail)[-1].upper()
                if any(x in after for x in ['INPUT', 'PCIE', 'HPWR']):
                    continue
                return series.min() < low or series.max() > high

        if any(x in raw for x in ['VCORE', 'CPU CORE VOLTAGE', 'VID']):
            lo, hi = self.cpu_volt_range
            return series.min() < lo or series.max() > hi

        if any(x in raw for x in ['VCORE', 'CPU CORE VOLTAGE']):
            if series.max() - series.min() > 0.3:
                return True

        if any(x in raw for x in ['DRAM VOLTAGE', 'DIMM VOLTAGE', 'MEMORY VOLTAGE',
                                   'VDIMM', 'VDDQ']):
            lo, hi = self.dram_volt_range
            return series.min() < lo or series.max() > hi

        if 'GPU CORE VOLTAGE' in raw and 'GFX' not in raw and 'VDDCR' not in raw:
            return series.max() > self.gpu_volt_max

        # Clock speed instability ───────────────────────────────────────────
        # If a CPU/GPU clock has very high variance relative to its mean it may
        # indicate throttling even when temperatures look acceptable.
        # Only check primary clocks, not per-core or effective/requested variants
        if any(x in raw for x in ['CPU CLOCK', 'GPU CLOCK', 'CORE CLOCK']):
            if not any(x in raw for x in ['EFFECTIVE', 'REQUESTED', 'CORE #', 'LIMIT']):
                if series.mean() > 100 and (series.std() / series.mean()) > 0.35:
                    return True

        # Fan speeds ───────────────────────────────────────────────────────
        # Only flag if the fan was actually spinning (not zero-RPM curve or disconnected)
        if any(x in raw for x in ['RPM', 'FAN SPEED']):
            if series.max() > self.fan_min_rpm and series.min() < self.fan_min_rpm:
                return True

        # Temperatures ─────────────────────────────────────────────────────
        if any(x in name for x in ['TEMP', '°C', 'HOTSPOT', 'TDIE', 'TCTL']):
            matched_limit = None
            matched_len   = 0
            for key, limit in self.temp_limits.items():
                key_norm = key.upper().replace(" ", "")
                if key_norm in name and len(key_norm) > matched_len:
                    matched_limit = limit
                    matched_len   = len(key_norm)
            if matched_limit is not None:
                return series.max() >= matched_limit
            return series.max() >= 90.0   # conservative fallback for unknown sensors

        # Drive health (SMART) ──────────────────────────────────────────────
        SMART_KW = ['HEALTH', 'WEAR LEVEL', 'REMAINING LIFE', 'ENDURANCE REMAINING']
        if any(x in raw for x in SMART_KW):
            return series.min() < 10      # <10% remaining life

        # Physical memory load ──────────────────────────────────────────────
        if 'PHYSICAL MEMORY' in raw and 'LOAD' in raw:
            return series.max() >= 95.0

        return False

    def _setup_ui(self):
        self.root.title(f"Log Viewer Pro v{CURRENT_VERSION} - {self.analyzer.path.name}")
        self.root.geometry("1600x950")
        self.root.minsize(1000, 700)
        for widget in self.root.winfo_children():
            widget.destroy()

        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.left = ttk.Frame(self.paned, padding="10")
        self.paned.add(self.left, weight=1)

        top = ttk.Frame(self.left)
        top.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(top, text="DASHBOARD", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        ttk.Button(top, text="◐", command=self._toggle_theme, width=3).pack(side=tk.RIGHT)
        # Update check button in the top bar
        ttk.Button(top, text="⟳", command=self._manual_update_check, width=3).pack(side=tk.RIGHT, padx=(0, 2))

        mode_f = ttk.LabelFrame(self.left, text=" View Settings ", padding=8)
        mode_f.pack(fill=tk.X, pady=5)

        btn_row1 = ttk.Frame(mode_f)
        btn_row1.pack(fill=tk.X, pady=2)
        self.multi_btn = ttk.Button(btn_row1, text="📊 Multi: ON" if self.multi_mode else "📊 Multi: OFF", command=self._toggle_multi)
        self.multi_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self.delta_btn = ttk.Button(btn_row1, text="Δ Delta: ON" if self.delta_mode else "Δ Delta: OFF", command=self._toggle_delta)
        self.delta_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        btn_row2 = ttk.Frame(mode_f)
        btn_row2.pack(fill=tk.X, pady=2)
        ttk.Button(btn_row2, text="📌 Set Ref", command=self._set_reference).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self.compare_btn = ttk.Button(btn_row2, text="🔍 Compare: OFF", command=self._toggle_compare,
                                      state="disabled" if self.ref_df is None else "normal")
        self.compare_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        btn_row3 = ttk.Frame(mode_f)
        btn_row3.pack(fill=tk.X, pady=2)
        has_time = bool(self.analyzer.time_col)
        time_label = "🕒 Time: ON" if self.time_mode else "🕒 Time: OFF"
        self.time_btn = ttk.Button(btn_row3, text=time_label, command=self._toggle_time,
                                   state="normal" if has_time else "disabled")
        self.time_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self.heatmap_btn = ttk.Button(btn_row3, text="🌡 Heatmap: ON" if self.heatmap_mode else "🌡 Heatmap: OFF",
                                      command=self._toggle_heatmap)
        self.heatmap_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        if not has_time:
            ttk.Label(mode_f, text="No time column detected", foreground="gray",
                      font=('Segoe UI', 7)).pack(pady=(0, 2))

        preset_master_f = ttk.LabelFrame(self.left, text=" Presets ", padding=5)
        preset_master_f.pack(fill=tk.X, pady=5)

        self.preset_canvas = tk.Canvas(preset_master_f, height=140, highlightthickness=0)
        self.preset_scroll = ttk.Scrollbar(preset_master_f, orient="vertical", command=self.preset_canvas.yview)
        self.grp_f = tk.Frame(self.preset_canvas)

        self.grp_f.columnconfigure(0, weight=1)
        self.preset_window = self.preset_canvas.create_window((0, 0), window=self.grp_f, anchor="nw")

        def _on_canvas_resize(event):
            self.preset_canvas.itemconfig(self.preset_window, width=event.width)
        self.preset_canvas.bind("<Configure>", _on_canvas_resize)
        self.grp_f.bind("<Configure>", lambda e: self.preset_canvas.configure(scrollregion=self.preset_canvas.bbox("all")))
        self.preset_canvas.configure(yscrollcommand=self.preset_scroll.set)
        self.preset_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.preset_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_preset_mw(event):
            self.preset_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.preset_canvas.bind("<Enter>", lambda _: self.preset_canvas.bind_all("<MouseWheel>", _on_preset_mw))
        self.preset_canvas.bind("<Leave>", lambda _: self.preset_canvas.unbind_all("<MouseWheel>"))

        self._refresh_group_buttons()

        ent_f = ttk.Frame(self.left)
        ent_f.pack(fill=tk.X, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(ent_f, textvariable=self.name_var).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(ent_f, text="Save", command=self._save_group, width=8).pack(side=tk.RIGHT)
        ttk.Button(self.left, text="📋 Import from Clipboard", command=self._import_from_clipboard).pack(fill=tk.X, pady=2)

        search_f = ttk.LabelFrame(self.left, text=" Sensor Selection ", padding=8)
        search_f.pack(fill=tk.BOTH, expand=True, pady=5)

        self.filter_btn = ttk.Button(search_f, text="🚨 Detect Out-of-Spec Issues", style="Issue.TButton", command=self._toggle_filter)
        self.filter_btn.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(search_f, text="⚙ Edit Detection Limits", command=self._open_limits_editor).pack(fill=tk.X, pady=(0, 8))

        search_top = ttk.Frame(search_f)
        search_top.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_top, text="🔍 Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._filter_sensors())
        ttk.Entry(search_top, textvariable=self.search_var).pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.canv_f = ttk.Frame(search_f)
        self.canv_f.pack(fill=tk.BOTH, expand=True)
        self.canvas_checklist = tk.Canvas(self.canv_f, highlightthickness=0)
        self.sc_checklist = ttk.Scrollbar(self.canv_f, orient="vertical", command=self.canvas_checklist.yview)
        self.scroll_frame = tk.Frame(self.canvas_checklist)
        self._checklist_window = self.canvas_checklist.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        def _refresh_scrollregion():
            self.root.update_idletasks()
            w = self.canvas_checklist.winfo_width()
            if w > 1:
                self.canvas_checklist.itemconfig(self._checklist_window, width=w)
            bbox = self.canvas_checklist.bbox("all")
            if bbox:
                self.canvas_checklist.configure(scrollregion=bbox)

        self._sash_after_id = None
        def _on_checklist_canvas_configure(e):
            if self._sash_after_id is not None:
                self.canvas_checklist.after_cancel(self._sash_after_id)
            self._sash_after_id = self.canvas_checklist.after(100, _refresh_scrollregion)

        def _on_sash_release(e):
            self.canvas_checklist.after(50, _refresh_scrollregion)

        self.scroll_frame.bind("<Configure>", lambda e: _refresh_scrollregion())
        self.canvas_checklist.bind("<Configure>", _on_checklist_canvas_configure)
        # Bind to paned sash release — fires once when user lets go of the divider
        self.paned.bind("<ButtonRelease-1>", _on_sash_release)
        self.canvas_checklist.configure(yscrollcommand=self.sc_checklist.set)

        def _on_checklist_mw(event):
            self.canvas_checklist.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas_checklist.bind("<Enter>", lambda _: self.canvas_checklist.bind_all("<MouseWheel>", _on_checklist_mw))
        self.canvas_checklist.bind("<Leave>", lambda _: self.canvas_checklist.unbind_all("<MouseWheel>"))

        self.canvas_checklist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sc_checklist.pack(side=tk.RIGHT, fill=tk.Y)
        self._build_checklist()

        btn_frame = ttk.Frame(self.left)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="New CSV", command=self._import_new_csv).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_frame, text="Clear", command=self._clear_all).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_frame, text="Export PNG", command=self._export, style="Action.TButton").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        self.right = ttk.Frame(self.paned, padding="5")
        self.paned.add(self.right, weight=4)

        self.fig = plt.figure(figsize=(10, 6))
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self.right)
        self.canvas_widget.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas_widget.mpl_connect('axes_leave_event', self._on_mouse_leave)

        toolbar_f = ttk.Frame(self.right)
        toolbar_f.pack(side=tk.TOP, fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_widget, toolbar_f, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side=tk.LEFT)
        self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _manual_update_check(self):
        """Called when the user clicks ⟳ — always gives feedback, respects ignore/disable via on_ignore/on_disable."""
        self.show_toast("Checking for updates...")
        check_for_updates(
            self.root,
            ignored_version="",          # Manual check always shows the dialog even for ignored versions
            updates_disabled=False,      # Manual check always runs regardless of disabled flag
            on_ignore=self._on_ignore_version,
            on_disable=self._on_disable_updates,
            silent=False
        )

    def _build_checklist(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.header_widgets = {}
        self.cb_widgets = {}
        self.group_map = {}
        for col in self.df.columns:
            cat = self._get_category(col)
            if cat not in self.group_map:
                self.group_map[cat] = []
            self.group_map[cat].append(col)

        ui_order = ["Temperatures (°C)", "Utilization / Load (%)", "Clock Speeds (MHz)", "Power / Wattage (W)", "Voltage (V)", "Fan Speeds (RPM)"]
        self.sorted_cats = [c for c in ui_order if c in self.group_map] + \
                           sorted([c for c in self.group_map.keys() if c not in ui_order])

        for cat in self.sorted_cats:
            h = tk.Label(self.scroll_frame, text=f" {cat.upper()} ", font=('Segoe UI', 8, 'bold'), anchor="w")
            h.pack(fill=tk.X, pady=(8, 2))
            self.header_widgets[cat] = h
            for col in sorted(self.group_map[cat]):
                v = self.vars.get(col, tk.BooleanVar(value=False))
                self.vars[col] = v
                cb = ttk.Checkbutton(self.scroll_frame, text=col, variable=v, command=self.update_plot,
                                     style="Alert.TCheckbutton" if self._is_critical(col) else "TCheckbutton")
                cb.pack(anchor=tk.W, padx=12)
                self.cb_widgets[col] = cb

    def _get_category(self, n: str) -> str:
        u = n.upper()
        if '°C' in u or 'TEMP' in u: return "Temperatures (°C)"
        if '%' in u or 'USAGE' in u or 'UTILIZATION' in u: return "Utilization / Load (%)"
        if 'MHZ' in u or 'CLOCK' in u: return "Clock Speeds (MHz)"
        if ' W' in u or 'WATT' in u or 'POWER' in u: return "Power / Wattage (W)"
        if ' V' in u or 'VOLT' in u or 'VCORE' in u: return "Voltage (V)"
        if 'RPM' in u or 'FAN' in u: return "Fan Speeds (RPM)"
        if any(x in u for x in ['GPU', 'NVIDIA', 'GEFORCE', 'AMD', 'RTX', 'GTX']): return "Graphics Card (GPU)"
        if any(x in u for x in ['CPU', 'CORE ', 'AMD RYZEN', 'INTEL']): return "Processor (CPU)"
        return "Other Sensors"

    def _toggle_filter(self):
        self.filter_active = not self.filter_active
        if self.filter_active:
            self.filter_btn.config(text="✅ Showing All Sensors")
            self._apply_issue_filter()
        else:
            self.filter_btn.config(text="🚨 Detect Out-of-Spec Issues")
            self._filter_sensors()
        self.canvas_checklist.yview_moveto(0)

    def _apply_issue_filter(self):
        for h in self.header_widgets.values():
            h.pack_forget()
        for cb in self.cb_widgets.values():
            cb.pack_forget()
        self.scroll_frame.config(height=1)
        self.scroll_frame.pack_propagate(True)
        for cat in self.sorted_cats:
            if cat not in self.group_map:
                continue
            issues = [col for col in self.group_map[cat] if self._is_critical(col)]
            if issues:
                self.header_widgets[cat].pack(fill=tk.X, pady=(8, 0))
                for col in sorted(issues):
                    self.cb_widgets[col].pack(anchor=tk.W, padx=12)
        self.root.update_idletasks()
        new_bbox = self.canvas_checklist.bbox("all")
        self.canvas_checklist.configure(scrollregion=new_bbox)
        self.canvas_checklist.yview_moveto(0)

    def _refresh_group_buttons(self):
        for w in self.grp_f.winfo_children():
            w.destroy()
        self.grp_f.columnconfigure(0, weight=1)
        self.grp_f.columnconfigure(1, weight=0)
        self.grp_f.columnconfigure(2, weight=0)
        self.grp_f.columnconfigure(3, weight=0)

        for i, g in enumerate(sorted(self.custom_groups.keys())):
            btn = ttk.Button(self.grp_f, text=g, command=lambda n=g: self._apply_group(n))
            btn.grid(row=i, column=0, sticky='ew', pady=1, padx=(1, 2))
            sh_btn = ttk.Button(self.grp_f, text="📋", width=3, command=lambda n=g: self._share_group(n))
            sh_btn.grid(row=i, column=1, pady=1, padx=1)
            rn_btn = ttk.Button(self.grp_f, text="✏️", width=3, command=lambda n=g: self._rename_group(n))
            rn_btn.grid(row=i, column=2, pady=1, padx=1)
            del_btn = ttk.Button(self.grp_f, text="✕", width=3, command=lambda n=g: self._delete_group(n), style="Delete.TButton")
            del_btn.grid(row=i, column=3, pady=1, padx=(1, 4))

    def _share_group(self, n):
        data = {"name": n, "sensors": self.custom_groups[n]}
        self.root.clipboard_clear()
        self.root.clipboard_append(json.dumps(data))
        self.show_toast(f"Copied '{n}'")

    def _prompt_rename(self, title: str, initial: str, on_confirm) -> None:
        """Generic rename dialog. Calls on_confirm(new_name) if valid and confirmed."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.attributes("-topmost", True)

        try:
            is_dark = self.is_dark
        except Exception:
            is_dark = False
        bg = "#121212" if is_dark else "#f8f9fa"
        fg = "#e0e0e0" if is_dark else "#212529"
        accent = "#1f6aa5" if is_dark else "#3498db"

        dialog.configure(bg=bg)
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 60
        dialog.geometry(f"350x120+{x}+{y}")

        tk.Label(dialog, text="Enter new name:", bg=bg, fg=fg,
                 font=('Segoe UI', 10)).pack(pady=(16, 4))

        name_var = tk.StringVar(value=initial)
        entry = ttk.Entry(dialog, textvariable=name_var, width=35)
        entry.pack(padx=20)
        entry.select_range(0, tk.END)
        entry.focus_set()

        btn_f = tk.Frame(dialog, bg=bg)
        btn_f.pack(pady=10)

        def _confirm():
            new_name = name_var.get().strip()
            if not new_name:
                return
            dialog.destroy()
            on_confirm(new_name)

        ttk.Button(btn_f, text="Confirm", command=_confirm,
                   style="Action.TButton").grid(row=0, column=0, padx=6)
        ttk.Button(btn_f, text="Cancel",
                   command=dialog.destroy).grid(row=0, column=1, padx=6)

        dialog.bind("<Return>", lambda e: _confirm())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _rename_group(self, old_name: str):
        def _do_rename(new_name: str):
            if new_name == old_name:
                return
            if new_name in self.custom_groups:
                messagebox.showwarning("Name Taken",
                    f"A preset named '{new_name}' already exists.\nPlease choose a different name.")
                # Re-open so user can try again
                self._rename_group(old_name)
                return
            self.custom_groups[new_name] = self.custom_groups.pop(old_name)
            self._save_config()
            self._refresh_group_buttons()
            self.show_toast(f"Renamed to '{new_name}'")

        self._prompt_rename("Rename Preset", old_name, _do_rename)

    def _import_from_clipboard(self):
        try:
            data = json.loads(self.root.clipboard_get())
            if "name" not in data or "sensors" not in data:
                raise ValueError("Missing fields")

            imported_name = data["name"]
            sensors = data["sensors"]

            if imported_name not in self.custom_groups:
                # No conflict — import directly
                self.custom_groups[imported_name] = sensors
                self._save_config()
                self._refresh_group_buttons()
                self.show_toast(f"Imported: '{imported_name}'")
                return

            # Conflict — ask user what to do
            dialog = tk.Toplevel(self.root)
            dialog.title("Name Already Exists")
            dialog.resizable(False, False)
            dialog.grab_set()
            dialog.attributes("-topmost", True)

            try:
                is_dark = self.is_dark
            except Exception:
                is_dark = False
            bg = "#121212" if is_dark else "#f8f9fa"
            fg = "#e0e0e0" if is_dark else "#212529"

            dialog.configure(bg=bg)
            self.root.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 190
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 70
            dialog.geometry(f"380x140+{x}+{y}")

            tk.Label(dialog,
                     text=f"A preset named '{imported_name}' already exists.\nWhat would you like to do?",
                     bg=bg, fg=fg, font=('Segoe UI', 10), justify='center').pack(pady=(16, 10))

            btn_f = tk.Frame(dialog, bg=bg)
            btn_f.pack()

            def _overwrite():
                dialog.destroy()
                self.custom_groups[imported_name] = sensors
                self._save_config()
                self._refresh_group_buttons()
                self.show_toast(f"Overwritten: '{imported_name}'")

            def _rename():
                dialog.destroy()
                def _do_import(new_name: str):
                    if new_name in self.custom_groups:
                        messagebox.showwarning("Name Taken",
                            f"A preset named '{new_name}' already exists.\nPlease choose a different name.")
                        _rename()
                        return
                    self.custom_groups[new_name] = sensors
                    self._save_config()
                    self._refresh_group_buttons()
                    self.show_toast(f"Imported as '{new_name}'")
                self._prompt_rename("Rename Imported Preset", imported_name, _do_import)

            ttk.Button(btn_f, text="Overwrite", command=_overwrite,
                       style="Action.TButton").grid(row=0, column=0, padx=6, pady=2)
            ttk.Button(btn_f, text="Rename Import", command=_rename
                       ).grid(row=0, column=1, padx=6, pady=2)
            ttk.Button(btn_f, text="Cancel", command=dialog.destroy
                       ).grid(row=0, column=2, padx=6, pady=2)

        except Exception:
            messagebox.showerror("Error", "Invalid Clipboard Data")

    def _delete_group(self, n):
        if messagebox.askyesno("Delete", f"Delete '{n}'?"):
            if n in self.custom_groups:
                del self.custom_groups[n]
                self._save_config()
                self._refresh_group_buttons()

    def _apply_group(self, n):
        for v in self.vars.values():
            v.set(False)
        for s in self.custom_groups.get(n, []):
            if s in self.vars:
                self.vars[s].set(True)
        self.update_plot()

    def _save_group(self):
        name = self.name_var.get().strip()
        sel = [c for c, v in self.vars.items() if v.get()]
        if not name or not sel:
            return
        if name in self.custom_groups:
            if not messagebox.askyesno("Overwrite Preset",
                    f"A preset named '{name}' already exists.\nDo you want to overwrite it?"):
                return
        self.custom_groups[name] = sel
        self._save_config()
        self._refresh_group_buttons()
        self.name_var.set("")
        self.show_toast(f"Saved: '{name}'")

    def _filter_sensors(self):
        if self.filter_active:
            return
        q = self.search_var.get().upper().replace(" ", "")
        for h in self.header_widgets.values():
            h.pack_forget()
        for cb in self.cb_widgets.values():
            cb.pack_forget()
        for cat in self.sorted_cats:
            if cat not in self.group_map:
                continue
            m = [col for col in self.group_map[cat] if q in col.upper().replace(" ", "")]
            if m:
                self.header_widgets[cat].pack(fill=tk.X, pady=(8, 0))
                for col in sorted(m):
                    self.cb_widgets[col].pack(anchor=tk.W, padx=12)
        self.scroll_frame.update_idletasks()
        self.canvas_checklist.configure(scrollregion=self.canvas_checklist.bbox("all"))
        self.canvas_checklist.yview_moveto(0)

    def _import_new_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            try:
                new_analyzer = TelemetryAnalyzer(path)
                new_analyzer.load()
                self.analyzer = new_analyzer
                self.df = self.analyzer.df
                new_cols = set(self.df.columns)
                for col, var in list(self.vars.items()):
                    if col not in new_cols:
                        var.set(False)
                self.filter_active = False
                self._setup_ui()
                self._apply_theme_colors()
                self.update_plot()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _clear_all(self):
        for v in self.vars.values():
            v.set(False)
        self.update_plot()

    def _export(self):
        f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if f:
            self.fig.savefig(f, dpi=300, bbox_inches='tight', facecolor=self.fig.get_facecolor())

    def _clear_cursors(self):
        for line in self.cursor_lines:
            try:
                line.remove()
            except:
                pass
        self.cursor_lines = []
        if self.cursor_text:
            try:
                self.cursor_text.remove()
            except:
                pass
            self.cursor_text = None

    def _on_mouse_leave(self, event):
        self._clear_cursors()
        self.canvas_widget.draw_idle()

    def _on_mouse_move(self, event):
        if event.inaxes is None:
            self._on_mouse_leave(event)
            return
        try:
            # Heatmap tooltip
            if self.heatmap_mode and hasattr(self, '_heatmap_sel') and self._heatmap_sel:
                x_vals = self._heatmap_x_vals
                raw_x  = event.xdata
                raw_y  = event.ydata
                idx = int(np.argmin(np.abs(x_vals - raw_x)))
                sensor_idx = int(round(raw_y))
                if 0 <= idx < len(x_vals) and 0 <= sensor_idx < len(self._heatmap_sel):
                    col = self._heatmap_sel[sensor_idx]
                    val = self._heatmap_matrix_raw[col][idx]
                    self._clear_cursors()
                    for ax in self.fig.axes:
                        self.cursor_lines.append(ax.axvline(x=x_vals[idx],
                            color='white' if self.is_dark else 'gray', ls='--', alpha=0.5))
                    x_label = self._format_elapsed(x_vals[idx]) if self.time_mode else f"Rec: {idx}"
                    txt = f"{x_label}\n{col[:35]}: {val:.2f}"
                    self.cursor_text = self.fig.text(0.01, 0.99, txt, va='top', ha='left',
                        bbox=dict(boxstyle='round',
                                  facecolor='#252525' if self.is_dark else 'white', alpha=0.85),
                        fontsize=8, color='white' if self.is_dark else 'black')
                    self.canvas_widget.draw_idle()
                return

            x_vals, ts, use_time = self._get_x_axis()
            raw_x = event.xdata

            if use_time:
                idx = int(np.argmin(np.abs(x_vals - raw_x)))
            else:
                idx = int(round(raw_x))

            if idx < 0 or idx >= len(self.df):
                self._on_mouse_leave(event)
                return

            self._clear_cursors()
            for ax in self.fig.axes:
                plot_x = x_vals[idx] if use_time else idx
                l = ax.axvline(x=plot_x, color='white' if self.is_dark else 'gray', ls='--', alpha=0.5)
                self.cursor_lines.append(l)

            sel = [c for c, v in self.vars.items() if v.get() and c in self.df.columns]

            if use_time:
                elapsed = x_vals[idx]
                time_str = self._format_elapsed(elapsed)
                txt = f"Time: {time_str}\n"
            else:
                txt = f"Rec: {idx}\n"

            if self.delta_mode and len(sel) >= 2:
                d_val = abs(self.df.iloc[idx][sel[0]] - self.df.iloc[idx][sel[1]])
                txt += f"Δ Delta: {d_val:.2f}\n---\n"
            txt += "\n".join([f"{c}: {self.df.iloc[idx][c]:.2f}" for c in sel])
            self.cursor_text = self.fig.text(0.01, 0.99, txt, va='top', ha='left',
                bbox=dict(boxstyle='round', facecolor='#252525' if self.is_dark else 'white', alpha=0.8),
                fontsize=8, color='white' if self.is_dark else 'black')
            self.canvas_widget.draw_idle()
        except Exception:
            pass

    def update_plot(self):
        self.fig.clear()
        self._clear_cursors()
        is_dark = self.is_dark
        bg_color, text_color, grid_color = ("#121212", "white", "#333333") if is_dark else ("white", "black", "#e0e0e0")
        self.fig.patch.set_facecolor(bg_color)
        sel = [c for c, v in self.vars.items() if v.get() and c in self.df.columns]

        # Heatmap mode — takes priority over all other modes
        if self.heatmap_mode:
            self._draw_heatmap(sel)
            return

        x_vals, ts, use_time = self._get_x_axis()
        ref_x = self._get_ref_x_axis()

        def _fmt_xticks(ax):
            if not use_time:
                return
            # Format X tick labels as MM:SS or H:MM:SS
            def _fmt(val, _):
                return self._format_elapsed(val)
            import matplotlib.ticker as ticker
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(_fmt))
            ax.tick_params(axis='x', labelrotation=30)

        if self.delta_mode and self.multi_mode:
            ax = self.fig.add_subplot(111)
            ax.set_facecolor("#1e1e1e" if is_dark else "#fdfdfd")
            ax.text(0.5, 0.5, "Turn off Multi Mode to use Delta",
                    ha='center', va='center', color='#ffcc00', fontsize=12, fontweight='bold')
            self.canvas_widget.draw_idle()
            return

        if not sel:
            ax = self.fig.add_subplot(111)
            ax.set_facecolor("#1e1e1e" if is_dark else "#fdfdfd")
            ax.text(0.5, 0.5, "No Sensors Selected", ha='center', va='center', color='gray')
            self.canvas_widget.draw_idle()
            return

        def _draw_spec_zones(ax, col_name):
            u_name = col_name.upper()
            for rail, (low, high) in self.volt_rails.items():
                if rail in u_name:
                    ax.axhspan(low - 0.2, low, color='red', alpha=0.1, zorder=0)
                    ax.axhspan(high, high + 0.2, color='red', alpha=0.1, zorder=0)
                    ax.axhline(y=low, color='#ff4d4d', ls='--', lw=1, alpha=0.5, zorder=1)
                    ax.axhline(y=high, color='#ff4d4d', ls='--', lw=1, alpha=0.5, zorder=1)
                    break

        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        if self.multi_mode:
            category_groups = {}
            for col in sel:
                cat = self._get_category(col)
                if cat not in category_groups:
                    category_groups[cat] = []
                category_groups[cat].append(col)

            active_cats = [c for c in self.sorted_cats if c in category_groups]
            num_plots = len(active_cats)
            axes = []
            color_idx = 0

            for i, cat_name in enumerate(active_cats):
                ax = self.fig.add_subplot(num_plots, 1, i + 1, sharex=axes[0] if axes else None)
                axes.append(ax)
                ax.set_facecolor("#1e1e1e" if is_dark else "#fdfdfd")
                ax.set_ylabel(cat_name, color=text_color, fontsize=8, fontweight='bold')

                for col_name in category_groups[cat_name]:
                    main_color = colors[color_idx % len(colors)]
                    if self.compare_mode and self.ref_df is not None and col_name in self.ref_df.columns:
                        ax.plot(ref_x, self.ref_df[col_name],
                                ls='--', lw=1, alpha=0.4, color=main_color, zorder=2)
                    series = self.df[col_name].dropna()
                    stats = f"Min: {series.min():.1f}  Avg: {series.mean():.1f}  Max: {series.max():.1f}"
                    ax.plot(x_vals, self.df[col_name], label=f"{col_name}\n{stats}",
                            lw=1.5, color=main_color, zorder=3)
                    _draw_spec_zones(ax, col_name)
                    color_idx += 1

                ax.grid(True, linestyle=':', alpha=0.4, color=grid_color)
                ax.tick_params(colors=text_color, labelsize=8)
                _fmt_xticks(ax)
                l = ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fontsize='x-small', frameon=False)
                if l:
                    for t in l.get_texts():
                        t.set_color(text_color)
            for ax in axes[:-1]:
                plt.setp(ax.get_xticklabels(), visible=False)
            self.fig.subplots_adjust(right=0.80, hspace=0.3)

        elif self.delta_mode and len(sel) >= 2:
            ax = self.fig.add_subplot(111)
            ax.set_facecolor("#1e1e1e" if is_dark else "#fdfdfd")
            s1, s2 = self.df[sel[0]], self.df[sel[1]]
            delta = (s1 - s2).abs()

            if self.compare_mode and self.ref_df is not None and sel[0] in self.ref_df.columns and sel[1] in self.ref_df.columns:
                ref_delta = (self.ref_df[sel[0]] - self.ref_df[sel[1]]).abs()
                ax.plot(ref_x, ref_delta, color="#ffcc00", ls='--', alpha=0.3, lw=1, zorder=1)

            def _stats_label(col, series):
                s = series.dropna()
                return f"{col}\nMin: {s.min():.1f}  Avg: {s.mean():.1f}  Max: {s.max():.1f}"

            ax.plot(x_vals, s1, label=_stats_label(sel[0], s1), alpha=0.4, ls='--', zorder=2)
            ax.plot(x_vals, s2, label=_stats_label(sel[1], s2), alpha=0.4, ls='--', zorder=2)
            d_stats = f"Min: {delta.min():.1f}  Avg: {delta.mean():.1f}  Max: {delta.max():.1f}"
            ax.plot(x_vals, delta, label=f"Δ ({sel[0]} - {sel[1]})\n{d_stats}", color="#ffcc00", lw=2, zorder=3)
            ax.grid(True, linestyle=':', alpha=0.4, color=grid_color)
            ax.tick_params(colors=text_color, labelsize=8)
            _fmt_xticks(ax)
            l = ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize='x-small', frameon=False)
            if l:
                for t in l.get_texts():
                    t.set_color(text_color)
        else:
            ax = self.fig.add_subplot(111)
            ax.set_facecolor("#1e1e1e" if is_dark else "#fdfdfd")
            for i, col_name in enumerate(sel):
                main_color = colors[i % len(colors)]
                if self.compare_mode and self.ref_df is not None and col_name in self.ref_df.columns:
                    ax.plot(ref_x, self.ref_df[col_name],
                            ls='--', lw=1, alpha=0.4, color=main_color, zorder=2)
                series = self.df[col_name].dropna()
                stats = f"Min: {series.min():.1f}  Avg: {series.mean():.1f}  Max: {series.max():.1f}"
                ax.plot(x_vals, self.df[col_name], label=f"{col_name}\n{stats}",
                        lw=1.5, color=main_color, zorder=3)
                _draw_spec_zones(ax, col_name)

            ax.grid(True, linestyle=':', alpha=0.4, color=grid_color)
            ax.tick_params(colors=text_color, labelsize=8)
            _fmt_xticks(ax)
            l = ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize='x-small', frameon=False)
            if l:
                for t in l.get_texts():
                    t.set_color(text_color)

        self.fig.tight_layout()
        if self.multi_mode:
            self.fig.subplots_adjust(right=0.80)
        else:
            self.fig.subplots_adjust(right=0.82)
        self.canvas_widget.draw_idle()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if path:
        try:
            a = TelemetryAnalyzer(path)
            a.load()
            root.deiconify()
            TelemetryApp(root, a)
            root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            root.destroy()
    else:
        root.destroy()
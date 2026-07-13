import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
import matplotlib.cm as mcm
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class _NoHistoryToolbar(NavigationToolbar2Tk):
    toolitems = tuple(
        item for item in NavigationToolbar2Tk.toolitems
        if item[0] not in ('Back', 'Forward')
    )

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

import threading as _threading
import tkinter as _tk_module

def _safe_var_del(self):
    if _threading.current_thread() is _threading.main_thread():
        if self._tk.getboolean(self._tk.call("info", "exists", self._name)):
            self._tk.call("unset", "-nocomplain", self._name)

def _safe_image_del(self):
    if _threading.current_thread() is _threading.main_thread():
        try:
            self.tk.call("image", "delete", self.name)
        except Exception:
            pass

_tk_module.Variable.__del__ = _safe_var_del
_tk_module.Image.__del__ = _safe_image_del

_EXCLUDE_RAW = frozenset([
    '[MB]', '[GB]', '[A]', 'PWM', '(STATIC)',
    'THERMAL LIMIT', 'POWER LIMIT', 'TDC LIMIT', 'PPT LIMIT', 'EDC LIMIT',
    'FREQUENCY LIMIT', 'CLOCK LIMIT',
])
_EXCLUDE_NAME = frozenset([
    'FREQUENCYLIMIT', 'ACCUMULATED', 'EFFECTIVECLOCK', 'REQUESTEDCLOCK',
    'TARGETTEMP', 'LIMITTEMP', 'THERMALLIMIT', 'POWERLIMIT',
    'CURRENTLIMIT', 'TDCLIMIT', 'PPTLIMIT', 'EDCLIMIT',
])
_THROTTLE_KW   = ('THROTTLING', 'RELIABILITY', 'PERFCAP')
_SMART_KW      = ('REMAINING LIFE', 'WEAR LEVEL', 'ENDURANCE REMAINING')
_WHEA_KW       = ('WHEA', 'MACHINE CHECK', 'MCE', 'MCA')
_ERROR_KW      = ('ECC', 'BAD SECTOR', 'REALLOCATED', 'PENDING SECTOR',
                  'UNCORRECTABLE', 'CRC ERROR')
_RAIL_SKIP     = ('GPU PCIE', 'PCIE', '12VHPWR', 'INPUT')
_TEMP_TRIGGERS = frozenset(['TEMP', '°C', 'HOTSPOT', 'TDIE', 'TCTL'])

GROUPS_FILE         = "groups.json"
SENSOR_ALIASES_FILE = "sensor_aliases.json"
THEME_FILE          = "theme.json"

_DEFAULT_DARK_THEME = {
    "bg":      "#121212",
    "bg2":     "#1e1e1e",
    "bg3":     "#2a2a2a",
    "fg":      "#e0e0e0",
    "accent":  "#1f6aa5",
    "accent2": "#4f8ef7",

    "plot_c0": "#4f8ef7",
    "plot_c1": "#2ecc71",
    "plot_c2": "#e74c3c",
    "plot_c3": "#f39c12",
    "plot_c4": "#9b59b6",
    "plot_c5": "#1abc9c",

    "hm_safe":  "#1a7a3a",
    "hm_ok":    "#2ecc71",
    "hm_warn":  "#f1c40f",
    "hm_hot":   "#e67e22",
    "hm_crit":  "#922b21",
    "hm_max":   "#641e16",
}
_DEFAULT_LIGHT_THEME = {
    "bg":      "#f8f9fa",
    "bg2":     "#ffffff",
    "bg3":     "#e9ecef",
    "fg":      "#212529",
    "accent":  "#3498db",
    "accent2": "#1a5fa8",

    "plot_c0": "#1f6aa5",
    "plot_c1": "#27ae60",
    "plot_c2": "#c0392b",
    "plot_c3": "#d35400",
    "plot_c4": "#8e44ad",
    "plot_c5": "#16a085",

    "hm_safe":  "#1a7a3a",
    "hm_ok":    "#2ecc71",
    "hm_warn":  "#f1c40f",
    "hm_hot":   "#e67e22",
    "hm_crit":  "#922b21",
    "hm_max":   "#641e16",
}

BUILTIN_PRESETS = {
    "Dark (Default)":  {"_dark": True,  **_DEFAULT_DARK_THEME},
    "Light (Default)": {"_dark": False, **_DEFAULT_LIGHT_THEME},
    "Slate":    {"_dark": True,
                      "bg": "#0d1117", "bg2": "#161b22", "bg3": "#21262d",
                      "fg": "#c9d1d9", "accent": "#58a6ff", "accent2": "#79c0ff",
                      "plot_c0": "#58a6ff", "plot_c1": "#3fb950", "plot_c2": "#f85149",
                      "plot_c3": "#d29922", "plot_c4": "#bc8cff", "plot_c5": "#39c5cf",
                      "hm_safe": "#0d4429", "hm_ok": "#2ea043", "hm_warn": "#9e6a03",
                      "hm_hot":  "#bd561d", "hm_crit": "#8b1a1a", "hm_max": "#5a0f0f"},
    "Teal":  {"_dark": True,
                      "bg": "#002b36", "bg2": "#073642", "bg3": "#586e75",
                      "fg": "#839496", "accent": "#268bd2", "accent2": "#2aa198",
                      "plot_c0": "#268bd2", "plot_c1": "#2aa198", "plot_c2": "#dc322f",
                      "plot_c3": "#b58900", "plot_c4": "#6c71c4", "plot_c5": "#859900",
                      "hm_safe": "#073642", "hm_ok": "#859900", "hm_warn": "#b58900",
                      "hm_hot":  "#cb4b16", "hm_crit": "#dc322f", "hm_max": "#6e1717"},
    "Forest Green":          {"_dark": True,
                      "bg": "#1a2d1a", "bg2": "#243324", "bg3": "#2d3f2d",
                      "fg": "#d4e6d4", "accent": "#4caf50", "accent2": "#81c784",
                      "plot_c0": "#81c784", "plot_c1": "#4fc3f7", "plot_c2": "#ef9a9a",
                      "plot_c3": "#ffe082", "plot_c4": "#ce93d8", "plot_c5": "#80cbc4",
                      "hm_safe": "#1b5e20", "hm_ok": "#4caf50", "hm_warn": "#f9a825",
                      "hm_hot":  "#e65100", "hm_crit": "#b71c1c", "hm_max": "#7f0000"},
    "Crimson":    {"_dark": True,
                      "bg": "#1a0a0a", "bg2": "#2d1010", "bg3": "#3f1818",
                      "fg": "#f0d0d0", "accent": "#ef5350", "accent2": "#ff8a80",
                      "plot_c0": "#ff8a80", "plot_c1": "#69f0ae", "plot_c2": "#ffab40",
                      "plot_c3": "#40c4ff", "plot_c4": "#ea80fc", "plot_c5": "#ccff90",
                      "hm_safe": "#1a3d1a", "hm_ok": "#43a047", "hm_warn": "#fb8c00",
                      "hm_hot":  "#e53935", "hm_crit": "#b71c1c", "hm_max": "#7f0000"},
    "Steel":        {"_dark": True,
                      "bg": "#2e3440", "bg2": "#3b4252", "bg3": "#434c5e",
                      "fg": "#eceff4", "accent": "#88c0d0", "accent2": "#81a1c1",
                      "plot_c0": "#88c0d0", "plot_c1": "#a3be8c", "plot_c2": "#bf616a",
                      "plot_c3": "#ebcb8b", "plot_c4": "#b48ead", "plot_c5": "#8fbcbb",
                      "hm_safe": "#2d4a3e", "hm_ok": "#a3be8c", "hm_warn": "#ebcb8b",
                      "hm_hot":  "#d08770", "hm_crit": "#bf616a", "hm_max": "#7a3f43"},
    "Lime":      {"_dark": True,
                      "bg": "#272822", "bg2": "#3e3d32", "bg3": "#49483e",
                      "fg": "#f8f8f2", "accent": "#a6e22e", "accent2": "#66d9e8",
                      "plot_c0": "#a6e22e", "plot_c1": "#66d9e8", "plot_c2": "#f92672",
                      "plot_c3": "#fd971f", "plot_c4": "#ae81ff", "plot_c5": "#e6db74",
                      "hm_safe": "#1d3d1d", "hm_ok": "#a6e22e", "hm_warn": "#e6db74",
                      "hm_hot":  "#fd971f", "hm_crit": "#f92672", "hm_max": "#7a1234"},
    "Violet":        {"_dark": True,
                      "bg": "#0a0e1a", "bg2": "#0f1526", "bg3": "#1a2340",
                      "fg": "#e8f0ff", "accent": "#57c7d4", "accent2": "#a78bfa",
                      "plot_c0": "#57c7d4", "plot_c1": "#a78bfa", "plot_c2": "#34d399",
                      "plot_c3": "#f472b6", "plot_c4": "#fbbf24", "plot_c5": "#60a5fa",
                      "hm_safe": "#064e3b", "hm_ok": "#34d399", "hm_warn": "#fbbf24",
                      "hm_hot":  "#f97316", "hm_crit": "#f43f5e", "hm_max": "#7f1d1d"},
    "Lavender":         {"_dark": False,
                      "bg": "#fafafa", "bg2": "#ffffff", "bg3": "#e2e8f0",
                      "fg": "#1a202c", "accent": "#5a67d8", "accent2": "#667eea",
                      "plot_c0": "#5a67d8", "plot_c1": "#38a169", "plot_c2": "#e53e3e",
                      "plot_c3": "#dd6b20", "plot_c4": "#805ad5", "plot_c5": "#319795",
                      "hm_safe": "#1a7a3a", "hm_ok": "#2ecc71", "hm_warn": "#f1c40f",
                      "hm_hot":  "#e67e22", "hm_crit": "#922b21", "hm_max": "#641e16"},
    "Cobalt":     {"_dark": False,
                      "bg": "#ffffff", "bg2": "#f5f5f5", "bg3": "#e0e0e0",
                      "fg": "#000000", "accent": "#0072b2", "accent2": "#56b4e9",
                      "plot_c0": "#0072b2", "plot_c1": "#e69f00", "plot_c2": "#009e73",
                      "plot_c3": "#cc79a7", "plot_c4": "#56b4e9", "plot_c5": "#d55e00",
                      "hm_safe": "#009e73", "hm_ok": "#56b4e9", "hm_warn": "#e69f00",
                      "hm_hot":  "#d55e00", "hm_crit": "#cc79a7", "hm_max": "#0072b2"},
    "Neon Blue":    {"_dark": True,
                      "bg": "#161616", "bg2": "#262626", "bg3": "#393939",
                      "fg": "#f4f4f4", "accent": "#0f62fe", "accent2": "#4589ff",
                      "plot_c0": "#4589ff", "plot_c1": "#42be65", "plot_c2": "#fa4d56",
                      "plot_c3": "#f1c21b", "plot_c4": "#be95ff", "plot_c5": "#3ddbd9",
                      "hm_safe": "#044317", "hm_ok": "#42be65", "hm_warn": "#f1c21b",
                      "hm_hot":  "#ff832b", "hm_crit": "#fa4d56", "hm_max": "#750e13"},
    "Sand":     {"_dark": False,
                      "bg": "#f8f8f8", "bg2": "#ffffff", "bg3": "#e8e8e8",
                      "fg": "#2b2b2b", "accent": "#332288", "accent2": "#44aa99",
                      "plot_c0": "#332288", "plot_c1": "#44aa99", "plot_c2": "#aa3377",
                      "plot_c3": "#88ccee", "plot_c4": "#ddcc77", "plot_c5": "#999933",
                      "hm_safe": "#44aa99", "hm_ok": "#88ccee", "hm_warn": "#ddcc77",
                      "hm_hot":  "#cc6677", "hm_crit": "#aa3377", "hm_max": "#332288"},
    "Helldivers 2":  {"_dark": True,
                      "bg": "#0a0c10", "bg2": "#111318", "bg3": "#1e2330",
                      "fg": "#e8dfc8", "accent": "#f0c030", "accent2": "#c8a820",
                      "plot_c0": "#f0c030", "plot_c1": "#e03020", "plot_c2": "#4090d0",
                      "plot_c3": "#60c060", "plot_c4": "#c060c0", "plot_c5": "#e08020",
                      "hm_safe": "#1a3a1a", "hm_ok": "#60c060", "hm_warn": "#f0c030",
                      "hm_hot":  "#e08020", "hm_crit": "#e03020", "hm_max": "#8b0000"},
    "Monochrome": {"_dark": True,
                      "bg": "#000000", "bg2": "#1a1a1a", "bg3": "#333333",
                      "fg": "#ffffff", "accent": "#ffff00", "accent2": "#00ffff",
                      "plot_c0": "#ffff00", "plot_c1": "#00ffff", "plot_c2": "#ff6600",
                      "plot_c3": "#ff00ff", "plot_c4": "#00ff00", "plot_c5": "#ffffff",
                      "hm_safe": "#004400", "hm_ok": "#00cc00", "hm_warn": "#ffff00",
                      "hm_hot":  "#ff6600", "hm_crit": "#ff0000", "hm_max": "#ffffff"},
    "Cathode": {"_dark": True,
                      "bg": "#160f08", "bg2": "#231809", "bg3": "#3a2a14",
                      "fg": "#ffb86b", "accent": "#ff5400", "accent2": "#ffb86b",
                      "plot_c0": "#ff5400", "plot_c1": "#ffb86b", "plot_c2": "#ff8c3c",
                      "plot_c3": "#d4a017", "plot_c4": "#c1440e", "plot_c5": "#ffd699",
                      "hm_safe": "#3a2a08", "hm_ok": "#d4a017", "hm_warn": "#ff8c3c",
                      "hm_hot":  "#ff5400", "hm_crit": "#c1440e", "hm_max": "#7a1f00"},
    "Garnet":         {"_dark": True,
                      "bg": "#241018", "bg2": "#321420", "bg3": "#46202f",
                      "fg": "#f0d8e0", "accent": "#d6336c", "accent2": "#f06595",
                      "plot_c0": "#f06595", "plot_c1": "#63c5da", "plot_c2": "#ffd166",
                      "plot_c3": "#a78bfa", "plot_c4": "#7ed6a5", "plot_c5": "#d6336c",
                      "hm_safe": "#2f3d2a", "hm_ok": "#7ed6a5", "hm_warn": "#ffd166",
                      "hm_hot":  "#f06595", "hm_crit": "#d6336c", "hm_max": "#80143f"},
    "Glacier":        {"_dark": False,
                      "bg": "#eef4f6", "bg2": "#ffffff", "bg3": "#d4e2e6",
                      "fg": "#16313a", "accent": "#0e9594", "accent2": "#0a6e6d",
                      "plot_c0": "#0e9594", "plot_c1": "#1d5b79", "plot_c2": "#e36414",
                      "plot_c3": "#774c60", "plot_c4": "#5fa8d3", "plot_c5": "#0a6e6d",
                      "hm_safe": "#0a6e6d", "hm_ok": "#5fa8d3", "hm_warn": "#e8a13b",
                      "hm_hot":  "#e36414", "hm_crit": "#b3331d", "hm_max": "#6e1a0f"},
    "Vaporwave":      {"_dark": True,
                      "bg": "#170824", "bg2": "#23103a", "bg3": "#3a1c5c",
                      "fg": "#f3e8ff", "accent": "#9d4edd", "accent2": "#ff2bd6",
                      "plot_c0": "#ff2bd6", "plot_c1": "#9d4edd", "plot_c2": "#00f5d4",
                      "plot_c3": "#fee440", "plot_c4": "#5390d9", "plot_c5": "#ff6392",
                      "hm_safe": "#1a3a4a", "hm_ok": "#00f5d4", "hm_warn": "#fee440",
                      "hm_hot":  "#ff6392", "hm_crit": "#ff2bd6", "hm_max": "#6b0f8c"},
    "Bunker":         {"_dark": True,
                      "bg": "#1c1f14", "bg2": "#262a1a", "bg3": "#3a3f26",
                      "fg": "#dfe3c8", "accent": "#7d8b4f", "accent2": "#a3ad6e",
                      "plot_c0": "#a3ad6e", "plot_c1": "#6e9b8c", "plot_c2": "#c19a4b",
                      "plot_c3": "#9a6e4b", "plot_c4": "#7d8b4f", "plot_c5": "#5f7a6b",
                      "hm_safe": "#2e3a22", "hm_ok": "#7d8b4f", "hm_warn": "#c19a4b",
                      "hm_hot":  "#a3702f", "hm_crit": "#7a3b1f", "hm_max": "#4a1f10"},
    "Stingray Analyzer": {"_dark": True,
                      "bg": "#0e1117", "bg2": "#161b22", "bg3": "#1c2333",
                      "fg": "#e6edf3", "accent": "#e85d04", "accent2": "#faa307",
                      "plot_c0": "#e85d04", "plot_c1": "#faa307", "plot_c2": "#3fb950",
                      "plot_c3": "#f85149", "plot_c4": "#a371f7", "plot_c5": "#8b949e",
                      "hm_safe": "#1c3a22", "hm_ok": "#3fb950", "hm_warn": "#d29922",
                      "hm_hot":  "#e85d04", "hm_crit": "#f85149", "hm_max": "#7a1410"},
}

def load_theme() -> dict:
    try:
        if Path(THEME_FILE).exists():
            with open(THEME_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_theme(theme: dict):
    try:
        with open(THEME_FILE, 'w') as f:
            json.dump(theme, f, indent=4)
    except Exception:
        pass
CURRENT_VERSION = "1.6.6"
GITHUB_REPO = "ERRORX2/HD2-LOG-VIEWER"

def save_config(groups_dict: Dict, is_dark: bool, multi_mode: bool = False, delta_mode: bool = False,
                ignored_version: str = "", updates_disabled: bool = False, time_mode: bool = False,
                thresholds: Dict = None, heatmap_mode: bool = False, disabled_sigs: list = None,
                sig_timeline_enabled: bool = True, tooltip_enabled: bool = True):
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
            "thresholds": thresholds or {},
            "disabled_sigs": disabled_sigs or [],
            "sig_timeline_enabled": sig_timeline_enabled,
            "tooltip_enabled": tooltip_enabled,
        }
    }
    try:
        with open(GROUPS_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except:
        pass

def load_config() -> Tuple[Dict, bool, bool, bool, str, bool, bool, Dict, bool, list, bool, bool]:
    if not Path(GROUPS_FILE).exists():
        return {}, False, False, False, "", False, False, {}, False, [], True, True
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
                        sets.get("heatmap_mode", False),
                        sets.get("disabled_sigs", []),
                        sets.get("sig_timeline_enabled", True),
                        sets.get("tooltip_enabled", True))
            return data if isinstance(data, dict) else {}, False, False, False, "", False, False, {}, False, [], True, True
    except:
        return {}, False, False, False, "", False, False, {}, False, [], False, True

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

        try:
            is_dark = root._app_ref.is_dark
            _t = root._app_ref._get_theme()
        except Exception:
            is_dark = False
            _t = _DEFAULT_DARK_THEME
        bg = _t["bg"]; fg = _t["fg"]; accent = _t["accent"]

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
    TIME_COLUMN_CANDIDATES = ['time', 'date', 'timestamp', 'elapsed', 'clock', '#']
    TIME_FORMATS = ['%H:%M:%S', '%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%H:%M']


    MANGOHUD_COL_MAP = {
        'fps':              'FPS [FPS]',
        'frametime':        'Frame Time [ms]',
        'cpu_load':         'CPU Usage [%]',
        'cpu_power':        'CPU Package Power [W]',
        'gpu_load':         'GPU Usage [%]',
        'cpu_temp':         'CPU Temperature [°C]',
        'gpu_temp':         'GPU Temperature [°C]',
        'gpu_core_clock':   'GPU Clock [MHz]',
        'gpu_mem_clock':    'GPU Memory Clock [MHz]',
        'gpu_vram_used':    'GPU VRAM Used [MB]',
        'gpu_power':        'GPU Power [W]',
        'ram_used':         'RAM Used [GB]',
        'swap_used':        'Swap Used [GB]',
        'process_rss':      'Process RSS [GB]',
        'cpu_mhz':          'CPU Clock [MHz]',
        'elapsed':          'elapsed',
        'gpu_voltage':      'GPU Voltage [V]',
        'gpu_mem_temp':     'GPU Memory Temperature [°C]',
        'cpu_power_limit':  'CPU Power Limit [W]',
        'fan_speed':        'Fan Speed [RPM]',
        'gpu_fan_speed':    'GPU Fan Speed [RPM]',
        'battery':          'Battery [%]',
        'gpu_load_change':  'GPU Load Change [%]',
    }

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self.df: pd.DataFrame = pd.DataFrame()
        self.time_col: str = ""
        self.time_series = None
        self.aliases: dict = {}
        self.is_mangohud: bool = False
        self.mangohud_sysinfo: dict = {}

    @staticmethod
    def load_aliases() -> dict:
        """Load user-confirmed sensor aliases from disk."""
        try:
            if Path(SENSOR_ALIASES_FILE).exists():
                with open(SENSOR_ALIASES_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    @staticmethod
    def save_aliases(aliases: dict) -> None:
        """Persist user-confirmed sensor aliases to disk."""
        try:
            with open(SENSOR_ALIASES_FILE, 'w') as f:
                json.dump(aliases, f, indent=2)
        except Exception:
            pass

    def resolve(self, key: str) -> str | None:
        """Return the first valid confirmed alias for key that exists in current df.
        Aliases are stored as a list so multiple CSVs with different column names all work."""
        entry = self.aliases.get(key)
        if not entry:
            return None
        candidates = entry if isinstance(entry, list) else [entry]
        for c in candidates:
            if c and c in self.df.columns:
                return c
        return None

    def _is_mangohud_file(self) -> bool:
        """Return True if this CSV is a MangoHud log."""
        try:
            with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
                first = f.readline().strip()
            return first == 'v1'
        except Exception:
            return False

    def _load_mangohud(self) -> None:
        """Parse a MangoHud log file into self.df with HWiNFO-style column names."""
        sysinfo = {}
        header_row = None
        data_start = 0

        with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()


        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('-----') and 'SYSTEM INFO' in line:

                if i + 2 < len(lines):
                    keys   = lines[i + 1].strip().split(',')
                    values = lines[i + 2].strip().split(',')
                    sysinfo = dict(zip(keys, values))
                i += 3
                continue
            if line.startswith('-----') and 'FRAME METRICS' in line:

                header_row = i + 1
                data_start = i + 2
                break
            i += 1

        if header_row is None:
            raise ValueError("MangoHud format not recognised - missing FRAME METRICS section")

        self.mangohud_sysinfo = sysinfo
        self.is_mangohud = True


        col_line = lines[header_row].strip()
        raw_cols = col_line.split(',')
        data_lines = [l for l in lines[data_start:] if l.strip() and not l.startswith('-')]

        import io
        data_str = col_line + '\n' + ''.join(data_lines)
        df = pd.read_csv(io.StringIO(data_str), on_bad_lines='skip')


        if 'elapsed' in df.columns:
            elapsed_ns = pd.to_numeric(df['elapsed'], errors='coerce')
            elapsed_ns = elapsed_ns - elapsed_ns.iloc[0]
            elapsed_s  = elapsed_ns / 1e9
            import pandas as pd_inner
            self.time_series = pd_inner.to_timedelta(elapsed_s, unit='s').reset_index(drop=True)
            self.time_col = 'elapsed'


        rename_map = {}
        for raw, display in self.MANGOHUD_COL_MAP.items():
            if raw in df.columns and raw != 'elapsed':
                rename_map[raw] = display
        df = df.rename(columns=rename_map)


        if 'elapsed' in df.columns:
            df = df.drop(columns=['elapsed'])


        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception:
                pass

        df = df.ffill().reset_index(drop=True)
        self.df = df

    def load(self) -> None:

        if self._is_mangohud_file():
            self._load_mangohud()
            self.aliases = self.load_aliases()
            return
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

        self._detect_time_column()

        for col in self.df.columns:
            if col == self.time_col:
                continue
            if '[Yes/No]' in col or '[yes/no]' in col.lower():
                continue
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

        for col in self.df.columns:
            if '[Yes/No]' in col or '[yes/no]' in col.lower():
                self.df[col] = (
                    self.df[col].astype(str).str.strip().str.lower()
                    .map({'yes': 1.0, 'no': 0.0, '1': 1.0, '0': 0.0,
                          '1.0': 1.0, '0.0': 0.0, 'true': 1.0, 'false': 0.0})
                )

        if self.time_series is not None:
            self.time_series = self.time_series.iloc[:len(self.df)].reset_index(drop=True)
        self.df = self.df.reset_index(drop=True)
        self.aliases = self.load_aliases()

    def extract_hardware_names(self) -> dict:

        if self.is_mangohud and self.mangohud_sysinfo:
            result = {}
            si = self.mangohud_sysinfo
            if si.get('cpu'):
                result.setdefault('CPU', []).append(si['cpu'])
            if si.get('gpu'):
                result.setdefault('GPU', []).append(si['gpu'])
            if si.get('ram'):
                try:
                    ram_mb = int(si['ram'])
                    result.setdefault('Memory (RAM)', []).append(f"{ram_mb // 1024} GB")
                except Exception:
                    result.setdefault('Memory (RAM)', []).append(si['ram'])
            if si.get('os'):
                result.setdefault('System / Motherboard', []).append(si['os'])
            if si.get('driver'):
                result.setdefault('GPU', []).append(f"Driver: {si['driver']}")
            if si.get('kernel'):
                result.setdefault('System / Motherboard', []).append(f"Kernel: {si['kernel']}")
            return result


        """
        Extract unique hardware device names from a HWiNFO64 CSV.

        HWiNFO64 appends a hardware-label row somewhere in the file (often row 2,
        but may also appear at the very end). Each cell in that row contains the
        source device for its column, e.g.:
            "CPU [#0]: Intel Core i7-13620H"
            "dGPU [#1]: NVIDIA GeForce RTX 4070 Laptop"
            "S.M.A.R.T.: WD PC SN560 ..."
            "System: ASUS TUF Gaming F15 ..."
            "Network: Intel Wi-Fi 6 AX201 160MHz - Wi-Fi"
            "Battery: AS3GWAF3KC GA50358"
            "PresentMon [AsusMyASUS.exe]"

        Strategy: read ALL rows of the raw file, find any row where a significant
        fraction of non-empty cells match the HWiNFO device-label pattern, then
        collect unique device names from that row.
        """
        _KNOWN_TAGS = re.compile(
            r'^(CPU|iGPU|dGPU|GPU|DDR\d*\s*DIMM|S\.M\.A\.R\.T\.|Drive|'
            r'Network|Battery|System|PresentMon|Memory Timings|'
            r'ASUS\s+NB\s+EC|ASUS\s+FX|PCH|Chipset|EC\b)',
            re.IGNORECASE
        )

        def _is_label_cell(cell: str) -> bool:
            """Return True if this cell looks like a HWiNFO device label."""
            c = cell.strip()
            if not c:
                return False
            if not _KNOWN_TAGS.match(c):
                return False
            if re.match(r'^-?\d+(\.\d+)?$', c):
                return False
            if c.upper() in ('YES', 'NO', 'N/A', 'OK', 'FAIL', 'WARNING'):
                return False
            if re.search(r'\[(°C|MHz|W|V|%|RPM|MB|GB|A|ms|FPS|x|T|GT/s)\]\s*$', c, re.IGNORECASE):
                return False
            if ': ' in c:
                _, device_part = c.split(': ', 1)
                if not re.search(r'[A-Za-z]', device_part):
                    return False
            return True

        all_rows = []
        for enc in ('utf-8-sig', 'latin-1', 'cp1252'):
            try:
                with open(self.path, 'r', encoding=enc, errors='ignore') as f:
                    reader = csv.reader(f)
                    all_rows = list(reader)
                break
            except Exception:
                continue

        if not all_rows:
            return {}

        best_row = []
        best_score = 0.0

        for row in all_rows:
            non_empty = [c for c in row if c.strip()]
            if not non_empty:
                continue
            label_cells = [c for c in non_empty if _is_label_cell(c)]
            score = len(label_cells) / len(non_empty)
            if score > best_score:
                best_score = score
                best_row = row

        if best_score < 0.25 or not best_row:
            return {}
        if sum(1 for c in best_row if _is_label_cell(c)) < 3:
            return {}

        _TYPE_CATEGORY = [
            (['IGPU'],                                      'iGPU (Integrated Graphics)'),
            (['DGPU', 'GPU'],                               'GPU'),
            (['CPU'],                                       'CPU'),
            (['DDR', 'DIMM'],                               'Memory (RAM)'),
            (['S.M.A.R.T', 'SMART', 'DRIVE', 'DISK'],      'Storage'),
            (['NETWORK', 'NIC'],                            'Network'),
            (['BATTERY'],                                   'Battery'),
            (['PRESENTMON'],                                'PresentMon (Frame Timing)'),
            (['MEMORY TIMING'],                             'Memory Timings'),
            (['PCH', 'CHIPSET'],                            'Chipset'),
            (['EC', 'EMBEDDED'],                            'Embedded Controller'),
            (['SYSTEM', 'ASUS', 'GIGABYTE', 'MSI',
              'ASROCK', 'EVGA', 'BIOSTAR', 'MAINBOARD',
              'MOTHERBOARD'],                               'System / Motherboard'),
        ]

        def _categorize(type_tag: str) -> str:
            tt = type_tag.upper().strip()
            for keywords, label in _TYPE_CATEGORY:
                if any(k in tt for k in keywords):
                    return label
            return 'Other'

        def _clean_parens(s: str) -> str:
            """Remove trailing parenthesised serial/slot info."""
            return re.sub(r'\s*\([^)]*\)\s*$', '', s).strip()

        seen: dict = {}

        for cell in best_row:
            cell = cell.strip().strip('\ufeff')
            if not cell or not _is_label_cell(cell):
                continue

            if ': ' in cell:
                type_tag, device_part = cell.split(': ', 1)
                _SUBLABEL = re.compile(
                    r':\s*(DTS|Enhanced|C-State Residency|Performance Limit Reasons|'
                    r'Clocks?|Temperatures?|Voltages?|Powers?|Fan\s*Speeds?|'
                    r'Throttling|Usage|Utilization|Residency|Load|Misc\w*)\s*$',
                    re.IGNORECASE
                )
                device_part = _SUBLABEL.sub('', device_part).strip()
                if ': ' in device_part:
                    left, right = device_part.split(': ', 1)
                    device_name = _clean_parens(left if len(left) >= len(right) else right)
                else:
                    device_name = _clean_parens(device_part.strip())
            else:
                type_tag = cell
                device_name = cell.strip()

            if not device_name or len(device_name) <= 1:
                continue
            if device_name.upper() in ('DATE', 'TIME', 'TIMESTAMP', '#'):
                continue

            cat = _categorize(type_tag)

            existing = [k for k in seen if cat == seen[k]]
            dominated = None
            for ex in existing:
                if device_name.startswith(ex) or ex.startswith(device_name):
                    dominated = ex
                    break
            if dominated is not None:
                if len(device_name) > len(dominated):
                    del seen[dominated]
                else:
                    continue

            if device_name not in seen:
                seen[device_name] = cat

        _CAT_ORDER = [
            'System / Motherboard', 'CPU', 'iGPU (Integrated Graphics)', 'GPU',
            'Memory (RAM)', 'Memory Timings', 'Storage', 'Chipset',
            'Embedded Controller', 'Network', 'Battery',
            'PresentMon (Frame Timing)', 'Other',
        ]
        result: dict = {}
        for name, cat in seen.items():
            result.setdefault(cat, []).append(name)

        ordered = {}
        for cat in _CAT_ORDER:
            if cat in result:
                ordered[cat] = sorted(result[cat])
        for cat in sorted(result):
            if cat not in ordered:
                ordered[cat] = sorted(result[cat])

        return ordered

    def _detect_time_column(self):
        """Find the best time column and parse it into self.time_series."""
        cols_lower = {c.lower().strip(): c for c in self.df.columns}

        found_col = None
        for candidate in self.TIME_COLUMN_CANDIDATES:
            if candidate in cols_lower:
                found_col = cols_lower[candidate]
                break

        if not found_col:
            return

        raw = self.df[found_col].astype(str).str.strip()

        for fmt in self.TIME_FORMATS:
            try:
                parsed = pd.to_datetime(raw, format=fmt, errors='coerce')
                if parsed.notna().sum() > len(parsed) * 0.8:
                    self.time_col = found_col
                    first = parsed.dropna().iloc[0]
                    self.time_series = parsed - first
                    return
            except Exception:
                continue

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
        self._x_axis_cache = None
        self._sensor_stats_cache = {}

        self.ref_df = None
        self.ref_analyzer = None
        self.compare_mode = False
        self.sessions = []
        self.session_compare_active = False
        self._cmp_single_mode = True
        self._cmp_sensor_var = None

        (self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode,
         self.ignored_version, self.updates_disabled, self.time_mode,
         saved_thresholds, self.heatmap_mode, disabled_sigs_list, sig_tl_enabled, tooltip_en) = load_config()
        self.sig_timeline_enabled = sig_tl_enabled
        self.disabled_sigs = set(disabled_sigs_list)
        self.custom_theme  = load_theme()

        self.vars = {}
        self.cb_widgets = {}
        self.header_widgets = {}
        self.group_map = {}
        self.cursor_lines = []
        self.cursor_text = None
        self._tooltip_enabled = tooltip_en
        self.filter_active = False
        self.debug_mode    = False

        self._sig_hits        = []
        self._sig_running     = False
        self._sig_dirty       = True
        self._sig_badge_var   = None
        self._sig_badge_lbl   = None
        self._badge_crit_lbl  = None
        self._badge_warn_lbl  = None
        self._badge_info_lbl  = None
        self._badge_ok_lbl    = None
        self._sig_watcher_id  = None
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
            'DRIVE': 70.0,
            'TEMPERATURE': 70.0,
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
            'memory_load_max': 95.0,
            'drive_spare_min': 10.0,
            'drive_life_min': 10.0,
            'vcore_droop_max': 0.3,
            'clock_instability': 0.35,
            'throttle_threshold': 0.9,
            'sig_cpu_thermal_pct': 0.85,
            'sig_cpu_thermal_samples': 10,
            'sig_fan_stall_rpm': 100.0,
            'sig_fan_min_spinning': 200.0,
            'sig_fan_hot_cpu_c': 70.0,
            'sig_fan_hot_gpu_c': 65.0,
            'sig_drive_temp_max': 70.0,
            'sig_vrm_temp_max': 105.0,
            'sig_ram_exhaust_pct': 95.0,
            'sig_vram_overflow_pct': 98.0,
            'sig_cpu_bn_gpu_pct': 60.0,
            'sig_cpu_bn_cpu_pct': 85.0,
            'sig_cpu_bn_samples': 10,
            'sig_stutter_mult': 3.0,
            'sig_stutter_min_hits': 5,
            'sig_tdr_clock_frac': 0.5,
            'sig_ppt_sat_pct': 0.98,
            'sig_ppt_sat_samples': 15,
            'sig_clock_stretch_mhz': 500.0,
            'sig_disk_busy_pct': 99.9,
            'sig_disk_busy_samples': 3,
            'sig_v12_lo': 11.4,
            'sig_v5_lo': 4.75,  'sig_v5_hi': 5.25,
            'sig_v33_lo': 3.14, 'sig_v33_hi': 3.47,
        }

        self.temp_limits  = {**self._default_temp_limits,
                             **saved_thresholds.get('temp_limits', {})}
        self.volt_rails   = {k: tuple(v) for k, v in
                             {**self._default_volt_rails,
                              **saved_thresholds.get('volt_rails', {})}.items()}
        misc              = {**self._default_misc,
                             **saved_thresholds.get('misc', {})}
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
        self.memory_load_max  = misc['memory_load_max']
        self.drive_spare_min  = misc['drive_spare_min']
        self.drive_life_min   = misc['drive_life_min']
        self.vcore_droop_max  = misc['vcore_droop_max']
        self.clock_instability = misc['clock_instability']
        self.throttle_threshold = misc['throttle_threshold']
        self.sig_cpu_thermal_pct    = misc['sig_cpu_thermal_pct']
        self.sig_cpu_thermal_samples = int(misc['sig_cpu_thermal_samples'])
        self.sig_fan_stall_rpm      = misc['sig_fan_stall_rpm']
        self.sig_fan_min_spinning   = misc['sig_fan_min_spinning']
        self.sig_fan_hot_cpu_c      = misc['sig_fan_hot_cpu_c']
        self.sig_fan_hot_gpu_c      = misc['sig_fan_hot_gpu_c']
        self.sig_drive_temp_max     = misc['sig_drive_temp_max']
        self.sig_vrm_temp_max       = misc['sig_vrm_temp_max']
        self.sig_ram_exhaust_pct    = misc['sig_ram_exhaust_pct']
        self.sig_vram_overflow_pct  = misc['sig_vram_overflow_pct']
        self.sig_cpu_bn_gpu_pct     = misc['sig_cpu_bn_gpu_pct']
        self.sig_cpu_bn_cpu_pct     = misc['sig_cpu_bn_cpu_pct']
        self.sig_cpu_bn_samples     = int(misc['sig_cpu_bn_samples'])
        self.sig_stutter_mult       = misc['sig_stutter_mult']
        self.sig_stutter_min_hits   = int(misc['sig_stutter_min_hits'])
        self.sig_tdr_clock_frac     = misc['sig_tdr_clock_frac']
        self.sig_ppt_sat_pct        = misc['sig_ppt_sat_pct']
        self.sig_ppt_sat_samples    = int(misc['sig_ppt_sat_samples'])
        self.sig_clock_stretch_mhz  = misc['sig_clock_stretch_mhz']
        self.sig_disk_busy_pct      = misc['sig_disk_busy_pct']
        self.sig_disk_busy_samples  = int(misc['sig_disk_busy_samples'])
        self.sig_v12_lo             = misc['sig_v12_lo']
        self.sig_v5_lo              = misc['sig_v5_lo']
        self.sig_v5_hi              = misc['sig_v5_hi']
        self.sig_v33_lo             = misc['sig_v33_lo']
        self.sig_v33_hi             = misc['sig_v33_hi']

        self.root._app_ref = self

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._setup_ui()
        self._apply_theme_colors()
        self.update_plot()
        self.root.after(300, self._prompt_sensor_aliases)

        check_for_updates(
            self.root,
            ignored_version=self.ignored_version,
            updates_disabled=self.updates_disabled,
            on_ignore=self._on_ignore_version,
            on_disable=self._on_disable_updates,
            silent=True
        )

    def _on_close(self):
        self._teardown()
        self.root.quit()
        self.root.destroy()
        os._exit(0)

    def _open_limits_editor(self):
        """Open a scrollable dialog to view and edit all detection thresholds."""
        is_dark = self.is_dark
        _t = self._get_theme(); bg = _t["bg"]; bg2 = _t["bg2"]; fg = _t["fg"]; accent = _t["accent"]; bg3 = _t["bg3"]

        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("560x680")
        dialog.minsize(480, 500)
        dialog.grab_set()
        dialog.configure(bg=bg)
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 280
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 340
        dialog.geometry(f"560x680+{x}+{y}")

        outer = tk.Frame(dialog, bg=bg)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview,
                        bg=bg3, troughcolor=bg, activebackground=accent)
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

        entries = {}

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

        section("Temperature Limits (°C)")
        temp_display = [
            ("GPU Core",              "GPU"),
            ("GPU Hotspot",           "HOTSPOT"),
            ("GPU VRAM",              "VRAM"),
            ("GPU VRM",               "VRM"),
            ("CPU Core",              "CORE"),
            ("CPU Tdie/Tctl",         "TDIE"),
            ("CPU CCD/CCX",           "CCD"),
            ("CPU Socket",            "SOCKET"),
            ("Coolant/Liquid",        "COOLANT"),
            ("SSD/NVMe",              "SSD"),
            ("HDD",                   "HDD"),
            ("Drive (generic)",       "DRIVE"),
            ("Chipset/PCH",           "CHIPSET"),
            ("MOSFET/Choke",          "MOSFET"),
        ]
        for label, key in temp_display:
            if key in self.temp_limits:
                row(label, f"temp_{key}", self.temp_limits[key], "°C")

        section("Voltage Rails - Safe Range (V)")
        range_row("+12V Rail",   "rail_12v_lo",   "rail_12v_hi",   *self.volt_rails['+12V'],  "V")
        range_row("+5V Rail",    "rail_5v_lo",    "rail_5v_hi",    *self.volt_rails['+5V'],   "V")
        range_row("+3.3V Rail",  "rail_33v_lo",   "rail_33v_hi",   *self.volt_rails['+3.3V'], "V")

        section("Component Voltages")
        range_row("CPU Vcore",   "cpu_volt_lo", "cpu_volt_hi", *self.cpu_volt_range,  "V")
        range_row("DRAM Voltage","dram_volt_lo","dram_volt_hi",*self.dram_volt_range, "V")
        row("GPU Core Voltage max", "gpu_volt_max", self.gpu_volt_max, "V")

        section("Power Draw Limits (W)")
        row("CPU max power",    "cpu_power_max",   self.cpu_power_max,   "W")
        row("GPU max power",    "gpu_power_max",   self.gpu_power_max,   "W")
        row("Total system max", "total_power_max", self.total_power_max, "W")

        section("Frame Timing & Latency")
        row("Frame time spike (1% high)", "frametime_max_ms", self.frametime_max_ms, "ms")
        row("Min FPS (0.1% low)",         "fps_min",          self.fps_min,          "FPS")
        row("Latency max",                "latency_max_ms",   self.latency_max_ms,   "ms")

        section("Miscellaneous")
        row("Fan stall threshold",          "fan_min_rpm",        self.fan_min_rpm,        "RPM")

        section("Drive Health")
        row("Available spare min",          "drive_spare_min",    self.drive_spare_min,    "%")
        row("Remaining life min",           "drive_life_min",     self.drive_life_min,     "%")

        section("Memory Load")
        row("RAM / VRAM load max",          "memory_load_max",    self.memory_load_max,    "%")

        section("Stability Detection")
        row("Throttle sensitivity (0–1)",   "throttle_threshold", self.throttle_threshold, "")
        row("Vcore max droop",              "vcore_droop_max",    self.vcore_droop_max,    "V")
        row("Clock instability ratio",      "clock_instability",  self.clock_instability,  "std/mean")

        section("Hardware Signature Thresholds")
        row("CPU thermal trigger (% of limit)",  "sig_cpu_thermal_pct",    self.sig_cpu_thermal_pct,    "0–1")
        row("CPU thermal sustained samples",     "sig_cpu_thermal_samples",self.sig_cpu_thermal_samples,"")
        row("Fan stall RPM threshold",           "sig_fan_stall_rpm",      self.sig_fan_stall_rpm,      "RPM")
        row("Fan min peak RPM (ever spun?)",     "sig_fan_min_spinning",   self.sig_fan_min_spinning,   "RPM")
        row("Fan stall: CPU hot threshold",      "sig_fan_hot_cpu_c",      self.sig_fan_hot_cpu_c,      "°C")
        row("Fan stall: GPU hot threshold",      "sig_fan_hot_gpu_c",      self.sig_fan_hot_gpu_c,      "°C")
        row("Storage overheating max",           "sig_drive_temp_max",     self.sig_drive_temp_max,     "°C")
        row("VRM overheating max",               "sig_vrm_temp_max",       self.sig_vrm_temp_max,       "°C")
        row("RAM exhaustion trigger",            "sig_ram_exhaust_pct",    self.sig_ram_exhaust_pct,    "%")
        row("VRAM overflow trigger",             "sig_vram_overflow_pct",  self.sig_vram_overflow_pct,  "%")
        row("Bottleneck: GPU below",             "sig_cpu_bn_gpu_pct",     self.sig_cpu_bn_gpu_pct,     "%")
        row("Bottleneck: CPU above",             "sig_cpu_bn_cpu_pct",     self.sig_cpu_bn_cpu_pct,     "%")
        row("Bottleneck: sustained samples",     "sig_cpu_bn_samples",     self.sig_cpu_bn_samples,     "")
        row("Stutter: frametime multiplier",     "sig_stutter_mult",       self.sig_stutter_mult,       "× median")
        row("Stutter: minimum events",           "sig_stutter_min_hits",   self.sig_stutter_min_hits,   "")
        row("TDR: GPU clock fraction",           "sig_tdr_clock_frac",     self.sig_tdr_clock_frac,     "0–1")
        row("PPT saturation: % of limit",        "sig_ppt_sat_pct",        self.sig_ppt_sat_pct,        "0–1")
        row("PPT saturation: sustained samples", "sig_ppt_sat_samples",    self.sig_ppt_sat_samples,    "")
        row("Clock stretch gap",                 "sig_clock_stretch_mhz",  self.sig_clock_stretch_mhz,  "MHz")
        row("Disk congestion: busy %",           "sig_disk_busy_pct",      self.sig_disk_busy_pct,      "%")
        row("Disk congestion: samples",          "sig_disk_busy_samples",  self.sig_disk_busy_samples,  "")

        section("Signature PSU Rail Specs")
        row("+12V lower limit",  "sig_v12_lo",  self.sig_v12_lo,  "V")
        range_row("+5V range",   "sig_v5_lo",   "sig_v5_hi",   self.sig_v5_lo,  self.sig_v5_hi,  "V")
        range_row("+3.3V range", "sig_v33_lo",  "sig_v33_hi",  self.sig_v33_lo, self.sig_v33_hi, "V")

        section("Signature Timeline")
        tk.Label(body, text="Show signature events as a timeline strip above the plot.",
                 bg=bg, fg="#888", font=('Segoe UI', 8), wraplength=480,
                 justify='left').pack(anchor='w', padx=8, pady=(2, 4))
        tl_frame = tk.Frame(body, bg=bg)
        tl_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        tl_enabled_var = tk.BooleanVar(value=self.sig_timeline_enabled if hasattr(self, 'sig_timeline_enabled') else True)
        tk.Checkbutton(tl_frame, text="Enable signature timeline strip",
                       variable=tl_enabled_var, bg=bg, activebackground=bg,
                       selectcolor="#1f6aa5" if is_dark else "#ffffff",
                       fg=fg, font=('Segoe UI', 9)).pack(side=tk.LEFT)

        section("Signature Enable / Disable")
        tk.Label(body, text="Uncheck a signature to exclude it from detection and reports.",
                 bg=bg, fg="#888", font=('Segoe UI', 8), wraplength=480,
                 justify='left').pack(anchor='w', padx=8, pady=(2, 6))

        _ALL_SIGNATURES = [
            ("CPU Thermal Throttling",          "CRITICAL/WARNING"),
            ("CPU Power Limit Reached",         "WARNING"),
            ("CPU Bottleneck",                  "WARNING"),
            ("GPU Overheating (Hotspot)",        "CRITICAL"),
            ("GPU Thermal Warning",              "WARNING"),
            ("GPU VRAM Overflow Analysis",       "WARNING"),
            ("PSU +12V Rail Sag",               "CRITICAL/WARNING"),
            ("PSU +5V Rail Unstable",           "WARNING"),
            ("PSU +3.3V Rail Unstable",         "WARNING"),
            ("Fan Stall Detected",              "CRITICAL"),
            ("PSU Hardware Failure Indicators", "CRITICAL"),
            ("Hardware (WHEA) Errors",          "CRITICAL"),
            ("VRM Overheating",                 "CRITICAL"),
            ("System RAM Exhaustion",           "WARNING"),
            ("Virtual Memory Limit",            "CRITICAL"),
            ("Storage Thermal Critical",        "CRITICAL"),
            ("Storage Overheating",             "WARNING"),
            ("Storage Congestion",              "INFO"),
            ("S.M.A.R.T. Hardware Failure",     "CRITICAL"),
            ("SSD Lifespan Critical",           "CRITICAL"),
            ("SSD Wear Warning",                "WARNING"),
            ("Micro-Stuttering Detected",       "WARNING"),
            ("Memory XMP/EXPO Profile Disabled", "WARNING"),
        ]

        _SEV_COLORS = {"CRITICAL": "#ff4d4d", "WARNING": "#f59e0b",
                       "INFO": "#38bdf8", "CRITICAL/WARNING": "#ff8c42"}
        sig_vars = {}
        for sig_name, sev_hint in _ALL_SIGNATURES:
            enabled = sig_name not in self.disabled_sigs
            var = tk.BooleanVar(value=enabled)
            sig_vars[sig_name] = var
            sev_color = _SEV_COLORS.get(sev_hint, "#aaa")

            row_f = tk.Frame(body, bg=bg)
            row_f.pack(fill=tk.X, pady=1, padx=8)
            cb = tk.Checkbutton(row_f, variable=var, bg=bg, activebackground=bg,
                                selectcolor="#1f6aa5" if is_dark else "#ffffff",
                                fg=fg, activeforeground=fg,
                                relief='flat', cursor='hand2')
            cb.pack(side=tk.LEFT)
            tk.Label(row_f, text=sig_name, bg=bg, fg=fg,
                     font=('Segoe UI', 9), anchor='w').pack(side=tk.LEFT)
            tk.Label(row_f, text=sev_hint, bg=bg, fg=sev_color,
                     font=('Segoe UI', 8), anchor='w').pack(side=tk.LEFT, padx=(6, 0))

        btn_f = tk.Frame(dialog, bg=bg)
        btn_f.pack(fill=tk.X, padx=10, pady=10)

        status_var = tk.StringVar(value="")
        status_lbl = tk.Label(dialog, textvariable=status_var, bg=bg,
                              font=('Segoe UI', 8), fg="#888")
        status_lbl.pack(pady=(0, 4))

        def _try_apply(show_toast=False, close=False):
            """Parse all fields and apply if all valid. Called on every keystroke."""
            try:
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

                self.volt_rails['+12V']  = (float(entries['rail_12v_lo'].get()),
                                             float(entries['rail_12v_hi'].get()))
                self.volt_rails['+5V']   = (float(entries['rail_5v_lo'].get()),
                                             float(entries['rail_5v_hi'].get()))
                self.volt_rails['+3.3V'] = (float(entries['rail_33v_lo'].get()),
                                             float(entries['rail_33v_hi'].get()))

                self.cpu_volt_range  = (float(entries['cpu_volt_lo'].get()),
                                        float(entries['cpu_volt_hi'].get()))
                self.dram_volt_range = (float(entries['dram_volt_lo'].get()),
                                        float(entries['dram_volt_hi'].get()))
                self.gpu_volt_max    = float(entries['gpu_volt_max'].get())

                self.cpu_power_max   = float(entries['cpu_power_max'].get())
                self.gpu_power_max   = float(entries['gpu_power_max'].get())
                self.total_power_max = float(entries['total_power_max'].get())

                self.frametime_max_ms = float(entries['frametime_max_ms'].get())
                self.fps_min          = float(entries['fps_min'].get())
                self.latency_max_ms   = float(entries['latency_max_ms'].get())

                self.fan_min_rpm      = float(entries['fan_min_rpm'].get())
                self.drive_spare_min  = float(entries['drive_spare_min'].get())
                self.drive_life_min   = float(entries['drive_life_min'].get())
                self.memory_load_max  = float(entries['memory_load_max'].get())
                self.throttle_threshold = float(entries['throttle_threshold'].get())
                self.vcore_droop_max  = float(entries['vcore_droop_max'].get())
                self.clock_instability = float(entries['clock_instability'].get())

                self.sig_cpu_thermal_pct     = float(entries['sig_cpu_thermal_pct'].get())
                self.sig_cpu_thermal_samples = int(float(entries['sig_cpu_thermal_samples'].get()))
                self.sig_fan_stall_rpm       = float(entries['sig_fan_stall_rpm'].get())
                self.sig_fan_min_spinning    = float(entries['sig_fan_min_spinning'].get())
                self.sig_fan_hot_cpu_c       = float(entries['sig_fan_hot_cpu_c'].get())
                self.sig_fan_hot_gpu_c       = float(entries['sig_fan_hot_gpu_c'].get())
                self.sig_drive_temp_max      = float(entries['sig_drive_temp_max'].get())
                self.sig_vrm_temp_max        = float(entries['sig_vrm_temp_max'].get())
                self.sig_ram_exhaust_pct     = float(entries['sig_ram_exhaust_pct'].get())
                self.sig_vram_overflow_pct   = float(entries['sig_vram_overflow_pct'].get())
                self.sig_cpu_bn_gpu_pct      = float(entries['sig_cpu_bn_gpu_pct'].get())
                self.sig_cpu_bn_cpu_pct      = float(entries['sig_cpu_bn_cpu_pct'].get())
                self.sig_cpu_bn_samples      = int(float(entries['sig_cpu_bn_samples'].get()))
                self.sig_stutter_mult        = float(entries['sig_stutter_mult'].get())
                self.sig_stutter_min_hits    = int(float(entries['sig_stutter_min_hits'].get()))
                self.sig_tdr_clock_frac      = float(entries['sig_tdr_clock_frac'].get())
                self.sig_ppt_sat_pct         = float(entries['sig_ppt_sat_pct'].get())
                self.sig_ppt_sat_samples     = int(float(entries['sig_ppt_sat_samples'].get()))
                self.sig_clock_stretch_mhz   = float(entries['sig_clock_stretch_mhz'].get())
                self.sig_disk_busy_pct       = float(entries['sig_disk_busy_pct'].get())
                self.sig_disk_busy_samples   = int(float(entries['sig_disk_busy_samples'].get()))
                self.sig_v12_lo              = float(entries['sig_v12_lo'].get())
                self.sig_v5_lo               = float(entries['sig_v5_lo'].get())
                self.sig_v5_hi               = float(entries['sig_v5_hi'].get())
                self.sig_v33_lo              = float(entries['sig_v33_lo'].get())
                self.sig_v33_hi              = float(entries['sig_v33_hi'].get())

                self.disabled_sigs = {name for name, var in sig_vars.items() if not var.get()}
                self.sig_timeline_enabled = tl_enabled_var.get()

                self._save_config()
                self._build_checklist()
                self._apply_theme_colors()
                if self.filter_active:
                    self._apply_issue_filter()
                else:
                    self._filter_sensors()
                self.update_plot()
                self._mark_sig_dirty()
                status_var.set("✔ Saved")
                status_lbl.config(fg="#2ecc71")

                if show_toast:
                    self.show_toast("Limits saved")
                if close:
                    dialog.destroy()

            except ValueError:
                status_var.set("⚠ Invalid value - fix before closing")
                status_lbl.config(fg="#e74c3c")

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
                self.memory_load_max  = misc['memory_load_max']
                self.drive_spare_min  = misc['drive_spare_min']
                self.drive_life_min   = misc['drive_life_min']
                self.vcore_droop_max  = misc['vcore_droop_max']
                self.clock_instability = misc['clock_instability']
                self.throttle_threshold = misc['throttle_threshold']
                self.sig_cpu_thermal_pct     = misc['sig_cpu_thermal_pct']
                self.sig_cpu_thermal_samples = int(misc['sig_cpu_thermal_samples'])
                self.sig_fan_stall_rpm       = misc['sig_fan_stall_rpm']
                self.sig_fan_min_spinning    = misc['sig_fan_min_spinning']
                self.sig_fan_hot_cpu_c       = misc['sig_fan_hot_cpu_c']
                self.sig_fan_hot_gpu_c       = misc['sig_fan_hot_gpu_c']
                self.sig_drive_temp_max      = misc['sig_drive_temp_max']
                self.sig_vrm_temp_max        = misc['sig_vrm_temp_max']
                self.sig_ram_exhaust_pct     = misc['sig_ram_exhaust_pct']
                self.sig_vram_overflow_pct   = misc['sig_vram_overflow_pct']
                self.sig_cpu_bn_gpu_pct      = misc['sig_cpu_bn_gpu_pct']
                self.sig_cpu_bn_cpu_pct      = misc['sig_cpu_bn_cpu_pct']
                self.sig_cpu_bn_samples      = int(misc['sig_cpu_bn_samples'])
                self.sig_stutter_mult        = misc['sig_stutter_mult']
                self.sig_stutter_min_hits    = int(misc['sig_stutter_min_hits'])
                self.sig_tdr_clock_frac      = misc['sig_tdr_clock_frac']
                self.sig_ppt_sat_pct         = misc['sig_ppt_sat_pct']
                self.sig_ppt_sat_samples     = int(misc['sig_ppt_sat_samples'])
                self.sig_clock_stretch_mhz   = misc['sig_clock_stretch_mhz']
                self.sig_disk_busy_pct       = misc['sig_disk_busy_pct']
                self.sig_disk_busy_samples   = int(misc['sig_disk_busy_samples'])
                self.sig_v12_lo              = misc['sig_v12_lo']
                self.sig_v5_lo               = misc['sig_v5_lo']
                self.sig_v5_hi               = misc['sig_v5_hi']
                self.sig_v33_lo              = misc['sig_v33_lo']
                self.sig_v33_hi              = misc['sig_v33_hi']
                self.disabled_sigs           = set()
                self.sig_timeline_enabled    = True
                tl_enabled_var.set(True)
                for name, var in sig_vars.items():
                    var.set(True)
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
        ttk.Button(btn_f, text="Manage Sensor Aliases",
                   command=self._open_alias_manager).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,4))
        ttk.Button(btn_f, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4,0))

    def _on_ignore_version(self, version: str):
        self.ignored_version = version
        self._save_config()
        self.show_toast(f"Ignored v{version} - you'll be notified about future versions")

    def _on_disable_updates(self):
        self.updates_disabled = True
        self._save_config()
        self.show_toast("Update notifications disabled")

    def _save_config(self):
        misc = {
            'cpu_volt_lo':      self.cpu_volt_range[0],
            'cpu_volt_hi':      self.cpu_volt_range[1],
            'gpu_volt_max':     self.gpu_volt_max,
            'dram_volt_lo':     self.dram_volt_range[0],
            'dram_volt_hi':     self.dram_volt_range[1],
            'fan_min_rpm':      self.fan_min_rpm,
            'cpu_power_max':    self.cpu_power_max,
            'gpu_power_max':    self.gpu_power_max,
            'total_power_max':  self.total_power_max,
            'latency_max_ms':   self.latency_max_ms,
            'frametime_max_ms': self.frametime_max_ms,
            'fps_min':          self.fps_min,
            'coolant_max':      self.temp_limits.get('COOLANT', 45.0),
            'memory_load_max':  self.memory_load_max,
            'drive_spare_min':  self.drive_spare_min,
            'drive_life_min':   self.drive_life_min,
            'vcore_droop_max':  self.vcore_droop_max,
            'clock_instability': self.clock_instability,
            'throttle_threshold': self.throttle_threshold,
            'sig_cpu_thermal_pct':    self.sig_cpu_thermal_pct,
            'sig_cpu_thermal_samples': self.sig_cpu_thermal_samples,
            'sig_fan_stall_rpm':      self.sig_fan_stall_rpm,
            'sig_fan_min_spinning':   self.sig_fan_min_spinning,
            'sig_fan_hot_cpu_c':      self.sig_fan_hot_cpu_c,
            'sig_fan_hot_gpu_c':      self.sig_fan_hot_gpu_c,
            'sig_drive_temp_max':     self.sig_drive_temp_max,
            'sig_vrm_temp_max':       self.sig_vrm_temp_max,
            'sig_ram_exhaust_pct':    self.sig_ram_exhaust_pct,
            'sig_vram_overflow_pct':  self.sig_vram_overflow_pct,
            'sig_cpu_bn_gpu_pct':     self.sig_cpu_bn_gpu_pct,
            'sig_cpu_bn_cpu_pct':     self.sig_cpu_bn_cpu_pct,
            'sig_cpu_bn_samples':     self.sig_cpu_bn_samples,
            'sig_stutter_mult':       self.sig_stutter_mult,
            'sig_stutter_min_hits':   self.sig_stutter_min_hits,
            'sig_tdr_clock_frac':     self.sig_tdr_clock_frac,
            'sig_ppt_sat_pct':        self.sig_ppt_sat_pct,
            'sig_ppt_sat_samples':    self.sig_ppt_sat_samples,
            'sig_clock_stretch_mhz':  self.sig_clock_stretch_mhz,
            'sig_disk_busy_pct':      self.sig_disk_busy_pct,
            'sig_disk_busy_samples':  self.sig_disk_busy_samples,
            'sig_v12_lo':             self.sig_v12_lo,
            'sig_v5_lo':              self.sig_v5_lo,
            'sig_v5_hi':              self.sig_v5_hi,
            'sig_v33_lo':             self.sig_v33_lo,
            'sig_v33_hi':             self.sig_v33_hi,
        }
        thresholds = {
            'temp_limits': self.temp_limits,
            'volt_rails':  {k: list(v) for k, v in self.volt_rails.items()},
            'misc':        misc,
        }
        save_config(self.custom_groups, self.is_dark, self.multi_mode, self.delta_mode,
                    self.ignored_version, self.updates_disabled, self.time_mode, thresholds,
                    self.heatmap_mode, list(self.disabled_sigs),
                    getattr(self, 'sig_timeline_enabled', True),
                    getattr(self, '_tooltip_enabled', True))

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

    def _toggle_tooltip(self):
        self._tooltip_enabled = not getattr(self, '_tooltip_enabled', True)
        self._tooltip_btn.config(
            text="Tooltip: ON" if self._tooltip_enabled else "Tooltip: OFF")
        if not self._tooltip_enabled:
            self._clear_cursors()
            self.canvas_widget.draw_idle()
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
        self._invalidate_x_cache()
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
        is_dark    = self.is_dark
        _t         = self._get_theme()
        bg_color   = _t["bg"]
        bg2_color  = _t["bg2"]
        text_color = _t["fg"]
        grid_color = _t["bg3"]

        self.fig.clear()
        self._clear_cursors()
        self.fig.patch.set_facecolor(bg_color)

        if not sel:
            if hasattr(self, '_legend_panel'):
                self._legend_panel.grid(row=0, column=1, sticky='ns')
            self._update_tk_legend([])
            ax = self.fig.add_subplot(111)
            ax.set_facecolor(bg2_color)
            ax.text(0.5, 0.5, "No Sensors Selected", ha='center', va='center', color='gray')
            self.canvas_widget.draw_idle()
            return

        import matplotlib.colors as mcolors
        import matplotlib.cm as mcm

        _hm = self._get_theme()
        band_colors = [
            (0.00, _hm.get("hm_safe", "#1a7a3a")),
            (0.55, _hm.get("hm_ok",   "#2ecc71")),
            (0.60, _hm.get("hm_warn",  "#f1c40f")),
            (0.80, _hm.get("hm_hot",   "#e67e22")),
            (0.85, _hm.get("hm_crit",  "#922b21")),
            (1.00, _hm.get("hm_max",   "#641e16")),
        ]
        cmap_discrete = mcolors.LinearSegmentedColormap.from_list(
            'threshold_map',
            [(pos, col) for pos, col in band_colors],
            N=512)

        def _get_limit(col: str):
            """Return the configured danger threshold for this sensor, or None."""
            raw  = col.upper()
            name = raw.replace(" ", "")

            if any(x in name for x in ['TEMP', '°C', 'HOTSPOT', 'TDIE', 'TCTL']):
                matched_limit = None
                matched_len   = 0
                for key, limit in self.temp_limits.items():
                    key_norm = key.upper().replace(" ", "")
                    if key_norm in name and len(key_norm) > matched_len:
                        matched_limit = limit
                        matched_len   = len(key_norm)
                return matched_limit if matched_limit is not None else 90.0

            if '[%]' in raw and any(x in raw for x in ['USAGE', 'LOAD']):
                return 95.0

            if '[W]' in raw and 'LIMIT' not in raw and 'STATIC' not in raw:
                if 'CPU' in raw: return self.cpu_power_max
                if 'GPU' in raw: return self.gpu_power_max
                if 'TOTAL' in raw: return self.total_power_max

            if any(x in raw for x in ['FRAME TIME', 'FRAMETIME']):
                return self.frametime_max_ms

            if any(x in raw for x in ['LATENCY', 'GPU BUSY', 'CPU BUSY']):
                return self.latency_max_ms

            return None

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
                warn_start = limit * 0.75
                result = np.where(
                    data <= warn_start,
                    0.60 * (data / warn_start),
                    np.where(
                        data <= limit,
                        0.60 + 0.25 * ((data - warn_start) / (limit - warn_start)),
                        np.clip(0.85 + 0.15 * ((data - limit) / (limit * 0.15)), 0.85, 1.0)
                    )
                )
                return np.clip(result, 0.0, 1.0)

            for rail, (lo, hi) in self.volt_rails.items():
                if rail in raw and not any(x in raw for x in ['GPU PCIE', 'PCIE', '12VHPWR', 'INPUT']):
                    centre   = (lo + hi) / 2
                    half_tol = (hi - lo) / 2
                    dist = np.abs(data - centre) / half_tol
                    return np.clip(dist * 0.85, 0.0, 1.0)

            if 'RPM' in raw or 'FAN SPEED' in raw:
                mx = data.max()
                if mx > 0:
                    inv = 1.0 - np.clip(data / mx, 0.0, 1.0)
                    return inv * 0.85
                return np.zeros_like(data)

            if 'FPS' in raw or 'FRAMERATE' in raw:
                safe_fps = self.fps_min * 6
                return np.clip(1.0 - (data / max(safe_fps, 1.0)), 0.0, 0.95)

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
            short = col
            for bracket in ['[°C]', '[%]', '[MHz]', '[W]', '[V]', '[RPM]',
                            '[ms]', '[FPS]', '[A]', '[MB]', '[GB]']:
                short = short.replace(bracket, '').strip()
            labels.append(short[:45])

        matrix = np.array(matrix)

        x_vals, ts, use_time = self._get_x_axis()

        ax = self.fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        extent = [x_vals[0], x_vals[-1], len(sel) - 0.5, -0.5]
        ax.imshow(matrix, aspect='auto', cmap=cmap_discrete,
                  vmin=0, vmax=1, extent=extent,
                  interpolation='nearest', origin='upper')

        for i in range(1, len(sel)):
            ax.axhline(i - 0.5, color=grid_color, lw=1.0)

        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, color=text_color, fontsize=7)
        ax.tick_params(axis='y', length=0)

        ax.tick_params(axis='x', colors=text_color, labelsize=8)
        if use_time:
            import matplotlib.ticker as ticker
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(
                lambda v, _: self._format_elapsed(v)))
            ax.tick_params(axis='x', labelrotation=30)

        sm = mcm.ScalarMappable(cmap=cmap_discrete,
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
        ax.set_title("Sensor Heatmap  -  Green: safe  |  Yellow: approaching limit  |  Red: at/above limit",
                     color=text_color, fontsize=8, pad=6)

        try:
            self.fig.tight_layout(h_pad=0.5)
        except Exception:
            pass
        self.canvas_widget.draw_idle()

        self._heatmap_matrix_raw = raw_data_map
        self._heatmap_sel        = sel
        self._heatmap_x_vals     = x_vals

    def _toggle_session_compare(self):
        if self.session_compare_active:
            self._close_session_compare()
            if hasattr(self, 'session_cmp_btn'):
                self.session_cmp_btn.config(text="📊 Session Compare")
        else:
            if hasattr(self, 'session_cmp_btn'):
                self.session_cmp_btn.config(text="📊 Session Compare: ON")
            self._open_session_compare()

    def _get_ref_x_axis(self):
        """Returns x values for the reference df, independent of current df length."""
        if self.ref_df is not None:
            return self.ref_df.index.values
        return None

    def _get_x_axis(self):
        """Returns (x_values, x_labels, use_time) - cached until CSV or time_mode changes."""
        cached = getattr(self, '_x_axis_cache', None)
        if cached is not None:
            return cached
        if self.time_mode and self.analyzer.time_series is not None:
            ts = self.analyzer.time_series
            if len(ts) != len(self.df):
                result = (self.df.index.values, None, False)
            else:
                x_vals = ts.dt.total_seconds().values
                result = (x_vals, ts, True)
        else:
            result = (self.df.index.values, None, False)
        self._x_axis_cache = result
        return result

    def _session_x_vals(self, session: dict):
        """Return normalised x values (seconds from 0) for a session dict."""
        analyzer = session['analyzer']
        df       = session['df']
        if self.time_mode and analyzer.time_series is not None and len(analyzer.time_series) == len(df):
            return analyzer.time_series.dt.total_seconds().values
        return df.index.values
    def _open_session_compare(self):
        self.session_compare_active = True
        if not self.sessions:
            self.sessions = [{'label': self.analyzer.path.stem,
                              'analyzer': self.analyzer,
                              'df': self.df,
                              'color': '#4f8ef7'}]
        self._draw_session_compare()
    def _close_session_compare(self):
        self.session_compare_active = False
        cmp_widget = getattr(self, '_cmp_widget', None)
        if cmp_widget and cmp_widget.winfo_exists():
            cmp_widget.destroy()
        self._cmp_widget = None
        self._cmp_fig    = None
        self._cmp_canvas = None
        self.root.bind('<Control-c>', lambda e: self._copy_png_to_clipboard())
        if hasattr(self, '_legend_panel'):
            self._legend_panel.grid(row=0, column=1, sticky='ns')
        self.update_plot()

    def _draw_session_compare(self):
        """Session compare: uses normal sensor checklist, multi-mode aware,
        crosshair tooltip, Ctrl+C support, no redundant exit button."""
        import numpy as np
        import matplotlib.ticker as _ticker
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        if not self.session_compare_active:
            return

        _t     = self._get_theme()
        bg     = _t['bg'];  bg2 = _t['bg2'];  bg3 = _t['bg3']
        fg     = _t['fg'];  accent = _t['accent']

        WIN_COLOR  = '#2ecc71'
        LOSE_COLOR = '#e74c3c'

        BASE6 = [_t.get(f'plot_c{i}', '#888') for i in range(6)]
        def _assign_colors():
            for i, s in enumerate(self.sessions):
                s['color'] = BASE6[i % len(BASE6)]
        _assign_colors()

        self.fig.clear()
        self._clear_cursors()
        self.fig.patch.set_facecolor(bg)

        if hasattr(self, '_legend_panel'):
            self._legend_panel.grid_remove()

        cmp_widget = getattr(self, '_cmp_widget', None)
        if cmp_widget and cmp_widget.winfo_exists():
            cmp_widget.destroy()

        plot_widget = self.canvas_widget.get_tk_widget()
        parent = plot_widget.master

        root_f = tk.Frame(parent, bg=bg)
        root_f.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        self._cmp_widget = root_f

        top_bar = tk.Frame(root_f, bg=bg2, pady=5, padx=10)
        top_bar.pack(fill='x', side='top')

        tk.Label(top_bar, text='📊  Session Compare',
                 font=('Segoe UI', 11, 'bold'), bg=bg2, fg=accent).pack(side='left')

        ttk.Button(top_bar, text='📄  Export Report',
                   command=self._export_compare_report).pack(side='right', padx=4)

        chart_mode_var = tk.StringVar(value='overlay')
        mode_f = tk.Frame(top_bar, bg=bg2)
        mode_f.pack(side='right', padx=12)
        tk.Label(mode_f, text='Chart:', bg=bg2, fg=fg,
                 font=('Segoe UI', 9)).pack(side='left', padx=(0, 4))
        for val, lbl in [('overlay', 'Overlay'), ('normalized', 'Normalized 0–100%')]:
            tk.Radiobutton(mode_f, text=lbl, variable=chart_mode_var, value=val,
                           bg=bg2, fg=fg, selectcolor=bg3, activebackground=bg2,
                           font=('Segoe UI', 9),
                           command=lambda: _refresh()).pack(side='left', padx=3)


        sess_bar = tk.Frame(root_f, bg=bg3, padx=10, pady=5)
        sess_bar.pack(fill='x', side='top')

        def _rebuild_session_chips():
            for w in sess_bar.winfo_children():
                w.destroy()
            for i, sess in enumerate(self.sessions):
                chip = tk.Frame(sess_bar, bg=sess['color'], padx=8, pady=3)
                chip.pack(side='left', padx=(0, 6))
                tk.Label(chip, text=sess['label'][:22],
                         bg=sess['color'], fg='#000',
                         font=('Segoe UI', 8, 'bold')).pack(side='left')
                if i > 0:
                    def _rm(idx=i):
                        self.sessions.pop(idx)
                        _assign_colors()
                        _rebuild_session_chips()
                        _refresh()
                    tk.Button(chip, text=' ✕', bg=sess['color'], fg='#000',
                              relief='flat', font=('Segoe UI', 8, 'bold'),
                              cursor='hand2', padx=0, pady=0,
                              command=_rm).pack(side='left')

            def _add():
                if len(self.sessions) >= 6:
                    self.show_toast('Maximum 6 sessions')
                    return
                path = filedialog.askopenfilename(filetypes=[('CSV', '*.csv')])
                if not path:
                    return
                def _on_load(analyzer):
                    self.sessions.append({'label': analyzer.path.stem[:22],
                                          'analyzer': analyzer,
                                          'df': analyzer.df,
                                          'color': '#888'})
                    _assign_colors()
                    _rebuild_session_chips()
                    _refresh()
                self._load_csv_threaded(path, on_success=_on_load)

            ttk.Button(sess_bar, text='＋  Add Session',
                       command=_add).pack(side='left')

        _rebuild_session_chips()

        hint_bar = tk.Frame(root_f, bg=bg2, padx=10, pady=4)
        hint_bar.pack(fill='x', side='top')
        tk.Label(hint_bar,
                 text='Select sensors using the checklist on the left  •  Multi mode applies here too',
                 bg=bg2, fg='#888', font=('Segoe UI', 8)).pack(side='left')

        paned = tk.PanedWindow(root_f, orient='vertical',
                               bg=bg, sashwidth=6, sashrelief='flat', sashpad=2)
        paned.pack(fill='both', expand=True)

        chart_f = tk.Frame(paned, bg=bg)
        table_f = tk.Frame(paned, bg=bg)
        paned.add(chart_f, stretch='always', minsize=140)
        paned.add(table_f, stretch='always', minsize=100)

        def _set_initial_sash(event=None):
            h = paned.winfo_height()
            if h > 10:
                paned.sash_place(0, 0, int(h * 0.35))
                paned.unbind('<Map>')
        paned.bind('<Map>', _set_initial_sash)

        cmp_fig    = Figure(figsize=(10, 4))
        cmp_canvas = FigureCanvasTkAgg(cmp_fig, master=chart_f)
        cmp_canvas.get_tk_widget().pack(fill='both', expand=True)
        self._cmp_fig    = cmp_fig
        self._cmp_canvas = cmp_canvas

        def _cmp_copy(event=None):
            try:
                import io, sys, ctypes
                from PIL import Image, ImageGrab

                cmp_fig.canvas.draw()
                buf = io.BytesIO()
                cmp_fig.savefig(buf, format='png', dpi=150,
                                bbox_inches='tight',
                                facecolor=cmp_fig.get_facecolor())
                buf.seek(0)
                chart_img = Image.open(buf).convert('RGB')

                table_img = None
                try:
                    if table_f.winfo_exists() and table_f.winfo_width() > 10:
                        self.root.update_idletasks()
                        tx = table_f.winfo_rootx()
                        ty = table_f.winfo_rooty()
                        tw = table_f.winfo_width()
                        th = table_f.winfo_height()
                        if tw > 10 and th > 10:
                            table_img = ImageGrab.grab(bbox=(tx, ty, tx + tw, ty + th)).convert('RGB')
                except Exception:
                    table_img = None

                if table_img is not None:
                    scale   = chart_img.width / table_img.width
                    new_th  = int(table_img.height * scale)
                    table_img = table_img.resize((chart_img.width, new_th), Image.LANCZOS)
                    total_h = chart_img.height + new_th
                    fc      = cmp_fig.get_facecolor()
                    bg_col  = tuple(int(fc[i] * 255) for i in range(3))
                    composite = Image.new('RGB', (chart_img.width, total_h), bg_col)
                    composite.paste(chart_img, (0, 0))
                    composite.paste(table_img, (0, chart_img.height))
                    final = composite
                else:
                    final = chart_img

                if sys.platform == 'win32':
                    k32 = ctypes.windll.kernel32
                    u32 = ctypes.windll.user32
                    k32.GlobalAlloc.restype   = ctypes.c_void_p
                    k32.GlobalAlloc.argtypes  = [ctypes.c_uint, ctypes.c_size_t]
                    k32.GlobalLock.restype    = ctypes.c_void_p
                    k32.GlobalLock.argtypes   = [ctypes.c_void_p]
                    k32.GlobalUnlock.argtypes = [ctypes.c_void_p]
                    u32.SetClipboardData.restype  = ctypes.c_void_p
                    u32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
                    u32.OpenClipboard.argtypes    = [ctypes.c_void_p]
                    u32.OpenClipboard.restype     = ctypes.c_bool
                    hwnd = ctypes.windll.user32.GetForegroundWindow()
                    out = io.BytesIO()
                    final.save(out, 'BMP')
                    data = out.getvalue()[14:]
                    import time as _time
                    for _attempt in range(5):
                        if u32.OpenClipboard(hwnd):
                            break
                        _time.sleep(0.05)
                    else:
                        self.show_toast('Clipboard locked – try again')
                        return
                    u32.EmptyClipboard()
                    h_mem = k32.GlobalAlloc(0x0042, len(data))
                    ptr   = k32.GlobalLock(h_mem)
                    ctypes.memmove(ptr, data, len(data))
                    k32.GlobalUnlock(h_mem)
                    u32.SetClipboardData(8, h_mem)
                    u32.CloseClipboard()
                    self.show_toast('Compare chart + table copied to clipboard')
                else:
                    self.show_toast('Clipboard copy is Windows-only')
            except Exception as e:
                self.show_toast(f'Copy failed: {e}')

        self.root.bind('<Control-c>', _cmp_copy)

        lower_is_better_kw = ['TEMP', '°C', 'FRAME TIME', 'FRAMETIME', '[MS]',
                               'LATENCY', 'POWER', 'VRAM USED', 'RAM USED']
        def _lib(col):
            u = col.upper()
            return any(k in u for k in lower_is_better_kw) and 'FPS' not in u

        def _pct(series, p):
            try:    return float(np.percentile(series.dropna(), p))
            except: return float('nan')

        STAT_COLS = [
            ('Min',  lambda s: float(s.min())),
            ('Avg',  lambda s: float(s.mean())),
            ('Max',  lambda s: float(s.max())),
            ('P1',   lambda s: _pct(s, 1)),
            ('P95',  lambda s: _pct(s, 95)),
            ('P99',  lambda s: _pct(s, 99)),
            ('σ',    lambda s: float(s.std())),
        ]

        def _build_table(sensors):
            try:
                if not table_f.winfo_exists():
                    return
                for w in table_f.winfo_children():
                    w.destroy()
            except Exception:
                return
            if not sensors or not self.sessions:
                return

            canv = tk.Canvas(table_f, bg=bg, highlightthickness=0)
            vsb  = tk.Scrollbar(table_f, orient='vertical', command=canv.yview,
                                bg=bg3, troughcolor=bg, activebackground=accent)
            canv.configure(yscrollcommand=vsb.set)
            vsb.pack(side='right', fill='y')
            canv.pack(fill='both', expand=True)

            tbl = tk.Frame(canv, bg=bg)
            win_id = canv.create_window((0, 0), window=tbl, anchor='nw')
            tbl.bind('<Configure>',
                     lambda e: canv.configure(scrollregion=canv.bbox('all')))
            canv.bind('<Configure>',
                      lambda e: canv.itemconfig(win_id, width=e.width))

            n_cols = len(STAT_COLS) + 3
            tbl.columnconfigure(0, weight=3)
            for _ci in range(1, n_cols):
                tbl.columnconfigure(_ci, weight=1)

            def _scroll(e):
                try:
                    canv.yview_scroll(int(-1 * (e.delta / 120)), 'units')
                except Exception:
                    pass

            canv.bind('<MouseWheel>', _scroll)
            tbl.bind('<MouseWheel>',  _scroll)
            canv.bind('<Enter>', lambda _: canv.bind_all('<MouseWheel>', _scroll))
            canv.bind('<Leave>', lambda _: canv.unbind_all('<MouseWheel>'))

            def _cell(parent, text, r, c,
                      bold=False, bg_=bg2, fg_=fg, anchor_='center'):
                lbl = tk.Label(parent, text=text,
                               font=('Segoe UI', 8, 'bold' if bold else 'normal'),
                               bg=bg_, fg=fg_, anchor=anchor_,
                               padx=4, pady=4, relief='flat')
                lbl.grid(row=r, column=c, sticky='ew', padx=1, pady=1)
                lbl.bind('<MouseWheel>', _scroll)

            _cell(tbl, 'Sensor / Session', 0, 0,
                  bold=True, bg_=bg3, fg_=accent, anchor_='w')
            for ci, (sn, _) in enumerate(STAT_COLS, start=1):
                _cell(tbl, sn, 0, ci, bold=True, bg_=bg3, fg_=accent)
            _cell(tbl, 'Δ Avg vs S1', 0, len(STAT_COLS)+1,
                  bold=True, bg_=bg3, fg_=accent)
            _cell(tbl, 'Δ Avg %',     0, len(STAT_COLS)+2,
                  bold=True, bg_=bg3, fg_=accent)

            row_idx = 1

            for sensor in sensors:
                lib = _lib(sensor)

                stat_rows = []
                base_avg  = None
                for sess in self.sessions:
                    df_s = sess['df']
                    if sensor not in df_s.columns:
                        stat_rows.append(None)
                        continue
                    s = df_s[sensor].dropna()
                    d = {fn: func(s) for fn, func in STAT_COLS}
                    if base_avg is None:
                        base_avg = d['Avg']
                    stat_rows.append(d)

                short = sensor[:40] + ('…' if len(sensor) > 40 else '')
                tk.Label(tbl, text=f'  {short}',
                         font=('Segoe UI', 8, 'bold'),
                         bg=bg3, fg=accent,
                         anchor='w', padx=4, pady=3
                         ).grid(row=row_idx, column=0,
                                columnspan=len(STAT_COLS)+3,
                                sticky='ew', padx=1, pady=(4, 0))
                row_idx += 1

                for si, (sess, d) in enumerate(zip(self.sessions, stat_rows)):
                    row_bg = bg if si % 2 == 0 else bg2

                    name_f = tk.Frame(tbl, bg=sess['color'], padx=3)
                    name_f.grid(row=row_idx, column=0, sticky='ew', padx=1, pady=1)
                    name_lbl = tk.Label(name_f, text=sess['label'][:24],
                                        bg=sess['color'], fg='#000',
                                        font=('Segoe UI', 8, 'bold'),
                                        anchor='w', padx=4)
                    name_lbl.pack(fill='x')
                    name_f.bind('<MouseWheel>',   _scroll)
                    name_lbl.bind('<MouseWheel>', _scroll)

                    if d is None:
                        for ci in range(1, len(STAT_COLS)+3):
                            _cell(tbl, '—', row_idx, ci, bg_=row_bg, fg_='#555')
                        row_idx += 1
                        continue

                    for ci, (sn, _) in enumerate(STAT_COLS, start=1):
                        val = d[sn]
                        if val != val:
                            _cell(tbl, '—', row_idx, ci, bg_=row_bg, fg_='#555')
                            continue
                        other_vals = [stat_rows[j][sn] for j in range(len(self.sessions))
                                      if stat_rows[j] is not None]
                        if len(other_vals) > 1:
                            is_best  = val == (min(other_vals) if (lib or sn == 'σ') else max(other_vals))
                            is_worst = val == (max(other_vals) if (lib or sn == 'σ') else min(other_vals))
                        else:
                            is_best = is_worst = False
                        badge_fg = WIN_COLOR if is_best else (LOSE_COLOR if is_worst else fg)
                        prefix   = '▲ ' if is_best else ('▼ ' if is_worst else '')
                        _cell(tbl, f'{prefix}{val:.2f}', row_idx, ci,
                              bold=is_best, bg_=row_bg, fg_=badge_fg)

                    d_col = len(STAT_COLS)+1
                    if si == 0:
                        _cell(tbl, 'baseline', row_idx, d_col,   bg_=row_bg, fg_='#888')
                        _cell(tbl, '—',        row_idx, d_col+1, bg_=row_bg, fg_='#888')
                    else:
                        delta  = d['Avg'] - base_avg
                        better = (delta < 0) if lib else (delta > 0)
                        d_fg   = WIN_COLOR if better else (LOSE_COLOR if delta != 0 else fg)
                        sign   = '+' if delta >= 0 else ''
                        pct_d  = (delta / abs(base_avg) * 100) if base_avg else float('nan')
                        pct_s  = f'{sign}{pct_d:.1f}%' if pct_d == pct_d else '—'
                        _cell(tbl, f'{sign}{delta:.2f}', row_idx, d_col,
                              bold=abs(delta) > 0, bg_=row_bg, fg_=d_fg)
                        _cell(tbl, pct_s, row_idx, d_col+1,
                              bold=abs(delta) > 0, bg_=row_bg, fg_=d_fg)

                    row_idx += 1

        _cmp_cursor_lines = []
        _cmp_tooltip      = [None]
        _cmp_last_idx     = [-1]

        def _cmp_on_move(event):
            if event.inaxes is None:
                for ln in _cmp_cursor_lines: ln.remove()
                _cmp_cursor_lines.clear()
                if _cmp_tooltip[0]:
                    _cmp_tooltip[0].set_visible(False)
                cmp_canvas.draw_idle()
                _cmp_last_idx[0] = -1
                return

            sensors = [c for c, v in self.vars.items() if v.get()]
            if not sensors or not self.sessions:
                return

            x0 = self._session_x_vals(self.sessions[0])
            raw_x = event.xdata
            idx = int(np.argmin(np.abs(x0 - raw_x))) if raw_x is not None else 0

            if idx == _cmp_last_idx[0]:
                return
            _cmp_last_idx[0] = idx

            for ln in _cmp_cursor_lines: ln.remove()
            _cmp_cursor_lines.clear()
            if _cmp_tooltip[0]:
                try: _cmp_tooltip[0].remove()
                except Exception: pass
                _cmp_tooltip[0] = None

            ax = event.inaxes
            cursor_col = 'white' if self.is_dark else 'gray'
            _cmp_cursor_lines.append(ax.axvline(x=raw_x, color=cursor_col,
                                                ls='--', alpha=0.5, lw=1))

            _t2 = self._get_theme()
            fc  = _t2['bg2']
            tc  = _t2['fg']

            lines_txt = []
            use_time  = self.time_mode
            x_label   = self._format_elapsed(raw_x) if use_time else f'Rec: {idx}'
            lines_txt.append(x_label)

            for sensor in sensors[:6]:
                for sess in self.sessions:
                    y_arr = sess['df'].get(sensor, None)
                    if y_arr is None:
                        continue
                    y_arr = y_arr.ffill().values.astype(float)
                    yi = min(idx, len(y_arr)-1)
                    lines_txt.append(f"{sess['label'][:16]}  {sensor[:24]}: {y_arr[yi]:.2f}")

            txt = '\n'.join(lines_txt)
            _cmp_tooltip[0] = cmp_fig.text(
                0.01, 0.99, txt, va='top', ha='left',
                bbox=dict(boxstyle='round', facecolor=fc, alpha=0.85, edgecolor='#555'),
                fontsize=7.5, color=tc, zorder=10)
            cmp_canvas.draw_idle()

        cmp_canvas.mpl_connect('motion_notify_event', _cmp_on_move)
        cmp_canvas.mpl_connect('axes_leave_event',
            lambda e: (
                [ln.remove() for ln in _cmp_cursor_lines],
                _cmp_cursor_lines.clear(),
                _cmp_tooltip[0].set_visible(False) if _cmp_tooltip[0] else None,
                cmp_canvas.draw_idle()
            ))

        def _refresh():
            cmp_fig.clear()
            cmp_fig.patch.set_facecolor(bg)

            sensors = [c for c, v in self.vars.items()
                       if v.get() and any(c in s['df'].columns for s in self.sessions)]

            if not sensors or not self.sessions:
                ax = cmp_fig.add_subplot(111)
                ax.set_facecolor(bg2)
                ax.tick_params(colors=fg, labelsize=8)
                ax.text(0.5, 0.5, 'No sensors selected — use the left panel',
                        ha='center', va='center', color='#888',
                        transform=ax.transAxes)
                cmp_canvas.draw_idle()
                _build_table([])
                return

            use_time = self.time_mode
            mode     = chart_mode_var.get()
            multi    = self.multi_mode

            if multi and len(sensors) > 1:
                from matplotlib.gridspec import GridSpec
                n_plots = len(sensors)
                gs = GridSpec(n_plots, 1, figure=cmp_fig, hspace=0.15)
                axes = []
                for pi, sensor in enumerate(sensors):
                    ax = cmp_fig.add_subplot(gs[pi], sharex=axes[0] if axes else None)
                    axes.append(ax)
                    ax.set_facecolor(bg2)
                    ax.tick_params(colors=fg, labelsize=7)
                    ax.grid(True, ls=':', alpha=0.4, color=bg3)
                    for spine in ax.spines.values():
                        spine.set_edgecolor(bg3)
                    lib = _lib(sensor)
                    session1_vals = None
                    for si, sess in enumerate(self.sessions):
                        if sensor not in sess['df'].columns:
                            continue
                        x = self._session_x_vals(sess)
                        y = sess['df'][sensor].ffill().values.astype(float)
                        if mode == 'normalized':
                            mn, mx = np.nanmin(y), np.nanmax(y)
                            y_plot = (y - mn) / (mx - mn) * 100 if mx > mn else np.zeros_like(y)
                        else:
                            y_plot = y
                        ax.plot(x, y_plot, color=sess['color'], lw=1.6,
                                label=sess['label'], alpha=0.92, zorder=3)
                        if mode == 'overlay' and si == 0:
                            session1_vals = (x, y_plot)
                        elif mode == 'overlay' and session1_vals is not None:
                            x1a, y1a = session1_vals
                            ml = min(len(x1a), len(x), len(y1a), len(y_plot))
                            if ml > 1:
                                better = (y_plot[:ml] < y1a[:ml]) if lib else (y_plot[:ml] > y1a[:ml])
                                ax.fill_between(x1a[:ml], y1a[:ml], y_plot[:ml],
                                                where=better,  alpha=0.12, color=WIN_COLOR, zorder=2)
                                ax.fill_between(x1a[:ml], y1a[:ml], y_plot[:ml],
                                                where=~better, alpha=0.12, color=LOSE_COLOR, zorder=2)
                    short = sensor.split('[')[0].strip()[:30]
                    ax.set_ylabel(short, color=fg, fontsize=7, labelpad=2)
                    if use_time:
                        ax.xaxis.set_major_formatter(
                            _ticker.FuncFormatter(lambda v, _: self._format_elapsed(v)))
                    if pi < n_plots - 1:
                        for lbl in ax.get_xticklabels():
                            lbl.set_visible(False)
                    ax.legend_.remove() if ax.get_legend() else None

            else:
                ax = cmp_fig.add_subplot(111)
                ax.set_facecolor(bg2)
                ax.tick_params(colors=fg, labelsize=8)
                ax.grid(True, ls=':', alpha=0.4, color=bg3)
                for spine in ax.spines.values():
                    spine.set_edgecolor(bg3)

                sensor = sensors[0]
                lib = _lib(sensor)
                session1_vals = None

                for si, sess in enumerate(self.sessions):
                    if sensor not in sess['df'].columns:
                        continue
                    x = self._session_x_vals(sess)
                    y = sess['df'][sensor].ffill().values.astype(float)
                    if mode == 'normalized':
                        mn, mx = np.nanmin(y), np.nanmax(y)
                        y_plot = (y - mn) / (mx - mn) * 100 if mx > mn else np.zeros_like(y)
                    else:
                        y_plot = y
                    ax.plot(x, y_plot, color=sess['color'], lw=1.8,
                            label=sess['label'], alpha=0.92, zorder=3)
                    if mode == 'overlay' and si == 0:
                        session1_vals = (x, y_plot)
                    elif mode == 'overlay' and session1_vals is not None:
                        x1a, y1a = session1_vals
                        ml = min(len(x1a), len(x), len(y1a), len(y_plot))
                        if ml > 1:
                            better = (y_plot[:ml] < y1a[:ml]) if lib else (y_plot[:ml] > y1a[:ml])
                            ax.fill_between(x1a[:ml], y1a[:ml], y_plot[:ml],
                                            where=better,  alpha=0.12, color=WIN_COLOR, zorder=2)
                            ax.fill_between(x1a[:ml], y1a[:ml], y_plot[:ml],
                                            where=~better, alpha=0.12, color=LOSE_COLOR, zorder=2)

                if use_time:
                    ax.xaxis.set_major_formatter(
                        _ticker.FuncFormatter(lambda v, _: self._format_elapsed(v)))
                    ax.tick_params(axis='x', labelrotation=20)
                    ax.set_xlabel('Elapsed Time', color=fg, fontsize=8)
                else:
                    ax.set_xlabel('Sample Index', color=fg, fontsize=8)

                y_label = '% of range' if mode == 'normalized' else sensor[:50]
                ax.set_ylabel(y_label, color=fg, fontsize=8)
                title_sfx = '  (normalized 0–100%)' if mode == 'normalized' else ''
                ax.set_title(f'{sensor[:60]}{title_sfx}', color=fg, fontsize=9, pad=4)

            try:
                cmp_fig.tight_layout()
            except Exception:
                pass

            _seen_labels = set()
            _leg_handles = []
            _leg_labels  = []
            for _ax in cmp_fig.axes:
                for _line in _ax.get_lines():
                    _lbl = _line.get_label()
                    if _lbl and not _lbl.startswith('_') and _lbl not in _seen_labels:
                        _seen_labels.add(_lbl)
                        _leg_handles.append(_line)
                        _leg_labels.append(_lbl)
            if _leg_handles:
                _ncol = max(1, len(_leg_handles))
                _fig_leg = cmp_fig.legend(
                    _leg_handles, _leg_labels,
                    loc='upper center',
                    bbox_to_anchor=(0.5, 1.0),
                    ncol=_ncol,
                    fontsize=8,
                    frameon=True,
                    framealpha=0.85,
                    facecolor=bg2,
                    edgecolor=bg3,
                    borderpad=0.5,
                    columnspacing=1.2,
                )
                for _t in _fig_leg.get_texts():
                    _t.set_color(fg)
                try:
                    cmp_fig.subplots_adjust(top=0.88)
                except Exception:
                    pass

            cmp_canvas.draw_idle()
            _build_table(sensors)

        def _on_var_change(*_):
            try:
                if self.session_compare_active and root_f.winfo_exists():
                    _refresh()
            except Exception:
                pass

        for v in self.vars.values():
            v.trace_add('write', _on_var_change)

        _refresh()

    def _export_compare_report(self):
        """Export compare report with loading bar spinner."""
        import datetime, html as html_mod, io, base64, threading, traceback
        import numpy as np
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        import matplotlib.ticker as _ticker

        f_path = filedialog.asksaveasfilename(
            defaultextension='.html',
            filetypes=[('HTML Report', '*.html')],
            initialfile=(f"RESYNC_Compare_"
                         f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        )
        if not f_path:
            return

        is_dark = self.is_dark
        _t = self._get_theme(); bg = _t['bg']; fg = _t['fg']; accent = _t['accent']

        wait_win = tk.Toplevel(self.root)
        wait_win.title('Generating Report')
        wait_win.resizable(False, False)
        wait_win.protocol('WM_DELETE_WINDOW', lambda: None)
        wait_win.configure(bg=bg)
        self.root.update_idletasks()
        pw, ph = 340, 120
        rx = self.root.winfo_x() + (self.root.winfo_width()  // 2) - pw // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() // 2) - ph // 2
        wait_win.geometry(f'{pw}x{ph}+{rx}+{ry}')
        wait_win.transient(self.root)
        wait_win.grab_set()

        outer = tk.Frame(wait_win, bg=accent, padx=2, pady=2)
        outer.pack(fill='both', expand=True)
        inner = tk.Frame(outer, bg=bg, padx=20, pady=16)
        inner.pack(fill='both', expand=True)

        title_row = tk.Frame(inner, bg=bg)
        title_row.pack(anchor='w')
        tk.Label(title_row, text='📄  Generating Compare Report',
                 font=('Segoe UI', 10, 'bold'), bg=bg, fg=accent).pack(side='left')
        spin_var = tk.StringVar(value=' ⠋')
        tk.Label(title_row, textvariable=spin_var,
                 font=('Segoe UI', 10), bg=bg, fg=accent).pack(side='left', padx=(6, 0))

        status_var = tk.StringVar(value='Preparing data…')
        tk.Label(inner, textvariable=status_var,
                 font=('Segoe UI', 9), bg=bg, fg='#888').pack(anchor='w', pady=(6, 0))

        bar_frame = tk.Frame(inner, bg=bg)
        bar_frame.pack(fill='x', pady=(8, 0))
        bar_bg = tk.Frame(bar_frame, bg='#2a2a2a' if is_dark else '#dee2e6', height=4)
        bar_bg.pack(fill='x')
        bar_fg = tk.Frame(bar_bg, bg=accent, height=4)
        bar_fg.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        _SPIN = [' ⠋',' ⠙',' ⠹',' ⠸',' ⠼',' ⠴',' ⠦',' ⠧',' ⠇',' ⠏']
        _si = [0]
        def _tick():
            if not wait_win.winfo_exists(): return
            _si[0] = (_si[0] + 1) % len(_SPIN)
            spin_var.set(_SPIN[_si[0]])
            wait_win.after(80, _tick)
        _tick()

        def _set_status(msg, prog=None):
            def _do():
                if not wait_win.winfo_exists(): return
                status_var.set(msg)
                if prog is not None:
                    bar_fg.place(relwidth=min(prog, 1.0))
            self.root.after(0, _do)

        def _close_wait():
            def _do():
                if wait_win.winfo_exists():
                    wait_win.grab_release()
                    wait_win.destroy()
            self.root.after(0, _do)

        def _generate():
            try:
                sensors  = [c for c, v in self.vars.items() if v.get()] or []
                use_time = self.time_mode

                lower_is_better_kw = ['TEMP', '°C', 'FRAME TIME', 'FRAMETIME', '[MS]',
                                       'LATENCY', 'POWER', 'VRAM USED', 'RAM USED']
                def _lib(col):
                    u = col.upper()
                    return any(k in u for k in lower_is_better_kw) and 'FPS' not in u

                def _pct2(series, p):
                    try:    return float(np.percentile(series.dropna(), p))
                    except: return float('nan')

                STAT_COLS = [
                    ('Min',  lambda s: float(s.min())),
                    ('Avg',  lambda s: float(s.mean())),
                    ('Max',  lambda s: float(s.max())),
                    ('P1',   lambda s: _pct2(s, 1)),
                    ('P95',  lambda s: _pct2(s, 95)),
                    ('P99',  lambda s: _pct2(s, 99)),
                    ('σ',    lambda s: float(s.std())),
                ]

                def _fig_to_b64(fig):
                    FigureCanvasAgg(fig)
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=150,
                                bbox_inches='tight', facecolor='#0d0d1a')
                    buf.seek(0)
                    return base64.b64encode(buf.read()).decode()

                _set_status('Rendering charts…', 0.15)

                chart_blocks = []
                for sensor in sensors[:8]:
                    fig = Figure(figsize=(13, 3.5))
                    fig.patch.set_facecolor('#0d0d1a')
                    ax = fig.add_subplot(111)
                    ax.set_facecolor('#13132b')
                    lib = _lib(sensor)
                    session1_vals = None
                    for si, sess in enumerate(self.sessions):
                        if sensor not in sess['df'].columns:
                            continue
                        x = self._session_x_vals(sess)
                        y = sess['df'][sensor].ffill().values.astype(float)
                        ax.plot(x, y, lw=1.5, color=sess['color'],
                                label=sess['label'], alpha=0.85)
                        if si == 0:
                            session1_vals = (x, y)
                        elif session1_vals is not None:
                            x1, y1 = session1_vals
                            ml = min(len(x1), len(x), len(y1), len(y))
                            better = (y[:ml] < y1[:ml]) if lib else (y[:ml] > y1[:ml])
                            ax.fill_between(x1[:ml], y1[:ml], y[:ml],
                                            where=better,  alpha=0.10, color='#2ecc71')
                            ax.fill_between(x1[:ml], y1[:ml], y[:ml],
                                            where=~better, alpha=0.10, color='#e74c3c')
                    if use_time:
                        ax.xaxis.set_major_formatter(
                            _ticker.FuncFormatter(lambda v, _: self._format_elapsed(v)))
                    ax.set_title(sensor[:70], color='#a0c4ff', fontsize=8, pad=3)
                    ax.tick_params(colors='#ccc', labelsize=7)
                    ax.grid(True, ls=':', alpha=0.3, color='#444')
                    for spine in ax.spines.values():
                        spine.set_edgecolor('#333')
                    leg = ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1),
                                    fontsize=6, frameon=False)
                    if leg:
                        for t in leg.get_texts():
                            t.set_color('#ddd')
                    fig.subplots_adjust(right=0.72)
                    b64 = _fig_to_b64(fig)
                    fig.clf()
                    chart_blocks.append(
                        f'<h3 style="color:#a78bfa;margin-top:18px">{html_mod.escape(sensor)}</h3>'
                        f'<figure><img src="data:image/png;base64,{b64}" '
                        f'style="width:100%;border-radius:8px;"></figure>'
                    )

                _set_status('Building stats table…', 0.70)

                hdr_sess = ''.join(
                    f'<th colspan="{len(STAT_COLS) + (2 if si > 0 else 0)}" '
                    f'style="color:{s["color"]}">{html_mod.escape(s["label"])}</th>'
                    for si, s in enumerate(self.sessions)
                )
                sub_hdr = '<tr><th></th>'
                for si in range(len(self.sessions)):
                    for sn, _ in STAT_COLS:
                        sub_hdr += f'<th>{sn}</th>'
                    if si > 0:
                        sub_hdr += '<th>Δ Avg</th><th>Δ%</th>'
                sub_hdr += '</tr>'

                rows_html = ''
                for sensor in sensors:
                    lib = _lib(sensor)
                    stat_rows = []
                    base_avg  = None
                    for sess in self.sessions:
                        df_s = sess['df']
                        if sensor not in df_s.columns:
                            stat_rows.append(None)
                            continue
                        s = df_s[sensor].dropna()
                        d = {fn: func(s) for fn, func in STAT_COLS}
                        if base_avg is None:
                            base_avg = d['Avg']
                        stat_rows.append(d)

                    row = f'<tr><td>{html_mod.escape(sensor)}</td>'
                    for si, (sess, d) in enumerate(zip(self.sessions, stat_rows)):
                        if d is None:
                            row += (f'<td colspan="{len(STAT_COLS)+(2 if si>0 else 0)}">—</td>')
                            continue
                        for sn, _ in STAT_COLS:
                            vals = [stat_rows[j][sn] for j in range(len(self.sessions))
                                    if stat_rows[j] is not None]
                            if len(vals) > 1:
                                best  = min(vals) if (lib or sn == 'σ') else max(vals)
                                worst = max(vals) if (lib or sn == 'σ') else min(vals)
                                style = ('color:#2ecc71;font-weight:bold' if d[sn] == best
                                         else 'color:#e74c3c' if d[sn] == worst else '')
                            else:
                                style = ''
                            row += f'<td style="{style}">{d[sn]:.2f}</td>'
                        if si > 0 and base_avg is not None:
                            delta  = d['Avg'] - base_avg
                            better = (delta < 0) if lib else (delta > 0)
                            col_s  = '#2ecc71' if better else ('#e74c3c' if delta != 0 else '#aaa')
                            sign   = '+' if delta >= 0 else ''
                            pct_d  = (delta / abs(base_avg) * 100) if base_avg else float('nan')
                            pct_s  = f'{sign}{pct_d:.1f}%' if pct_d == pct_d else '—'
                            row += (f'<td style="color:{col_s};font-weight:bold">'
                                    f'{sign}{delta:.2f}</td>'
                                    f'<td style="color:{col_s}">{pct_s}</td>')
                    rows_html += row + '</tr>'

                _set_status('Writing file…', 0.90)

                generated_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                charts_html  = '\n'.join(chart_blocks) if chart_blocks\
                               else "<p style='color:#64748b'>No sensors selected.</p>"
                sess_list    = ''.join(
                    '<li style="color:' + s['color'] + '">' + html_mod.escape(s['label']) + '</li>'
                    for s in self.sessions)

                html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>RESYNC.ERR Session Compare</title>
<style>
body{{background:#0d0d1a;color:#e2e8f0;font-family:'Segoe UI',sans-serif;padding:32px;}}
h1{{color:#4f8ef7;}}
h2{{color:#a78bfa;border-bottom:1px solid #1e1e3a;padding-bottom:6px;margin-top:28px;}}
h3{{color:#a78bfa;margin-top:10px;}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin-top:12px;}}
th{{background:#1a1a38;color:#4f8ef7;padding:6px 10px;text-align:left;}}
td{{padding:5px 10px;border-bottom:1px solid #1e1e3a;}}
tr:hover td{{background:#13132b;}}
.footer{{color:#64748b;font-size:11px;margin-top:32px;}}
figure{{margin:0 0 8px;}}
figure img{{border-radius:8px;}}
</style></head><body>
<h1>RESYNC.ERR — Session Compare Report</h1>
<p style="color:#64748b">Generated {generated_at} · {len(self.sessions)} sessions · {len(sensors)} sensors</p>
<h2>Sessions</h2><ul>{sess_list}</ul>
<h2>Charts  <small style="color:#64748b;font-size:11px">green = S2 better · red = S2 worse</small></h2>
{charts_html}
<h2>Statistics  <small style="color:#64748b;font-size:11px">▲ green = best · ▼ red = worst</small></h2>
<table><thead><tr><th>Sensor</th>{hdr_sess}</tr>{sub_hdr}</thead>
<tbody>{rows_html}</tbody></table>
<p class="footer">RESYNC.ERR v{CURRENT_VERSION} · {generated_at}</p>
</body></html>"""

                with open(f_path, 'w', encoding='utf-8') as fh:
                    fh.write(html)

                fname = str(f_path).replace('\\', '/').split('/')[-1]
                def _done():
                    _close_wait()
                    self.show_toast(f'Report saved: {fname}')
                self.root.after(0, _done)

            except Exception as e:
                _err_text = f'{type(e).__name__}: {e}'
                def _fail():
                    _close_wait()
                    from tkinter import messagebox
                    messagebox.showerror('Export Error', _err_text)
                self.root.after(0, _fail)

        threading.Thread(target=_generate, daemon=True).start()


    def _invalidate_x_cache(self):
        self._x_axis_cache = None
        self._sensor_stats_cache = {}

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
        self.ref_analyzer = self.analyzer
        self.show_toast("Current log saved as Reference")
        self.compare_btn.config(state="normal")
        if hasattr(self, 'swap_ref_btn'):
            self.swap_ref_btn.config(state="normal")

    def _set_reference_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        def _on_success(analyzer):
            self.ref_df = analyzer.df.copy()
            self.ref_analyzer = analyzer
            self.show_toast(f"Reference set: {analyzer.path.name}")
            self.compare_btn.config(state="normal")
            if hasattr(self, 'swap_ref_btn'):
                self.swap_ref_btn.config(state="normal")
            if self.compare_mode:
                self.update_plot()
        def _on_error(exc):
            messagebox.showerror("Reference Load Error", str(exc))
        self._load_csv_threaded(path, on_success=_on_success, on_error=_on_error)

    def _swap_reference(self):
        if self.ref_df is None or self.ref_analyzer is None:
            return
        self.df, self.ref_df = self.ref_df, self.df.copy()
        self.analyzer, self.ref_analyzer = self.ref_analyzer, self.analyzer
        self._sig_hits  = []
        self._sig_dirty = True
        self._setup_ui()
        self._apply_theme_colors()
        self.update_plot()

    def _get_theme(self):
        """Return the active colour dict by name - user themes take priority, then built-ins."""
        active = self.custom_theme.get("active", "Dark (Default)")
        user = self.custom_theme.get("user_themes", {})
        if active in user:
            return dict(user[active])
        if active in BUILTIN_PRESETS:
            return {k: v for k, v in BUILTIN_PRESETS[active].items() if not k.startswith("_")}
        return dict(_DEFAULT_DARK_THEME)

    def _apply_theme_colors(self):
        t        = self._get_theme()
        bg       = t["bg"]
        fg       = t["fg"]
        accent   = t["accent"]
        hover_bg = t["bg3"]

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

        button_styles = ["TButton", "Action.TButton", "Delete.TButton", "Issue.TButton"]
        for s in button_styles:
            self.style.map(s,
                background=[('pressed', accent), ('active', hover_bg)],
                foreground=[('active', fg)],
                lightcolor=[('active', hover_bg)],
                darkcolor=[('active', hover_bg)],
                bordercolor=[('active', accent)]
            )

        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.configure("Alert.TCheckbutton", background=bg, foreground="#ff4d4d", font=('Segoe UI', 9, 'bold'))
        self.style.map("TCheckbutton", background=[('active', bg)])
        self.style.map("Alert.TCheckbutton", background=[('active', bg)])

        self.root.configure(bg=bg)
        self.canvas_checklist.configure(bg=bg)
        self.scroll_frame.configure(bg=bg)
        self.preset_canvas.configure(bg=bg)
        self.grp_f.configure(bg=bg)

        for hdr in self.header_widgets.values():
            hdr.configure(bg=bg, fg=accent if self.is_dark else "#2c3e50")

        if hasattr(self, '_diag_row_frame'):
            self._diag_row_frame.configure(bg=bg)
            for lbl in (self._badge_crit_lbl, self._badge_warn_lbl,
                        self._badge_info_lbl, self._badge_ok_lbl):
                try: lbl.configure(bg=bg)
                except Exception: pass

        if hasattr(self, '_legend_panel'):
            try:
                bg2 = t["bg2"]
                bg3 = t["bg3"]
                self._legend_panel.configure(bg=bg2)
                if hasattr(self, '_legend_canvas'):
                    self._legend_canvas.configure(bg=bg2)
                if hasattr(self, '_legend_scroll_frame'):
                    self._legend_scroll_frame.configure(bg=bg2)
                if hasattr(self, '_legend_inner'):
                    self._legend_inner.configure(bg=bg2)
                if hasattr(self, '_legend_title'):
                    self._legend_title.configure(bg=bg2, fg=accent)
                if hasattr(self, '_legend_vsb'):
                    self._legend_vsb.configure(bg=bg3, troughcolor=bg2,
                                               activebackground=accent)
                if hasattr(self, '_legend_scroll_frame'):
                    self._legend_scroll_frame.configure(bg=bg2)
            except Exception:
                pass

        if hasattr(self, 'sc_checklist'):
            try: self.sc_checklist.configure(bg=bg3, troughcolor=bg, activebackground=accent)
            except Exception: pass
        if hasattr(self, 'preset_scroll'):
            try: self.preset_scroll.configure(bg=bg3, troughcolor=bg, activebackground=accent)
            except Exception: pass

        self._style_mpl_toolbar()

    def _style_mpl_toolbar(self):
        """Recolor the matplotlib NavigationToolbar2Tk (plain Tk widgets, not
        ttk) so it doesn't show up as OS-default white/gray against a dark
        theme. Safe to call repeatedly (e.g. on every theme switch)."""
        toolbar = getattr(self, 'toolbar', None)
        if not toolbar or not toolbar.winfo_exists():
            return
        t   = self._get_theme()
        bg  = t["bg"]
        bg3 = t["bg3"]
        fg  = t["fg"]
        accent = t["accent"]
        try:
            _tf = getattr(self, '_toolbar_f', None)
            if _tf and _tf.winfo_exists():
                _tf.configure(bg=bg)
        except Exception:
            pass
        try:
            toolbar.configure(background=bg)
        except Exception:
            pass
        for child in toolbar.winfo_children():
            cls = child.winfo_class()
            try:
                if cls in ('Button', 'Checkbutton'):
                    child.configure(
                        background=bg, foreground=fg,
                        activebackground=bg3, activeforeground=fg,
                        highlightbackground=bg, highlightcolor=accent,
                        relief='flat', bd=0
                    )
                    if cls == 'Checkbutton':                
                        child.configure(
                            selectcolor=bg3,
                            indicatoron=False
                        )
                elif cls == 'Label':
                    child.configure(background=bg, foreground=fg)
                elif cls == 'Frame':
                    child.configure(background=bg)
                else:
                    child.configure(background=bg)
            except Exception:
                pass
        try:
            for button in getattr(toolbar, '_buttons', {}).values():
                if button is not None and button.winfo_exists():
                    toolbar._set_image_for_button(button)
        except Exception:
            pass
        try:
            toolbar.update_idletasks()
        except Exception:
            pass
    def _is_critical(self, col: str) -> bool:
        raw  = col.upper()
        name = raw.replace(' ', '')
        series = self.df[col].dropna()
        if series.empty:
            return False

        if any(x in raw for x in _EXCLUDE_RAW) or any(x in name for x in _EXCLUDE_NAME):
            return False

        if 'FRAME TIME' in raw or 'FRAMETIME' in raw:
            if '1% HIGH' in raw and '0.1%' not in raw:
                return series.max() > self.frametime_max_ms
            return False

        if 'FRAMERATE' in raw or ' FPS' in raw or 'FRAMES PER SECOND' in raw:
            if '0.1%' in raw and 'LOW' in raw and 'PRESENTED' not in raw:
                return series.min() <= self.fps_min and series.max() > 0
            return False

        if 'LATENCY' in raw or 'RENDER TIME' in raw or 'PRESENT TIME' in raw\
                or 'GPU BUSY' in raw or 'CPU BUSY' in raw or 'DISPLAY LATENCY' in raw:
            return series.max() > self.latency_max_ms

        if '[MS]' in raw:
            return False

        if any(x in raw for x in _THROTTLE_KW):
            return series.max() >= self.throttle_threshold

        if 'YES/NO' in raw:
            _ALWAYS_CRIT = (
                'DRIVE FAILURE', 'DRIVE FAIL',
                'CRITICAL TEMPERATURE', 'CORE CRITICAL',
                'PACKAGE/RING CRITICAL',
                'HARDWARE ERROR', 'WHEA',
                'PMIC HIGH TEMPERATURE', 'PMIC OVER VOLTAGE', 'PMIC UNDER VOLTAGE',
                'FATAL ERROR',
                'CHASSIS INTRUSION',
                'ELECTRICAL DESIGN POINT',
                'ICCMAX',
                'ICCmax PL4',
            )
            if any(k in raw for k in _ALWAYS_CRIT):
                return series.max() >= 1.0

            _WARN_THRESH = (
                'THERMAL THROTTL',
                'PACKAGE/RING THERMAL',
                'POWER LIMIT EXCEEDED',

                'IA: PROCHOT',
                'IA: THERMAL EVENT',
                'IA: RESIDENCY STATE REGULATION',
                'IA: RUNNING AVERAGE THERMAL LIMIT',
                'IA: VR THERMAL ALERT',
                'IA: VR TDC',
                'IA: PACKAGE-LEVEL RAPL',
                'IA: MAX TURBO LIMIT',
                'IA: TURBO ATTENUATION',
                'IA: THERMAL VELOCITY BOOST',
                'IA LIMIT REASONS',

                'GT: PROCHOT',
                'GT: THERMAL EVENT',
                'GT: DDR RAPL',
                'GT: RESIDENCY STATE REGULATION',
                'GT: RUNNING AVERAGE THERMAL LIMIT',
                'GT: VR THERMAL ALERT',
                'GT: VR TDC',
                'GT: MAX VR VOLTAGE',
                'GT: DOMAIN-LEVEL PBM',
                'GT: PACKAGE-LEVEL RAPL',
                'GT: INEFFICIENT OPERATION',
                'GT: FUSES LIMIT',
                'GT LIMIT REASONS',

                'RING: PROCHOT',
                'RING: THERMAL EVENT',
                'RING: DDR RAPL',
                'RING: RESIDENCY STATE REGULATION',
                'RING: RUNNING AVERAGE THERMAL LIMIT',
                'RING: VR THERMAL ALERT',
                'RING: VR TDC',
                'RING: MAX VR VOLTAGE',
                'RING: PACKAGE-LEVEL RAPL',
                'RING LIMIT REASONS',

                'PERFORMANCE LIMIT - POWER',
                'PERFORMANCE LIMIT - THERMAL',
                'PERFORMANCE LIMIT - RELIABILITY VOLTAGE',
                'PERFORMANCE LIMIT - MAX OPERATING VOLTAGE',
                'PERFORMANCE LIMIT - UTILIZATION',
                'PERFORMANCE LIMIT - SLI',
                'GPU PERFORMANCE LIMITERS',

                'AVG. POWER (PL1)',
                'BURST POWER (PL2)',
                'CURRENT (PL4)',
                'THERMAL',
                'POWER SUPPLY',
                'SOFTWARE LIMIT',
                'HARDWARE LIMIT',
                'GPU THROTTLE REASONS',

                'DRIVE WARNING', 'DRIVE WARN',

                'PPT LIMIT', 'TDC LIMIT', 'EDC LIMIT',
                'SOC THROTTLE', 'GFX THROTTLE',
                'STAPM LIMIT', 'SLOW PPT', 'FAST PPT',
            )
            if any(k in raw for k in _WARN_THRESH):
                return series.max() >= 1.0 and (series >= 1.0).mean() > 0.01

            return False

        if 'TOTAL ERRORS' in raw:
            return series.max() > 0

        if 'AVAILABLE SPARE' in raw and '[%]' in raw:
            return series.min() < self.drive_spare_min

        if any(x in raw for x in _SMART_KW):
            return series.min() < self.drive_life_min

        if '[%]' in raw:
            if 'LIMIT' in raw:
                return False
            if ('MEMORY' in raw or 'RAM' in raw) and ('USAGE' in raw or 'LOAD' in raw):
                return series.max() >= self.memory_load_max
            if 'DECODE' in raw or 'ENCODE' in raw or 'VIDEO' in raw or 'MEDIA' in raw:
                return False

        if any(x in raw for x in _WHEA_KW):
            return series.max() > 0

        if any(x in raw for x in _ERROR_KW):
            return series.max() > 0

        if '[W]' in raw and 'STATIC' not in raw and 'LIMIT' not in raw and 'PPT' not in raw:
            if 'CPU' in raw and self._sustained(col, self.cpu_power_max, n_samples=5):
                return True
            if 'GPU' in raw and self._sustained(col, self.gpu_power_max, n_samples=5):
                return True
            if 'TOTAL' in raw and self._sustained(col, self.total_power_max, n_samples=5):
                return True

        if 'CPU PPT' in raw and '[W]' in raw and 'LIMIT' not in raw:
            ppt_limit_col = next(
                (c for c in self.df.columns if 'PPT' in c.upper() and 'LIMIT' in c.upper()
                 and '[W]' in c.upper() and 'CPU' in c.upper()), None)
            if ppt_limit_col is not None:
                limit_val = self.df[ppt_limit_col].dropna().mean()
                if limit_val > 0 and series.mean() >= limit_val * 0.98:
                    return True

        for rail, (low, high) in self.volt_rails.items():
            if rail in raw:
                if any(x in raw for x in _RAIL_SKIP):
                    continue
                after = raw.split(rail)[-1]
                if 'INPUT' in after or 'PCIE' in after or 'HPWR' in after:
                    continue
                return series.min() < low or series.max() > high

        if 'VCORE' in raw or 'CPU CORE VOLTAGE' in raw:
            lo, hi = self.cpu_volt_range
            out_of_range = series.min() < lo or series.max() > hi
            drooping = series.max() - series.min() > self.vcore_droop_max
            if out_of_range or drooping:
                return True

        if 'VID' in raw and 'GPU' not in raw and 'VIDEO' not in raw:
            lo, hi = self.cpu_volt_range
            return series.min() < lo or series.max() > hi

        if ('DRAM VOLTAGE' in raw or 'DIMM VOLTAGE' in raw or 'MEMORY VOLTAGE' in raw
                or 'VDIMM' in raw or 'VDDQ' in raw):
            if 'GPU' in raw:
                return False
            lo, hi = self.dram_volt_range
            return series.min() < lo or series.max() > hi

        if 'GPU CORE VOLTAGE' in raw and 'GFX' not in raw and 'VDDCR' not in raw:
            return series.max() > self.gpu_volt_max

        if 'CPU CLOCK' in raw or 'GPU CLOCK' in raw or 'CORE CLOCK' in raw:
            if 'EFFECTIVE' not in raw and 'REQUESTED' not in raw\
                    and 'CORE #' not in raw and 'LIMIT' not in raw:
                if series.mean() > 100 and (series.std() / series.mean()) > self.clock_instability:
                    return True

        if 'RPM' in raw or 'FAN SPEED' in raw:
            if 'GPU' in raw:
                gpu_temp_col = self._col('GPU', 'TEMP') or self._col('HOTSPOT')
                if gpu_temp_col is not None:
                    gpu_hot = self.df[gpu_temp_col].max() > self.temp_limits.get('GPU', 88.0) * 0.8
                    if gpu_hot and series.max() == 0:
                        return True
            else:
                if series.max() > self.fan_min_rpm and series.min() < self.fan_min_rpm:
                    return True

        if any(x in name for x in _TEMP_TRIGGERS):
            matched_limit = None
            matched_len   = 0
            for key, limit in self.temp_limits.items():
                key_norm = key.upper().replace(' ', '')
                if key_norm in name and len(key_norm) > matched_len:
                    matched_limit = limit
                    matched_len   = len(key_norm)
            if matched_limit is not None and matched_len == len('TEMPERATURE'):
                for specific in ('CORE', 'GPU', 'HOTSPOT', 'TDIE', 'TCTL', 'CCD',
                                 'SSD', 'NVME', 'HDD', 'VRM', 'CHIPSET', 'SOCKET'):
                    if specific.replace(' ', '') in name:
                        matched_limit = self.temp_limits.get(specific, matched_limit)
                        break
            return self._sustained(col, matched_limit if matched_limit is not None else 90.0, n_samples=3)

        if 'PHYSICAL MEMORY' in raw and 'LOAD' in raw:
            return series.max() >= self.memory_load_max

        return False

    def _sustained(self, col: str, threshold: float, n_samples: int = 5,
                   above: bool = True) -> bool:
        """Return True only if the column exceeds threshold for at least
        n_samples consecutive rows. Prevents single-spike false positives."""
        if col not in self.df.columns:
            return False
        s = self.df[col].ffill().fillna(0).values
        count = 0
        for v in s:
            if (v >= threshold if above else v <= threshold):
                count += 1
                if count >= n_samples:
                    return True
            else:
                count = 0
        return False

    def _col(self, *keywords) -> str | None:
        """Find the first column whose name contains ALL given keywords (case-insensitive)."""
        kw = [k.upper() for k in keywords]
        for c in self.df.columns:
            u = c.upper()
            if all(k in u for k in kw):
                return c
        return None

    def _col_any(self, *keywords) -> str | None:
        """Find the first column whose name contains ANY of the given keywords."""
        kw = [k.upper() for k in keywords]
        for c in self.df.columns:
            u = c.upper()
            if any(k in u for k in kw):
                return c
        return None

    def _col_excl(self, keywords, excl=()) -> str | None:
        """Find the first column containing ALL keywords but NONE of the exclusions (case-insensitive)."""
        kw   = [k.upper() for k in keywords]
        skip = [e.upper() for e in excl]
        for c in self.df.columns:
            u = c.upper()
            if all(k in u for k in kw) and not any(e in u for e in skip):
                return c
        return None

    def _col_candidates(self, keywords, excl=()) -> list[str]:
        kw   = [k.upper() for k in keywords]
        skip = [e.upper() for e in excl]
        out  = []
        for c in self.df.columns:
            u = c.upper()
            if all(k in u for k in kw) and not any(e in u for e in skip):
                out.append(c)
        return out

    def _col_active(self, keywords, excl=(), min_unique: int = 3) -> str | None:
        candidates = self._col_candidates(keywords, excl=excl)
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        df = self.df
        best_col   = candidates[0]
        best_score = -1.0
        for c in candidates:
            s = pd.to_numeric(df[c], errors='coerce').dropna()
            if s.empty:
                score = -1.0
            else:
                nunique = s.nunique()
                score = float(nunique)
                if nunique < min_unique:
                    score *= 0.001
            if score > best_score:
                best_score = score
                best_col   = c
        return best_col

    def _toggle_debug(self):
        """Ctrl+F8 - open/refresh the debug window."""
        self.debug_mode = not self.debug_mode
        flag = " [DEBUG]" if self.debug_mode else ""
        self.root.title(f"RESYNC.ERR v{CURRENT_VERSION} - {self.analyzer.path.name}{flag}")
        if self.debug_mode:
            self._open_debug_window()
        else:
            if hasattr(self, '_debug_win') and self._debug_win and self._debug_win.winfo_exists():
                self._debug_win.destroy()
            self.show_toast("Debug mode OFF")

    def _open_debug_window(self):
        """Open (or refresh) the debug output window."""
        is_dark = self.is_dark
        t        = self._get_theme()
        bg       = t["bg"]
        bg2      = t["bg2"]
        bg3      = t["bg3"]
        fg       = t["fg"]
        accent   = t["accent"]
        fg_ok    = t.get("hm_ok",   "#4ec94e")
        fg_miss  = t.get("hm_crit", "#ff5555")
        fg_warn  = t.get("hm_warn", "#f59e0b")
        fg_hot   = t.get("hm_hot",  "#ff9800")
        fg_sec   = t.get("plot_c0", accent)
        fg_val   = t.get("plot_c3", "#f0c060")
        mono     = ('Cascadia Code', 9) if is_dark else ('Consolas', 9)

        rebuilding = hasattr(self, '_debug_win') and self._debug_win and self._debug_win.winfo_exists()
        if rebuilding:
            win = self._debug_win
            txt = self._debug_txt
            for w_ in win.winfo_children():
                w_.destroy()
        else:
            win = tk.Toplevel(self.root)
            win.geometry("900x720")
            win.minsize(640, 420)
            win.transient(self.root)
            self._debug_win = win

        win.title(f"RESYNC.ERR - Debug Dump  [{self.analyzer.path.name}]")
        win.configure(bg=bg)

        def _on_debug_close():
            self.debug_mode = False
            self.root.title(f"RESYNC.ERR v{CURRENT_VERSION} - {self.analyzer.path.name}")
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", _on_debug_close)

        tk.Frame(win, bg=accent, height=3).pack(fill=tk.X)

        toolbar = ttk.Frame(win, padding=(8, 6))
        toolbar.pack(fill=tk.X)
        ttk.Label(toolbar, text="🐛  Debug Dump", font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)
        ttk.Label(toolbar, text=f"Ctrl+F8 to refresh / close",
                  foreground=t.get("fg", fg)).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Button(toolbar, text="✕ Close", command=_on_debug_close).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="⟳ Refresh", command=self._open_debug_window).pack(side=tk.RIGHT, padx=2)

        def _copy_all():
            win.clipboard_clear()
            win.clipboard_append(txt.get('1.0', tk.END))
            self.show_toast("Debug output copied to clipboard")
        ttk.Button(toolbar, text="📋 Copy All", command=_copy_all).pack(side=tk.RIGHT, padx=2)

        def _save_to_file():
            from tkinter import filedialog as _fd
            path = _fd.asksaveasfilename(defaultextension=".txt",
                                          initialfile=f"{self.analyzer.path.stem}_debug.txt",
                                          filetypes=[("Text file", "*.txt")])
            if path:
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(txt.get('1.0', tk.END))
                    self.show_toast("Debug dump saved")
                except Exception as e:
                    messagebox.showerror("Save Failed", str(e), parent=win)
        ttk.Button(toolbar, text="💾 Save…", command=_save_to_file).pack(side=tk.RIGHT, padx=2)

        search_row = ttk.Frame(win, padding=(8, 0, 8, 6))
        search_row.pack(fill=tk.X)
        ttk.Label(search_row, text="🔍 Filter:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(search_row, text="▲", width=3,
                   command=lambda: _jump_match(-1)).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(search_row, text="▼", width=3,
                   command=lambda: _jump_match(1)).pack(side=tk.LEFT, padx=(2, 0))
        match_lbl = ttk.Label(search_row, text="")
        match_lbl.pack(side=tk.LEFT, padx=(8, 0))

        problems_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(search_row, text="⚠ Problems only", variable=problems_var,
                         command=lambda: _apply_problems_filter()).pack(side=tk.RIGHT)

        body = tk.Frame(win, bg=bg)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

                                          
        nav_frame = tk.Frame(body, bg=bg, width=190)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        nav_frame.pack_propagate(False)
        ttk.Label(nav_frame, text="📑 Sections", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        nav_list_holder = tk.Frame(nav_frame, bg=bg)
        nav_list_holder.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        nav_list = tk.Listbox(nav_list_holder, bg=bg2, fg=fg, font=('Segoe UI', 9),
                               relief='flat', selectbackground=accent, selectforeground="#ffffff",
                               highlightthickness=1, highlightbackground=bg3, highlightcolor=accent,
                               activestyle='none')
        nav_sb = ttk.Scrollbar(nav_list_holder, orient='vertical', command=nav_list.yview)
        nav_list.configure(yscrollcommand=nav_sb.set)
        nav_sb.pack(side=tk.RIGHT, fill=tk.Y)
        nav_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._debug_nav_marks = []                              

        def _on_nav_select(event=None):
            sel = nav_list.curselection()
            if not sel:
                return
            _title, mark = self._debug_nav_marks[sel[0]]
            txt.see(mark)
            txt.see(f"{mark} + 1 line")                                                
            txt.mark_set('insert', mark)
        nav_list.bind('<<ListboxSelect>>', _on_nav_select)

                                     
        frame = tk.Frame(body, bg=bg)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt = tk.Text(frame, bg=bg2, fg=fg, font=mono,
                      wrap='none', relief='flat', padx=10, pady=8,
                      insertbackground=fg, selectbackground=accent,
                      highlightthickness=1, highlightbackground=bg3, highlightcolor=accent)
        sb_y = ttk.Scrollbar(frame, orient='vertical',   command=txt.yview)
        sb_x = ttk.Scrollbar(frame, orient='horizontal',  command=txt.xview)
        txt.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side=tk.RIGHT,  fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(fill=tk.BOTH, expand=True)
        self._debug_txt = txt
        txt.tag_config('header',  foreground=accent,   font=(mono[0], 9, 'bold'))
        txt.tag_config('section', foreground=fg_sec,    font=(mono[0], 9, 'bold'))
        txt.tag_config('ok',      foreground=fg_ok)
        txt.tag_config('miss',    foreground=fg_miss)
        txt.tag_config('val',     foreground=fg_val)
        txt.tag_config('crit',    foreground=fg_miss, font=(mono[0], 9, 'bold'))
        txt.tag_config('warn',    foreground=fg_warn,  font=(mono[0], 9, 'bold'))
        txt.tag_config('info',    foreground=t.get("plot_c5", "#38bdf8"))
        txt.tag_config('muted',   foreground=bg3 if is_dark else "#999")
        txt.tag_config('search_hit', background=fg_hot, foreground="#000000")
        txt.tag_config('search_cur', background=accent, foreground="#ffffff")
        txt.tag_config('hidden_line', elide=True)

        self._debug_matches = []
        self._debug_match_idx = -1

        def _apply_filter(*_):
            txt.tag_remove('search_hit', '1.0', tk.END)
            txt.tag_remove('search_cur', '1.0', tk.END)
            query = search_var.get().strip()
            self._debug_matches = []
            self._debug_match_idx = -1
            if not query:
                match_lbl.config(text="")
                return
            start = '1.0'
            while True:
                pos = txt.search(query, start, stopindex=tk.END, nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(query)}c"
                txt.tag_add('search_hit', pos, end)
                self._debug_matches.append((pos, end))
                start = end
            count = len(self._debug_matches)
            match_lbl.config(text=f"{count} match{'es' if count != 1 else ''}" if count else "no matches")
            if count:
                _jump_match(1)

        def _jump_match(direction):
            if not self._debug_matches:
                return
            if self._debug_match_idx >= 0:
                old_pos, old_end = self._debug_matches[self._debug_match_idx]
                txt.tag_remove('search_cur', old_pos, old_end)
            self._debug_match_idx = (self._debug_match_idx + direction) % len(self._debug_matches)
            pos, end = self._debug_matches[self._debug_match_idx]
            txt.tag_add('search_cur', pos, end)
            txt.see(pos)
            query = search_var.get().strip()
            count = len(self._debug_matches)
            match_lbl.config(text=f"{self._debug_match_idx + 1} of {count} matches")

        def _apply_problems_filter():
            """Hide everything except lines tagged crit / warn / miss / header / section when enabled."""
            keep_tags = ('crit', 'warn', 'miss', 'header', 'section')
            if not problems_var.get():
                txt.tag_remove('hidden_line', '1.0', tk.END)
                return
            total_lines = int(txt.index('end-1c').split('.')[0])
            keep_lines = set()
            for t in keep_tags:
                start = '1.0'
                while True:
                    rng = txt.tag_nextrange(t, start, tk.END)
                    if not rng:
                        break
                    line_no = int(str(rng[0]).split('.')[0])
                    keep_lines.add(line_no)
                    start = rng[1]
            for ln in range(1, total_lines + 1):
                line_start = f"{ln}.0"
                line_end_plus = f"{ln}.end+1c"
                if ln in keep_lines:
                    txt.tag_remove('hidden_line', line_start, line_end_plus)
                else:
                    txt.tag_add('hidden_line', line_start, line_end_plus)
        search_var.trace_add('write', _apply_filter)
        search_entry.bind('<Return>', lambda e: _jump_match(1))
        search_entry.bind('<Shift-Return>', lambda e: _jump_match(-1))

        df   = self.df
        MISS = "<not found>"
        SEP  = "-" * 72

        def w(text, tag=None):
            txt.insert(tk.END, text, tag or '')

        def wl(text='', tag=None):
            w(text + '\n', tag)

        def col(name, value):
            tag = 'ok' if value else 'miss'
            sym = '✓' if value else '✗'
            w(f"  [{sym}] {name:44s} → ", tag)
            wl(value or MISS, tag)

        def val(name, value, fmt=".2f"):
            try:    v = f"{value:{fmt}}" if value is not None else MISS
            except: v = str(value)
            w(f"       {name:44s} = ")
            wl(v, 'val')

        def section(title):
            wl()
            mark_name = f"sec_{len(self._debug_nav_marks)}"
            txt.mark_set(mark_name, tk.INSERT)
            txt.mark_gravity(mark_name, 'left')
            self._debug_nav_marks.append((title, mark_name))
            nav_list.insert(tk.END, title)
            wl(SEP, 'section')
            wl(f"  {title}", 'section')
            wl(SEP, 'section')

        def mx(c):  return df[c].max()  if c and c in df.columns else None
        def avg(c): return df[c].mean() if c and c in df.columns else None

        import os as _os, sys as _sys
        try:
            csv_bytes = _os.path.getsize(self.analyzer.path)
            csv_mb    = csv_bytes / 1024 / 1024
            csv_size  = f"{csv_mb:.2f} MB  ({csv_bytes:,} bytes)"
        except Exception:
            csv_size = "unknown"
        try:
            import psutil as _psutil
            proc = _psutil.Process(_os.getpid())
            ram_mb = proc.memory_info().rss / 1024 / 1024
            mem_in_use = f"{ram_mb:.1f} MB"
        except Exception:
            mem_in_use = "psutil not installed"

        wl('=' * 72, 'header')
        wl(f"  RESYNC.ERR v{CURRENT_VERSION}  -  Debug Dump", 'header')
        wl(f"  CSV file  : {self.analyzer.path}", 'header')
        wl(f"  CSV size  : {csv_size}", 'header')
        wl(f"  Rows      : {len(df):,}   Columns: {len(df.columns):,}", 'header')
        wl(f"  RAM in use: {mem_in_use}  (this process)", 'header')
        wl(f"  Disabled  : {sorted(self.disabled_sigs) or 'none'}", 'header')
        wl(f"  Format    : {'MangoHud' if self.analyzer.is_mangohud else 'HWiNFO64 / Generic CSV'}", 'header')
        wl('=' * 72, 'header')

        section("DEPENDENCY CHECK")
        _deps = [
            ("pandas",                  "pd",          "1.3.0"),
            ("numpy",                   "np",          "1.21.0"),
            ("matplotlib",              "matplotlib",  "3.4.0"),
            ("matplotlib.backends.backend_tkagg", None, None),
            ("tkinter",                 "tk",          None),
            ("PIL",                     None,          None),
            ("psutil",                  None,          None),
            ("scipy",                   None,          None),
            ("urllib.request",          None,          None),
            ("pathlib",                 None,          None),
            ("csv",                     None,          None),
            ("json",                    None,          None),
            ("threading",               None,          None),
        ]
        _all_ok = True
        for _mod, _alias, _min_ver in _deps:
            try:
                import importlib
                _m = importlib.import_module(_mod)
                _ver_raw = getattr(_m, '__version__', None) or getattr(_m, 'version', None)
                _ver = str(_ver_raw) if isinstance(_ver_raw, (str, int, float)) else None
                if _ver:
                    _ver_str = str(_ver)
                    if _min_ver:
                        try:
                            _parts_have = [int(x) for x in _ver_str.split('.')[:3]]
                            _parts_need = [int(x) for x in _min_ver.split('.')[:3]]
                            if _parts_have < _parts_need:
                                wl(f"  [!] {_mod:45s} v{_ver_str}  (min: {_min_ver}) - OUTDATED", 'warn')
                                _all_ok = False
                                continue
                        except Exception:
                            pass
                    wl(f"  [✓] {_mod:45s} v{_ver_str}", 'ok')
                else:
                    wl(f"  [✓] {_mod:45s} (no version info)", 'ok')
            except ImportError:
                _critical = _mod in ("pandas", "numpy", "matplotlib",
                                     "matplotlib.backends.backend_tkagg", "tkinter")
                _tag = 'crit' if _critical else 'warn'
                _label = "MISSING - REQUIRED" if _critical else "not installed (optional)"
                wl(f"  [✗] {_mod:45s} {_label}", _tag)
                _all_ok = False
        wl()
        if _all_ok:
            wl("  All dependencies satisfied.", 'ok')
        else:
            wl("  Some dependencies are missing or outdated.", 'warn')
            wl("  Install missing packages with:  pip install pandas numpy matplotlib pillow psutil scipy", 'warn')

        section("RUNTIME ENVIRONMENT")
        import sys as _sys, platform as _platform, os as _os2

        _frozen = getattr(_sys, 'frozen', False)
        _frozen_tag = 'warn' if _frozen else 'ok'
        wl(f"  Frozen (compiled exe)  : {_frozen}", _frozen_tag)
        wl(f"  Executable             : {_sys.executable}", 'val')
        wl(f"  Script / entry point   : {getattr(_sys, '_MEIPASS', __file__ if '__file__' in dir() else 'N/A')}", 'val')
        try:
            import __main__ as _main
            wl(f"  __main__.__file__      : {getattr(_main, '__file__', 'N/A')}", 'val')
        except Exception:
            pass
        wl()
        wl(f"  Python version         : {_sys.version}", 'val')
        wl(f"  Platform               : {_platform.platform()}", 'val')
        wl(f"  Architecture           : {_platform.machine()}  {_platform.architecture()[0]}", 'val')
        wl(f"  Windows ver            : {_platform.win32_ver()}", 'val')
        wl()

        wl("  --- sys.path ---", 'section')
        for _p in _sys.path:
            wl(f"  {_p}", 'val')
        wl()

        wl("  --- Matplotlib config ---", 'section')
        try:
            import matplotlib as _mpl
            wl(f"  backend                : {_mpl.get_backend()}", 'val')
            wl(f"  matplotlib data path   : {_mpl.get_data_path()}", 'val')
            wl(f"  config dir             : {_mpl.get_configdir()}", 'val')
            wl(f"  cache dir              : {_mpl.get_cachedir()}", 'val')
            wl(f"  rcParams backend       : {_mpl.rcParams.get('backend', 'N/A')}", 'val')
            wl(f"  rcParams dpi           : {_mpl.rcParams.get('figure.dpi', 'N/A')}", 'val')
        except Exception as _e:
            wl(f"  (error reading matplotlib config: {_e})", 'warn')
        wl()

        wl("  --- Tkinter config ---", 'section')
        try:
            import tkinter as _tki
            _r = _tki.Tk()
            _r.withdraw()
            wl(f"  tcl version            : {_r.tk.call('info', 'patchlevel')}", 'val')
            wl(f"  tk scaling             : {_r.tk.call('tk', 'scaling')}", 'val')
            wl(f"  screen width x height  : {_r.winfo_screenwidth()} x {_r.winfo_screenheight()}", 'val')
            wl(f"  screen DPI             : {_r.winfo_fpixels('1i'):.1f}", 'val')
            _r.destroy()
        except Exception as _e:
            wl(f"  (error reading tkinter config: {_e})", 'warn')
        wl()

        wl("  --- Environment variables ---", 'section')
        _env_keys = [
            'MPLBACKEND', 'MPLCONFIGDIR', 'MATPLOTLIBDATA',
            'TCL_LIBRARY', 'TK_LIBRARY', 'TCLLIBPATH',
            'PATH', 'PYTHONPATH', 'PYTHONHOME',
            'PYINSTALLER_RESET_ENVIRONMENT',
        ]
        for _k in _env_keys:
            _v = _os2.environ.get(_k)
            if _v:
                _display = _v if len(_v) < 120 else _v[:120] + '...'
                wl(f"  {_k:35s} = {_display}", 'val')
            else:
                wl(f"  {_k:35s} = (not set)", 'muted')
        wl()

        wl("  --- Key loaded modules (from sys.modules) ---", 'section')
        _track_mods = [
            'pandas', 'numpy', 'matplotlib', 'matplotlib.backends.backend_tkagg',
            'matplotlib.backends._backend_tk', 'PIL', 'PIL.Image',
            'tkinter', '_tkinter', 'scipy', 'psutil',
            'pkg_resources', 'importlib.metadata',
        ]
        for _mn in _track_mods:
            _mo = _sys.modules.get(_mn)
            if _mo is not None:
                _mv = getattr(_mo, '__version__', getattr(_mo, 'version', None))
                _mf = getattr(_mo, '__file__', None)
                _vstr = f"  v{_mv}" if _mv else ""
                _fstr = f"  [{_mf}]" if _mf else ""
                wl(f"  {_mn:45s}{_vstr}{_fstr}", 'ok')
            else:
                wl(f"  {_mn:45s}  (not in sys.modules)", 'muted')

        if self.analyzer.is_mangohud:
            section("MANGOHUD FILE DETECTED")
            si = self.analyzer.mangohud_sysinfo
            if si:
                for k, v in si.items():
                    if v:
                        w(f"  {k:20s} = ")
                        wl(v, 'val')
            else:
                wl("  No system info block found.", 'muted')
            wl()
            wl("  Columns resolved from MangoHud short names:", 'section')
            for short, display in self.analyzer.MANGOHUD_COL_MAP.items():
                if display in df.columns:
                    s = df[display].dropna()
                    tag = 'ok'
                    sym = '✓'
                else:
                    s = None
                    tag = 'miss'
                    sym = '✗'
                w(f"  [{sym}] {short:25s} → {display:40s}", tag)
                if s is not None and not s.empty:
                    wl(f"  min={s.min():.2f}  avg={s.mean():.2f}  max={s.max():.2f}", 'val')
                else:
                    wl("  not present", 'muted')

        cpu_temp      = self._col('TCTL') or self._col('TDIE') or self._col_excl(['CPU'], excl=['USAGE','UTIL','LOAD','THREAD','W]','%]','MHz','RPM'])
        cpu_clock     = self._col('KERN', 'TAKT') or self._col('CORE', 'CLOCK') or self._col('CLOCK')
        cpu_usage_col = self._col_excl(['CPU','USAGE'], excl=['°C','TEMP','W]']) or self._col_excl(['CPU','UTIL'], excl=['°C','TEMP','W]']) or self._col_excl(['CPU','LOAD'], excl=['°C','TEMP','W]']) or self._col('TOTAL', 'CPU')
        cpu_power     = self._col_excl(['CPU','PACKAGE','W'], excl=['°C','TEMP','USAGE','LOAD','%']) or self._col_excl(['CPU','PPT'], excl=['°C','TEMP']) or self._col_excl(['CPU','POWER'], excl=['°C','TEMP'])
        throttle      = self._col('THROTTLE') or self._col('PROCHOT')

        section("CPU COLUMNS")
        col("cpu_temp",      cpu_temp)
        col("cpu_clock",     cpu_clock)
        col("cpu_usage_col", cpu_usage_col)
        col("cpu_power",     cpu_power)
        col("throttle",      throttle)

        if cpu_temp:
            limit = self.temp_limits.get('TDIE', 95.0)
            section("CPU THERMAL VALUES")
            val("Max temp",       mx(cpu_temp))
            val("Mean temp",      avg(cpu_temp))
            val("TDIE limit",     limit)
            val("Warn threshold", limit * 0.85)
            val("Crit threshold", limit * 0.92)

        if cpu_power:
            section("CPU POWER VALUES")
            val("Max power",  mx(cpu_power))
            val("Mean power", avg(cpu_power))

        section("CPU CLOCK STRETCHING COLUMNS")
        req_cols = [c for c in df.columns if 'Clock (perf #' in c]
        eff_cols = [c for c in df.columns if 'Effective Clock' in c and 'GPU' not in c]
        wl(f"  Requested clock cols ({len(req_cols)}): {req_cols[:5] or MISS}")
        wl(f"  Effective clock cols ({len(eff_cols)}): {eff_cols[:5] or MISS}")

        gpu_hotspot       = self._col_excl(('GPU', 'HOT'),  excl=('CPU', 'LIMIT')) or self._col_excl(('GPU', 'TEMP'), excl=('CPU',))
        gpu_usage_col     = self._col_active(('GPU', 'USAGE')) or self._col_active(('GPU', 'LOAD'))
        gpu_clock         = self._col_active(('GPU', 'CLOCK'), excl=('EFFECTIVE', 'MEMORY', 'CROSSBAR', 'SOC', 'VCN', 'VIDEO')) or self._col_active(('GPU', 'FREQUENCY'))
        gpu_power         = self._col_active(('GPU', 'POWER'))
        gpu_throttle      = self._col_excl(('GPU', 'THROTTL'), excl=('CPU',)) or self._col('PERFCAP')
        gpu_pwr_limit     = self._col('Performance Limit - Power [Yes/No]') or self._col('PERFCAP', 'PWR')
        gpu_eff_clock     = self._col('GPU Effective Clock [MHz]')
        gpu_mem_usage     = self._col('GPU', 'MEMORY', 'USAGE') or self._col('GPU', 'MEMORY', 'ALLOCATED')
        gpu_mem_dedicated = self._col('GPU D3D Memory Dedicated')
        gpu_mem_dynamic   = self._col('GPU D3D Memory Dynamic')
        gpu_bus_col       = self._col('GPU Bus Load') or self._col('Bus Load')
        vram_junc         = self._col('GPU Memory Junction Temperature [°C]')
        gpu_edge          = self._col('GPU Temperature') or self._col_excl(
                                ('GPU', 'TEMP'),
                                excl=('HOTSPOT', 'MEMORY', 'CPU', 'VR', 'VRM', 'JUNCTION', 'SOC')
                            )

        section("GPU COLUMNS")
        col("gpu_hotspot",        gpu_hotspot)
        col("gpu_edge",           gpu_edge)
        col("gpu_usage_col",      gpu_usage_col)
        col("gpu_clock",          gpu_clock)
        col("gpu_eff_clock",      gpu_eff_clock)
        col("gpu_power",          gpu_power)
        col("gpu_throttle",       gpu_throttle)
        col("gpu_pwr_limit",      gpu_pwr_limit)
        col("gpu_mem_usage",      gpu_mem_usage)
        col("gpu_mem_dedicated",  gpu_mem_dedicated)
        col("gpu_mem_dynamic",    gpu_mem_dynamic)
        col("gpu_bus_col",        gpu_bus_col)
        col("vram_junction_temp", vram_junc)

        gpu_temp_candidates = [c for c in df.columns
                                if 'GPU' in c.upper() and ('TEMP' in c.upper() or 'HOT' in c.upper())]
        if gpu_temp_candidates:
            wl()
            wl("  All GPU temperature-like columns found in this CSV (in header order):", 'section')
            for c in gpu_temp_candidates:
                picked = []
                if c == gpu_hotspot: picked.append('gpu_hotspot')
                if c == gpu_edge:    picked.append('gpu_edge')
                tag = 'ok' if picked else 'muted'
                marker = f"  <- used as {', '.join(picked)}" if picked else ""
                w(f"    {'[*]' if picked else '[ ]'} ", tag)
                wl(f"{c}{marker}", tag)

        if gpu_hotspot:
            section("GPU THERMAL VALUES")
            val("Max hotspot",   mx(gpu_hotspot))
            val("Mean hotspot",  avg(gpu_hotspot))
            val("Hotspot limit", self.temp_limits.get('GPU_HOTSPOT', 110.0))

            if gpu_edge:
                section("GPU THERMAL DELTA  (hotspot - edge, used by alert logic)")
                delta_series = df[gpu_hotspot] - df[gpu_edge]
                val("Edge column used",       gpu_edge, "")
                val("Max delta",              delta_series.max())
                val("Mean delta",             delta_series.mean())
                val("Warning threshold",      21.0)
                if delta_series.max() >= 21.0:
                    wl(f"  ⚠ Max delta exceeds warning threshold - verify gpu_edge above is "
                       f"a real die/edge sensor, not a VRM/SoC/junction sensor.", 'warn')
            else:
                wl()
                wl("  ⚠ No gpu_edge column resolved - thermal delta warning is skipped entirely.", 'warn')

        clk_candidates   = self._col_candidates(('GPU', 'CLOCK'))
        usage_candidates = self._col_candidates(('GPU', 'USAGE')) + self._col_candidates(('GPU', 'LOAD'))
        if clk_candidates or usage_candidates:
            wl()
            wl("  All GPU clock/usage-like columns found in this CSV (in header order):", 'section')
            for c in clk_candidates + usage_candidates:
                s = pd.to_numeric(df[c], errors='coerce').dropna()
                flat = s.empty or s.nunique() <= 1
                picked = []
                if c == gpu_clock:     picked.append('gpu_clock')
                if c == gpu_usage_col: picked.append('gpu_usage_col')
                tag = 'ok' if picked else ('muted' if not flat else 'warn')
                marker = f"  <- used as {', '.join(picked)}" if picked else ""
                flat_note = "  [flat/constant - likely idle/decoy]" if flat and not picked else ""
                w(f"    {'[*]' if picked else '[ ]'} ", tag)
                wl(f"{c}{marker}{flat_note}", tag)
            if gpu_clock:
                s = pd.to_numeric(df[gpu_clock], errors='coerce').dropna()
                if not s.empty and s.nunique() <= 1:
                    wl("  ⚠ The selected gpu_clock is flat/constant for the entire log - if another "
                       "candidate above shows real variance, that one is likely the active GPU.", 'warn')

        if gpu_clock and gpu_usage_col:
            section("GPU CLOCK / TDR VALUES")
            val("Max clock",  mx(gpu_clock))
            val("Min clock",  df[gpu_clock].min())
            val("Clock std",  df[gpu_clock].std())
            low_u  = df[gpu_usage_col] < 5
            stall  = (df[gpu_clock].rolling(3).std() < 1.0) & (df[gpu_clock] > 0)
            tdr_ev = (low_u & stall).rolling(5).sum() >= 3
            val("TDR candidate samples", int(tdr_ev.sum()), "d")

        ft_col      = self._col('Frametime [ms]') or self._col('Frame Time')
        gpu_busy_ms = self._col('GPU Busy (avg) [ms]')
        gpu_wait_ms = self._col('GPU Wait (avg) [ms]')

        section("FRAME TIMING COLUMNS")
        col("ft_col",      ft_col)
        col("gpu_busy_ms", gpu_busy_ms)
        col("gpu_wait_ms", gpu_wait_ms)

        if ft_col:
            section("FRAME TIMING VALUES")
            val("Avg frame time", avg(ft_col))
            val("Max frame time", mx(ft_col))
            val("P99 frame time", df[ft_col].quantile(0.99))
            if gpu_busy_ms and gpu_wait_ms:
                wr = df[gpu_wait_ms] / (df[gpu_busy_ms] + df[gpu_wait_ms] + 1e-9)
                val("Max wait ratio",  wr.max())
                val("Mean wait ratio", wr.mean())

        section("STORAGE COLUMNS")
        drive_t = [c for c in df.columns if 'TEMP' in c.upper()
                   and any(k in c.upper() for k in ['DRIVE','NVME','SSD','HDD'])]
        drive_h = [c for c in df.columns if any(k in c.upper()
                   for k in ['REMAINING LIFE','WEAR LEVEL','AVAILABLE SPARE'])]
        wl(f"  Drive temp cols   ({len(drive_t)}): {drive_t or MISS}")
        wl(f"  Drive health cols ({len(drive_h)}): {drive_h or MISS}")
        for c in drive_t:
            val(f"  Max {c[:35]}", mx(c))

        fclk_col = self._col('FCLK')
        uclk_col = next((c for c in df.columns if 'UCLK' in c), None)
        mclk_col = self._col('MCLK') or self._col('MEMORY CLOCK') or self._col('DRAM CLOCK')

        section("FABRIC / MEMORY CLOCK COLUMNS")
        col("fclk_col", fclk_col)
        col("uclk_col", uclk_col)
        col("mclk_col", mclk_col)
        if fclk_col and uclk_col and mclk_col:
            section("FABRIC VALUES  (Ryzen Desync detection)")
            val("FCLK median",         df[fclk_col].median())
            val("UCLK median",         df[uclk_col].median())
            val("MCLK median",         df[mclk_col].median())
            delta = (df[fclk_col] - df[uclk_col]).abs()
            val("FCLK/UCLK max delta", delta.max())
            val("Desync fraction",     float((delta > 10).mean()), ".4f")

        section("PSU RAIL COLUMNS")

        _RAIL_EXCL = ['[W]', '[A]', 'POWER', 'CURRENT', 'WATT', 'VID', 'OFFSET',
                      'LIMIT', 'PPT', 'TDP', 'PCIE', 'INPUT', 'GPU', 'HPWR', 'FBVDD']

        def _safe_alias(key, *fallbacks):
            """Return alias or fallback column only if it exists in df.
            Supports list of aliases - tries each in order."""
            entry = self.analyzer.aliases.get(key)
            if entry:
                candidates = entry if isinstance(entry, list) else [entry]
                for c in candidates:
                    if c and c in df.columns:
                        return c
            for c in fallbacks:
                if c and c in df.columns:
                    return c
            return None

        def _find_rail(keywords, excl, target_v, tolerance=0.5):
            """Find best matching voltage column.
            First tries columns whose mean value is within tolerance of target_v,
            then falls back to first keyword match regardless of value."""
            matches = []
            for c in df.columns:
                cu = c.upper()
                if '[V]' not in cu:
                    continue
                if any(e in cu for e in excl):
                    continue
                if any(k.upper() in cu for k in keywords):
                    s = df[c].dropna()
                    if not s.empty:
                        mean_v = pd.to_numeric(s, errors='coerce').dropna().mean()
                        matches.append((c, mean_v))

            if not matches:
                return None
            close = [(c, v) for c, v in matches
                     if not pd.isna(v) and abs(v - target_v) <= tolerance]
            if close:
                return min(close, key=lambda x: abs(x[1] - target_v))[0]
            return matches[0][0]

        rail_map = {
            '+12V':  _find_rail(
                ['12V', '12 V', 'ATX 12', 'EPS 12'],
                excl=_RAIL_EXCL + ['PCIE', 'INPUT'],
                target_v=12.0, tolerance=1.0),
            '+5V':   _find_rail(
                ['+5V', '5V [V', 'ATX 5', '5VSB', 'AVCC'],
                excl=_RAIL_EXCL + ['12V', '3.3', '3V3'],
                target_v=5.0, tolerance=0.4),
            '+3.3V': _safe_alias('rail_33v',
                _find_rail(
                    ['+3.3V', '3.3V', '3V3', 'VCC3', 'VCCIO', 'AVCC3',
                     'AVDD', 'VDD (SWA)', '3VSB', '3.3VSB'],
                    excl=['[W]', '[A]', 'POWER', 'CURRENT', 'GPU', 'VDDQ TX',
                          'VDDQ (SWB)', '12V', '+5V', 'VPP'],
                    target_v=3.3, tolerance=0.4)),
        }

        for r_name, c in rail_map.items():
            col(r_name, c)
            if c and c in df.columns:
                s = df[c].dropna()
                val(f"  {r_name} min",         s.min())
                val(f"  {r_name} max",         s.max())
                val(f"  {r_name} mean",        s.mean())
                val(f"  {r_name} σ (ripple)",  s.std(), ".4f")

        section("PSU FAILURE ANALYSIS")
        _psu_score = 0

        v12c = rail_map['+12V']
        if v12c:
            s12 = df[v12c].dropna()
            sag_pct = float((s12 < self.sig_v12_lo).mean()) * 100
            ripple  = s12.std()
            w(f"  +12V sag >limit in ")
            wl(f"{sag_pct:.1f}% of samples", 'crit' if sag_pct > 5 else 'ok')
            w(f"  +12V ripple σ = ")
            wl(f"{ripple:.4f}V", 'crit' if ripple > 0.15 else 'ok')
            if sag_pct > 5:  _psu_score += 2 if s12.min() < 11.2 else 1
            if ripple > 0.15: _psu_score += 1

        v5c  = rail_map['+5V']
        v33c = rail_map['+3.3V']

        if v5c:
            s5 = df[v5c].dropna()
            out = s5.min() < self.sig_v5_lo or s5.max() > self.sig_v5_hi
            w(f"  +5V in spec: ")
            wl("NO" if out else "YES", 'crit' if out else 'ok')
            if out: _psu_score += 1

        if v33c:
            s33 = df[v33c].dropna()
            out = s33.min() < self.sig_v33_lo or s33.max() > self.sig_v33_hi
            w(f"  +3.3V in spec: ")
            wl("NO" if out else "YES", 'crit' if out else 'ok')
            if out: _psu_score += 1

        rails_below = sum(1 for c2, lo in [(v12c, self.sig_v12_lo),
                                            (v5c, self.sig_v5_lo),
                                            (v33c, self.sig_v33_lo)]
                          if c2 and df[c2].dropna().min() < lo)
        w(f"  Rails simultaneously below spec: ")
        wl(str(rails_below), 'crit' if rails_below >= 2 else 'val')
        if rails_below >= 2: _psu_score += 2

        psu_yn_cols = [c2 for c2 in df.columns if 'YES/NO' in c2.upper()
                       and any(k in c2.upper() for k in
                               ('POWER SUPPLY','HARDWARE LIMIT','AVG. POWER',
                                'BURST POWER','CURRENT (PL4)'))]
        for c2 in psu_yn_cols:
            s2 = df[c2].dropna()
            pct = float((s2 >= 1.0).mean()) * 100
            if pct > 1.0:
                w(f"  {c2.replace(' [Yes/No]','')[:50]:50s} ")
                wl(f"{pct:.1f}% active", 'warn')
                _psu_score += 1

        w(f"\n  PSU failure score: ")
        score_tag = 'crit' if _psu_score >= 4 else ('warn' if _psu_score >= 2 else 'ok')
        wl(f"{_psu_score}/10  ({'CRITICAL' if _psu_score >= 4 else 'WARNING' if _psu_score >= 2 else 'CLEAR'})", score_tag)
        if not any([v12c, v5c, v33c]):
            wl("  No voltage rail columns found - PSU analysis unavailable.", 'muted')

        chipset_t      = self._col('Chipset [°C]') or self._col('Motherboard [°C]')
        pcie_errors    = self._col('PCI Express Error Counters (avg)')
        sys_interrupts = self._col('System Interrupts') or self._col('DPC Latency')
        is_laptop      = any(k in "".join(df.columns).upper()
                             for k in ['BATTERY','CHARGE','AC ADAPTER','DISCHARGE'])

        section("SYSTEM COLUMNS")
        col("chipset_t",      chipset_t)
        col("pcie_errors",    pcie_errors)
        col("sys_interrupts", sys_interrupts)
        w(f"       {'is_laptop':44s} = ")
        wl(str(is_laptop), 'val')
        if pcie_errors and pcie_errors in df.columns:
            pcie_s = pd.to_numeric(df[pcie_errors], errors='coerce').dropna()
            val("Max PCIe errors", mx(pcie_errors))
            is_live_gauge = '(AVG' in pcie_errors.upper()
            alert_value = pcie_s.max() if (is_live_gauge or pcie_s.empty) else pcie_s.sum()
            val("Naive sum (NOT used by alert)", pcie_s.sum() if not pcie_s.empty else 0)
            wl(f"       Alert logic uses: {'max (live gauge, per column name)' if is_live_gauge else 'sum (cumulative counter)'}"
               f" -> {alert_value:g}", 'val')

        section("ACTIVE THRESHOLDS  (limits editor)")
        val("CPU thermal samples",  self.sig_cpu_thermal_samples, "d")
        val("Fan stall RPM",        self.sig_fan_stall_rpm)
        val("Fan min spinning RPM", self.sig_fan_min_spinning)
        val("Fan hot CPU °C",       self.sig_fan_hot_cpu_c)
        val("Fan hot GPU °C",       self.sig_fan_hot_gpu_c)
        val("Drive temp max °C",    self.sig_drive_temp_max)
        val("VRM temp max °C",      self.sig_vrm_temp_max)
        val("RAM exhaust %",        self.sig_ram_exhaust_pct)
        val("VRAM overflow %",      self.sig_vram_overflow_pct)
        val("+12V lower limit V",   self.sig_v12_lo)
        val("+5V range V",          f"{self.sig_v5_lo} – {self.sig_v5_hi}", "s")
        val("+3.3V range V",        f"{self.sig_v33_lo} – {self.sig_v33_hi}", "s")

        section("SENSOR ALIASES  (user-confirmed)")
        aliases = self.analyzer.aliases
        if aliases:
            for k, v in sorted(aliases.items()):
                entries = v if isinstance(v, list) else [v]
                active = next((c for c in entries if c in df.columns), None)
                total  = len(entries)
                w(f"  {k:20s}  [{total} alias(es)]  active → ")
                if active:
                    wl(active, 'ok')
                else:
                    wl("none match current CSV", 'warn')
                for c in entries:
                    tag = 'ok' if c in df.columns else 'muted'
                    sym = '✓' if c in df.columns else '○'
                    wl(f"               [{sym}] {c}", tag)
        else:
            wl("  No aliases set yet.", 'muted')

        section("TEMPERATURE LIMITS  (active values)")
        for k, v in sorted(self.temp_limits.items()):
            default = self._default_temp_limits.get(k)
            modified = " ★ modified" if default is not None and abs(v - default) > 0.01 else ""
            w(f"       {k:20s} = ")
            wl(f"{v:.1f} °C{modified}", 'val')

        section("VOLTAGE RAIL LIMITS  (active values)")
        for rail, (lo, hi) in self.volt_rails.items():
            d_lo, d_hi = self._default_volt_rails.get(rail, (lo, hi))
            modified = " ★" if abs(lo - d_lo) > 0.001 or abs(hi - d_hi) > 0.001 else ""
            w(f"       {rail:10s} = ")
            wl(f"{lo}V – {hi}V{modified}", 'val')

        section("MISC THRESHOLDS  (active values)")
        misc_display = [
            ("cpu_volt_range",       f"{self.cpu_volt_range[0]}V – {self.cpu_volt_range[1]}V"),
            ("gpu_volt_max",         f"{self.gpu_volt_max}V"),
            ("dram_volt_range",      f"{self.dram_volt_range[0]}V – {self.dram_volt_range[1]}V"),
            ("fan_min_rpm",          f"{self.fan_min_rpm} RPM"),
            ("cpu_power_max",        f"{self.cpu_power_max} W"),
            ("gpu_power_max",        f"{self.gpu_power_max} W"),
            ("total_power_max",      f"{self.total_power_max} W"),
            ("frametime_max_ms",     f"{self.frametime_max_ms} ms"),
            ("fps_min",              f"{self.fps_min}"),
            ("sig_cpu_thermal_pct",  f"{self.sig_cpu_thermal_pct}"),
            ("sig_cpu_thermal_samp", f"{self.sig_cpu_thermal_samples}"),
            ("sig_fan_stall_rpm",    f"{self.sig_fan_stall_rpm} RPM"),
            ("sig_fan_hot_cpu_c",    f"{self.sig_fan_hot_cpu_c} °C"),
            ("sig_fan_hot_gpu_c",    f"{self.sig_fan_hot_gpu_c} °C"),
            ("sig_drive_temp_max",   f"{self.sig_drive_temp_max} °C"),
            ("sig_vrm_temp_max",     f"{self.sig_vrm_temp_max} °C"),
            ("sig_ram_exhaust_pct",  f"{self.sig_ram_exhaust_pct} %"),
            ("sig_vram_overflow_pct",f"{self.sig_vram_overflow_pct} %"),
            ("sig_stutter_mult",     f"{self.sig_stutter_mult}×"),
            ("sig_stutter_min_hits", f"{self.sig_stutter_min_hits}"),
            ("sig_tdr_clock_frac",   f"{self.sig_tdr_clock_frac}"),
            ("sig_ppt_sat_pct",      f"{self.sig_ppt_sat_pct}"),
            ("sig_clock_stretch_mhz",f"{self.sig_clock_stretch_mhz} MHz"),
        ]
        for name, v in misc_display:
            w(f"       {name:26s} = ")
            wl(v, 'val')

        section("FAN / COOLING COLUMNS")
        fan_cols = [c for c in df.columns if any(k in c.upper() for k in ['FAN','RPM','PUMP','COOLER'])]
        if fan_cols:
            for c in fan_cols[:10]:
                mn, av, mx2 = df[c].min(), df[c].mean(), df[c].max()
                w(f"  {c[:50]:50s}  ")
                wl(f"min={mn:.0f}  avg={av:.0f}  max={mx2:.0f}", 'val')
        else:
            wl(f"  {MISS}", 'miss')

        section("VRM / MOSFET COLUMNS")
        vrm_cols = [c for c in df.columns if any(k in c.upper()
                    for k in ['VRM','MOSFET','CHOKE','PHASE','MOS TEMP'])]
        if vrm_cols:
            for c in vrm_cols[:8]:
                w(f"  {c[:50]:50s}  ")
                wl(f"max={df[c].max():.1f}", 'val')
        else:
            wl(f"  {MISS}", 'miss')

        section("BATTERY / LAPTOP COLUMNS")
        batt_cols = [c for c in df.columns if any(k in c.upper()
                     for k in ['BATTERY','CHARGE','DISCHARGE','AC ADAPTER','REMAINING CAPACITY'])]
        if batt_cols:
            for c in batt_cols[:8]:
                w(f"  {c[:50]:50s}  ")
                wl(f"min={df[c].min():.2f}  max={df[c].max():.2f}", 'val')
        else:
            wl("  No battery/laptop columns found - desktop system assumed.", 'muted')

        section("OUT-OF-SPEC SENSOR SUMMARY")
        oos = [c for c in df.columns if self._is_critical(c)]
        if oos:
            wl(f"  {len(oos)} column(s) currently flagged as out-of-spec:", 'crit')
            for c in oos[:15]:
                s = df[c].dropna()
                if s.empty: continue
                w(f"  ⚠ {c[:55]:55s}  ")
                wl(f"peak={s.max():.2f}", 'crit')
            if len(oos) > 15:
                wl(f"  … and {len(oos)-15} more", 'muted')
        else:
            wl("  No out-of-spec sensors detected.", 'ok')

        section("COLUMN COVERAGE SCORE")
        _key_cols = {
            "CPU temp":        cpu_temp,
            "CPU usage":       cpu_usage_col,
            "CPU power":       cpu_power,
            "CPU throttle":    throttle,
            "GPU temp":        gpu_hotspot,
            "GPU usage":       gpu_usage_col,
            "GPU clock":       gpu_clock,
            "GPU power":       gpu_power,
            "GPU mem usage":   gpu_mem_usage,
            "VRAM junction":   vram_junc,
            "Frame time":      ft_col,
            "GPU busy ms":     gpu_busy_ms,
            "GPU wait ms":     gpu_wait_ms,
            "FCLK":            fclk_col,
            "UCLK":            uclk_col,
            "MCLK":            mclk_col,
            "PCIe errors":     pcie_errors,
            "Sys interrupts":  sys_interrupts,
            "Chipset temp":    chipset_t,
        }
        found_n = sum(1 for v in _key_cols.values() if v)
        total_n = len(_key_cols)
        pct = found_n / total_n * 100
        score_tag = 'ok' if pct >= 70 else ('warn' if pct >= 40 else 'crit')
        wl(f"  {found_n}/{total_n} key columns resolved  ({pct:.0f}%)", score_tag)
        wl()
        for name, c in _key_cols.items():
            tag = 'ok' if c else 'miss'
            sym = '✓' if c else '✗'
            wl(f"  [{sym}] {name}", tag)

        section("SIGNATURE HIT SUMMARY")
        hits = self._run_signatures()
        if hits:
            _sev_tag = {'CRITICAL': 'crit', 'WARNING': 'warn', 'INFO': 'info'}
            for h in sorted(hits, key=lambda x: ['CRITICAL','WARNING','INFO'].index(x.get('severity','INFO'))):
                tag = _sev_tag.get(h['severity'], 'info')
                wl(f"  [{h['severity']:8s}] {h['name']}", tag)
                for ev in h.get('evidence', []):
                    wl(f"             • {ev}", 'muted')
        else:
            wl("  No signatures triggered.", 'ok')

        section("MCLK / XMP DETECTION")
        mclk_debug = self._col_excl(['MCLK'],        excl=['GPU','VRAM','GDDR','VIDEO'])\
                  or self._col_excl(['MEMORY CLOCK'], excl=['GPU','VRAM','GDDR','VIDEO'])\
                  or self._col_excl(['DRAM CLOCK'],   excl=['GPU','VRAM','GDDR','VIDEO'])
        col("mclk_col (excl GPU)", mclk_debug)
        if mclk_debug and mclk_debug in df.columns:
            m_med = df[mclk_debug].median()
            is_ddr5 = m_med > 2400
            effective = int(m_med * 2)
            stock_ceiling = 2400 if is_ddr5 else 1333
            val("MCLK median (MHz)", m_med)
            val("Effective MT/s",    effective, "d")
            w(f"       {'DDR generation':44s} = ")
            wl("DDR5" if is_ddr5 else "DDR4", 'val')
            at_stock = m_med <= stock_ceiling
            w(f"       {'At stock speed (XMP off?)':44s} = ")
            wl("YES" if at_stock else "NO", 'warn' if at_stock else 'ok')

        section("UI STATE")
        t = self._get_theme()
        active_theme = self.custom_theme.get("active", "Dark (Default)")
        pinned = getattr(self, '_pinned_line', None)
        tooltip_on = getattr(self, '_tooltip_enabled', True)
        sel_count = len([c for c, v in self.vars.items() if v.get() and c in df.columns])
        w(f"       {'Active theme':44s} = ");     wl(active_theme, 'val')
        w(f"       {'is_dark':44s} = ");          wl(str(self.is_dark), 'val')
        w(f"       {'Theme bg / accent':44s} = ");wl(f"{t['bg']}  /  {t['accent']}", 'val')
        w(f"       {'Pinned sensor':44s} = ");    wl(pinned or "none", 'ok' if not pinned else 'warn')
        w(f"       {'Tooltip enabled':44s} = ");  wl(str(tooltip_on), 'ok' if tooltip_on else 'miss')
        w(f"       {'Selected sensors':44s} = "); wl(str(sel_count), 'val')
        w(f"       {'Multi mode':44s} = ");       wl(str(self.multi_mode), 'val')
        w(f"       {'Heatmap mode':44s} = ");     wl(str(self.heatmap_mode), 'val')
        w(f"       {'Delta mode':44s} = ");       wl(str(self.delta_mode), 'val')

        section("LEGEND & PLOT WIDGET STATE")
        def _winfo(widget, label):
            try:
                exists  = widget.winfo_exists()
                mapped  = widget.winfo_ismapped()
                w_px    = widget.winfo_width()
                h_px    = widget.winfo_height()
                rw_px   = widget.winfo_reqwidth()
                rh_px   = widget.winfo_reqheight()
                x       = widget.winfo_x()
                y       = widget.winfo_y()
                cls     = widget.winfo_class()
                wl(f"  {label}", 'section')
                wl(f"    exists={exists}  mapped={mapped}  class={cls}", 'val')
                wl(f"    size   : {w_px} x {h_px} px  (requested: {rw_px} x {rh_px})", 'val')
                wl(f"    pos    : x={x}  y={y}", 'val')
            except Exception as _e:
                wl(f"  {label}  ERROR: {_e}", 'warn')

        for _attr, _lbl in [
            ('canvas_widget',    'canvas_widget (matplotlib Tk canvas)'),
            ('fig',              'fig (matplotlib Figure)'),
            ('toolbar',          'toolbar (_NoHistoryToolbar)'),
            ('_legend_panel',    '_legend_panel'),
            ('_legend_scroll_frame', '_legend_scroll_frame'),
            ('_legend_canvas',   '_legend_canvas (Tk Canvas)'),
            ('_legend_inner',    '_legend_inner (Tk Frame inside canvas)'),
        ]:
            _obj = getattr(self, _attr, None)
            if _obj is None:
                wl(f"  {_lbl}  : (not set)", 'muted')
            elif _attr == 'fig':
                try:
                    wl(f"  fig", 'section')
                    wl(f"    size (in)  : {self.fig.get_size_inches()}", 'val')
                    wl(f"    dpi        : {self.fig.dpi}", 'val')
                    wl(f"    axes count : {len(self.fig.axes)}", 'val')
                    if self.fig.axes:
                        _ax = self.fig.axes[0]
                        wl(f"    ax lines   : {len(_ax.get_lines())}", 'val')
                        for _ln in _ax.get_lines():
                            _lbl2 = _ln.get_label()
                            _col  = _ln.get_color()
                            wl(f"      line: label={repr(_lbl2[:60])}  color={_col}", 'val')
                except Exception as _e:
                    wl(f"  fig  ERROR: {_e}", 'warn')
            elif _attr == 'canvas_widget':
                try:
                    _tkw = _obj.get_tk_widget()
                    _winfo(_tkw, _lbl)
                except Exception as _e:
                    wl(f"  {_lbl}  ERROR: {_e}", 'warn')
            else:
                _winfo(_obj, _lbl)

        wl()
        wl("  --- Legend canvas detail ---", 'section')
        try:
            _lc = self._legend_canvas
            wl(f"    winfo_width()       : {_lc.winfo_width()}", 'val')
            wl(f"    winfo_height()      : {_lc.winfo_height()}", 'val')
            wl(f"    winfo_reqwidth()    : {_lc.winfo_reqwidth()}", 'val')
            wl(f"    winfo_reqheight()   : {_lc.winfo_reqheight()}", 'val')
            wl(f"    winfo_ismapped()    : {_lc.winfo_ismapped()}", 'val')
            wl(f"    bbox('all')         : {_lc.bbox('all')}", 'val')
            wl(f"    cget(scrollregion)  : {_lc.cget('scrollregion')}", 'val')
            _items = _lc.find_all()
            wl(f"    canvas items        : {len(_items)}", 'val')
            for _item in _items:
                _itype  = _lc.type(_item)
                _icoords = _lc.coords(_item)
                _ibbox  = _lc.bbox(_item)
                wl(f"      item {_item}: type={_itype}  coords={_icoords}  bbox={_ibbox}", 'val')
        except Exception as _e:
            wl(f"    ERROR reading legend canvas: {_e}", 'warn')

        wl()
        wl("  --- Legend inner frame children ---", 'section')
        try:
            _li = self._legend_inner
            _children = _li.winfo_children()
            wl(f"    child count         : {len(_children)}", 'val')
            for _i, _ch in enumerate(_children[:10]):
                try:
                    wl(f"    [{_i}] {_ch.winfo_class():12s}  "
                       f"mapped={_ch.winfo_ismapped()}  "
                       f"size={_ch.winfo_width()}x{_ch.winfo_height()}  "
                       f"req={_ch.winfo_reqwidth()}x{_ch.winfo_reqheight()}", 'val')
                except Exception:
                    pass
            if len(_children) > 10:
                wl(f"    ... and {len(_children)-10} more", 'muted')
        except Exception as _e:
            wl(f"    ERROR reading legend inner: {_e}", 'warn')

        wl()
        wl("  --- Plot mode at dump time ---", 'section')
        wl(f"    delta_mode    : {self.delta_mode}", 'val')
        wl(f"    multi_mode    : {self.multi_mode}", 'val')
        wl(f"    heatmap_mode  : {self.heatmap_mode}", 'val')
        wl(f"    compare_mode  : {self.compare_mode}", 'val')
        sel = [c for c, v in self.vars.items() if v.get() and c in df.columns]
        wl(f"    selected cols : {sel[:5]}{'...' if len(sel)>5 else ''}", 'val')

        wl()
        wl("  --- Toolbar internals ---", 'section')
        try:
            _tb = self.toolbar
            wl(f"    buttons : {list(getattr(_tb, '_buttons', {}).keys())}", 'val')
            for _name, _btn in getattr(_tb, '_buttons', {}).items():
                if _btn:
                    try:
                        wl(f"      {_name:10s}  mapped={_btn.winfo_ismapped()}  "
                           f"size={_btn.winfo_width()}x{_btn.winfo_height()}", 'val')
                    except Exception:
                        pass
            _msg = getattr(_tb, '_message_label', None) or getattr(_tb, 'message', None)
            if _msg:
                try:
                    _side = _msg.pack_info().get('side', '?')
                    wl(f"    message label  mapped={_msg.winfo_ismapped()}  "
                       f"size={_msg.winfo_width()}x{_msg.winfo_height()}  "
                       f"pack_side={_side}", 'val')
                except Exception as _e:
                    wl(f"    message label  ERROR: {_e}", 'warn')
        except Exception as _e:
            wl(f"    ERROR reading toolbar: {_e}", 'warn')

        wl()
        wl("  --- Root window geometry ---", 'section')
        try:
            wl(f"    geometry        : {self.root.winfo_geometry()}", 'val')
            wl(f"    state           : {self.root.state()}", 'val')
            wl(f"    winfo_width     : {self.root.winfo_width()}", 'val')
            wl(f"    winfo_height    : {self.root.winfo_height()}", 'val')
            wl(f"    scaling         : {self.root.tk.call('tk', 'scaling')}", 'val')
            wl(f"    winfo_fpixels   : {self.root.winfo_fpixels('1i'):.1f} dpi", 'val')
        except Exception as _e:
            wl(f"    ERROR: {_e}", 'warn')

        wl()
        wl("  --- _finalize_legend retry log (last run) ---", 'section')
        _flog = getattr(self, '_legend_finalize_log', [])
        if _flog:
            for _entry in _flog:
                _tag = 'ok' if 'SUCCESS' in _entry else ('crit' if 'FAILED' in _entry or 'EXCEPTION' in _entry else 'val')
                wl(f"    {_entry}", _tag)
        else:
            wl("    (no log yet - open delta mode then refresh dump)", 'muted')

        wl()
        wl("  --- Full widget hierarchy (self.right) ---", 'section')
        def _dump_widget(w, indent=0):
            try:
                cls   = w.winfo_class()
                wx    = w.winfo_x()
                wy    = w.winfo_y()
                ww    = w.winfo_width()
                wh    = w.winfo_height()
                mapped = w.winfo_ismapped()
                try:    bg = w.cget('bg')
                except Exception: bg = 'N/A'
                try:    hl = w.cget('highlightthickness')
                except Exception: hl = 'N/A'
                try:    bd = w.cget('bd')
                except Exception: bd = 'N/A'
                try:    relief = w.cget('relief')
                except Exception: relief = 'N/A'
                prefix = '  ' * indent
                wl(f"    {prefix}{cls}  pos=({wx},{wy})  size={ww}x{wh}  "
                   f"mapped={mapped}  bg={bg}  hl={hl}  bd={bd}  relief={relief}", 'val')
                for child in w.winfo_children():
                    _dump_widget(child, indent + 1)
            except Exception as _de:
                wl(f"    {'  '*indent}ERROR: {_de}", 'warn')
        try:
            _dump_widget(self.right)
        except Exception as _e:
            wl(f"    ERROR dumping hierarchy: {_e}", 'warn')

        section("SENSOR STATS CACHE")
        cache = getattr(self, '_sensor_stats_cache', {})
        if cache:
            wl(f"  {len(cache)} sensor(s) cached:", 'ok')
            for cname, (s_min, s_max) in list(cache.items())[:10]:
                w(f"  {cname[:50]:50s}  ")
                wl(f"min={s_min:.2f}  max={s_max:.2f}", 'val')
            if len(cache) > 10:
                wl(f"  ... and {len(cache)-10} more", 'muted')
        else:
            wl("  Cache empty - no sensors selected or plot not yet drawn.", 'muted')

        wl()
        wl('=' * 72, 'header')
        wl(f"  End of dump - Ctrl+F8 to refresh, X to close", 'header')
        wl('=' * 72, 'header')

        txt.config(state='disabled')
        txt.see('1.0')

    def _run_debug_dump(self):
        """Legacy stub - debug output now goes to the in-app window via _open_debug_window()."""
        self._open_debug_window()

    def _start_sig_watcher(self):
        """Start the background signature evaluation loop.
        Runs signatures in a thread whenever _sig_dirty is True,
        then updates the live badge on the main thread."""
        import threading

        def _worker():
            try:
                hits = self._run_signatures()
            except Exception:
                hits = []
            def _done():
                self._sig_hits    = hits
                self._sig_running = False
                self._update_sig_badge()
                if getattr(self, 'sig_timeline_enabled', True):
                    sel = [c for c, v in self.vars.items() if v.get() and c in self.df.columns]


                    if not sel:
                        self.update_plot()
            self.root.after(0, _done)

        def _tick():
            if self._sig_dirty and not self._sig_running:
                self._sig_dirty   = False
                self._sig_running = True
                threading.Thread(target=_worker, daemon=True).start()
            self._sig_watcher_id = self.root.after(3000, _tick)

        if self._sig_watcher_id:
            self.root.after_cancel(self._sig_watcher_id)
        _tick()

    def _update_sig_badge(self):
        """Update the per-severity badge labels from completed signature results."""
        def _safe(lbl, text):
            if lbl and lbl.winfo_exists():
                lbl.config(text=text)

        hits  = self._sig_hits
        crits = sum(1 for h in hits if h.get('severity') == 'CRITICAL')
        warns = sum(1 for h in hits if h.get('severity') == 'WARNING')
        infos = sum(1 for h in hits if h.get('severity') == 'INFO')

        if not hits:
            _safe(self._badge_crit_lbl, "")
            _safe(self._badge_warn_lbl, "")
            _safe(self._badge_info_lbl, "")
            _safe(self._badge_ok_lbl,   "✅ Clear")
        else:
            _safe(self._badge_crit_lbl, f"🔴 {crits}" if crits else "")
            _safe(self._badge_warn_lbl, f"🟡 {warns}" if warns else "")
            _safe(self._badge_info_lbl, f"🔵 {infos}" if infos else "")
            _safe(self._badge_ok_lbl,   "")

    def _mark_sig_dirty(self):
        """Call whenever something changes that requires a signature re-run."""
        self._sig_dirty = True

    def _run_signatures(self) -> list:
        hits = []
        df = self.df

        def add(name, severity, description, evidence, mask=None, cols=None, advice=None):
            if advice:
                description = description + " " + advice
            if name in self.disabled_sigs:
                return
            clean_ev = [str(e) for e in evidence if e and str(e).strip()]
            start_idx, end_idx = None, None
            if mask is not None:
                try:
                    active = mask.values if hasattr(mask, 'values') else mask
                    idxs = [i for i, v in enumerate(active) if v]
                    if idxs:
                        start_idx, end_idx = idxs[0], idxs[-1]
                except Exception:
                    pass
            spans = []
            if start_idx is not None and end_idx is not None:
                spans = [(start_idx, end_idx)]
            if not spans:
                try:
                    sig_cols = [c for c in self._sensors_for_sig(name) if c in df.columns]
                    if sig_cols:
                        numeric = df[sig_cols].select_dtypes(include='number')
                        if not numeric.empty:
                            import numpy as _np
                            score     = numeric.rank(pct=True).max(axis=1)
                            peak      = int(score.idxmax())
                            threshold = max(score.quantile(0.80), score.iloc[peak] * 0.75)
                            arr    = score.values >= threshold
                            padded = _np.concatenate(([False], arr, [False]))
                            diff   = _np.diff(padded.astype(int))
                            raw_s  = _np.where(diff == 1)[0].tolist()
                            raw_e  = (_np.where(diff == -1)[0] - 1).tolist()
                            max_gap = max(1, int(len(df) * 0.05))
                            merged_s, merged_e = list(raw_s), list(raw_e)
                            i = 0
                            while i < len(merged_s) - 1:
                                if merged_s[i + 1] - merged_e[i] <= max_gap:
                                    merged_e[i] = merged_e[i + 1]
                                    del merged_s[i + 1]
                                    del merged_e[i + 1]
                                else:
                                    i += 1
                            spans = [(int(s), int(e)) for s, e in zip(merged_s, merged_e)]
                except Exception:
                    pass
            hits.append({
                'name': name,
                'severity': severity,
                'description': description,
                'evidence': clean_ev,
                'start_idx': spans[0][0] if spans else None,
                'end_idx':   spans[0][1] if spans else None,
                'spans':     spans,
                'cols': [c for c in (cols or []) if c and c in df.columns],
            })

        def _a(key):
            """Return first valid user-confirmed alias column for key, else None.
            Supports multiple aliases per key (list) so different CSVs all resolve."""
            entry = self.analyzer.aliases.get(key)
            if not entry:
                return None
            candidates = entry if isinstance(entry, list) else [entry]
            return next((c for c in candidates
                         if c and c in df.columns), None)

        cpu_temp      = _a('cpu_temp') or self._col('TCTL') or self._col('TDIE') or self._col('PROZESSOR', 'TEMPERATUR') or self._col('TEMPERATUR') or self._col_excl(['CPU'], excl=['USAGE','UTIL','LOAD','THREAD','W]','%]','MHz','RPM'])
        cpu_clock     = self._col('KERN', 'TAKT') or self._col('CORE', 'CLOCK') or self._col('CLOCK')
        cpu_usage_col = _a('cpu_usage') or self._col('CPU', 'AUSLASTUNG') or self._col_excl(['CPU','USAGE'], excl=['°C','TEMP','W]']) or self._col_excl(['CPU','UTIL'], excl=['°C','TEMP','W]']) or self._col_excl(['CPU','LOAD'], excl=['°C','TEMP','W]']) or self._col('PROZESSOR') or self._col('TOTAL', 'CPU')
        cpu_power     = _a('cpu_power') or self._col('CPU-Gesamt-Leistungsaufnahme') or self._col_excl(['CPU','PACKAGE','W'], excl=['°C','TEMP','USAGE','LOAD','%']) or self._col_excl(['CPU','PPT'], excl=['°C','TEMP']) or self._col_excl(['CPU','POWER'], excl=['°C','TEMP']) or self._col('CPU Package Power')
        throttle      = self._col('THROTTLE') or self._col('PROCHOT')
        cpu_utility   = self._col('CPU USAGE') or self._col('CPU UTILIZATION') or self._col('CPU AUSLASTUNG') or self._col('TOTAL CPU USAGE')

        gpu_hotspot   = _a('gpu_temp') or self._col_excl(('GPU', 'HOT'), excl=('CPU', 'LIMIT')) or self._col_excl(('GPU', 'TEMP'), excl=('CPU',))
        gpu_usage_col = _a('gpu_usage') or self._col_active(('GPU', 'USAGE')) or self._col_active(('GPU', 'LOAD')) or self._col_active(('GPU', 'AUSLASTUNG')) or self._col('GPU USAGE')
        gpu_clock     = _a('gpu_clock') or self._col_active(('GPU', 'CLOCK'), excl=('EFFECTIVE', 'MEMORY', 'CROSSBAR', 'SOC', 'VCN', 'VIDEO')) or self._col_active(('GPU', 'FREQUENCY')) or self._col_active(('GPU', 'TAKT'))
        gpu_throttle  = self._col_excl(('GPU', 'THROTTL'), excl=('CPU',)) or self._col('PERFCAP')
        gpu_power     = _a('gpu_power') or self._col_active(('GPU', 'POWER')) or self._col('BOARD', 'POWER') or self._col('TOTAL', 'BOARD') or self._col('TGP') or self._col('TBP') or self._col('ASIC') or self._col('NVVDD') or self._col('PCIe') or self._col('LEISTUNG') or self._col('EINGANGSLEISTUNG') or self._col('POWER')
        gpu_clk_col   = self._col_active(('GPU', 'CLOCK'), excl=('EFFECTIVE', 'MEMORY', 'CROSSBAR', 'SOC', 'VCN', 'VIDEO')) or self._col('GPU Clock [MHz]')

        gpu_12v_input_v = self._col('GPU 12VHPWR Voltage') or self._col('GPU PCIe +12V Input Voltage') or self._col('GPU 12V Input Voltage')
        gpu_12v_input_w = self._col('GPU 12VHPWR Power') or self._col('GPU Power [W]') or self._col('GPU Board Power')
        gpu_pwr_limit   = self._col('Performance Limit - Power [Yes/No]') or self._col('PERFCAP', 'PWR')

        gpu_mem_usage = self._col('GPU','MEMORY','USAGE') or self._col('GPU','MEMORY','ALLOCATED') or self._col('GPU','MEM','USAGE') or self._col('GPU','MEM','LOAD') or self._col('D3D','MEMORY') or self._col('VRAM','USAGE') or self._col('FRAMEBUFFER') or self._col('ADAPTER','MEMORY')
        vram_junction_temp = self._col('GPU Memory Junction Temperature [°C]')
        gpu_mem_dedicated = self._col('GPU D3D Memory Dedicated')
        gpu_mem_dynamic   = self._col('GPU D3D Memory Dynamic')
        gpu_bus_col       = self._col('GPU Bus Load') or self._col('Bus Load')

        is_laptop     = any(k in "".join(self.df.columns).upper() for k in ['BATTERY', 'CHARGE', 'AC ADAPTER', 'DISCHARGE', 'MOBILE', 'LAPTOP'])
        chipset_t     = _a('chipset_temp') or self._col('Chipset [°C]') or self._col('Motherboard [°C]') or self._col('PCH') or self._col('SMU')
        usb_v_col     = self._col('USB VCC') or self._col('USB Voltage')
        pcie_errors   = _a('pcie_errors') or self._col('PCI Express Error Counters (avg)')
        system_interrupts = _a('sys_interrupts') or self._col('System Interrupts') or self._col('DPC Latency')

        ft_col        = _a('frame_time') or self._col('Frametime [ms]') or self._col('GPU Frametime') or self._col('Frame Time')
        gpu_busy_ms   = _a('gpu_busy') or self._col('GPU Busy (avg) [ms]') or self._col('GPU Busy')
        gpu_wait_ms   = _a('gpu_wait') or self._col('GPU Wait (avg) [ms]') or self._col('GPU Wait')
        gpu_eff_clock = self._col('GPU Effective Clock [MHz]')
        fclk_col = _a('fclk') or self._col('FCLK') or None
        uclk_col = _a('uclk') or next((c for c in df.columns if 'UCLK' in c), None)
        mclk_col = _a('mclk') or self._col_excl(['MCLK'],         excl=['GPU','VRAM','GDDR','VIDEO'])\
                              or self._col_excl(['MEMORY CLOCK'], excl=['GPU','VRAM','GDDR','VIDEO'])\
                              or self._col_excl(['DRAM CLOCK'],   excl=['GPU','VRAM','GDDR','VIDEO'])\
                              or None

        def mx(col): return df[col].max() if col and col in df.columns else 0
        def avg(col): return df[col].mean() if col and col in df.columns else 0

        if cpu_temp:
            limit = self.temp_limits.get('TDIE', 95.0)
            warn_threshold = limit * 0.85
            crit_threshold = limit * 0.92

            peak_temp   = mx(cpu_temp)
            is_critical = peak_temp >= crit_threshold and self._sustained(cpu_temp, crit_threshold,
                                          n_samples=self.sig_cpu_thermal_samples)
            is_warning  = peak_temp >= warn_threshold and self._sustained(cpu_temp, warn_threshold,
                                          n_samples=self.sig_cpu_thermal_samples)
            if not is_critical and peak_temp >= limit:
                is_critical = True
            elif not is_warning and peak_temp >= warn_threshold:
                is_warning = True

            if is_critical or is_warning:
                thr_active = throttle and mx(throttle) >= 1.0
                severity = "CRITICAL" if is_critical else "WARNING"
                _cpu_thresh = crit_threshold if is_critical else warn_threshold
                _cpu_mask = df[cpu_temp] >= _cpu_thresh
                add("CPU Thermal Throttling", severity,
                    "CPU is hitting its thermal ceiling. ADVICE: Check CPU cooler mounting, re-apply thermal paste, or ensure your AIO pump hasn't failed.",
                    [f"Peak Temp: {mx(cpu_temp):.1f}°C",
                     f"Limit: {limit:.0f}°C",
                     f"Throttling Flag: {'Active' if thr_active else 'Inactive'}"],
                    mask=_cpu_mask, cols=[cpu_temp, throttle])

        if gpu_hotspot:
            hs_max = mx(gpu_hotspot)
            hs_limit = self.temp_limits.get('HOTSPOT', 95.0)

            gpu_edge = self._col('GPU Temperature') or self._col_excl(
                ('GPU', 'TEMP'),
                excl=('HOTSPOT', 'MEMORY', 'CPU', 'VR', 'VRM', 'JUNCTION', 'SOC')
            )

            delta_val = 0
            if gpu_edge:
                delta_series = self.df[gpu_hotspot] - self.df[gpu_edge]
                delta_val = delta_series.max()

            evidence = [
                f"Hotspot Max: {hs_max:.1f}°C",
                f"Thermal Delta: {delta_val:.1f}°C"
            ]

            if hs_max >= hs_limit:
                add("GPU Overheating (Hotspot)", "CRITICAL",
                    "The GPU Hotspot is at dangerous levels. ADVICE: Immediately increase GPU fan curves in Afterburner and check for obstructed case airflow.",
                    evidence + [f"Hardware Limit: {hs_limit}°C"], cols=[gpu_hotspot, gpu_edge])

            elif hs_max > (hs_limit - 10) or delta_val >= 21.0:
                if delta_val >= 21.0:
                    msg = "High thermal delta detected. ADVICE: A gap over 21°C suggests poor mounting pressure or 'pump-out' of thermal paste. Consider re-pasting the GPU."
                else:
                    msg = "GPU Hotspot is approaching dangerous levels. ADVICE: Increase fan speeds or reduce the power limit."

                add("GPU Thermal Warning", "WARNING", msg, evidence, cols=[gpu_hotspot, gpu_edge])

        if not is_laptop:
            v12 = self._col('+12V')
            if v12:
                v_min = df[v12].min()
                if v_min < self.sig_v12_lo:
                    severity = "CRITICAL" if v_min < 11.2 else "WARNING"
                    add("PSU +12V Rail Sag", severity,
                        "The 12V rail (GPU/CPU power) is sagging below safe limits. This causes system-wide instability or 'black screen' crashes under load. "
                        "ADVICE: Check that PCIe and EPS power cables are fully seated. If the sag persists, the PSU is likely underpowered or failing.",
                        [f"Min Voltage: {v_min:.2f}V", f"Safety Limit: {self.sig_v12_lo}V"])

        if gpu_usage_col and gpu_clock:
            low_usage = df[gpu_usage_col] < 5
            clock_stall = (df[gpu_clock].rolling(3).std() < 1.0) & (df[gpu_clock] > 0)

            tdr_mask = low_usage & clock_stall

            confirmed_tdr = tdr_mask.rolling(5).sum() >= 3

            if (df[gpu_usage_col].rolling(10).mean() > 20).any() and confirmed_tdr.any():
                add(
                    "GPU Driver TDR (Timeout)", "CRITICAL",
                    "A GPU driver timeout pattern was detected. Likely driver stall or reset event.",
                    [
                f"Confirmed Events: {int(confirmed_tdr.sum())} samples detected."
                    ],
                    mask=confirmed_tdr, cols=[gpu_usage_col, gpu_clock])

        drive_temps = [c for c in df.columns if 'TEMP' in c.upper() and any(k in c.upper() for k in ['DRIVE', 'NVME', 'SSD'])]

        for d_col in drive_temps:
            peak = mx(d_col)
            u_col = d_col.upper()

            if any(k in u_col for k in ['HDD', 'HARD DRIVE', 'ST']):
                crit_limit = 55.0
                warn_limit = 45.0
                drive_type = "HDD (Mechanical)"
            else:
                crit_limit = self.sig_drive_temp_max
                warn_limit = self.sig_drive_temp_max - 10.0
                drive_type = "SSD/NVMe"

            if peak >= crit_limit:
                desc = (f"Critical heat on {drive_type} '{d_col}'. "
                        "For HDDs, this can cause mechanical failure and head crashes. "
                        "For SSDs, this triggers emergency shutdowns and disconnects. "
                        "ADVICE: Power off immediately to prevent permanent data loss.")
                add("Storage Thermal Critical", "CRITICAL", desc,
                    [f"Peak: {peak:.1f}°C", f"Limit: {crit_limit}°C", f"Type: {drive_type}"])

            elif peak > warn_limit:
                desc = (f"High temperature on {drive_type} '{d_col}'. "
                        "This leads to thermal throttling and reduced lifespan. "
                        "ADVICE: Improve case airflow or move the drive away from heat sources (like the GPU).")
                add("Storage Overheating", "WARNING", desc,
                    [f"Peak: {peak:.1f}°C", f"Warning: {warn_limit}°C", f"Type: {drive_type}"])

        whea = self._col('WHEA')
        if whea and mx(whea) > 0:
            add("Hardware (WHEA) Errors", "CRITICAL",
                "Windows detected physical hardware errors. ADVICE: This is often caused by unstable RAM (XMP/EXPO) or CPU undervolts. Revert to BIOS defaults.",
                [f"Total Errors: {int(mx(whea))}"], cols=[whea])

        ppt_limit = self._col('CPU', 'PPT', 'LIMIT')
        if cpu_power and ppt_limit and self._sustained(cpu_power, mx(ppt_limit)*self.sig_ppt_sat_pct,
                                                        self.sig_ppt_sat_samples):
            add("CPU Power Limit Reached", "WARNING",
                "CPU performance is being capped by power limits. ADVICE: If temps are safe, you can increase 'PPT' or 'PL1/PL2' limits in BIOS.",
                [f"Power Sustained at: {avg(cpu_power):.1f}W"], cols=[cpu_power])

        for col in df.columns:
            if ('FAN' in col.upper() or 'RPM' in col.upper()) and '[%]' not in col:
                fan_s = df[col].ffill().fillna(0)
                if fan_s.max() > self.sig_fan_min_spinning:
                    is_stalled = (fan_s < self.sig_fan_stall_rpm)
                    is_hot = pd.Series(False, index=df.index)
                    if 'GPU' in col.upper() and gpu_hotspot: is_hot = df[gpu_hotspot] > self.sig_fan_hot_gpu_c
                    elif 'CPU' in col.upper() and cpu_temp: is_hot = df[cpu_temp] > self.sig_fan_hot_cpu_c
                    else:
                        if gpu_hotspot: is_hot |= (df[gpu_hotspot] > self.sig_fan_hot_gpu_c)
                        if cpu_temp: is_hot |= (df[cpu_temp] > self.sig_fan_hot_cpu_c)

                    _fan_mask = (is_stalled & is_hot).rolling(window=3).sum() >= 3
                    if _fan_mask.max() >= 1:
                        add("Fan Stall Detected", "CRITICAL",
                            f"Fan '{col}' stopped while components were hot. ADVICE: Check for cables blocking the fan blades or a failing motor.",
                            ["RPM hit 0 during load samples."],
                            mask=_fan_mask, cols=[col, cpu_temp, gpu_hotspot])
                        break

        df = df.copy()
        if gpu_mem_usage and gpu_mem_dynamic:

            vram = df[gpu_mem_usage]
            spill = df[gpu_mem_dynamic]

            vram_pct = vram / vram.max() * 100
            spill_trend = spill.diff().rolling(5, min_periods=1).mean()
            spill_active = spill_trend > spill.std() * 0.6
            overflow = (vram_pct > 95) & spill_active
            overflow = overflow.rolling(3, min_periods=1).sum() >= 2
            overflow_shifted = overflow.shift(1, fill_value=False)

            event_start = (~overflow_shifted) & overflow
            event_end   = overflow_shifted & (~overflow)

            overflow_events = event_start.sum()
            df["_overflow_state"] = overflow.astype(int)
            if "Timestamp" in df.columns:
                df["Timestamp"] = pd.to_datetime(df["Timestamp"])
                df["_time_diff"] = df["Timestamp"].diff().dt.total_seconds().fillna(0)
                time_unit = "seconds"
            else:
                df["_time_diff"] = 1
                time_unit = "samples"

            overflow_time = df["_time_diff"] * df["_overflow_state"]

            total_overflow_duration = overflow_time.sum()

            event_durations = []
            current = 0

            for state, dt in zip(overflow, df["_time_diff"]):
                if state:
                    current += dt
                elif current > 0:
                    event_durations.append(current)
                    current = 0

            if current > 0:
                event_durations.append(current)

            avg_duration = sum(event_durations) / len(event_durations) if event_durations else 0

            if overflow_events > 0:

                add(
                    "GPU VRAM Overflow Analysis",
                    "WARNING",
                    "VRAM pressure caused system memory spillover. This leads to PCIe transfers, "
                    "stuttering, and frame-time instability.",
                    [
                        f"Overflow Events: {int(overflow_events)}",
                        f"Total Duration: {total_overflow_duration:.2f} {time_unit}",
                        f"Average Event Duration: {avg_duration:.2f} {time_unit}",
                        f"Max VRAM Pressure: {vram_pct.max():.1f}%",
                        f"Max Spill Memory: {spill.max():.0f}"
                    ],
                    mask=overflow, cols=[gpu_mem_usage, gpu_mem_dynamic])

            df.drop(columns=["_overflow_state", "_time_diff"], inplace=True, errors="ignore")

        fail_cols = [c for c in df.columns if any(k in c.upper() for k in ['DRIVE', 'SSD', 'NVME'])
                     and any(k in c.upper() for k in ['FAILURE', 'WARNING'])]

        life_cols = [c for c in df.columns if 'REMAINING LIFE' in c.upper() or 'DRIVE HEALTH' in c.upper()]

        def _flag_active(col) -> bool:
            s = df[col]
            s_num = pd.to_numeric(s, errors='coerce')
            if s_num.notna().any() and s_num.max() >= 1.0:
                return True
            return s.astype(str).str.strip().str.upper().eq('YES').any()

        for f_col in fail_cols:
            if _flag_active(f_col):
                add(
                    name="S.M.A.R.T. Hardware Failure",
                    severity="CRITICAL",
                    description=(
                        f"The drive '{f_col}' reports an imminent hardware failure. This is a definitive "
                        "signal from the drive's own logic that it is dying. ADVICE: Stop all heavy tasks. "
                        "Backup your data immediately and replace the drive today."
                    ),
                    evidence=[f"Status: FAILURE FLAG ACTIVE"]
                )

        for l_col in life_cols:
            current_life = df[l_col].min()

            if current_life <= 5.0:
                add(
                    name="SSD Lifespan Critical",
                    severity="CRITICAL",
                    description=(
                        f"The drive '{l_col}' has reached the absolute end of its life ({current_life:.1f}%). "
                        "The pool of spare cells is likely empty. To prevent data loss, the drive may soon "
                        "refuse to write new data. ADVICE: Replace this drive immediately."
                    ),
                    evidence=[f"Remaining Life: {current_life:.1f}%", "Safety Limit: 5.0%"]
                )

            elif current_life <= 20.0:
                add(
                    name="SSD Wear Warning",
                    severity="WARNING",
                    description=(
                        f"The drive '{l_col}' is significantly worn ({current_life:.1f}% health). "
                        "While not failing yet, the reliability of the NAND flash begins to degrade at this level. "
                        "ADVICE: Start planning for a replacement drive to avoid an emergency clone later."
                    ),
                    evidence=[f"Remaining Life: {current_life:.1f}%", "Warning Threshold: 20.0%"]
                )

        ram_load = self._col('PHYSICAL', 'MEMORY', 'LOAD')
        if ram_load and mx(ram_load) > self.sig_ram_exhaust_pct:
            add("System RAM Exhaustion", "CRITICAL",
                "Physical RAM is nearly full. ADVICE: Close browser tabs, Discord, or other background apps. Consider upgrading to 32GB RAM.",
                [f"Max Load: {mx(ram_load):.1f}%", f"Threshold: {self.sig_ram_exhaust_pct}%"],
                mask=df[ram_load] > self.sig_ram_exhaust_pct, cols=[ram_load])

        v_load = self._col('VIRTUAL', 'MEMORY', 'LOAD') or self._col('PAGE', 'FILE', 'USAGE')
        if v_load and mx(v_load) > 98:
            add("Virtual Memory Limit", "CRITICAL",
                "The system 'Commit Limit' is full. ADVICE: Ensure your Windows Page File is set to 'System Managed' and your C: drive is not full.",
                [f"Commit Charge: {mx(v_load):.1f}%"])

        if gpu_usage_col and cpu_usage_col:
            bn = (df[gpu_usage_col] < self.sig_cpu_bn_gpu_pct) & (df[cpu_usage_col] > self.sig_cpu_bn_cpu_pct)
            if bn.rolling(window=self.sig_cpu_bn_samples).sum().max() >= self.sig_cpu_bn_samples:
                add("CPU Bottleneck", "INFO",
                    "CPU is maxed out while GPU is idling. ADVICE: Increase resolution/graphics settings to shift load to GPU, or close background apps.",
                    [f"Avg GPU Usage during spike: {df.loc[bn, gpu_usage_col].mean():.1f}%",
                     f"Thresholds: GPU < {self.sig_cpu_bn_gpu_pct}%, CPU > {self.sig_cpu_bn_cpu_pct}%"],
                    mask=bn, cols=[cpu_usage_col, gpu_usage_col])

        vrm_temp = self._col('VRM') or self._col('MOS')
        if vrm_temp and mx(vrm_temp) > self.sig_vrm_temp_max:
            add("VRM Overheating", "CRITICAL",
                "Motherboard power delivery is too hot. ADVICE: Improve case airflow or add a small fan directed at the motherboard heatsinks.",
                [f"Max: {mx(vrm_temp):.1f}°C", f"Threshold: {self.sig_vrm_temp_max}°C"], cols=[vrm_temp])

        req_cols = [c for c in df.columns if 'Clock (perf #' in c]
        if req_cols:
            n_cores        = len(req_cols)
            per_core_ratios  = []
            per_core_active  = []

            for i, req_col in enumerate(req_cols):
                t0_col = f"Core {i} T0 Effective Clock [MHz]"
                t1_col = f"Core {i} T1 Effective Clock [MHz]"

                req = df[req_col].replace(0, np.nan)

                valid_req = req > 300

                core_ratios  = []
                core_weights = []
                core_active  = pd.Series(False, index=df.index)

                for eff_col in [t0_col, t1_col]:
                    if eff_col not in df.columns:
                        continue
                    eff = df[eff_col]

                    active = valid_req & (eff > (0.35 * req + 100))

                    ratio  = (eff / req).where(active)
                    weight = eff.where(active)

                    core_ratios.append(ratio)
                    core_weights.append(weight)
                    core_active = core_active | active

                if not core_ratios:
                    continue

                ratios  = pd.concat(core_ratios,  axis=1)
                weights = pd.concat(core_weights, axis=1)

                core_ratio  = ratios.median(axis=1)

                core_weight = ratios.notna().astype(float).mean(axis=1)

                stable_active = core_active.rolling(5, min_periods=3).sum() >= 3
                core_ratio  = core_ratio.where(stable_active)
                core_weight = core_weight.where(stable_active)

                per_core_ratios.append(core_ratio)
                per_core_active.append(core_active.astype(int))

            if per_core_ratios:
                all_ratios  = pd.concat(per_core_ratios, axis=1)
                all_active  = pd.concat(per_core_active, axis=1)

                weight_mat   = all_ratios.notna().astype(float)
                weight_total = weight_mat.sum(axis=1).replace(0, np.nan)
                weighted_sum = (all_ratios.fillna(0) * weight_mat).sum(axis=1)
                mean_ratio   = (weighted_sum / weight_total).replace([np.inf, -np.inf], np.nan)

                worst_core_ratio = all_ratios.min(axis=1)

                active_count  = all_active.sum(axis=1)
                core_pressure = (active_count / n_cores).rolling(5, min_periods=3).mean()

                system_load = df.get(
                    'Total CPU Usage [%]',
                    pd.Series(0.0, index=df.index)
                ).fillna(0)

                sys_signal  = np.clip(system_load / 100.0, 0, 1)
                core_signal = np.clip(core_pressure.fillna(0), 0, 1)
                load_score  = 0.6 * sys_signal + 0.4 * core_signal
                valid_load  = load_score > 0.55

                load_std       = system_load.rolling(5, min_periods=3).std().fillna(0)
                in_transition  = load_std > 15.0

                major = (
                    (mean_ratio < 0.60) &
                    valid_load &
                    ~in_transition
                )
                minor = (
                    (mean_ratio >= 0.60) &
                    (mean_ratio < 0.80) &
                    valid_load &
                    ~in_transition
                )

                major_event = major.rolling(8, min_periods=5).mean() > 0.55
                minor_event = minor.rolling(8, min_periods=5).mean() > 0.50

                core_avg_ratios = all_ratios.mean()
                worst_cores     = core_avg_ratios.nsmallest(3)

                if major_event.any():
                    avg_r     = mean_ratio[major_event].mean()
                    worst_r   = mean_ratio[major_event].min()
                    peak_load = system_load[major_event].max()
                    peak_pressure = core_pressure[major_event].max()

                    cause_hints = []
                    cpu_temp_col = self._col('CPU', 'TEMP') or self._col('TDIE') or self._col('TCTL')
                    if cpu_temp_col:
                        peak_temp = df[cpu_temp_col][major_event].max()
                        t_limit   = self.temp_limits.get('TDIE', self.temp_limits.get('CORE', 95.0))
                        if peak_temp >= t_limit * 0.92:
                            cause_hints.append(f"CPU temp {peak_temp:.1f}°C near limit - likely thermal throttle")
                    ppt_col = self._col('CPU', 'PPT') or self._col('CPU', 'POWER')
                    ppt_lim_col = self._col('CPU', 'PPT', 'LIMIT') or self._col('CPU', 'POWER', 'LIMIT')
                    if ppt_col and ppt_lim_col:
                        ppt_ratio = df[ppt_col].mean() / (df[ppt_lim_col].mean() + 1e-9)
                        if ppt_ratio >= 0.95:
                            cause_hints.append("CPU PPT at limit - power throttling")
                    if not cause_hints:
                        cause_hints.append("No obvious thermal/power cause found - check for OS scheduler issues or BIOS power limits")

                    worst_core_strs = [
                        f"Core {c.split()[1] if 'Core' in str(c) else c}: avg ratio {v:.2f}"
                        for c, v in worst_cores.items() if not np.isnan(v)
                    ]

                    add(
                        name="CPU Clock Stretching - Major",
                        severity="CRITICAL",
                        description=(
                            "The CPU is consistently running well below its requested frequency "
                            "under load. This means the CPU is not delivering the performance "
                            "it should be. Causes include thermal throttling, power limit "
                            "throttling, or a BIOS/OS scheduling misconfiguration. "
                            "ADVICE: Check CPU temperatures, power limits in BIOS, and whether "
                            "Windows power plan is set to Balanced instead of High Performance."
                        ),
                        evidence=[
                            f"Average eff/req ratio under load: {avg_r:.2f} (target >0.90)",
                            f"Worst ratio recorded: {worst_r:.2f}",
                            f"Peak system load during event: {peak_load:.1f}%",
                            f"Peak core pressure: {peak_pressure:.2f}",
                        ] + worst_core_strs + cause_hints
                    )

                if minor_event.any() and not major_event.any():
                    avg_r     = mean_ratio[minor_event].mean()
                    peak_load = system_load[minor_event].max()

                    add(
                        name="CPU Clock Stretching - Minor",
                        severity="WARNING",
                        description=(
                            "The CPU is running moderately below its requested frequency under "
                            "load. This is often a sign of a soft power or thermal limit being "
                            "reached. Performance impact is mild but consistent. "
                            "ADVICE: Monitor CPU temperatures and check BIOS power limits. "
                            "If on a laptop, try a cooling pad or update the BIOS."
                        ),
                        evidence=[
                            f"Average eff/req ratio under load: {avg_r:.2f} (target >0.90)",
                            f"Peak system load during event: {peak_load:.1f}%",
                        ]
                    )

        if not is_laptop:
            for r_name, low, high in [('+5V', self.sig_v5_lo, self.sig_v5_hi),
                                       ('+3.3V', self.sig_v33_lo, self.sig_v33_hi)]:
                col = self._col(r_name)
                if col and (df[col].min() < low or df[col].max() > high):
                    add(f"PSU {r_name} Rail Unstable", "WARNING",
                        f"Low-voltage rail {r_name} is out of spec. ADVICE: This can cause random USB disconnects or drive errors. Check PSU health.",
                        [f"Detected Range: {df[col].min():.2f}V - {df[col].max():.2f}V",
                         f"Spec: {low}V - {high}V"])

            _psu_evidence = []
            _psu_severity_score = 0

            def _best_rail_col(keywords, excl, target_v, tol=0.5):
                """Return the voltage column closest in mean value to target_v."""
                import pandas as _pd
                matches = []
                for c in df.columns:
                    cu = c.upper()
                    if '[V]' not in cu:
                        continue
                    if any(e in cu for e in excl):
                        continue
                    if any(k.upper() in cu for k in keywords):
                        try:
                            mean_v = _pd.to_numeric(df[c], errors='coerce').dropna().mean()
                            matches.append((c, mean_v))
                        except Exception:
                            pass
                if not matches:
                    return None
                close = [(c, v) for c, v in matches
                         if not _pd.isna(v) and abs(v - target_v) <= tol]
                if close:
                    return min(close, key=lambda x: abs(x[1] - target_v))[0]
                return matches[0][0]

            _SIG_EXCL_BASE = ['[W]','[A]','POWER','CURRENT','WATT','VID','OFFSET',
                               'LIMIT','PPT','TDP','GPU','HPWR','FBVDD']

            v12_col = _a('rail_12v') or _best_rail_col(
                ['12V', '12 V', 'ATX 12', 'EPS 12'],
                excl=_SIG_EXCL_BASE + ['PCIE','INPUT'],
                target_v=12.0, tol=1.0)
            if v12_col:
                v12s = df[v12_col].dropna()
                sag_mask = v12s < self.sig_v12_lo
                sag_pct  = float(sag_mask.mean()) * 100
                if sag_pct > 5.0:
                    _psu_evidence.append(f"+12V sagging below {self.sig_v12_lo}V in {sag_pct:.1f}% of samples (min {v12s.min():.2f}V)")
                    _psu_severity_score += 2 if v12s.min() < 11.2 else 1

            v5_col = _a('rail_5v') or _best_rail_col(
                ['+5V', '5V [V', 'ATX 5', '5VSB', 'AVCC'],
                excl=_SIG_EXCL_BASE + ['12V','3.3','3V3'],
                target_v=5.0, tol=0.4)
            if v5_col:
                v5s = df[v5_col].dropna()
                if v5s.min() < self.sig_v5_lo or v5s.max() > self.sig_v5_hi:
                    _psu_evidence.append(f"+5V rail out of spec: {v5s.min():.2f}V \u2013 {v5s.max():.2f}V (spec {self.sig_v5_lo}\u2013{self.sig_v5_hi}V)")
                    _psu_severity_score += 1

            v33_col = _a('rail_33v') or _best_rail_col(
                ['+3.3V', '3.3V', '3V3', 'VCC3', 'AVCC3', '3VSB', 'VDD (SWA)'],
                excl=['[W]','[A]','POWER','CURRENT','GPU','VDDQ TX','VDDQ (SWB)','12V','+5V','VPP'],
                target_v=3.3, tol=0.4)
            if v33_col:
                v33s = df[v33_col].dropna()
                if v33s.min() < self.sig_v33_lo or v33s.max() > self.sig_v33_hi:
                    _psu_evidence.append(f"+3.3V rail out of spec: {v33s.min():.2f}V \u2013 {v33s.max():.2f}V (spec {self.sig_v33_lo}\u2013{self.sig_v33_hi}V)")
                    _psu_severity_score += 1

            _psu_yn_triggers = []
            for c in df.columns:
                cu = c.upper()
                if 'YES/NO' not in cu:
                    continue
                if not any(k in cu for k in ('POWER SUPPLY', 'HARDWARE LIMIT',
                                              'AVG. POWER (PL1)', 'BURST POWER (PL2)',
                                              'CURRENT (PL4)', 'THROTTL')):
                    continue
                s = df[c].dropna()
                if s.empty or s.max() < 1.0:
                    continue
                pct = float((s >= 1.0).mean()) * 100
                if pct > 1.0:
                    _psu_yn_triggers.append(f"{c.replace(' [Yes/No]', '')} active {pct:.1f}% of session")
            if _psu_yn_triggers:
                _psu_evidence.extend(_psu_yn_triggers[:4])
                _psu_severity_score += min(len(_psu_yn_triggers), 2)

            rails_sagging = sum([
                1 for col, lo in [(v12_col, self.sig_v12_lo),
                                   (v5_col, self.sig_v5_lo),
                                   (v33_col, self.sig_v33_lo)]
                if col and df[col].dropna().min() < lo
            ])
            if rails_sagging >= 2:
                _psu_evidence.append(f"{rails_sagging} rails simultaneously below spec - strong indicator of PSU output stage degradation")
                _psu_severity_score += 2

            for lbl, col in [('+12V', v12_col), ('+5V', v5_col), ('+3.3V', v33_col)]:
                if col:
                    ripple = df[col].dropna().std()
                    if ripple > 0.15:
                        _psu_evidence.append(f"{lbl} rail ripple/noise: σ={ripple:.3f}V (>0.15V suggests capacitor wear)")
                        _psu_severity_score += 1

            if v12_col and gpu_usage_col and gpu_clock:
                sag_now  = df[v12_col] < self.sig_v12_lo
                low_gpu  = df[gpu_usage_col] < 5
                clk_dead = (df[gpu_clock].rolling(3).std() < 1.0) & (df[gpu_clock] > 0)
                co_occur = (sag_now & low_gpu & clk_dead).sum()
                if co_occur >= 3:
                    _psu_evidence.append(f"+12V sag coincides with GPU stall in {co_occur} samples - likely PSU-induced GPU crash")
                    _psu_severity_score += 2

            if _psu_severity_score >= 2 and _psu_evidence:
                add("PSU Hardware Failure Indicators", "CRITICAL",
                    "Multiple independent signals suggest PSU output degradation or failure. "
                    "Rail sag, voltage ripple, and power limit throttling are consistent with "
                    "an aging or undersized power supply. "
                    "ADVICE: Test with a known-good PSU, check all power cable connections, "
                    "and consider replacement if symptoms persist.",
                    _psu_evidence)

        ft_col = self._col('FRAME TIME') or self._col('FRAMETIME')
        if ft_col:
            ft_series = df[ft_col].ffill().dropna()
            stutter_limit = ft_series.median() * self.sig_stutter_mult
            stutters = ft_series[ft_series > stutter_limit]
            if len(stutters) > self.sig_stutter_min_hits:
                add("Micro-Stuttering Detected", "WARNING",
                    "Frequent frametime spikes detected. ADVICE: Cap your framerate to a stable number or enable G-Sync/FreeSync.",
                    [f"Worst Spike: {stutters.max():.1f}ms",
                     f"Events above {self.sig_stutter_mult}× median: {len(stutters)}"])

        disk_busy = self._col('TOTAL', 'ACTIVE', 'TIME') or self._col('DISK', 'BUSY')
        if disk_busy and (df[disk_busy] >= self.sig_disk_busy_pct).rolling(
                window=self.sig_disk_busy_samples).sum().max() >= self.sig_disk_busy_samples:
            add("Storage Congestion", "INFO",
                "System drive was 100% busy. ADVICE: Check for background Windows Updates or Antivirus scans that may be fighting the game for disk access.",
                ["Persistent 100% disk usage detected.",
                 f"Threshold: {self.sig_disk_busy_pct}% for {self.sig_disk_busy_samples} samples"])

        if cpu_clock and cpu_usage_col:
            is_stuck = (df[cpu_clock] < 1000) & (df[cpu_usage_col] > 70)

            if is_stuck.rolling(window=5).sum().max() >= 5:
                add(
                    name="Phantom Clock Cap",
                    severity="CRITICAL",
                    description=(
                        "The CPU is stuck at low power-save speeds despite being under heavy load. "
                        "This is often caused by a 'PROCHOT' signal from a failing VRM or a "
                        "motherboard sensor glitch. ADVICE: Reset CMOS or check for a 'Slow Mode' "
                        "switch on your motherboard."
                    ),
                    evidence=[f"Clock stuck at: {df.loc[is_stuck, cpu_clock].mean():.0f} MHz"]
                )

        if gpu_pwr_limit and gpu_power:
            pwr_limit_active = df[gpu_pwr_limit] >= 1.0
            hit_pct = (pwr_limit_active.sum() / len(df)) * 100
            peak_watts = mx(gpu_power)
            avg_watts = avg(gpu_power)

            is_stalled = (avg_watts < 25.0) and (hit_pct > 30.0)

            if is_laptop and is_stalled:
                add(
                    name="Laptop Power Delivery Failure (Limp Mode)",
                    severity="CRITICAL",
                    description=(
                        f"The GPU is stuck in 'Limp Mode' (Average: {avg_watts:.1f}W). "
                        "The system is hitting a power limit at an extremely low level. "
                        "ADVICE: This is a hardware communication error. Your laptop may not be "
                        "recognizing the charger. Check the charger pin for damage or try a "
                        "'Hard Reset' (Hold Power for 60s) to reset the EC controller."
                    ),
                    evidence=[
                        f"Avg Power: {avg_watts:.1f}W",
                        f"Peak Power: {peak_watts:.1f}W",
                        f"PerfCap PWR Duration: {hit_pct:.1f}%"
                    ]
                )

            elif hit_pct > 25.0:
                desc = f"The GPU reached its power limit (Peak: {peak_watts:.1f}W)."
                if is_laptop:
                    desc += " ADVICE: Ensure you are in 'Performance' mode and the original charger is connected."
                else:
                    desc += " ADVICE: If temps are safe, you can increase the Power Limit in Afterburner."

                add(
                    name="GPU Power Limit Saturated",
                    severity="INFO",
                    description=desc,
                    evidence=[f"Average Load: {avg_watts:.1f}W", f"Limit Duration: {hit_pct:.1f}%"]
                )

        pcie_width = self._col('GPU', 'PCIE', 'WIDTH')
        pcie_gen   = self._col('GPU', 'PCIE', 'GENERATION') or self._col('GPU', 'BUS', 'GEN')

        if pcie_width and pcie_gen:
            max_width = mx(pcie_width)
            max_gen   = mx(pcie_gen)

            is_choked = (max_width <= 4.0) and (df[gpu_usage_col] > 50).any()

            if is_choked:
                add(
                    name="PCIe Bus Interface Chokepoint",
                    severity="CRITICAL" if max_width <= 1.0 else "WARNING",
                    description=(
                        f"The GPU is operating at a very narrow bus width (x{int(max_width)}). "
                        "This severely limits the data flow between the CPU and GPU. "
                        "ADVICE: Ensure the GPU is in the topmost PCIe slot on the motherboard. "
                        "If using a riser cable, it may be faulty or incompatible with PCIe Gen 4/5."
                    ),
                    evidence=[
                        f"Max Width: x{int(max_width)}",
                        f"Max Gen: {max_gen}",
                        "Status: Potential Physical Seating Issue"
                    ]
                )

        if cpu_usage_col and gpu_usage_col:
            os_jitter = (df[cpu_usage_col] > 70) & (df[gpu_usage_col] < 40)

            if os_jitter.rolling(window=self.sig_cpu_bn_samples).sum().max() >= self.sig_cpu_bn_samples:
                add(
                    name="Background Process Interference",
                    severity="WARNING",
                    description=(
                        "High CPU activity detected that isn't being driven by the GPU. "
                        "This usually means a background task (Antivirus, Windows Update, or "
                        "Chrome) is stealing CPU cycles, causing 'hiccups' in your game performance. "
                        "ADVICE: Open Task Manager and sort by CPU usage. Close unneeded apps before gaming."
                    ),
                    evidence=[
                        f"Avg CPU during spike: {df.loc[os_jitter, cpu_usage_col].mean():.1f}%",
                        f"Avg GPU during spike: {df.loc[os_jitter, gpu_usage_col].mean():.1f}%"
                    ]
                )

        df = df.copy()

        if ft_col and gpu_usage_col:

            rolling_avg_ft = df[ft_col].rolling(window=10, center=True).mean()
            df = df.assign(jitter_calc = df[ft_col] / rolling_avg_ft)

            is_stuttering = df['jitter_calc'] > 1.5
            stutter_count = is_stuttering.sum()

            if stutter_count > 3:
                stutter_indices = df[is_stuttering].index
                avg_gpu_load = df.loc[stutter_indices, gpu_usage_col].mean()

                bus_activity = df.loc[stutter_indices, gpu_bus_col].max() if gpu_bus_col else 0

                if (avg_gpu_load < 92) or (bus_activity > 5.0):
                    usage_gap = 100 - avg_gpu_load
                    add(
                        name="GPU Priority Conflict (Background App)",
                        severity="WARNING",
                        description=(
                            f"The GPU is losing ~{usage_gap:.1f}% potential throughput due to priority "
                            "contention. High frametime jitter was detected while the GPU had idle headroom. "
                            "This is a classic symptom of 'Hardware Acceleration' in Discord or Chrome."
                        ),
                        evidence=[
                            f"Micro-Stutters: {stutter_count} instances",
                            f"GPU Bus Activity: {bus_activity:.1f}%",
                            "ADVICE: Disable 'Hardware Acceleration' in Discord (Advanced) and your browser."
                        ]
                    )
        if gpu_mem_dedicated and gpu_mem_dynamic:

            vram_used = df[gpu_mem_dedicated]
            spill_mem = df[gpu_mem_dynamic]

            vram_saturated = vram_used > vram_used.quantile(0.98)
            spill_growth = spill_mem.diff().rolling(3, min_periods=1).mean()

            spill_threshold = spill_mem.std() * 0.6
            is_spilling = vram_saturated & (spill_growth > spill_threshold)

            persistence = is_spilling.rolling(window=5, min_periods=1).sum() >= 3
            confirmed_spill = is_spilling & persistence

            avg_bus_load = 0

            if gpu_bus_col and confirmed_spill.any():
                bus_series = df.loc[confirmed_spill, gpu_bus_col].dropna()

                if not bus_series.empty:
                    avg_bus_load = bus_series.median()

            if confirmed_spill.any():
                severity = "CRITICAL" if spill_mem.max() > spill_mem.quantile(0.99) else "WARNING"

                add(
                    name="VRAM Swapping / System Memory Spillover",
                    severity=severity,
                    description=(
                        "The GPU has exceeded effective VRAM capacity and is now spilling into "
                        "system memory (D3D dynamic allocation). This causes PCIe transfers, "
                        "high latency, and severe frame-time instability."
                    ),
                    evidence=[
                        f"VRAM Usage Peak: {vram_used.max():.0f}",
                        f"System Spill Memory Peak: {spill_mem.max():.0f} MB",
                        f"PCIe Bus Load (median during event): {avg_bus_load:.1f}%" if gpu_bus_col else "PCIe Bus Load: N/A"
                    ]
                )
        if gpu_12v_input_v and gpu_12v_input_w:

            high_load_mask = df[gpu_12v_input_w] > 300

            if high_load_mask.any():
                min_v = df.loc[high_load_mask, gpu_12v_input_v].min()
                max_w = df[gpu_12v_input_w].max()

                if min_v < 11.7:
                    add(
                        name="GPU Power Connector Safety Risk (Melting/Fire)",
                        severity="CRITICAL" if min_v < 11.5 else "WARNING",
                        description=(
                            f"The GPU power connector voltage dropped to {min_v:.2f}V while "
                            f"drawing {max_w:.1f}W. This indicates high resistance at the plug. "
                            "Poor contact at these power levels generates extreme heat that can "
                            "melt the connector or cause a fire."
                        ),
                        evidence=[
                            f"Critical Voltage Drop: {min_v:.2f}V",
                            f"Current Load: {max_w:.1f} Watts",
                            "ADVICE: IMMEDIATELY shut down and reseat the 12VHPWR/12-pin cable. "
                            "Ensure there is a 'click' and no gap between the plug and the GPU."
                        ]
                    )
        if vram_junction_temp:
            max_vram_temp = df[vram_junction_temp].max()
            if max_vram_temp > 102:
                add(
                    name="VRAM Thermal Throttling",
                    severity="CRITICAL" if max_vram_temp > 106 else "WARNING",
                    description=(
                        f"The GPU Memory (VRAM) hit {max_vram_temp:.1f}°C. GDDR6X memory throttles "
                        "at 105°C, which will cause massive FPS drops even if the GPU core is cool."
                    ),
                    evidence=[f"Max VRAM Temp: {max_vram_temp:.1f}°C", "Check: GPU Backplate airflow."]
                )

        if pcie_errors:
            pcie_series = pd.to_numeric(df[pcie_errors], errors='coerce').dropna()
            is_live_gauge = '(AVG' in pcie_errors.upper()
            if is_live_gauge:
                total_pcie_errors = pcie_series.max() if not pcie_series.empty else 0
                pcie_label = "Peak PCIe Errors (per-sample gauge)"
            else:
                total_pcie_errors = pcie_series.sum() if not pcie_series.empty else 0
                pcie_label = "Total PCIe Errors (lifetime counter)"
            if total_pcie_errors > 0:
                add(
                    name="PCIe Bus Signal Instability",
                    severity="CRITICAL",
                    description=(
                        "Detected hardware-level PCIe errors. This is usually caused by a "
                        "faulty PCIe Riser cable, a loose GPU seating, or an unstable PCIe Gen 4/5 link."
                    ),
                    evidence=[f"{pcie_label}: {total_pcie_errors:g}", "ADVICE: Reseat GPU or replace Riser."]
                )

        if gpu_wait_ms and ft_col:
            df = df.assign(wait_ratio = df[gpu_wait_ms] / df[ft_col])

            is_waiting = df['wait_ratio'] > 0.25

            if is_waiting.any():
                max_wait = df[gpu_wait_ms].max()
                avg_ratio = df.loc[is_waiting, 'wait_ratio'].mean() * 100

                add(
                    name="GPU Engine Wait Bottleneck",
                    severity="WARNING" if avg_ratio < 40 else "CRITICAL",
                    description=(
                        f"The GPU is idle for {avg_ratio:.1f}% of the frame duration. "
                        "Even if wait times are low (e.g., 1-2ms), this ratio indicates the "
                        "GPU is being 'starved' by the CPU or background app priority."
                    ),
                    evidence=[
                        f"Max Wait: {max_wait:.2f} ms",
                        f"Idle Ratio: {avg_ratio:.1f}% of frame",
                        "ADVICE: Disable Discord/Browser Hardware Acceleration."
                    ]
                )

        if fclk_col and uclk_col and mclk_col:

            f_med = df[fclk_col].median()
            u_med = df[uclk_col].median()
            m_med = df[mclk_col].median()

            is_ddr5 = m_med > 2400

            if is_ddr5:

                delta = (df[uclk_col] - df[mclk_col]).abs()

                desync_mask = delta > 10

                if desync_mask.mean() > 0.05:

                    u_val = df.loc[desync_mask, uclk_col].median()
                    m_val = df.loc[desync_mask, mclk_col].median()
                    mismatch = abs(u_val - m_val)

                    add(
                        name="Memory Controller Desync",
                        severity="WARNING" if mismatch > 50 else "INFO",
                        description=(
                            f"UCLK ({u_val:.0f}) is not synchronized with MCLK ({m_val:.0f}). "
                            "This increases memory latency."
                        ),
                        evidence=[
                            f"UCLK/MCLK Mismatch: {mismatch:.0f} MHz",
                            f"Desync Duration: {desync_mask.mean()*100:.1f}%",
                            "Expected: UCLK = MCLK (1:1)",
                            "ADVICE: Set UCLK=MCLK in BIOS."
                        ]
                    )

            else:

                delta = (df[fclk_col] - df[uclk_col]).abs()

                desync_mask = delta > 5

                if desync_mask.mean() > 0.05:

                    f_val = df.loc[desync_mask, fclk_col].median()
                    u_val = df.loc[desync_mask, uclk_col].median()
                    mismatch = abs(f_val - u_val)

                    ratio = u_val / f_val if f_val else 0

                    if 0.95 <= ratio <= 1.05:
                        state = "1:1 (Optimal)"
                        severity = "INFO"
                    elif 1.9 <= ratio <= 2.1:
                        state = "1:2 (High Latency Mode)"
                        severity = "WARNING"
                    else:
                        state = "Invalid / Misreported"
                        severity = "CRITICAL"

                    add(
                        name="Ryzen Fabric Desync",
                        severity=severity,
                        description=(
                            f"FCLK ({f_val:.0f}) and UCLK ({u_val:.0f}) are not synchronized."
                        ),
                        evidence=[
                            f"Ratio: {ratio:.2f} → {state}",
                            f"Mismatch: {mismatch:.0f} MHz",
                            f"Desync Duration: {desync_mask.mean()*100:.1f}%",
                            "Expected: FCLK = UCLK (1:1)",
                            "ADVICE: Set Infinity Fabric to match memory clock."
                        ]
                    )

        if mclk_col:
            m_med = df[mclk_col].median()

            is_ddr5_mem = m_med > 2400

            xmp_threshold = 3000 if is_ddr5_mem else 1600
            stock_ceiling = 2400 if is_ddr5_mem else 1333
            if m_med <= stock_ceiling:
                effective = int(m_med * 2)
                rated_guess = 6000 if is_ddr5_mem else 3200
                add(
                    name="Memory XMP/EXPO Profile Disabled",
                    severity="WARNING",
                    description=(
                        f"RAM is running at its stock JEDEC speed ({effective} MT/s effective), "
                        f"which is well below its likely rated XMP/EXPO profile (typically "
                        f"{rated_guess}+ MT/s for modern kits). "
                        "Running at stock speed increases memory latency and reduces bandwidth, "
                        "directly impacting CPU-bound and latency-sensitive workloads. "
                        "ADVICE: Enter BIOS and enable the XMP (Intel) or EXPO (AMD) profile."
                    ),
                    evidence=[
                        f"Detected MCLK: {m_med:.0f} MHz ({effective} MT/s effective)",
                        f"Stock JEDEC ceiling: {int(stock_ceiling * 2)} MT/s",
                        "Action: Enable XMP/EXPO in BIOS → Save & Exit"
                    ],
                    cols=[mclk_col]
                )

        if gpu_pwr_limit and gpu_clk_col:
            limit_active = df[gpu_pwr_limit].apply(lambda x: 1 if x == 'Yes' else 0)

            toggles = limit_active.diff().abs().sum()

            if toggles > 5:
                clk_variance = df[gpu_clk_col].std()
                add(
                    name="GPU Power Limit Oscillation",
                    severity="WARNING",
                    description=(
                        "The GPU is rapidly 'ping-ponging' against its power limit. "
                        "This causes clock speed fluctuations and uneven frame delivery."
                    ),
                    evidence=[
                        f"Power Limit Toggles: {toggles:.0f} times",
                        f"Clock Std Dev: {clk_variance:.1f} MHz",
                        "ADVICE: Increase Power Limit in Afterburner or undervolt the GPU."
                    ]
                )
        if cpu_utility:

            usage_std = df[cpu_utility].std()

            if usage_std > 15:
                add(
                    name="Kernel Driver Latency (DPC/ISR)",
                    severity="INFO",
                    description=(
                        "Detected high volatility in system utility. This usually indicates "
                        "a background driver (Wi-Fi, Audio, or USB) is causing micro-stutters."
                    ),
                    evidence=[
                        f"System Load Variance: {usage_std:.2f}%",
                        "ADVICE: Update network/audio drivers or disable unused USB controllers."
                    ]
                )

        drive_activity   = self._col('Total Activity [%]') or self._col('Read Activity [%]')
        drive_warn_cols  = self._col_candidates(('DRIVE', 'WARNING'))
        drive_fail_cols  = self._col_candidates(('DRIVE', 'FAILURE'))

        def _any_drive_flag(flag_cols):
            for c in flag_cols:
                if (df[c].astype(str).str.strip().str.upper() == 'YES').any():
                    return c
            return None

        warned_drive_col = _any_drive_flag(drive_warn_cols)
        failed_drive_col = _any_drive_flag(drive_fail_cols)
        drive_warning     = warned_drive_col or (drive_warn_cols[0] if drive_warn_cols else None)

        if drive_activity:
            is_pinned = (df[drive_activity] > 98).sum() > 3

            if is_pinned or warned_drive_col or failed_drive_col:
                flagged_col = failed_drive_col or warned_drive_col
                add(
                    name="Storage I/O Bottleneck / Hitching",
                    severity="CRITICAL" if (warned_drive_col or failed_drive_col) else "WARNING",
                    description="The system drive is maxed out or reporting hardware warnings, causing asset-loading hitches.",
                    evidence=["Drive at 100% activity" if is_pinned else f"Hardware Warning Flag Detected ({flagged_col})",
                              "ADVICE: Check SSD health or move game to a faster drive."],
                )

        if usb_v_col or chipset_t:
            if chipset_t and (df[chipset_t] > 80).any():
                add(
                    name="Chipset Thermal Throttling",
                    severity="WARNING",
                    description="Motherboard chipset is overheating. This often causes USB and NVMe dropouts.",
                    evidence=[f"Max Chipset Temp: {df[chipset_t].max():.1f}°C"],
                    advice="Ensure GPU isn't blocking chipset airflow."
                )

            if usb_v_col:
                min_usb_v = df[usb_v_col].min()
                if min_usb_v < 4.75:
                    add(
                        name="USB Rail Voltage Sag",
                        severity="WARNING",
                        description="USB 5V rail dropped below safety limits. This causes peripheral disconnects.",
                        evidence=[f"Min USB Voltage: {min_usb_v:.2f}V"],
                        advice="Unplug non-essential USB devices or use a powered USB hub."
                    )

        return hits

    def _build_narrative(self, results: list) -> str:
        """Build a hedged plain-English summary paragraph from signature results."""
        if not results:
            return (
                "No issues were detected in this session. All signatures passed based on "
                "the available telemetry data."
            )

        SEV_WEIGHT = {'CRITICAL': 3, 'WARNING': 2, 'INFO': 1}

        total_samples = max(len(self.df), 1)

        def _span_frac(hit):
            spans = hit.get('spans') or []
            if not spans:
                return 0.0
            xv = getattr(self, '_sig_timeline_x_vals', None)
            if xv is None or len(xv) == 0:
                return 0.0
            total_x = xv[-1] - xv[0]
            if total_x <= 0:
                return 0.0
            max_idx = len(xv) - 1
            covered = sum(
                max(0, xv[min(e, max_idx)] - xv[min(s, max_idx)])
                for s, e in spans
            )
            return min(covered / total_x, 1.0)

        scored = []
        for r in results:
            w   = SEV_WEIGHT.get(r.get('severity', 'INFO'), 1)
            frac = _span_frac(r)
            score = w * (1 + frac)
            scored.append((score, r))
        scored.sort(key=lambda x: -x[0])

        sevs = {r.get('severity') for r in results}
        if 'CRITICAL' in sevs:
            health = 'issues requiring attention'
            health_opener = 'Several potential concerns were identified in this session'
        elif 'WARNING' in sevs:
            health = 'potential concerns'
            health_opener = 'Some areas of potential concern were identified in this session'
        else:
            health = 'minor observations'
            health_opener = 'Only minor observations were noted in this session'

        CAUSAL_PAIRS = [
            ('VRM Overheating',           'CPU Thermal Throttling',
             'VRM overheating was also detected, which may have contributed to thermal throttling'),
            ('CPU Thermal Throttling',    'CPU Power Limit Reached',
             'CPU power limits and thermal throttling were both present, suggesting the CPU may have been operating near its sustained limits'),
            ('GPU Overheating (Hotspot)', 'Micro-Stuttering Detected',
             'GPU overheating coincided with stuttering events, which may be related'),
            ('VRAM Swapping / System Memory Spillover', 'Micro-Stuttering Detected',
             'VRAM spillover into system memory coincided with stuttering, which is a common relationship'),
            ('PSU Hardware Failure Indicators', 'GPU Driver TDR (Timeout)',
             'PSU stress indicators and GPU timeouts were both present in this session - these can sometimes be related'),
            ('System RAM Exhaustion',     'Virtual Memory Limit',
             'Both physical RAM exhaustion and virtual memory pressure were detected, suggesting the system may have been significantly memory-constrained'),
            ('Fan Stall Detected',        'CPU Thermal Throttling',
             'A fan stall was detected alongside thermal throttling, which may be a contributing factor'),
            ('Fan Stall Detected',        'GPU Overheating (Hotspot)',
             'A fan stall was detected alongside GPU overheating, which may be a contributing factor'),
            ('Memory XMP/EXPO Profile Disabled', 'CPU Bottleneck',
             'Running RAM at stock speed alongside a CPU bottleneck may suggest the system is more latency-sensitive than typical'),
        ]

        hit_names = {r['name'] for r in results}
        causal_notes = []
        seen_pairs = set()
        for a, b, note in CAUSAL_PAIRS:
            if a in hit_names and b in hit_names:
                key = tuple(sorted([a, b]))
                if key not in seen_pairs:
                    causal_notes.append(note)
                    seen_pairs.add(key)

        sentences = []
        for score, r in scored[:3]:
            name = r['name']
            sev  = r.get('severity', 'INFO')
            frac = _span_frac(r)

            ev_vals = []
            for ev in r.get('evidence', []):
                import re as _re
                nums = _re.findall(r'[\d]+\.?\d*', str(ev))
                if nums:
                    ev_vals.append((str(ev), nums[0]))

            frac_str = f', active for approximately {frac*100:.0f}% of the session,' if frac > 0.05 else ''

            if sev == 'CRITICAL':
                opener = f'{name} was detected{frac_str} and may warrant investigation'
            elif sev == 'WARNING':
                opener = f'{name} was detected{frac_str}'
            else:
                opener = f'{name} was noted{frac_str}'

            if ev_vals:
                label, val = ev_vals[0]
                opener += f' (logged value: {label.strip()})'

            sentences.append(opener + '.')

        parts = [health_opener + '.']
        parts += sentences
        if causal_notes:
            parts.append('Additionally, ' + '; and '.join(causal_notes) + '.')
        parts.append(
            'This summary is based on logged telemetry and should be treated as a '
            'starting point for investigation, not a definitive diagnosis.'
        )
        return ' '.join(parts)

    def _open_theme_editor(self):
        """Colour theme editor - named themes, user themes, import/export/delete."""
        import tkinter.colorchooser as cc

        def _lum(h):
            try: r,g,b_=int(h[1:3],16),int(h[3:5],16),int(h[5:7],16); return 0.2126*r+0.7152*g+0.0722*b_
            except: return 128

        t        = self._get_theme()
        bg       = t["bg"]
        bg3      = t["bg3"]
        fg       = t["fg"]
        accent   = t["accent"]
        muted_fg  = "#666666" if _lum(bg) > 128 else "#aaaaaa"
        accent_fg = "#000000" if _lum(accent) > 140 else "#ffffff"

        user_themes = dict(self.custom_theme.get("user_themes", {}))
        active_name  = self.custom_theme.get("active", "Dark (Default)")
        overrides    = dict(t)

        FIELDS = [
            ("bg",      "Background"),
            ("bg2",     "Surface (cards / inputs)"),
            ("bg3",     "Hover / border"),
            ("fg",      "Text"),
            ("accent",  "Accent (buttons / headers)"),
            ("accent2", "Accent secondary"),
        ]
        PLOT_FIELDS = [("plot_c0","Line 1"),("plot_c1","Line 2"),("plot_c2","Line 3"),
                       ("plot_c3","Line 4"),("plot_c4","Line 5"),("plot_c5","Line 6")]
        HM_FIELDS   = [("hm_safe","Safe"),("hm_ok","Normal"),("hm_warn","Warning"),
                       ("hm_hot","At Limit"),("hm_crit","Critical"),("hm_max","Max")]

        swatches = {}

        dialog = tk.Toplevel(self.root)
        dialog.title("Theme Editor")
        dialog.geometry("560x820")
        dialog.minsize(460, 640)
        dialog.grab_set()
        dialog.configure(bg=bg)
        x = self.root.winfo_x() + (self.root.winfo_width()  // 2) - 280
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 410
        dialog.geometry(f"560x820+{x}+{y}")

        def _refresh_swatches():
            for key, (sf, hv) in swatches.items():
                col = overrides.get(key, "#888")
                hv.set(col)
                sf.configure(bg=col)

        def _pick(key):
            current = overrides.get(key, "#ffffff")
            result = cc.askcolor(color=current, parent=dialog, title=f"Pick colour - {key}")
            if result and result[1]:
                overrides[key] = result[1]
                _refresh_swatches()

        selected_name = [active_name]

        def _load_preset(name):
            nonlocal overrides
            src = BUILTIN_PRESETS.get(name) or user_themes.get(name, {})
            overrides = {k: v for k, v in src.items() if not k.startswith("_")}
            selected_name[0] = name
            _refresh_swatches()

            for bname, (btn, _) in all_theme_btns.items():
                is_sel = (bname == name)
                btn.configure(text=("✓ " if is_sel else "") + bname,
                              font=('Segoe UI', 8, 'bold' if is_sel else 'normal'))

        def _delete_theme(name):
            if name in BUILTIN_PRESETS:
                messagebox.showwarning("Cannot Delete", f"\"{name}\" is a built-in theme and cannot be deleted.", parent=dialog)
                return
            if not messagebox.askyesno("Delete Theme", f"Delete \"{name}\"?", parent=dialog):
                return
            user_themes.pop(name, None)
            new_active = active_name if active_name != name else "Dark (Default)"
            _commit(new_active, rebuild=True)

        def _commit(new_active, rebuild=False):
            full = dict(self.custom_theme)
            full["user_themes"] = dict(user_themes)
            full["active"]      = new_active
            self.custom_theme   = full
            save_theme(full)
            self._save_config()

            src = BUILTIN_PRESETS.get(new_active) or user_themes.get(new_active, {})
            self.is_dark = src.get("_dark", True)
            self._apply_theme_colors()
            self.update_plot()
            if rebuild:
                dialog.destroy()
                self._open_theme_editor()

        def _name_dialog(title, initial, on_confirm):
            win = tk.Toplevel(dialog)
            win.title(title)
            win.geometry("340x130")
            win.grab_set()
            win.configure(bg=bg)
            win.resizable(False, False)
            win.geometry(f"340x130+{dialog.winfo_x()+110}+{dialog.winfo_y()+180}")
            tk.Label(win, text="Theme name:", bg=bg, fg=fg,
                     font=('Segoe UI', 9)).pack(anchor='w', padx=16, pady=(14, 4))
            name_var = tk.StringVar(value=initial)
            entry = tk.Entry(win, textvariable=name_var, font=('Segoe UI', 10),
                             bg=bg3, fg=fg, insertbackground=fg, relief='flat')
            entry.pack(fill=tk.X, padx=16)
            entry.select_range(0, tk.END)
            entry.focus_set()
            def _ok():
                name = name_var.get().strip()
                if not name: return
                if name in BUILTIN_PRESETS:
                    messagebox.showwarning("Reserved Name",
                        f'"{name}" is a built-in theme. Choose a different name.',
                        parent=win)
                    return
                win.destroy()
                on_confirm(name)
            btn_r = tk.Frame(win, bg=bg)
            btn_r.pack(fill=tk.X, padx=16, pady=10)
            tk.Button(btn_r, text="Cancel", bg=bg3, fg=fg, relief='flat',
                      padx=8, command=win.destroy).pack(side=tk.RIGHT, padx=(6, 0))
            tk.Button(btn_r, text="OK", bg=accent, fg=accent_fg, relief='flat',
                      font=('Segoe UI', 9, 'bold'), padx=12, command=_ok).pack(side=tk.RIGHT)
            win.bind("<Return>", lambda e: _ok())

        def _do_save(name):
            user_themes[name] = dict(overrides)
            try:
                r,g,b_ = int(overrides["bg"][1:3],16),int(overrides["bg"][3:5],16),int(overrides["bg"][5:7],16)
                user_themes[name]["_dark"] = (0.2126*r+0.7152*g+0.0722*b_) < 128
            except Exception:
                user_themes[name]["_dark"] = True
            _commit(name, rebuild=True)
            self.show_toast(f'Theme "{name}" saved')

        def _save():
            initial = active_name if active_name not in BUILTIN_PRESETS else "My Theme"
            _name_dialog("Save Theme As", initial, _do_save)

        def _apply():
            name = selected_name[0]
            src = BUILTIN_PRESETS.get(name) or user_themes.get(name, {})
            full = dict(self.custom_theme)
            full["active"] = name

            self.custom_theme = full
            save_theme(full)
            self.is_dark = src.get("_dark", True)
            self._apply_theme_colors()
            self.update_plot()
            self.show_toast(f'Theme "{name}" applied')

        def _rename_theme(old_name):
            if old_name in BUILTIN_PRESETS:
                messagebox.showwarning("Cannot Rename",
                    f'"{old_name}" is a built-in theme.', parent=dialog)
                return
            def _do_rename(new_name):
                if new_name == old_name: return
                if new_name in user_themes:
                    messagebox.showwarning("Name Taken", f'"{new_name}" already exists.', parent=dialog)
                    return
                user_themes[new_name] = user_themes.pop(old_name)
                new_active = new_name if active_name == old_name else active_name
                _commit(new_active, rebuild=True)
                self.show_toast(f'Renamed to "{new_name}"')
            _name_dialog("Rename Theme", old_name, _do_rename)

        def _export_theme():
            path = filedialog.asksaveasfilename(
                parent=dialog, title="Export Theme",
                defaultextension=".json",
                filetypes=[("Theme JSON", "*.json"), ("All files", "*.*")],
                initialfile=f"{active_name.replace(' ', '_')}.json"
            )
            if not path:
                return
            try:
                export_data = {"hd2_theme": {"name": active_name, "colors": dict(overrides)}}
                with open(path, 'w') as f:
                    json.dump(export_data, f, indent=4)
                self.show_toast("Theme exported")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e), parent=dialog)

        def _import_theme():
            path = filedialog.askopenfilename(
                parent=dialog, title="Import Theme",
                filetypes=[("Theme JSON", "*.json"), ("All files", "*.*")]
            )
            if not path:
                return
            try:
                with open(path, 'r') as f:
                    data = json.load(f)

                if "hd2_theme" in data:
                    payload = data["hd2_theme"]
                    imp_name   = payload.get("name", Path(path).stem)
                    imp_colors = payload.get("colors", payload)
                else:
                    imp_name   = Path(path).stem
                    imp_colors = data
                if not isinstance(imp_colors, dict):
                    raise ValueError("Invalid theme file")
                overrides.clear()
                overrides.update(imp_colors)
                _refresh_swatches()

                if imp_name in BUILTIN_PRESETS or imp_name in user_themes:
                    self.show_toast(f'Name "{imp_name}" taken - enter a new name')
                    def _do_import(name):
                        user_themes[name] = dict(imp_colors)
                        _commit(name, rebuild=True)
                        self.show_toast(f'Imported as "{name}"')
                    _name_dialog("Import - Name Clash", imp_name + " (imported)", _do_import)
                else:
                    user_themes[imp_name] = dict(imp_colors)
                    self.show_toast(f'Imported "{imp_name}" - click Apply to use it')
            except Exception as e:
                messagebox.showerror("Import Failed", str(e), parent=dialog)

        def _reset():
            nonlocal overrides
            overrides = dict(self._get_theme())
            _refresh_swatches()

        header = tk.Frame(dialog, bg=accent, height=4)
        header.pack(fill=tk.X)

        body = tk.Frame(dialog, bg=bg, padx=18, pady=14)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="Theme Editor", font=('Segoe UI', 12, 'bold'),
                 bg=bg, fg=fg).pack(anchor='w', pady=(0, 10))

        tk.Label(body, text="Built-in Themes", font=('Segoe UI', 9, 'bold'),
                 bg=bg, fg=accent).pack(anchor='w', pady=(0, 4))
        preset_frame = tk.Frame(body, bg=bg)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        all_theme_btns = {}

        for col_i, (pname, pdata) in enumerate(BUILTIN_PRESETS.items()):
            btn_accent = pdata.get("accent", accent)
            try:
                r,g,b_=int(btn_accent[1:3],16),int(btn_accent[3:5],16),int(btn_accent[5:7],16)
                btn_fg = "#000000" if (0.2126*r+0.7152*g+0.0722*b_) > 140 else "#ffffff"
            except: btn_fg = "#ffffff"
            is_active = (pname == active_name)
            btn = tk.Button(preset_frame, text=("✓ " if is_active else "") + pname,
                            font=('Segoe UI', 8, 'bold' if is_active else 'normal'),
                            relief='flat', bg=btn_accent, fg=btn_fg,
                            padx=6, pady=4,
                            command=lambda n=pname: _load_preset(n))
            btn.grid(row=col_i // 5, column=col_i % 5, padx=3, pady=2, sticky='ew')
            all_theme_btns[pname] = (btn, pname)
        for c in range(5):
            preset_frame.columnconfigure(c, weight=1)

        if user_themes:
            tk.Label(body, text="My Themes", font=('Segoe UI', 9, 'bold'),
                     bg=bg, fg=accent).pack(anchor='w', pady=(4, 4))
            user_frame = tk.Frame(body, bg=bg)
            user_frame.pack(fill=tk.X, pady=(0, 10))
            for utheme_name, udata in user_themes.items():
                row = tk.Frame(user_frame, bg=bg)
                row.pack(fill=tk.X, pady=1)
                u_accent = udata.get("accent", accent)
                try:
                    r,g,b_=int(u_accent[1:3],16),int(u_accent[3:5],16),int(u_accent[5:7],16)
                    u_fg = "#000000" if (0.2126*r+0.7152*g+0.0722*b_) > 140 else "#ffffff"
                except: u_fg = "#ffffff"
                is_active = (utheme_name == active_name)
                ubtn = tk.Button(row, text=("✓ " if is_active else "") + utheme_name,
                          font=('Segoe UI', 8, 'bold' if is_active else 'normal'),
                          relief='flat', bg=u_accent, fg=u_fg, padx=8, pady=3,
                          command=lambda n=utheme_name: _load_preset(n))
                ubtn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,4))
                all_theme_btns[utheme_name] = (ubtn, utheme_name)
                tk.Button(row, text="✕", font=('Segoe UI', 8), relief='flat',
                          bg="#c0392b", fg="#fff", padx=6, pady=3,
                          command=lambda n=utheme_name: _delete_theme(n)).pack(side=tk.RIGHT)
                tk.Button(row, text="✎", font=('Segoe UI', 8), relief='flat',
                          bg=bg3, fg=fg, padx=6, pady=3,
                          command=lambda n=utheme_name: _rename_theme(n)).pack(side=tk.RIGHT, padx=(0, 4))

        tk.Label(body, text="Customise", font=('Segoe UI', 9, 'bold'),
                 bg=bg, fg=accent).pack(anchor='w', pady=(6, 4))
        for key, label in FIELDS:
            row_f = tk.Frame(body, bg=bg)
            row_f.pack(fill=tk.X, pady=3)
            current_col = overrides.get(key, "#888888")
            hex_var = tk.StringVar(value=current_col)
            sf = tk.Frame(row_f, bg=current_col, width=28, height=22, relief='flat', bd=1)
            sf.pack(side=tk.LEFT, padx=(0, 8))
            sf.pack_propagate(False)
            tk.Label(row_f, text=label, bg=bg, fg=fg,
                     font=('Segoe UI', 9), width=24, anchor='w').pack(side=tk.LEFT)
            tk.Label(row_f, textvariable=hex_var, bg=bg, fg=muted_fg,
                     font=('Consolas', 8)).pack(side=tk.LEFT, padx=6)
            tk.Button(row_f, text="Pick", font=('Segoe UI', 8), relief='flat',
                      bg=accent, fg=accent_fg, padx=8,
                      command=lambda k=key: _pick(k)).pack(side=tk.RIGHT)
            swatches[key] = (sf, hex_var)

        def _make_color_section(title, fields):
            tk.Label(body, text=title, font=('Segoe UI', 9, 'bold'),
                     bg=bg, fg=accent).pack(anchor='w', pady=(10, 4))
            row_outer = tk.Frame(body, bg=bg)
            row_outer.pack(fill=tk.X)
            for col_i, (key, label) in enumerate(fields):
                cell = tk.Frame(row_outer, bg=bg)
                cell.grid(row=0, column=col_i, padx=4, pady=2, sticky='ew')
                row_outer.columnconfigure(col_i, weight=1)
                current_col = overrides.get(key, "#888888")
                hex_var = tk.StringVar(value=current_col)
                sf = tk.Frame(cell, bg=current_col, width=28, height=20, relief='flat', bd=1)
                sf.pack()
                sf.pack_propagate(False)
                tk.Label(cell, text=label, bg=bg, fg=fg,
                         font=('Segoe UI', 7), anchor='center').pack()
                tk.Button(cell, text="Pick", font=('Segoe UI', 7), relief='flat',
                          bg=accent, fg=accent_fg,
                          command=lambda k=key: _pick(k)).pack(fill=tk.X)
                swatches[key] = (sf, hex_var)

        _make_color_section("Plot Line Colors", PLOT_FIELDS)
        _make_color_section("Heatmap Band Colors", HM_FIELDS)

        btn_row = tk.Frame(dialog, bg=bg, padx=18, pady=10)
        btn_row.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(btn_row, text="Reset",   font=('Segoe UI', 9), relief='flat',
                  bg=bg3, fg=fg, padx=10, command=_reset).pack(side=tk.LEFT, padx=(0,4))
        tk.Button(btn_row, text="Export",  font=('Segoe UI', 9), relief='flat',
                  bg=bg3, fg=fg, padx=10, command=_export_theme).pack(side=tk.LEFT, padx=(0,4))
        tk.Button(btn_row, text="Import",  font=('Segoe UI', 9), relief='flat',
                  bg=bg3, fg=fg, padx=10, command=_import_theme).pack(side=tk.LEFT)
        tk.Button(btn_row, text="Cancel", font=('Segoe UI', 9), relief='flat',
                  bg=bg3, fg=fg, padx=10,
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(btn_row, text="Save As...", font=('Segoe UI', 9, 'bold'), relief='flat',
                  bg=accent, fg=accent_fg, padx=12,
                  command=_save).pack(side=tk.RIGHT, padx=(4, 0))
        tk.Button(btn_row, text="Apply", font=('Segoe UI', 9), relief='flat',
                  bg=bg3, fg=fg, padx=10,
                  command=_apply).pack(side=tk.RIGHT, padx=(4, 0))
    def _open_alias_manager(self):
        """Open the sensor alias manager - view, delete individual aliases, or clear all."""
        is_dark = self.is_dark
        _t = self._get_theme(); bg = _t["bg"]; bg2 = _t["bg2"]; fg = _t["fg"]; accent = _t["accent"]
        bg3  = "#2a2a2a" if is_dark else "#e9ecef"
        acc  = "#1f6aa5"
        muted = "#666" if is_dark else "#999"

        _KEY_LABELS = {
            "cpu_temp":    "CPU Temperature",
            "gpu_temp":    "GPU Temperature / Hotspot",
            "cpu_power":   "CPU Package Power",
            "gpu_power":   "GPU Total Power",
            "gpu_usage":   "GPU Core Usage / Load",
            "gpu_clock":   "GPU Core Clock",
            "cpu_usage":   "Total CPU Usage",
            "frame_time":  "Frame Time (PresentMon)",
            "rail_33v":    "+3.3V Rail Voltage",
            "fclk":        "Fabric Clock (FCLK) - AMD Ryzen",
            "uclk":        "Unified Memory Clock (UCLK) - AMD Ryzen",
            "mclk":        "Memory Clock (MCLK)",
            "gpu_busy":    "GPU Busy Time (PresentMon)",
            "gpu_wait":    "GPU Wait Time (PresentMon)",
            "chipset_temp":"Chipset Temperature",
            "pcie_errors": "PCIe Error Counters",
            "sys_interrupts": "System Interrupts / DPC Latency",
        }

        aliases = dict(self.analyzer.aliases)

        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Sensor Aliases")
        dialog.geometry("620x500")
        dialog.minsize(500, 350)
        dialog.grab_set()
        dialog.configure(bg=bg)
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  // 2) - 310
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 250
        dialog.geometry(f"620x500+{x}+{y}")

        outer = tk.Frame(dialog, bg=accent, padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg=bg, padx=14, pady=12)
        inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(inner, text="⚙  Sensor Alias Manager",
                 font=('Segoe UI', 12, 'bold'), bg=bg, fg=accent).pack(anchor='w')
        tk.Label(inner,
                 text="Click ✕ next to any alias to remove it. Changes apply immediately.",
                 font=('Segoe UI', 9), bg=bg, fg=muted).pack(anchor='w', pady=(2, 10))

        list_outer = tk.Frame(inner, bg=bg2, bd=1, relief='flat')
        list_outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(list_outer, bg=bg2, highlightthickness=0)
        sb = tk.Scrollbar(list_outer, orient='vertical', command=canvas.yview,
                       bg=bg3, troughcolor=bg, activebackground=accent)
        body = tk.Frame(canvas, bg=bg2)
        win_id = canvas.create_window((0, 0), window=body, anchor='nw')
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units")))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        row_widgets = {}

        def _rebuild():
            """Redraw the alias list from current `aliases` dict."""
            for w in body.winfo_children():
                w.destroy()
            row_widgets.clear()

            has_any = False
            for key, label in _KEY_LABELS.items():
                entry = aliases.get(key)
                if not entry:
                    continue
                entries = entry if isinstance(entry, list) else [entry]
                real = [e for e in entries]
                if not real:
                    continue
                has_any = True

                hdr = tk.Frame(body, bg=bg3)
                hdr.pack(fill=tk.X, pady=(8, 0), padx=6)
                tk.Label(hdr, text=label, font=('Segoe UI', 9, 'bold'),
                         bg=bg3, fg=acc, padx=8, pady=4).pack(side=tk.LEFT)

                for alias_val in real:
                    in_csv = alias_val in self.df.columns
                    row = tk.Frame(body, bg=bg2)
                    row.pack(fill=tk.X, padx=6, pady=1)

                    status_col = "#4ec94e" if in_csv else muted
                    status_sym = "✓" if in_csv else "○"
                    tk.Label(row, text=status_sym, fg=status_col, bg=bg2,
                             font=('Segoe UI', 9), width=2).pack(side=tk.LEFT, padx=(8, 4))
                    tk.Label(row, text=alias_val, fg=fg, bg=bg2,
                             font=('Segoe UI', 9), anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True)

                    def _make_delete(k, v):
                        def _delete():
                            entry2 = aliases.get(k, [])
                            lst = entry2 if isinstance(entry2, list) else [entry2]
                            lst = [x for x in lst if x != v]
                            if lst:
                                aliases[k] = lst
                            else:
                                del aliases[k]
                            _rebuild()
                        return _delete

                    tk.Button(row, text="✕", fg="#ff5555", bg=bg2,
                              activebackground=bg2, activeforeground="#ff3333",
                              relief='flat', cursor='hand2', font=('Segoe UI', 9, 'bold'),
                              command=_make_delete(key, alias_val),
                              padx=6).pack(side=tk.RIGHT, padx=4)

            if not has_any:
                tk.Label(body, text="No aliases saved yet.",
                         font=('Segoe UI', 10), bg=bg2, fg=muted,
                         pady=20).pack()

        _rebuild()

        btn_f = tk.Frame(inner, bg=bg)
        btn_f.pack(fill=tk.X, pady=(10, 0))

        def _save_and_close():
            self.analyzer.save_aliases(aliases)
            self.analyzer.aliases = aliases
            self.show_toast("Aliases saved")
            dialog.destroy()

        def _clear_all():
            if messagebox.askyesno("Clear All Aliases",
                                   "Remove all saved sensor aliases?\n"
                                   "You will be prompted again on next CSV load.",
                                   parent=dialog):
                aliases.clear()
                _rebuild()

        ttk.Button(btn_f, text="💾 Save & Close", command=_save_and_close,
                   style="Action.TButton").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(btn_f, text="🗑 Clear All",
                   command=_clear_all).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(btn_f, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, expand=True, fill=tk.X)

    def _prompt_sensor_aliases(self):
        """For each critical sensor that couldn't be auto-resolved, ask the user
        once to pick the right column. Saves the answer to disk permanently."""

        _CRITICAL = [
            ("cpu_temp",      "CPU Temperature",
             "Used for thermal throttling, clock stretching, and VRM overheating detection.\n"
             "Look for a column showing °C values in the 30–105°C range at idle/load.\n"
             "Common names: Tdie, Tctl, CPU Package, Core Temperatures (avg)",
             self._col('TCTL') or self._col('TDIE') or self._col('CPU'),
             lambda c: any(k in c.upper() for k in
                           ['TEMP','°C','TDIE','TCTL','TJMAX','PACKAGE','CORE','THERMAL'])
             and '[W]' not in c and '[%]' not in c and '[MHZ]' not in c.upper()),
            ("gpu_temp",      "GPU Temperature / Hotspot",
             "Used for GPU overheating and hotspot detection.\n"
             "Look for a column showing °C values, ideally the hotspot/junction reading.\n"
             "Common names: GPU Temperature, GPU Hot Spot, GPU Memory Junction Temperature",
             self._col_excl(('GPU','HOT'), excl=('CPU','LIMIT')) or
             self._col_excl(('GPU','TEMP'), excl=('CPU',)),
             lambda c: any(k in c.upper() for k in
                           ['GPU','TEMP','HOT','°C','JUNCTION','EDGE','HOTSPOT'])
             and '[W]' not in c and '[%]' not in c and '[MHZ]' not in c.upper()),
            ("cpu_power",     "CPU Package Power",
             "Used for CPU power limit and throttling detection.\n"
             "Look for total CPU power draw in Watts (not per-core).\n"
             "Common names: CPU Package Power, CPU PPT, IA Cores Power",
             self._col('CPU','PACKAGE') or self._col('CPU','PPT') or self._col('CPU','POWER'),
             lambda c: any(k in c.upper() for k in ['CPU','PPT','PACKAGE'])
             and any(k in c.upper() for k in ['[W]','POWER','WATT'])),
            ("gpu_power",     "GPU Total Power",
             "Used for GPU power limit saturation and PSU failure detection.\n"
             "Look for total GPU board power in Watts.\n"
             "Common names: GPU Power, GPU Board Power, TGP",
             self._col('GPU','POWER') or self._col('TGP') or self._col('TBP'),
             lambda c: 'GPU' in c.upper()
             and any(k in c.upper() for k in ['[W]','POWER','WATT','TGP','TBP'])
             and 'LIMIT' not in c.upper() and '[%]' not in c),
            ("gpu_usage",     "GPU Core Usage / Load",
             "Used for GPU bottleneck, TDR, and priority conflict detection.\n"
             "Look for GPU core utilisation as a percentage (not memory or video).\n"
             "Common names: GPU Core Load, GPU Usage, GPU D3D Usage",
             self._col('GPU','USAGE') or self._col('GPU','LOAD'),
             lambda c: any(k in c.upper() for k in ['GPU','AUSLASTUNG'])
             and any(k in c.upper() for k in ['USAGE','LOAD','[%]'])
             and 'MEMORY' not in c.upper()),
            ("gpu_clock",     "GPU Core Clock",
             "Used for TDR detection, clock cap, and power limit oscillation.\n"
             "Look for the GPU core/shader clock speed in MHz.\n"
             "Common names: GPU Clock, GPU Core Clock, GPU Effective Clock",
             self._col('GPU','CLOCK') or self._col('GPU','FREQUENCY'),
             lambda c: any(k in c.upper() for k in ['GPU','GRAFIK'])
             and any(k in c.upper() for k in ['CLOCK','FREQ','[MHZ]','TAKT'])
             and 'MEMORY' not in c.upper() and 'VIDEO' not in c.upper()),
            ("cpu_usage",     "Total CPU Usage",
             "Used for CPU bottleneck and background process interference detection.\n"
             "Look for overall CPU utilisation as a percentage across all cores.\n"
             "Common names: Total CPU Usage, CPU Load, Max CPU/Thread Usage",
             self._col('TOTAL','CPU') or self._col('CPU','USAGE') or self._col('CPU','LOAD'),
             lambda c: any(k in c.upper() for k in ['CPU','PROZESSOR'])
             and any(k in c.upper() for k in ['USAGE','LOAD','TOTAL','[%]','AUSLASTUNG'])
             and '[W]' not in c and '[MHZ]' not in c.upper() and '°C' not in c),
            ("frame_time",    "Frame Time (PresentMon)",
             "Used for stutter, GPU engine wait, and priority conflict detection.\n"
             "Look for per-frame render time in milliseconds from PresentMon.\n"
             "Common names: Frame Time Presented (avg), Frametime [ms]",
             self._col('Frame Time') or self._col('Frametime'),
             lambda c: any(k in c.upper() for k in ['FRAME','FRAMETIME'])
             and any(k in c.upper() for k in ['TIME','[MS]','PRESENTED'])),
            ("rail_33v",      "+3.3V Rail Voltage",
             "Used for PSU rail stability and hardware failure detection.\n"
             "Look for a voltage column reading ~3.3V at idle.\n"
             "Common names: +3.3V, 3.3V, 3V3, VCCIO, VDD (SWA)",
             self._col('+3.3V') or self._col('3V3') or self._col('3.3V'),
             lambda c: any(k in c.upper() for k in
                           ['3.3', '3V3', 'VCC3', 'VCCIO', 'VDDA', 'AVDD',
                            'VSB', 'VDD (SWA)', 'VDDQ', 'VPP'])
             and '[W]' not in c and '[%]' not in c),
            ("fclk",          "Fabric Clock (FCLK) - AMD Ryzen",
             "Used for Ryzen fabric desync detection.\n"
             "Look for the Infinity Fabric clock speed in MHz (AMD systems only).\n"
             "Common names: FCLK [MHz]",
             self._col('FCLK'),
             lambda c: 'FCLK' in c.upper() and '[MHZ]' in c.upper()),
            ("uclk",          "Unified Memory Clock (UCLK) - AMD Ryzen",
             "Used alongside FCLK for Ryzen fabric desync detection.\n"
             "Look for the unified memory controller clock in MHz (AMD systems only).\n"
             "Common names: UCLK [MHz]",
             next((c for c in self.df.columns if 'UCLK' in c), None),
             lambda c: 'UCLK' in c.upper() and '[MHZ]' in c.upper()),
            ("mclk",          "Memory Clock (MCLK)",
             "Used for memory desync detection on AMD Ryzen systems.\n"
             "Look for the DRAM/memory clock speed in MHz.\n"
             "Common names: Memory Clock [MHz], MCLK [MHz], DRAM Clock",
             self._col('MCLK') or self._col('MEMORY CLOCK') or self._col('DRAM CLOCK'),
             lambda c: any(k in c.upper() for k in ['MCLK','MEMORY CLOCK','DRAM CLOCK'])
             and '[MHZ]' in c.upper()),
            ("gpu_busy",      "GPU Busy Time (PresentMon)",
             "Used for GPU engine wait bottleneck detection.\n"
             "Look for time in milliseconds the GPU spent actively rendering.\n"
             "Common names: GPU Busy (avg) [ms]",
             self._col('GPU Busy (avg) [ms]') or self._col('GPU Busy'),
             lambda c: 'GPU' in c.upper() and 'BUSY' in c.upper()),
            ("gpu_wait",      "GPU Wait Time (PresentMon)",
             "Used for GPU engine wait bottleneck detection.\n"
             "Look for time in milliseconds the GPU spent waiting (stalled).\n"
             "Common names: GPU Wait (avg) [ms]",
             self._col('GPU Wait (avg) [ms]') or self._col('GPU Wait'),
             lambda c: 'GPU' in c.upper() and 'WAIT' in c.upper()),
            ("chipset_temp",  "Chipset / PCH Temperature",
             "Used for chipset thermal throttling detection.\n"
             "Look for the motherboard chipset or PCH temperature in °C.\n"
             "Common names: PCH Temperature, Chipset [°C], Motherboard [°C]",
             self._col('Chipset [°C]') or self._col('Motherboard [°C]') or self._col('PCH'),
             lambda c: any(k in c.upper() for k in
                           ['PCH','CHIPSET','MOTHERBOARD','NB TEMP','SMU'])
             and ('°C' in c or 'TEMP' in c.upper())),
            ("pcie_errors",   "PCIe Error Counters",
             "Used for PCIe bus signal instability and WHEA error detection.\n"
             "Look for a column counting PCIe errors (usually 0 on healthy systems).\n"
             "Common names: PCI Express Error Counters (avg), Receiver Errors",
             self._col('PCI Express Error Counters (avg)'),
             lambda c: any(k in c.upper() for k in
                           ['PCIE','PCI EXPRESS','RECEIVER ERROR','REPLAY','BAD TLP'])),
            ("sys_interrupts","System Interrupts / DPC Latency",
             "Used for kernel driver latency detection.\n"
             "Look for system interrupt count or DPC latency in ms.\n"
             "Common names: System Interrupts, DPC Latency",
             self._col('System Interrupts') or self._col('DPC Latency'),
             lambda c: any(k in c.upper() for k in
                           ['SYSTEM INTERRUPT','DPC','ISR','LATENCY'])),
        ]

        aliases = self.analyzer.aliases
        changed = False
        df_cols = list(self.df.columns)

        for key, label, desc, auto_result, filt in _CRITICAL:
            entry = aliases.get(key)
            if entry:
                existing = entry if isinstance(entry, list) else [entry]
                if any(c in self.df.columns for c in existing):
                    continue

            if auto_result:
                continue

            already_known = set(entry if isinstance(entry, list) else ([entry] if entry else []))
            candidates = [c for c in df_cols
                          if filt(c) and c != self.analyzer.time_col
                          and c not in already_known]
            if not candidates:
                continue

            chosen = self._sensor_picker_dialog(label, candidates, desc)
            if chosen:
                existing_list = aliases.get(key, [])\
                    if isinstance(aliases.get(key), list) else\
                    ([aliases[key]] if key in aliases else [])
                if chosen not in existing_list:
                    existing_list.append(chosen)
                aliases[key] = existing_list
                changed = True
        if changed:
            self.analyzer.save_aliases(aliases)
            self.analyzer.aliases = aliases

    def _sensor_picker_dialog(self, sensor_label: str, candidates: list,
                               description: str = "") -> str | None | bool:
        """Show a dialog asking the user to pick the correct column for a sensor.
        Returns the chosen column name, None if dismissed, or False if 'None of these'."""
        is_dark = self.is_dark
        _t = self._get_theme(); bg = _t["bg"]; bg2 = _t["bg2"]; fg = _t["fg"]; accent = _t["accent"]
        bg3  = _t.get("bg3", "#1a2a3a" if is_dark else "#e8f4fd")
        acc  = accent

        result = [None]

        dialog = tk.Toplevel(self.root)
        dialog.title("Sensor Setup")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(bg=bg)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

        self.root.update_idletasks()
        pw, ph = 560, min(160 + len(candidates) * 28 + 80, 560)
        rx = self.root.winfo_x() + (self.root.winfo_width()  // 2) - pw // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() // 2) - ph // 2
        dialog.geometry(f"{pw}x{ph}+{rx}+{ry}")

        outer = tk.Frame(dialog, bg=acc, padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg=bg, padx=20, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(inner,
                 text=f"⚙  Could not auto-detect:  {sensor_label}",
                 font=('Segoe UI', 11, 'bold'), bg=bg, fg=acc).pack(anchor='w')
        tk.Label(inner,
                 text="Which of these columns is it? Your answer is saved permanently.",
                 font=('Segoe UI', 9), bg=bg, fg="#888").pack(anchor='w', pady=(2, 8))

        if description:
            desc_frame = tk.Frame(inner, bg=bg3, padx=10, pady=8,
                                  highlightthickness=1,
                                  highlightbackground=accent)
            desc_frame.pack(fill=tk.X, pady=(0, 10))
            tk.Label(desc_frame, text="ℹ  What to look for:",
                     font=('Segoe UI', 8, 'bold'), bg=bg3,
                     fg=accent, anchor='w').pack(anchor='w')
            tk.Label(desc_frame, text=description,
                     font=('Segoe UI', 8), bg=bg3,
                     fg=fg,
                     justify='left', anchor='w',
                     wraplength=pw - 60).pack(anchor='w', pady=(4, 0))

        list_frame = tk.Frame(inner, bg=bg2, bd=1, relief='flat')
        list_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(list_frame, bg=bg2, highlightthickness=0,
                           height=min(len(candidates) * 28, 320))
        sb = tk.Scrollbar(list_frame, orient='vertical', command=canvas.yview,
                       bg=bg3, troughcolor=bg, activebackground=accent)
        radio_frame = tk.Frame(canvas, bg=bg2)
        canvas.create_window((0, 0), window=radio_frame, anchor='nw')
        radio_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if len(candidates) > 11:
            sb.pack(side=tk.RIGHT, fill=tk.Y)

        var = tk.StringVar(value="")
        for c in candidates:
            tk.Radiobutton(radio_frame, text=c, variable=var, value=c,
                           bg=bg2, fg=fg, activebackground=bg2, activeforeground=fg,
                           selectcolor=acc, font=('Segoe UI', 9),
                           anchor='w').pack(fill=tk.X, padx=8, pady=2)

        btn_f = tk.Frame(inner, bg=bg)
        btn_f.pack(fill=tk.X, pady=(12, 0))

        def _confirm():
            if var.get():
                result[0] = var.get()
                dialog.destroy()

        def _none():
            result[0] = False
            dialog.destroy()

        ttk.Button(btn_f, text="✓ Use Selected", command=_confirm,
                   style="Action.TButton").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(btn_f, text="None of these",
                   command=_none).pack(side=tk.LEFT, expand=True, fill=tk.X)

        dialog.wait_window()
        return result[0]

    def _open_hardware_info(self):
        """Parse and display detected hardware device names from the loaded CSV."""
        import threading

        is_dark = self.is_dark
        _t = self._get_theme(); bg = _t["bg"]; bg2 = _t["bg2"]; fg = _t["fg"]; accent = _t["accent"]; bg3 = _t["bg3"]

        wait_win = tk.Toplevel(self.root)
        wait_win.title("Detecting Hardware")
        wait_win.resizable(False, False)
        wait_win.protocol("WM_DELETE_WINDOW", lambda: None)
        wait_win.configure(bg=bg)
        self.root.update_idletasks()
        pw, ph = 340, 120
        rx = self.root.winfo_x() + (self.root.winfo_width()  // 2) - pw // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() // 2) - ph // 2
        wait_win.geometry(f"{pw}x{ph}+{rx}+{ry}")
        wait_win.transient(self.root)
        wait_win.grab_set()

        outer_w = tk.Frame(wait_win, bg="#1f6aa5", padx=2, pady=2)
        outer_w.pack(fill=tk.BOTH, expand=True)
        inner_w = tk.Frame(outer_w, bg=bg, padx=20, pady=16)
        inner_w.pack(fill=tk.BOTH, expand=True)

        title_row = tk.Frame(inner_w, bg=bg)
        title_row.pack(anchor='w')
        tk.Label(title_row, text="🖥  Scanning Hardware",
                 font=('Segoe UI', 11, 'bold'), bg=bg, fg="#4f8ef7").pack(side=tk.LEFT)
        spin_var = tk.StringVar(value=" ⠋")
        tk.Label(title_row, textvariable=spin_var,
                 font=('Segoe UI', 11), bg=bg, fg="#1f6aa5").pack(side=tk.LEFT, padx=(6, 0))
        tk.Label(inner_w, text="Parsing hardware labels from CSV…",
                 font=('Segoe UI', 9), bg=bg, fg="#888").pack(anchor='w', pady=(6, 0))

        bar_frame = tk.Frame(inner_w, bg=bg)
        bar_frame.pack(fill=tk.X, pady=(8, 0))
        bar_bg = tk.Frame(bar_frame, bg="#2a2a2a" if is_dark else "#dee2e6", height=4, bd=0)
        bar_bg.pack(fill=tk.X)
        bar_fg = tk.Frame(bar_bg, bg="#1f6aa5", height=4, bd=0)
        bar_fg.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        _bar_pos = [0.0]; _bar_dir = [1]
        def _tick_bar():
            if not wait_win.winfo_exists(): return
            _bar_pos[0] += 0.06 * _bar_dir[0]
            if _bar_pos[0] >= 0.85:  _bar_dir[0] = -1
            elif _bar_pos[0] <= 0.0: _bar_dir[0] = 1
            bar_fg.place(relwidth=min(_bar_pos[0], 1.0))
            wait_win.after(40, _tick_bar)
        _tick_bar()

        _SPIN = [" ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏"]
        _si = [0]
        def _tick_spin():
            if not wait_win.winfo_exists(): return
            _si[0] = (_si[0] + 1) % len(_SPIN)
            spin_var.set(_SPIN[_si[0]])
            wait_win.after(80, _tick_spin)
        _tick_spin()

        def _worker():
            _tk_refs = [spin_var, wait_win, bar_fg, bar_bg, bar_frame, inner_w, outer_w]
            hw = self.analyzer.extract_hardware_names()
            def _done():
                _tk_refs.clear()
                _show_results(hw)
            self.root.after(0, _done)

        def _show_results(hw):
            if wait_win.winfo_exists():
                wait_win.grab_release()
                wait_win.destroy()

            dialog = tk.Toplevel(self.root)
            dialog.title("Detected Hardware")
            dialog.geometry("560x520")
            dialog.minsize(440, 380)
            dialog.grab_set()
            dialog.configure(bg=bg)
            self.root.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width()  // 2) - 280
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 260
            dialog.geometry(f"560x520+{x}+{y}")

            tk.Label(dialog, text="Detected Hardware",
                     font=('Segoe UI', 13, 'bold'), bg=bg, fg=accent).pack(pady=(14, 2))
            total = sum(len(v) for v in hw.values())
            tk.Label(dialog,
                     text=f"{total} unique device(s) identified across {len(hw)} category(ies)",
                     font=('Segoe UI', 9), bg=bg, fg="#888").pack(pady=(0, 10))

            outer = tk.Frame(dialog, bg=bg)
            outer.pack(fill=tk.BOTH, expand=True, padx=12)
            canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
            sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview,
                       bg=bg3, troughcolor=bg, activebackground=accent)
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

            _CATEGORY_ICONS = {
                'System / Motherboard': '🔧', 'CPU': '🖥',
                'iGPU (Integrated Graphics)': '💡', 'GPU': '🎮',
                'Memory (RAM)': '💾', 'Memory Timings': '⏱',
                'Storage': '💿', 'Network': '🌐', 'Battery': '🔋',
                'PresentMon (Frame Timing)': '📊', 'Chipset': '⚙', 'Other': '📡',
            }

            if not hw:
                tk.Label(body,
                         text="No hardware names could be extracted.\n"
                              "This CSV may not be in HWiNFO64 format,\n"
                              "or columns use a non-standard naming scheme.",
                         font=('Segoe UI', 10), bg=bg, fg="#888",
                         justify='center', pady=30).pack()
            else:
                for cat, names in hw.items():
                    icon = _CATEGORY_ICONS.get(cat, '📡')
                    hdr_f = tk.Frame(body, bg=bg)
                    hdr_f.pack(fill=tk.X, pady=(12, 2), padx=4)
                    tk.Label(hdr_f, text=f"{icon}  {cat.upper()}",
                             font=('Segoe UI', 9, 'bold'), bg=bg, fg=accent,
                             anchor='w').pack(side=tk.LEFT)
                    tk.Label(hdr_f, text=f"({len(names)})",
                             font=('Segoe UI', 8), bg=bg, fg="#666",
                             anchor='w').pack(side=tk.LEFT, padx=(4, 0))
                    tk.Frame(body, bg=accent, height=1).pack(fill=tk.X, padx=4)
                    for name in names:
                        row_f = tk.Frame(body, bg=bg2, padx=10, pady=6)
                        row_f.pack(fill=tk.X, padx=4, pady=2)
                        tk.Label(row_f, text=name, font=('Segoe UI', 9),
                                 bg=bg2, fg=fg, anchor='w',
                                 wraplength=480, justify='left').pack(anchor='w')

            def _copy_all():
                lines = []
                for cat, names in hw.items():
                    lines.append(f"[{cat}]")
                    for n in names:
                        lines.append(f"  {n}")
                self.root.clipboard_clear()
                self.root.clipboard_append("\n".join(lines))
                self.show_toast("Hardware list copied to clipboard")

            btn_f = tk.Frame(dialog, bg=bg)
            btn_f.pack(fill=tk.X, padx=12, pady=10)
            ttk.Button(btn_f, text="📋 Copy All to Clipboard",
                       command=_copy_all).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
            ttk.Button(btn_f, text="Close",
                       command=dialog.destroy).pack(side=tk.LEFT, expand=True, fill=tk.X)

        threading.Thread(target=_worker, daemon=True).start()

    def _export_html_report(self):
        """Generate a self-contained HTML session report.
        The heavy work runs in a background thread so the UI stays responsive."""
        import io
        import base64
        import datetime
        import html as html_mod
        import traceback
        import threading

        f_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html")],
            initialfile=f"RESYNC_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        if not f_path:
            return

        is_dark  = self.is_dark
        _t = self._get_theme(); bg_dark = _t["bg"]; bg = _t["bg"]; fg = _t["fg"]; accent = _t["accent"]

        wait_win = tk.Toplevel(self.root)
        wait_win.title("Generating Report")
        wait_win.resizable(False, False)
        wait_win.protocol("WM_DELETE_WINDOW", lambda: None)
        wait_win.configure(bg=bg_dark)

        self.root.update_idletasks()
        pw, ph = 340, 120
        rx = self.root.winfo_x() + (self.root.winfo_width()  // 2) - pw // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() // 2) - ph // 2
        wait_win.geometry(f"{pw}x{ph}+{rx}+{ry}")
        wait_win.transient(self.root)
        wait_win.grab_set()

        outer = tk.Frame(wait_win, bg="#1f6aa5", padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg=bg_dark, padx=20, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        title_row = tk.Frame(inner, bg=bg_dark)
        title_row.pack(anchor='w')
        tk.Label(title_row, text="\U0001f4c4  Generating HTML Report",
                 font=('Segoe UI', 11, 'bold'), bg=bg_dark, fg="#4f8ef7").pack(side=tk.LEFT)
        spin_var = tk.StringVar(value=" ⠋")
        tk.Label(title_row, textvariable=spin_var,
                 font=('Segoe UI', 11), bg=bg_dark, fg="#1f6aa5").pack(side=tk.LEFT, padx=(6, 0))

        status_var = tk.StringVar(value="Preparing data\u2026")
        tk.Label(inner, textvariable=status_var,
                 font=('Segoe UI', 9), bg=bg_dark, fg="#888").pack(anchor='w', pady=(6, 0))

        bar_frame = tk.Frame(inner, bg=bg_dark)
        bar_frame.pack(fill=tk.X, pady=(8, 0))
        bar_bg = tk.Frame(bar_frame, bg="#2a2a2a" if is_dark else "#dee2e6", height=4, bd=0)
        bar_bg.pack(fill=tk.X)
        bar_fg = tk.Frame(bar_bg, bg="#1f6aa5", height=4, bd=0)
        bar_fg.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        _SPIN_FRAMES = [" ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏"]
        _spin_idx = [0]
        def _tick_spinner():
            if not wait_win.winfo_exists():
                return
            _spin_idx[0] = (_spin_idx[0] + 1) % len(_SPIN_FRAMES)
            spin_var.set(_SPIN_FRAMES[_spin_idx[0]])
            wait_win.after(80, _tick_spinner)
        _tick_spinner()

        def _set_status(msg: str, progress: float = None):
            def _do():
                if not wait_win.winfo_exists():
                    return
                status_var.set(msg)
                if progress is not None:
                    bar_fg.place(relwidth=min(progress, 1.0))
            self.root.after(0, _do)

        def _close_wait():
            def _do():
                if wait_win.winfo_exists():
                    wait_win.grab_release()
                    wait_win.destroy()
            self.root.after(0, _do)

        def _show_error(err_msg: str):
            def _do():
                _close_wait()
                messagebox.showerror("Report Export Error", err_msg)
            self.root.after(0, _do)

        def _show_success(filename: str):
            def _do():
                _close_wait()
                self.show_toast(f"Report saved: {filename}")
            self.root.after(0, _do)

        def _generate():
            try:
                from matplotlib.figure import Figure
                from matplotlib.backends.backend_agg import FigureCanvasAgg
                import matplotlib.ticker as _ticker
                df   = self.df
                cols = list(df.columns)
                sel  = [c for c, v in self.vars.items() if v.get() and c in df.columns]
                x_vals, ts, use_time = self._get_x_axis()
                colors_cycle = matplotlib.rcParams['axes.prop_cycle'].by_key()['color']

                def _fig_to_b64(fig) -> str:
                    FigureCanvasAgg(fig)
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                                facecolor='#1a1a2e')
                    buf.seek(0)
                    return base64.b64encode(buf.read()).decode()

                def _chart_html(b64: str, caption: str) -> str:
                    return (f'<figure><img src="data:image/png;base64,{b64}" '
                            f'alt="{html_mod.escape(caption)}">'
                            f'<figcaption>{html_mod.escape(caption)}</figcaption></figure>')

                def _make_chart(sensor_cols: list, title: str, figsize=(13, 3.5)) -> str:
                    fig = Figure(figsize=figsize)
                    fig.patch.set_facecolor('#1a1a2e')
                    ax = fig.add_subplot(111)
                    ax.set_facecolor('#0f0f23')
                    for i, col in enumerate(sensor_cols):
                        if col not in df.columns:
                            continue
                        ax.plot(x_vals, df[col], lw=1.2,
                                color=colors_cycle[i % len(colors_cycle)],
                                label=col[:60])
                    ax.set_title(title, color='#a0c4ff', fontsize=9, pad=4)
                    ax.tick_params(colors='#ccc', labelsize=7)
                    ax.grid(True, ls=':', alpha=0.3, color='#444')
                    for spine in ax.spines.values():
                        spine.set_edgecolor('#333')
                    leg = ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1),
                                    fontsize=6, frameon=False)
                    if leg:
                        for t in leg.get_texts():
                            t.set_color('#ddd')
                    if use_time:
                        ax.xaxis.set_major_formatter(
                            _ticker.FuncFormatter(lambda v, _: self._format_elapsed(v)))
                        ax.tick_params(axis='x', labelrotation=20)
                    fig.subplots_adjust(right=0.72)
                    b64 = _fig_to_b64(fig)
                    fig.clf()
                    return _chart_html(b64, title)

                _set_status("Rendering selected sensor chart\u2026", 0.10)
                charts_selected_html = ""
                if sel:
                    charts_selected_html = _make_chart(
                        sel, "Selected Sensors",
                        figsize=(13, max(3.5, len(sel) * 0.35)))

                _set_status("Rendering category charts\u2026", 0.25)
                cat_charts_html = ""
                cat_groups: dict = {}
                _SKIP_UNITS = ['[yes/no]', '[t]', '[gb/s]', '[mb/s]', '[gt/s]',
                               '[]', '[gear mode]', '[cdtp level]']
                _SKIP_NAMES = ['date', 'time', 'timestamp', 'command rate',
                               'gear mode', 'memory clock ratio']
                for col in cols:
                    cu = col.lower()
                    if any(cu.endswith(u) for u in _SKIP_UNITS):
                        continue
                    if any(s in cu for s in _SKIP_NAMES):
                        continue
                    cat = self._get_category(col)
                    cat_groups.setdefault(cat, []).append(col)
                _SKIP_CATS = {'Other Sensors', 'Other', 'Memory Timings'}
                for cat_name in self.sorted_cats:
                    if cat_name in _SKIP_CATS:
                        continue
                    group = cat_groups.get(cat_name, [])
                    if not group:
                        continue
                    chunk = group[:20]
                    cat_charts_html += _make_chart(
                        chunk, f"Category: {cat_name}",
                        figsize=(13, max(3.5, len(chunk) * 0.28)))

                _set_status("Rendering PSU rail charts\u2026", 0.50)
                psu_charts_html = ""
                _RAIL_SPECS = {
                    '+12V':  (['12V', '12 V'], ['PCIE', 'INPUT'] + ['[W]', '[A]', 'POWER', 'CURRENT', 'WATT', 'VID', 'OFFSET', 'LIMIT', 'PPT', 'TDP', 'GPU', 'HPWR', 'VDDQ', 'FBVDD'], 12.0, 1.0),
                    '+5V':   (['+5V', '5V [V', 'ATX 5', '5VSB', 'AVCC'], ['12V', '3.3', '3V3', '[W]', '[A]', 'POWER', 'CURRENT', 'WATT', 'VID', 'OFFSET', 'LIMIT', 'PPT', 'TDP', 'GPU', 'HPWR', 'FBVDD'], 5.0, 0.4),
                    '+3.3V': (['+3.3V', '3.3V', '3V3', 'VCC3', 'AVCC3', '3VSB'], ['VDDQ TX', 'VDDQ (SWB)', '12V', '+5V', 'VPP', '[W]', '[A]', 'POWER', 'CURRENT', 'GPU'], 3.3, 0.4),
                }
                for rail_name, (keywords, excl, target_v, tol) in _RAIL_SPECS.items():
                    rail_matches = []
                    for c in cols:
                        if c not in df.columns:
                            continue
                        cu = c.upper()
                        if '[V]' not in cu:
                            continue
                        if any(ex in cu for ex in excl):
                            continue
                        if any(k.upper() in cu for k in keywords):
                            mean_v = df[c].dropna().mean()
                            rail_matches.append((c, mean_v))
                    if not rail_matches:
                        continue
                    close = [(c, v) for c, v in rail_matches
                             if not pd.isna(v) and abs(v - target_v) <= tol]
                    rail_cols = [c for c, _ in (close or rail_matches)]
                    lo, hi = self.volt_rails.get(rail_name, (None, None))

                    def _make_rail_chart(rcols, rtitle, rlo, rhi):
                        fig = Figure(figsize=(13, 3.5))
                        fig.patch.set_facecolor('#1a1a2e')
                        ax = fig.add_subplot(111)
                        ax.set_facecolor('#0f0f23')
                        for i, col in enumerate(rcols):
                            ax.plot(x_vals, df[col], lw=1.2,
                                    color=colors_cycle[i % len(colors_cycle)],
                                    label=col[:60])
                        if rlo is not None and rhi is not None:
                            ax.axhline(rlo, color='#ff4d4d', ls='--', lw=1, alpha=0.7,
                                       label=f'Min spec ({rlo}V)')
                            ax.axhline(rhi, color='#ff4d4d', ls='--', lw=1, alpha=0.7,
                                       label=f'Max spec ({rhi}V)')
                            ax.axhspan(rlo - 0.5, rlo, color='#ff4d4d', alpha=0.07)
                            ax.axhspan(rhi, rhi + 0.5, color='#ff4d4d', alpha=0.07)
                        ax.set_title(rtitle, color='#a0c4ff', fontsize=9, pad=4)
                        ax.tick_params(colors='#ccc', labelsize=7)
                        ax.grid(True, ls=':', alpha=0.3, color='#444')
                        for spine in ax.spines.values():
                            spine.set_edgecolor('#333')
                        leg = ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1),
                                        fontsize=6, frameon=False)
                        if leg:
                            for t in leg.get_texts():
                                t.set_color('#ddd')
                        if use_time:
                            ax.xaxis.set_major_formatter(
                                _ticker.FuncFormatter(lambda v, _: self._format_elapsed(v)))
                            ax.tick_params(axis='x', labelrotation=20)
                        fig.subplots_adjust(right=0.72)
                        b64 = _fig_to_b64(fig)
                        fig.clf()
                        return _chart_html(b64, rtitle)

                    spec_str = f"  |  Spec: {lo}V \u2013 {hi}V" if lo is not None else ""
                    psu_charts_html += _make_rail_chart(
                        rail_cols, f"PSU Rail: {rail_name}{spec_str}", lo, hi)

                _set_status("Extracting hardware info\u2026", 0.62)
                hw = self.analyzer.extract_hardware_names()
                _CAT_ICONS = {
                    'System / Motherboard': '\U0001f527', 'CPU': '\U0001f5a5',
                    'iGPU (Integrated Graphics)': '\U0001f4a1', 'GPU': '\U0001f3ae',
                    'Memory (RAM)': '\U0001f4be', 'Memory Timings': '\u23f1',
                    'Storage': '\U0001f4bf', 'Network': '\U0001f310',
                    'Battery': '\U0001f50b', 'PresentMon (Frame Timing)': '\U0001f4ca',
                    'Chipset': '\u2699', 'Other': '\U0001f4e1',
                }
                hw_rows = ""
                for cat, names in hw.items():
                    icon = _CAT_ICONS.get(cat, '\U0001f4e1')
                    for name in names:
                        hw_rows += (f'<tr><td class="hw-cat">{icon} {html_mod.escape(cat)}</td>'
                                    f'<td>{html_mod.escape(name)}</td></tr>')
                hw_section = (
                    f'<table class="hw-table"><thead><tr><th>Category</th><th>Device</th>'
                    f'</tr></thead><tbody>{hw_rows}</tbody></table>'
                ) if hw_rows else '<p class="muted">No hardware names detected in this CSV.</p>'

                generated_at    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                csv_name        = html_mod.escape(str(self.analyzer.path).replace('\\', '/').split('/')[-1])
                sample_count    = len(df)
                duration_str    = "N/A"
                sample_rate_str = "N/A"
                if use_time and len(x_vals) > 1:
                    duration_str = self._format_elapsed(float(x_vals[-1] - x_vals[0]))
                    intervals    = [x_vals[i+1] - x_vals[i] for i in range(min(20, len(x_vals)-1))]
                    avg_iv       = sum(intervals) / len(intervals)
                    sample_rate_str = f"{avg_iv:.2f}s / sample"

                _set_status("Computing sensor statistics\u2026", 0.70)
                stat_rows = ""
                for col in sel:
                    if col not in df.columns:
                        continue
                    s = df[col].dropna()
                    if s.empty:
                        continue
                    is_crit = self._is_critical(col)
                    flag = ' <span class="flag-crit">\u26a0 OUT OF SPEC</span>' if is_crit else ''
                    stat_rows += (
                        f'<tr class="{"crit-row" if is_crit else ""}">'
                        f'<td>{html_mod.escape(col)}{flag}</td>'
                        f'<td>{s.min():.2f}</td><td>{s.mean():.2f}</td>'
                        f'<td>{s.max():.2f}</td><td>{s.std():.2f}</td></tr>'
                    )
                stats_section = (
                    f'<table class="stat-table"><thead><tr>'
                    f'<th>Sensor</th><th>Min</th><th>Avg</th><th>Max</th><th>Std Dev</th>'
                    f'</tr></thead><tbody>{stat_rows}</tbody></table>'
                ) if stat_rows else '<p class="muted">No sensors selected.</p>'

                _set_status("Running signature analysis\u2026", 0.80)
                sigs = self._run_signatures()
                sig_narrative = self._build_narrative(sigs)
                _SEV_CLASS = {'CRITICAL': 'sev-crit', 'WARNING': 'sev-warn', 'INFO': 'sev-info'}
                _SEV_ICON  = {'CRITICAL': '\U0001f534', 'WARNING': '\U0001f7e1', 'INFO': '\U0001f535'}
                sig_cards = ""
                if sigs:
                    for s in sorted(sigs, key=lambda x: ['CRITICAL','WARNING','INFO'].index(x.get('severity','INFO'))):
                        sev  = s.get('severity', 'INFO')
                        cls  = _SEV_CLASS.get(sev, 'sev-info')
                        icon = _SEV_ICON.get(sev, '\U0001f535')
                        ev_items = "".join(f'<li>{html_mod.escape(str(e))}</li>'
                                           for e in s.get('evidence', []))
                        ev_block = f'<ul class="ev-list">{ev_items}</ul>' if ev_items else ''
                        sig_cards += (
                            f'<div class="sig-card {cls}">'
                            f'<div class="sig-title">{icon} {html_mod.escape(s["name"])} '
                            f'<span class="sev-badge">{sev}</span></div>'
                            f'<div class="sig-desc">{html_mod.escape(s.get("description",""))}</div>'
                            f'{ev_block}</div>'
                        )
                else:
                    sig_cards = '<p class="muted all-clear">\u2705 No issues detected. All signatures passed.</p>'

                oos_rows = ""
                for col in cols:
                    if self._is_critical(col) and col in df.columns:
                        s = df[col].dropna()
                        if s.empty:
                            continue
                        oos_rows += (f'<tr><td>{html_mod.escape(col)}</td>'
                                     f'<td>{s.min():.2f}</td><td>{s.mean():.2f}</td>'
                                     f'<td class="val-crit">{s.max():.2f}</td></tr>')
                oos_section = (
                    f'<table class="stat-table"><thead><tr>'
                    f'<th>Sensor</th><th>Min</th><th>Avg</th><th>Peak</th>'
                    f'</tr></thead><tbody>{oos_rows}</tbody></table>'
                ) if oos_rows else '<p class="muted all-clear">\u2705 No out-of-spec sensors detected.</p>'

                crit_count = sum(1 for s in sigs if s.get('severity') == 'CRITICAL')
                warn_count = sum(1 for s in sigs if s.get('severity') == 'WARNING')
                info_count = sum(1 for s in sigs if s.get('severity') == 'INFO')

                _set_status("Writing report file\u2026", 0.95)
                html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RESYNC.ERR Session Report \u2014 {csv_name}</title>
<style>
:root{{--bg:#0d0d1a;--bg2:#13132b;--bg3:#1a1a38;--accent:#4f8ef7;--accent2:#a78bfa;
      --text:#e2e8f0;--muted:#64748b;--border:#1e1e3a;--radius:8px;
      --crit:#ef4444;--warn:#f59e0b;--good:#22c55e;--info:#3b82f6;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.6;}}
.page-wrap{{max-width:1300px;margin:0 auto;padding:32px 24px;}}
.report-header{{background:linear-gradient(135deg,#1a1a38 0%,#0d0d1a 100%);border:1px solid var(--border);border-radius:var(--radius);padding:32px;margin-bottom:28px;}}
.report-header h1{{font-size:26px;color:var(--accent);letter-spacing:1px;}}
.report-header .sub{{color:var(--muted);font-size:13px;margin-top:6px;}}
.badges{{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap;}}
.badge{{padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}}
.badge-crit{{background:#3d0000;color:var(--crit);border:1px solid var(--crit);}}
.badge-warn{{background:#2d1800;color:var(--warn);border:1px solid var(--warn);}}
.badge-info{{background:#001a2d;color:var(--info);border:1px solid var(--info);}}
.badge-ok{{background:#001a0d;color:var(--good);border:1px solid var(--good);}}
.meta-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-top:20px;}}
.meta-item{{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:12px 16px;}}
.meta-item .label{{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:0.5px;}}
.meta-item .value{{font-size:18px;font-weight:700;color:var(--accent);margin-top:2px;}}
.section{{margin-bottom:32px;}}
.section-title{{font-size:16px;font-weight:700;color:var(--accent2);border-bottom:1px solid var(--border);padding-bottom:8px;margin-bottom:16px;letter-spacing:0.5px;}}
.hw-table,.stat-table{{width:100%;border-collapse:collapse;font-size:13px;}}
.hw-table th,.stat-table th{{background:var(--bg3);color:var(--accent);padding:8px 12px;text-align:left;border-bottom:1px solid var(--border);font-size:12px;text-transform:uppercase;letter-spacing:0.5px;}}
.hw-table td,.stat-table td{{padding:7px 12px;border-bottom:1px solid #1e1e3a;color:var(--text);}}
.hw-table tr:hover td,.stat-table tr:hover td{{background:var(--bg3);}}
.hw-cat{{color:var(--muted);font-size:12px;white-space:nowrap;}}
.crit-row td{{background:#1a0000!important;}}
.val-crit{{color:var(--crit)!important;font-weight:700;}}
.flag-crit{{color:var(--crit);font-size:11px;font-weight:600;}}
.sig-card{{border-radius:var(--radius);padding:16px 20px;margin-bottom:12px;border-left:4px solid transparent;}}
.sev-crit{{background:#1a0505;border-color:var(--crit);}}
.sev-warn{{background:#1a1005;border-color:var(--warn);}}
.sev-info{{background:#051525;border-color:var(--info);}}
.sig-title{{font-size:15px;font-weight:700;margin-bottom:6px;}}
.sig-desc{{color:#a0b0c0;font-size:13px;margin-bottom:8px;}}
.sev-badge{{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:700;vertical-align:middle;margin-left:6px;}}
.sev-crit .sev-badge{{background:var(--crit);color:#000;}}
.sev-warn .sev-badge{{background:var(--warn);color:#000;}}
.sev-info .sev-badge{{background:var(--info);color:#000;}}
.ev-list{{margin:8px 0 0 16px;color:#94a3b8;font-size:12px;font-family:monospace;}}
.narrative-box{{background:var(--card);border-left:4px solid var(--accent2);border-radius:var(--radius);padding:16px 20px;font-size:13.5px;line-height:1.7;color:var(--fg);margin-bottom:4px;}}
.ev-list li{{margin-bottom:2px;}}
figure{{margin-bottom:20px;}}
figure img{{width:100%;border-radius:8px;border:1px solid var(--border);display:block;}}
figcaption{{color:var(--muted);font-size:11px;margin-top:6px;text-align:center;}}
.muted{{color:var(--muted);font-style:italic;}}
.all-clear{{color:var(--good);font-style:normal;font-weight:600;}}
.toc{{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px;margin-bottom:28px;}}
.toc a{{display:block;padding:3px 0;font-size:13px;text-decoration:none;color:var(--accent);}}
.toc a:hover{{color:var(--accent2);}}
.footer{{text-align:center;color:var(--muted);font-size:12px;margin-top:48px;border-top:1px solid var(--border);padding-top:16px;}}
</style>
</head>
<body><div class="page-wrap">
<div class="report-header">
  <h1>RESYNC.ERR \u2014 Session Report</h1>
  <div class="sub">Generated {generated_at} &nbsp;&middot;&nbsp; Source: <strong>{csv_name}</strong></div>
  <div class="badges">
    {'<span class="badge badge-crit">\U0001f534 ' + str(crit_count) + ' Critical</span>' if crit_count else ''}
    {'<span class="badge badge-warn">\U0001f7e1 ' + str(warn_count) + ' Warning</span>' if warn_count else ''}
    {'<span class="badge badge-info">\U0001f535 ' + str(info_count) + ' Info</span>' if info_count else ''}
    {'<span class="badge badge-ok">\u2705 All Clear</span>' if not sigs else ''}
  </div>
  <div class="meta-grid">
    <div class="meta-item"><div class="label">Duration</div><div class="value">{duration_str}</div></div>
    <div class="meta-item"><div class="label">Samples</div><div class="value">{sample_count:,}</div></div>
    <div class="meta-item"><div class="label">Sample Rate</div><div class="value">{sample_rate_str}</div></div>
    <div class="meta-item"><div class="label">Sensors in File</div><div class="value">{len(cols):,}</div></div>
    <div class="meta-item"><div class="label">Selected Sensors</div><div class="value">{len(sel)}</div></div>
    <div class="meta-item"><div class="label">Signature Hits</div><div class="value">{len(sigs)}</div></div>
  </div>
</div>
<div class="toc">
  <strong style="color:var(--accent2)">Contents</strong>
  <a href="#hw">\U0001f527 Detected Hardware</a>
  <a href="#issues">\U0001f6a8 Issues &amp; Signature Hits</a>
  <a href="#oos">\u26a0 Out-of-Spec Sensors</a>
  <a href="#charts-sel">\U0001f4c8 Selected Sensor Charts</a>
  <a href="#psu-rails">\U0001f50c PSU Rail Voltages</a>
  <a href="#charts-cat">\U0001f4ca Category Overview Charts</a>
  <a href="#stats">\U0001f4cb Per-Sensor Statistics</a>
</div>
<div class="section" id="hw"><div class="section-title"><span>\U0001f527</span> Detected Hardware</div>{hw_section}</div>
<div class="section" id="narrative"><div class="section-title"><span>\U0001f4dd</span> Session Summary</div><div class="narrative-box">{sig_narrative}</div></div>
<div class="section" id="issues"><div class="section-title"><span>\U0001f6a8</span> Issues &amp; Signature Hits</div>{sig_cards}</div>
<div class="section" id="oos"><div class="section-title"><span>\u26a0</span> Out-of-Spec Sensors</div>{oos_section}</div>
<div class="section" id="charts-sel"><div class="section-title"><span>\U0001f4c8</span> Selected Sensor Charts</div>{charts_selected_html if charts_selected_html else '<p class="muted">No sensors selected.</p>'}</div>
<div class="section" id="psu-rails"><div class="section-title"><span>\U0001f50c</span> PSU Rail Voltages</div>{psu_charts_html if psu_charts_html else '<p class="muted">No PSU rail voltage columns detected (+12V, +5V, +3.3V).</p>'}</div>
<div class="section" id="charts-cat"><div class="section-title"><span>\U0001f4ca</span> Category Overview Charts</div>{cat_charts_html if cat_charts_html else '<p class="muted">No data.</p>'}</div>
<div class="section" id="stats"><div class="section-title"><span>\U0001f4cb</span> Per-Sensor Statistics</div>{stats_section}</div>
<div class="footer">RESYNC.ERR v{CURRENT_VERSION} &nbsp;&middot;&nbsp; Report generated {generated_at}</div>
</div></body></html>"""

                with open(f_path, 'w', encoding='utf-8') as fh:
                    fh.write(html_out)

                fname = str(f_path).replace('\\', '/').split('/')[-1]
                _show_success(fname)

            except Exception as e:
                _show_error(f"{type(e).__name__}: {e}\n\n{traceback.format_exc()[-1000:]}")

        threading.Thread(target=_generate, daemon=True).start()

    def _open_diagnosis(self):
        """Display signature analysis results. Uses cached results from the
        background watcher if fresh, otherwise runs a quick re-evaluation."""

        if hasattr(self, '_diag_window') and self._diag_window and self._diag_window.winfo_exists():
            self._diag_window.deiconify()
            self._diag_window.lift()
            self._diag_window.focus_force()
            return

        def _show(results):
            is_dark = self.is_dark
            _t = self._get_theme(); bg = _t["bg"]; fg = _t["fg"]; accent = _t["accent"]; bg3 = _t["bg3"]
            accent = "#1f6aa5" if is_dark else "#3498db"

            dialog = tk.Toplevel(self.root)
            dialog.title("Hardware Failure Diagnosis")
            dialog.geometry("680x620")
            dialog.minsize(520, 400)
            dialog.resizable(True, True)
            dialog.configure(bg=bg)
            self._diag_window = dialog
            dialog.protocol("WM_DELETE_WINDOW", lambda: (setattr(self, '_diag_window', None), dialog.destroy()))

            self.root.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 340
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 310
            dialog.geometry(f"680x620+{x}+{y}")

            tk.Label(dialog, text="Hardware Failure Diagnosis",
                    font=('Segoe UI', 13, 'bold'),
                    bg=bg, fg=accent).pack(pady=(14, 2))

            tk.Label(dialog,
                    text=f"Analyzed {len(self.df)} samples - {len(results)} signature(s) detected",
                    font=('Segoe UI', 9),
                    bg=bg, fg="#888").pack(pady=(0, 10))

            outer = tk.Frame(dialog, bg=bg)
            outer.pack(fill=tk.BOTH, expand=True, padx=12)

            canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
            sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview,
                       bg=bg3, troughcolor=bg, activebackground=accent)
            body = tk.Frame(canvas, bg=bg)

            wid = canvas.create_window((0, 0), window=body, anchor="nw")
            body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
            canvas.configure(yscrollcommand=sb.set)

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)

            canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>",
                lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units")))
            canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

            if not results:
                tk.Label(body,
                        text="No hardware failure signatures detected.",
                        font=('Segoe UI', 11),
                        bg=bg, fg="#2ecc71",
                        pady=30).pack()

                tk.Label(body,
                        text="The log looks clean based on the current signature library.",
                        font=('Segoe UI', 9),
                        bg=bg, fg="#888").pack()

            else:
                results.sort(key=lambda r: {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}.get(r['severity'], 3))

                cols = set(self.df.columns)

                def _cols(*keywords):
                    """Return all df columns whose name contains ALL given keywords (case-insensitive).
                    Use for precise multi-word matches e.g. _cols('GPU', 'TEMP')."""
                    kw = [k.upper() for k in keywords]
                    return {c for c in cols if all(k in c.upper() for k in kw)}

                def _any(*keywords):
                    """Return all df columns whose name contains ANY of the given keywords."""
                    kw = [k.upper() for k in keywords]
                    return {c for c in cols if any(k in c.upper() for k in kw)}

                def _sensors_for_signature(sig_name: str) -> set:
                    """Return df columns relevant to a given signature.
                    Uses _any() for OR matching (any keyword) and _cols() for AND matching
                    (all keywords must appear). Both are case-insensitive substring matches."""
                    m = {

                        "CPU Thermal Throttling": (
                            _any("TDIE", "TCTL", "TJMAX", "PROCHOT", "THROTTL",
                                 "CPU PACKAGE [", "CPU PACKAGE TEMP", "PACKAGE TEMP",
                                 "CORE TEMP", "CPU TEMP", "CPU TEMPERATURE",
                                 "CORE MAX", "CORE DISTANCE", "DISTANCE TO TJMAX",
                                 "CPU HOT", "THERMAL THROTTL", "CPU DIE",
                                 "CCD TEMP", "CCD1", "CCD2", "IOD TEMP", "CPU CCD",
                                 "P-CORE", "E-CORE", "RING TEMP",
                                 "PAKET", "KERN") |
                            _cols("CPU", "POWER") | _cols("CORE", "DISTANCE")
                        ),

                        "CPU Power Limit Reached": (
                            _any("PL1", "PL2", "PL3", "PL4", "PPT", "EDC", "TDC",
                                 "POWER LIMIT", "THROTTL", "PROCHOT",
                                 "PACKAGE POWER LIMIT", "CPU POWER LIMIT",
                                 "TURBO POWER", "POWER LIMIT EXCEEDED",
                                 "IA LIMIT", "GT LIMIT", "RING LIMIT",
                                 "RUNNING AVERAGE THERMAL", "RAPL",
                                 "PERFORMANCE LIMIT - POWER",
                                 "PERFORMANCE LIMIT - THERMAL",
                                 "CURRENT CDTP") |
                            _cols("CPU", "POWER") | _cols("CPU", "PACKAGE", "POWER") |
                            _cols("IA", "POWER")
                        ),

                        "CPU Bottleneck": (
                            _any("TOTAL CPU", "CPU USAGE", "CPU LOAD", "CPU UTIL",
                                 "CPU AUSLASTUNG", "CPU BELASTUNG",
                                 "GPU USAGE", "GPU CORE LOAD", "GPU LOAD",
                                 "GPU AUSLASTUNG", "GPU CORE USAGE",
                                 "MAX CPU", "CPU THREAD", "THREAD USAGE")
                        ),

                        "CPU Clock Stretching - Major": (
                            _cols("EFFECTIVE", "CLOCK") |
                            _cols("CLOCK", "PERF") |
                            _cols("CPU", "USAGE") | _cols("CPU", "LOAD") |
                            _any("TOTAL CPU USAGE", "TOTAL CPU LOAD",
                                 "AVERAGE EFFECTIVE", "EFF CLOCK",
                                 "T0 EFFECTIVE", "T1 EFFECTIVE",
                                 "CORE RATIO", "BUS CLOCK")
                        ),

                        "CPU Clock Stretching - Minor": (
                            _cols("EFFECTIVE", "CLOCK") |
                            _cols("CLOCK", "PERF") |
                            _cols("CPU", "USAGE") | _cols("CPU", "LOAD") |
                            _any("TOTAL CPU USAGE", "TOTAL CPU LOAD",
                                 "AVERAGE EFFECTIVE", "EFF CLOCK",
                                 "T0 EFFECTIVE", "T1 EFFECTIVE")
                        ),

                        "GPU Thermal Warning": (
                            _any("GPU TEMPERATURE", "GPU TEMP [",
                                 "GPU HOT", "GPU HOTSPOT", "HOT SPOT",
                                 "GPU JUNCTION", "GPU MEMORY JUNCTION",
                                 "GPU THERMAL", "THERMAL LIMIT",
                                 "GPU EDGE", "EDGE TEMP", "GPU JUNCTION TEMP",
                                 "GPU CORE TEMP", "GPU DIODE",
                                 "GPU TEMPERATUR")
                        ),

                        "GPU Overheating (Hotspot)": (
                            _any("GPU TEMPERATURE", "GPU TEMP [",
                                 "GPU HOT", "GPU HOTSPOT", "HOT SPOT",
                                 "GPU JUNCTION", "GPU MEMORY JUNCTION",
                                 "GPU THERMAL", "THERMAL LIMIT",
                                 "GPU EDGE", "EDGE TEMP", "GPU CORE TEMP",
                                 "GPU DIODE", "GPU TEMPERATUR") |
                            _cols("GPU", "POWER") | _cols("GPU", "CLOCK") |
                            _cols("GPU", "USAGE")
                        ),

                        "GPU Driver TDR (Timeout)": (
                            _cols("GPU", "USAGE") | _cols("GPU", "LOAD") |
                            _cols("GPU", "CLOCK") | _cols("GPU", "FREQUENCY") |
                            _any("GPU AUSLASTUNG", "GPU TAKT",
                                 "GPU CORE USAGE", "GPU CORE CLOCK",
                                 "GPU EFFECTIVE CLOCK", "GPU CROSSBAR")
                        ),

                        "GPU Power Limit Saturated": (
                            _any("GPU POWER", "GPU BOARD POWER", "GPU PACKAGE POWER",
                                 "TGP", "TBP", "GPU TGP", "GPU TBP",
                                 "GPU WATT", "GPU LEISTUNG",
                                 "PERFORMANCE LIMIT - POWER",
                                 "PERFORMANCE LIMIT - THERMAL",
                                 "PERFORMANCE LIMIT - UTILIZATION",
                                 "PERFORMANCE LIMIT - RELIABILITY",
                                 "PERFORMANCE LIMIT - MAX",
                                 "PERFCAP", "POWER LIMIT", "PERF LIMIT",
                                 "GPU INPUT POWER", "GPU RAIL POWER",
                                 "GPU 12VHPWR", "NVVDD", "FBVDD") |
                            _cols("GPU", "CLOCK") | _cols("GPU", "USAGE")
                        ),

                        "GPU Power Limit Oscillation": (
                            _any("GPU POWER", "GPU BOARD POWER", "TGP", "TBP",
                                 "PERFORMANCE LIMIT - POWER", "PERFCAP",
                                 "POWER LIMIT", "GPU WATT", "GPU LEISTUNG",
                                 "GPU INPUT POWER", "NVVDD", "FBVDD") |
                            _cols("GPU", "CLOCK")
                        ),

                        "GPU VRAM Overflow Analysis": (
                            _any("VRAM", "GPU MEMORY", "D3D MEMORY", "GPU MEM",
                                 "MEMORY ALLOCATED", "MEMORY AVAILABLE [MB",
                                 "GPU D3D", "DEDICATED VIDEO", "VIDEO MEMORY",
                                 "VIRTUAL MEMORY", "GDDR", "HBM",
                                 "GPU MEMORY USAGE", "GPU MEMORY LOAD",
                                 "GPU MEMORY ALLOCATED", "GPU MEMORY AVAILABLE",
                                 "D3D MEMORY DEDICATED", "D3D MEMORY DYNAMIC",
                                 "SHARED MEMORY")
                        ),

                        "VRAM Thermal Throttling": (
                            _any("GPU MEMORY JUNCTION", "MEMORY JUNCTION",
                                 "VRAM TEMP", "VRAM TEMPERATURE",
                                 "GPU MEM TEMP", "HBM TEMP", "GDDR TEMP",
                                 "GPU MEMORY TEMP", "MEMORY TEMP") |
                            _cols("GPU", "MEMORY", "CLOCK") |
                            _cols("GPU", "CLOCK")
                        ),

                        "VRAM Swapping / System Memory Spillover": (
                            _any("GPU D3D MEMORY", "D3D MEMORY DYNAMIC",
                                 "D3D MEMORY DEDICATED", "GPU MEMORY ALLOCATED",
                                 "SHARED MEMORY", "VIRTUAL MEMORY", "PAGE FILE",
                                 "GPU MEMORY AVAILABLE", "DEDICATED VIDEO MEMORY")
                        ),

                        "PSU +12V Rail Sag": (
                            _any("+12V [V]", "+12V VOLTAGE", "12V RAIL",
                                 "ATX 12V", "EPS 12V", "12V SUPPLY",
                                 "VBUS 12", "12V OUT", "12 VOLT",
                                 "VCC 12V", "12VDC",
                                 "+12.0V", "12.000V",
                                 "VCORE 12V", "MAIN 12V") |
                            _cols("GPU", "POWER")
                        ),

                        "PSU +5V Rail Unstable": (
                            _any("+5V [V]", "+5V VOLTAGE", "5V RAIL",
                                 "ATX 5V", "5V SUPPLY", "5VSB", "5V STANDBY",
                                 "VBUS 5", "5V OUT", "5 VOLT",
                                 "VCC 5V", "5VDC", "+5.0V", "5.000V",
                                 "MAIN 5V", "+5VS", "5V SB",
                                 "VIN 5V", "AVCC")
                        ),

                        "PSU +3.3V Rail Unstable": (
                            _any("+3.3V [V]", "+3.3V VOLTAGE", "3.3V RAIL",
                                 "3V3", "3.3V SUPPLY", "3.3V OUT",
                                 "ATX 3.3", "3.3 VOLT", "3.3VDC",
                                 "VCC 3.3", "+3.3VS", "3.3V SB",
                                 "VDD 3.3", "VDDA", "AVDD",
                                 "+3.30V", "3.300V", "3.3000V",
                                 "VDD (SWA)", "VDDQ (SWB)", "VPP (SWC)",
                                 "1.8V VOUT", "1.0V VOUT",
                                 "3VSB", "3V SB", "3.3VSB",
                                 "VIN 3.3", "+3V3", "3V3 RAIL",
                                 "3.3V VOLTAGE", "3.3V SENSOR",
                                 "VCC3", "VCC 3", "VCCIO")
                        ),

                        "PSU Hardware Failure Indicators": (
                            _any("+12V [V]", "+12V VOLTAGE", "12V RAIL", "ATX 12V", "EPS 12V") |
                            _any("+5V [V]", "+5V VOLTAGE", "5V RAIL", "ATX 5V") |
                            _any("+3.3V [V]", "+3.3V VOLTAGE", "3.3V RAIL", "3V3") |
                            _any("POWER SUPPLY", "HARDWARE LIMIT", "SOFTWARE LIMIT",
                                 "AVG. POWER (PL1)", "BURST POWER (PL2)", "CURRENT (PL4)",
                                 "THROTTL", "PERFORMANCE LIMIT") |
                            _cols("GPU", "USAGE") | _cols("GPU", "CLOCK")
                        ),
                        "Fan Stall Detected": (
                            _any("FAN", "RPM", "PUMP", "COOLER",
                                 "FAN SPEED", "FAN RPM", "CPU FAN", "GPU FAN",
                                 "CHASSIS FAN", "CASE FAN", "SYS FAN",
                                 "AIO PUMP", "WATER PUMP",
                                 "LÜFTER", "VENTILATEUR",
                                 "CPU [RPM]", "GPU [RPM]", "FAN1", "FAN2", "FAN3") |
                            _cols("CPU", "TEMP") | _cols("GPU", "TEMP")
                        ),

                        "VRM Overheating": (
                            _any("VRM", "MOSFET", "CHOKE", "MOS TEMP",
                                 "PHASE TEMP", "VCORE TEMP",
                                 "CPU VRM", "GPU VRM",
                                 "SVI", "VDDCR", "VDDCR_SOC",
                                 "POWER STAGE", "PWM TEMP", "PWMIC",
                                 "DIGI+ VRM", "ASUS VRM",
                                 "VRM HOT", "VRM TEMPERATURE",
                                 "MOSFet", "FET TEMP",
                                 "IA VR", "GT VR", "SA VR", "VR TEMP")
                        ),

                        "System RAM Exhaustion": (
                            _any("PHYSICAL MEMORY", "MEMORY USED", "MEMORY LOAD",
                                 "MEMORY AVAILABLE", "RAM LOAD", "RAM USAGE",
                                 "PHYSICAL MEMORY USED", "PHYSICAL MEMORY LOAD",
                                 "PHYSICAL MEMORY AVAILABLE",
                                 "MEMORY USAGE", "RAM USED", "RAM AVAILABLE",
                                 "SPEICHER", "ARBEITSSPEICHER")
                        ),

                        "Virtual Memory Limit": (
                            _any("VIRTUAL MEMORY", "PAGE FILE", "COMMIT",
                                 "PAGEFILE", "SWAP", "VIRTUAL MEMORY COMMITTED",
                                 "VIRTUAL MEMORY AVAILABLE", "VIRTUAL MEMORY LOAD",
                                 "PAGE FILE USAGE", "PAGE FILE TOTAL",
                                 "COMMITTED BYTES", "COMMIT LIMIT")
                        ),

                        "Storage Thermal Critical": (
                            _any("DRIVE TEMP", "SSD TEMP", "NVME TEMP", "HDD TEMP",
                                 "DRIVE TEMPERATURE", "DISK TEMP", "DISK TEMPERATURE",
                                 "M.2 TEMP", "STORAGE TEMP",
                                 "LAUFWERK TEMP", "FESTPLATTE TEMP",
                                 "TEMPERATURE [°C]", "DRIVE TEMPERATURE [°C]",
                                 "DRIVE TEMPERATURE 2", "DRIVE TEMPERATURE 3",
                                 "COMPOSITE TEMP", "SENSOR 1 TEMP", "SENSOR 2 TEMP")
                        ),

                        "Storage Overheating": (
                            _any("DRIVE TEMP", "SSD TEMP", "NVME TEMP", "HDD TEMP",
                                 "DRIVE TEMPERATURE", "DISK TEMP", "M.2 TEMP",
                                 "COMPOSITE TEMP", "STORAGE TEMP",
                                 "DRIVE TEMPERATURE 2", "DRIVE TEMPERATURE 3",
                                 "SENSOR 1 TEMP", "SENSOR 2 TEMP")
                        ),

                        "Storage Congestion": (
                            _any("READ RATE", "WRITE RATE", "READ ACTIVITY",
                                 "WRITE ACTIVITY", "TOTAL ACTIVITY", "DRIVE ACTIVITY",
                                 "DISK ACTIVITY", "IO RATE", "READ TOTAL", "WRITE TOTAL",
                                 "READ SPEED", "WRITE SPEED", "DISK SPEED",
                                 "MB/S", "READ [MB", "WRITE [MB")
                        ),

                        "Storage I/O Bottleneck / Hitching": (
                            _any("READ RATE", "WRITE RATE", "READ ACTIVITY",
                                 "WRITE ACTIVITY", "TOTAL ACTIVITY",
                                 "READ SPEED", "WRITE SPEED", "IO RATE",
                                 "FRAME TIME", "FRAMETIME", "GPU BUSY", "CPU BUSY")
                        ),

                        "S.M.A.R.T. Hardware Failure": (
                            _any("DRIVE FAIL", "DRIVE WARN", "DRIVE WARNING",
                                 "DRIVE FAILURE", "S.M.A.R.T", "SMART",
                                 "FAILURE [YES", "WARNING [YES",
                                 "REALLOCATED", "PENDING SECTOR",
                                 "UNCORRECTABLE", "OFFLINE UNCORRECTABLE",
                                 "CRC ERROR", "ULTRA DMA CRC")
                        ),

                        "SSD Lifespan Critical": (
                            _any("REMAINING LIFE", "DRIVE HEALTH", "WEAR LEVEL",
                                 "AVAILABLE SPARE", "DRIVE REMAINING",
                                 "NAND ENDURANCE", "MEDIA WEAROUT",
                                 "PERCENT USED", "PERCENT LIFETIME",
                                 "TOTAL BYTES WRITTEN", "TOTAL HOST WRITES",
                                 "HOST WRITES", "NAND WRITES",
                                 "DRIVE REMAINING LIFE", "SSD HEALTH",
                                 "ENDURANCE REMAINING")
                        ),

                        "SSD Wear Warning": (
                            _any("REMAINING LIFE", "DRIVE HEALTH", "WEAR LEVEL",
                                 "AVAILABLE SPARE", "NAND ENDURANCE",
                                 "PERCENT USED", "PERCENT LIFETIME",
                                 "TOTAL HOST WRITES", "HOST WRITES",
                                 "DRIVE REMAINING LIFE", "SSD HEALTH",
                                 "ENDURANCE REMAINING")
                        ),

                        "Memory XMP/EXPO Profile Disabled": (
                            _any("MCLK", "MEMORY CLOCK", "DRAM CLOCK",
                                 "RAM CLOCK", "MEM FREQ", "MEMORY FREQUENCY",
                                 "DRAM FREQUENCY", "RAM FREQUENCY",
                                 "MEMORY SPEED", "DRAM SPEED")
                        ),

                        "Micro-Stuttering Detected": (
                            _any("FRAME TIME", "FRAMETIME", "FPS", "FRAME RATE",
                                 "GPU BUSY", "CPU BUSY", "GPU WAIT", "CPU WAIT",
                                 "PRESENTED", "DISPLAYED", "ANIMATION ERROR",
                                 "FRAME TIME PRESENTED", "FRAME TIME DISPLAYED",
                                 "FRAMERATE PRESENTED", "FRAMERATE DISPLAYED",
                                 "1% LOW", "0.1% LOW", "99TH", "1ST PERCENTILE",
                                 "LATENCY", "RENDER TIME")
                        ),

                        "Background Process Interference": (
                            _any("CPU USAGE", "TOTAL CPU", "CPU LOAD", "CPU UTIL",
                                 "GPU USAGE", "GPU LOAD", "GPU CORE LOAD",
                                 "FRAME TIME", "FRAMETIME", "MAX CPU",
                                 "CPU THREAD", "THREAD USAGE",
                                 "PROCESS CPU", "CPU AUSLASTUNG")
                        ),

                        "GPU Priority Conflict (Background App)": (
                            _any("FRAME TIME", "FRAMETIME", "GPU USAGE", "GPU LOAD",
                                 "GPU BUS", "BUS LOAD", "GPU WAIT", "GPU BUSY",
                                 "GPU CLOCK", "FPS", "GPU CORE LOAD",
                                 "GPU D3D USAGE", "GPU GRAPHICS USAGE",
                                 "GPU COMPUTE USAGE", "GPU VIDEO USAGE")
                        ),

                        "GPU Engine Wait Bottleneck": (
                            _any("GPU WAIT", "GPU BUSY", "GPU WAIT (AVG)",
                                 "GPU BUSY (AVG)", "FRAME TIME", "FRAMETIME",
                                 "CPU WAIT", "CPU BUSY", "FPS",
                                 "GPU WAIT [MS]", "GPU BUSY [MS]",
                                 "CPU WAIT [MS]", "CPU BUSY [MS]",
                                 "ANIMATION ERROR")
                        ),

                        "Hardware (WHEA) Errors": (
                            _any("WHEA", "HARDWARE ERROR", "CORRECTABLE",
                                 "NON-FATAL", "FATAL ERROR", "PCIe LANE",
                                 "WINDOWS HARDWARE ERROR", "MCE",
                                 "MACHINE CHECK", "CORRECTABLE ERROR COUNT",
                                 "NON-FATAL ERROR COUNT", "FATAL ERROR COUNT",
                                 "WHEA ERROR", "HARDWARE ERRORS",
                                 "TOTAL ERRORS", "UNSUPPORTED REQUEST")
                        ),

                        "Chipset Thermal Throttling": (
                            _any("CHIPSET", "PCH TEMP", "PCH [",
                                 "PCH TEMPERATURE", "MOTHERBOARD [",
                                 "MOTHERBOARD TEMP", "NB TEMP", "NORTHBRIDGE",
                                 "SOUTHBRIDGE", "PLATFORM CONTROLLER",
                                 "PCH TEMPERATURE [", "PCH TEMPERATURE2",
                                 "PCH TEMPERATURE3", "PCH TEMPERATURE4",
                                 "SMU TEMP", "SPD HUB")
                        ),

                        "PCIe Bus Interface Chokepoint": (
                            _any("GPU BUS", "BUS LOAD", "PCIE LINK", "PCIE SPEED",
                                 "GPU USAGE", "GPU CLOCK", "FRAME TIME",
                                 "PCIE LINK SPEED", "PCIE BANDWIDTH",
                                 "GPU BUS LOAD", "GPU BUS INTERFACE",
                                 "GPU PCIE", "LINK SPEED", "GT/S")
                        ),

                        "PCIe Bus Signal Instability": (
                            _any("RECEIVER ERROR", "REPLAY COUNT",
                                 "REPLAY ROLLOVER", "BAD TLP", "BAD DLLP",
                                 "RECOVERY COUNT", "CORRECTABLE ERROR COUNT",
                                 "NON-FATAL ERROR COUNT", "FATAL ERROR COUNT",
                                 "UNSUPPORTED REQUEST", "PCIE LANE",
                                 "LCRC ERROR", "NAKS SENT", "NAKS RECEIVED",
                                 "PCI EXPRESS ERROR", "PCIE ERROR")
                        ),

                        "Kernel Driver Latency (DPC/ISR)": (
                            _any("DPC", "SYSTEM INTERRUPT", "LATENCY",
                                 "FRAME TIME", "FRAMETIME", "CPU BUSY", "CPU WAIT",
                                 "DPC LATENCY", "ISR LATENCY",
                                 "INTERRUPT LATENCY", "KERNEL LATENCY",
                                 "DPC/ISR", "DEFERRED PROCEDURE")
                        ),

                        "Laptop Power Delivery Failure (Limp Mode)": (
                            _any("BATTERY", "CHARGE", "DISCHARGE", "AC ADAPTER",
                                 "REMAINING CAPACITY", "CHARGE LEVEL", "CHARGE RATE",
                                 "BATTERY VOLTAGE", "BATTERY CAPACITY",
                                 "CHARGE CURRENT", "DISCHARGE RATE",
                                 "WEAR LEVEL", "FULL CHARGE CAPACITY",
                                 "DESIGN CAPACITY", "POWER SOURCE",
                                 "AC/DC", "PLUGGED IN", "ON BATTERY",
                                 "LAPTOP BATTERY", "BATTERY REMAINING",
                                 "BATTERY POWER", "DISCHARGE CURRENT") |
                            _cols("CPU", "POWER") | _cols("GPU", "POWER")
                        ),

                        "Phantom Clock Cap": (
                            _any("GPU CLOCK", "GPU CORE CLOCK", "GPU EFFECTIVE CLOCK",
                                 "GPU CROSSBAR", "GPU VIDEO CLOCK", "GPU MEMORY CLOCK",
                                 "PERFORMANCE LIMIT", "POWER LIMIT", "THERMAL LIMIT",
                                 "RELIABILITY VOLTAGE", "OPERATING VOLTAGE",
                                 "GPU BOOST CLOCK", "BOOST CLOCK",
                                 "GPU BASE CLOCK", "BASE CLOCK",
                                 "PERFCAP REASON", "CLOCK CAP", "CLOCK LIMIT")
                        ),
                    }
                    return m.get(sig_name, set()) & cols

                narrative_text = self._build_narrative(results)
                narr_bg = "#1a1a2e" if is_dark else "#eef4fb"
                narr_fg = "#a0c4ff" if is_dark else "#1a3a5c"
                narr_frame = tk.Frame(body, bg=narr_bg, padx=14, pady=10)
                narr_frame.pack(fill=tk.X, pady=(0, 10), padx=2)
                tk.Label(narr_frame,
                         text="Session Summary",
                         font=('Segoe UI', 9, 'bold'),
                         bg=narr_bg, fg=narr_fg).pack(anchor='w')
                tk.Label(narr_frame,
                         text=narrative_text,
                         font=('Segoe UI', 9),
                         bg=narr_bg, fg=fg,
                         wraplength=620,
                         justify='left').pack(anchor='w', pady=(4, 0))

                for r in results:

                    is_crit = r['severity'] == 'CRITICAL'
                    is_info = r.get('severity') == 'INFO'

                    card_bg   = "#2a0a0a" if (is_dark and is_crit) else\
                                "#1a2a1a" if (is_dark and not is_crit) else\
                                "#fdecea" if is_crit else "#eafaf1"

                    sev_color = "#e74c3c" if is_crit else "#f39c12"

                    if is_info:
                        sev_color = "#3498db"

                    card = tk.Frame(body, bg=card_bg, padx=12, pady=10)
                    card.pack(fill=tk.X, pady=5, padx=2)

                    hdr = tk.Frame(card, bg=card_bg)
                    hdr.pack(fill=tk.X)

                    tk.Label(hdr,
                            text="CRITICAL" if is_crit else "INFO" if is_info else "WARNING",
                            font=('Segoe UI', 8, 'bold'),
                            bg=sev_color,
                            fg="white",
                            padx=6,
                            pady=2).pack(side=tk.LEFT)

                    tk.Label(hdr,
                            text=f"  {r['name']}",
                            font=('Segoe UI', 10, 'bold'),
                            bg=card_bg,
                            fg=fg).pack(side=tk.LEFT)

                    tk.Label(card,
                            text=r['description'],
                            bg=card_bg,
                            fg=fg,
                            font=('Segoe UI', 9),
                            wraplength=580,
                            justify='left').pack(anchor='w', pady=(6, 4))

                    if r.get('evidence'):
                        for ev in r['evidence']:
                            if ev:
                                tk.Label(card,
                                        text=f"  • {ev}",
                                        bg=card_bg,
                                        fg="#aaaaaa" if is_dark else "#555555",
                                        font=('Segoe UI', 8)).pack(anchor='w')

                    def _make_select(sig_name):
                        def _select():
                            selected = _sensors_for_signature(sig_name)
                            if not selected:
                                self.show_toast(f"No matching sensors found for: {sig_name}")
                                return
                            for col, var in self.vars.items():
                                var.set(col in selected)
                            self.update_plot()
                            self.show_toast(f"Selected {len(selected)} sensor(s) for: {sig_name}")
                            dialog.lift()
                        return _select

                    ttk.Button(card, text="📌 Select Relevant Sensors",
                               command=_make_select(r['name'])).pack(anchor='w', pady=(6, 0))

            btn_row = tk.Frame(dialog, bg=bg)
            btn_row.pack(pady=10)

            def _copy_discord_summary():
                if not results:
                    summary = "✅ No issues detected — log looks clean."
                else:
                    SEV_EMOJI = {'CRITICAL': '🔴', 'WARNING': '🟡', 'INFO': '🔵'}
                    lines = []
                    for r in results:
                        emoji = SEV_EMOJI.get(r['severity'], '⚪')
                        name  = r['name']
                        line  = f"{emoji} **{name}**"
                        for ev in r.get('evidence') or []:
                            if ev:
                                line += f"\n  • {ev}"
                        lines.append(line)
                    summary = narrative_text + "\n\n" + "\n\n".join(lines)
                dialog.clipboard_clear()
                dialog.clipboard_append(summary)
                self.show_toast("Discord summary copied to clipboard")

            ttk.Button(btn_row, text="📋 Copy Discord Summary",
                       command=_copy_discord_summary).pack(side=tk.LEFT, padx=(0, 6))
            ttk.Button(btn_row, text="Close", command=lambda: (setattr(self, '_diag_window', None), dialog.destroy())).pack(side=tk.LEFT)

        if self._sig_hits and not self._sig_dirty:
            _show(self._sig_hits)
        else:
            self.show_toast("Analyzing signatures…")
            import threading
            def _run():
                results = self._run_signatures()
                def _done():
                    self._sig_hits    = results
                    self._sig_dirty   = False
                    self._sig_running = False
                    self._update_sig_badge()
                    _show(results)
                self.root.after(0, _done)
            threading.Thread(target=_run, daemon=True).start()

    def _open_about(self):
        """Show the About dialog with credits."""
        _t = self._get_theme()
        bg = _t["bg"]; bg2 = _t["bg2"]; bg3 = _t["bg3"]; fg = _t["fg"]; accent = _t["accent"]

        if hasattr(self, '_about_window') and self._about_window and self._about_window.winfo_exists():
            self._about_window.deiconify()
            self._about_window.lift()
            self._about_window.focus_force()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("About RESYNC.ERR")
        dialog.resizable(False, False)
        dialog.configure(bg=bg)
        self._about_window = dialog
        dialog.protocol("WM_DELETE_WINDOW",
                        lambda: (setattr(self, '_about_window', None), dialog.destroy()))

        self.root.update_idletasks()
        pw, ph = 540, 540
        x = self.root.winfo_x() + (self.root.winfo_width()  // 2) - pw // 2
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - ph // 2
        dialog.geometry(f"{pw}x{ph}+{x}+{y}")


        tk.Frame(dialog, bg=accent, height=4).pack(fill=tk.X)

        body = tk.Frame(dialog, bg=bg, padx=30, pady=22)
        body.pack(fill=tk.BOTH, expand=True)


        tk.Label(body, text="RESYNC.ERR",
                 font=('Segoe UI', 20, 'bold'), bg=bg, fg=accent).pack(anchor='w')
        tk.Label(body, text=f"Hardware Telemetry Log Viewer  \u2022  v{CURRENT_VERSION}",
                 font=('Segoe UI', 9), bg=bg, fg="#888").pack(anchor='w', pady=(0, 16))

        tk.Frame(body, bg=bg3, height=1).pack(fill=tk.X, pady=(0, 14))


        tk.Label(body, text="DEVELOPER",
                 font=('Segoe UI', 8, 'bold'), bg=bg, fg="#888").pack(anchor='w')
        tk.Label(body, text="ERROR_X2\u2122",
                 font=('Segoe UI', 12, 'bold'), bg=bg, fg=fg).pack(anchor='w', pady=(3, 0))
        tk.Label(body, text="ERROR_X2\u2122 | 418th Archmagos",
                 font=('Segoe UI', 9), bg=bg, fg="#888").pack(anchor='w')
        gh = tk.Label(body, text="\u238b  github.com/ERRORX2",
                      font=('Segoe UI', 9), bg=bg, fg=accent, cursor='hand2')
        gh.pack(anchor='w', pady=(2, 0))
        gh.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/ERRORX2"))

        tk.Frame(body, bg=bg3, height=1).pack(fill=tk.X, pady=(14, 14))


        tk.Label(body, text="SPECIAL THANKS",
                 font=('Segoe UI', 8, 'bold'), bg=bg, fg="#888").pack(anchor='w')

        for name, discord, roles in [
            ("Birby | 418th Technical Goose",None,
             "Bug Testing  \u2022  Suggestions  \u2022  Program Icon"),
             ("ShadyWizard",
              "ShadyWizard | 418th LinuxAdviser",
              "Github Contributions")
        ]:
            tk.Label(body, text=name,
                     font=('Segoe UI', 11, 'bold'), bg=bg, fg=fg).pack(anchor='w', pady=(6, 0))
            if discord:
                tk.Label(body, text=discord, 
                     font=('Segoe UI', 9), bg=bg, fg="#888").pack(anchor='w')
            tk.Label(body, text=roles,
                     font=('Segoe UI', 9), bg=bg, fg="#888").pack(anchor='w')

        tk.Frame(body, bg=bg3, height=1).pack(fill=tk.X, pady=(14, 14))

        tk.Label(body, text="Built for the Helldivers 2 community \U0001f985",
                 font=('Segoe UI', 9, 'italic'), bg=bg, fg="#888").pack(anchor='w')

        btn_row = tk.Frame(dialog, bg=bg)
        btn_row.pack(fill=tk.X, padx=30, pady=(0, 16))
        ttk.Button(btn_row, text="⟳ Check for Updates",
                   command=lambda: self._manual_update_check()
                   ).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Close",
                   command=lambda: (setattr(self, '_about_window', None), dialog.destroy())
                   ).pack(side=tk.RIGHT)

    def _setup_ui(self):
        flag = " [DEBUG]" if self.debug_mode else ""
        self.root.title(f"RESYNC.ERR v{CURRENT_VERSION} - {self.analyzer.path.name}{flag}")
        self.root.geometry("1440x900")
        self.root.minsize(1440, 900)
        _prev_left_width = getattr(self, '_user_left_width', None)

        for widget in self.root.winfo_children():
            widget.destroy()


        try:
            import sys as _sys, os as _os
            if getattr(_sys, 'frozen', False):
                self.root.iconbitmap(_sys.executable)
            else:
                _p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'assets', 'icon.ico')
                if _os.path.exists(_p):
                    self.root.iconbitmap(_p)
        except Exception:
            pass
        self.root.bind("<Control-F8>", lambda e: self._toggle_debug())
        self.root.bind("<Control-c>", lambda e: self._copy_png_to_clipboard())
        self.root.bind("<Control-h>", lambda e: self._launch_stratagem_hero())

        def _on_root_configure(e):
            if e.widget is not self.root:
                return
            try:
                self.root.update_idletasks()
            except Exception:
                pass
        self.root.bind("<Configure>", _on_root_configure, add="+")
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        _left_width = 370
        if _prev_left_width and 150 <= _prev_left_width <= 900:
            _left_width = _prev_left_width
        self._pending_left_width = _left_width
        self.left = ttk.Frame(self.paned, padding="10", width=_left_width)
        self.left.pack_propagate(False)
        self.paned.add(self.left, weight=1)

        top = ttk.Frame(self.left)
        top.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(top, text="DASHBOARD", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        ttk.Button(top, text="ℹ About", command=self._open_about).pack(side=tk.RIGHT)
        ttk.Button(top, text="Theme", command=self._open_theme_editor).pack(side=tk.RIGHT, padx=(0, 4))
        self._tooltip_btn = ttk.Button(top, text="Tooltip: ON" if getattr(self, "_tooltip_enabled", True) else "Tooltip: OFF", width=16,
                                       command=self._toggle_tooltip)
        self._tooltip_btn.pack(side=tk.RIGHT, padx=(0, 4))
        mode_f = ttk.LabelFrame(self.left, text=" View Settings ", padding=8)
        mode_f.pack(fill=tk.X, pady=5)
        btn_row1 = ttk.Frame(mode_f)
        btn_row1.pack(fill=tk.X, pady=2)
        self.multi_btn = ttk.Button(btn_row1, text="📊 Multi: ON" if self.multi_mode else "📊 Multi: OFF", command=self._toggle_multi)
        self.multi_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self.delta_btn = ttk.Button(btn_row1, text="Δ Delta: ON" if self.delta_mode else "Δ Delta: OFF", command=self._toggle_delta)
        self.delta_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        btn_row2b = ttk.Frame(mode_f)
        btn_row2b.pack(fill=tk.X, pady=2)
        self.session_cmp_btn = ttk.Button(btn_row2b,
            text="📊 Session Compare: ON" if self.session_compare_active else "📊 Session Compare",
            command=self._toggle_session_compare)
        self.session_cmp_btn.pack(fill=tk.X, padx=1)

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
        _t_ps = self._get_theme()
        self.preset_scroll = tk.Scrollbar(preset_master_f, orient="vertical", command=self.preset_canvas.yview,
                                          bg=_t_ps["bg3"], troughcolor=_t_ps["bg"], activebackground=_t_ps["accent"])
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

        btn_frame = ttk.Frame(self.left)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 2))
        ttk.Button(btn_frame, text="New CSV", command=self._import_new_csv).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_frame, text="Clear", command=self._clear_all).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_frame, text="Export PNG", command=self._export, style="Action.TButton").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_frame, text="📄 HTML Report", command=self._export_html_report, style="Action.TButton").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        search_f = ttk.LabelFrame(self.left, text=" Sensor Selection ", padding=8)
        search_f.pack(fill=tk.BOTH, expand=True, pady=5)

        self.filter_btn = ttk.Button(search_f, text="🚨 Detect Out-of-Spec Issues", style="Issue.TButton", command=self._toggle_filter)
        self.filter_btn.pack(fill=tk.X, pady=(0, 4))

        _bg = self._get_theme()["bg"]
        self._diag_row_frame = tk.Frame(search_f, bg=_bg)
        self._diag_row_frame.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(self._diag_row_frame, text="🔬 Diagnose Hardware Signatures",
                   command=self._open_diagnosis,
                   style="Action.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._sig_badge_var = tk.StringVar(value="⏳")
        self._sig_badge_lbl = None

        self._badge_crit_lbl = tk.Label(self._diag_row_frame, text="", font=('Segoe UI', 8, 'bold'),
                                         bg=_bg, fg="#ff4d4d", padx=3)
        self._badge_warn_lbl = tk.Label(self._diag_row_frame, text="", font=('Segoe UI', 8, 'bold'),
                                         bg=_bg, fg="#f59e0b", padx=3)
        self._badge_info_lbl = tk.Label(self._diag_row_frame, text="", font=('Segoe UI', 8, 'bold'),
                                         bg=_bg, fg="#38bdf8", padx=3)
        self._badge_ok_lbl   = tk.Label(self._diag_row_frame, text="⏳", font=('Segoe UI', 8),
                                         bg=_bg, fg="#888", padx=3)

        self._badge_ok_lbl.pack(side=tk.RIGHT)
        self._badge_info_lbl.pack(side=tk.RIGHT)
        self._badge_warn_lbl.pack(side=tk.RIGHT)
        self._badge_crit_lbl.pack(side=tk.RIGHT)

        ttk.Button(search_f, text="🖥 View Detected Hardware", command=self._open_hardware_info).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(search_f, text="⚙ Settings", command=self._open_limits_editor).pack(fill=tk.X, pady=(0, 8))

        self._sig_dirty = True
        self._start_sig_watcher()

        search_top = ttk.Frame(search_f)
        search_top.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_top, text="🔍 Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._filter_sensors())
        ttk.Entry(search_top, textvariable=self.search_var).pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.canv_f = ttk.Frame(search_f)
        self.canv_f.pack(fill=tk.BOTH, expand=True)
        self.canvas_checklist = tk.Canvas(self.canv_f, highlightthickness=0)
        _t_sc = self._get_theme()
        self.sc_checklist = tk.Scrollbar(self.canv_f, orient="vertical", command=self.canvas_checklist.yview,
                                         bg=_t_sc["bg3"], troughcolor=_t_sc["bg"], activebackground=_t_sc["accent"])
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

        self._sash_press_pos = None
        def _on_sash_press(e):
            try:
                self._sash_press_pos = self.paned.sashpos(0)
            except Exception:
                self._sash_press_pos = None

        def _on_sash_release(e):
            self.canvas_checklist.after(50, _refresh_scrollregion)
            try:
                new_pos = self.paned.sashpos(0)
            except Exception:
                return
            if self._sash_press_pos is not None and new_pos != self._sash_press_pos:
                self._user_left_width = new_pos
            self._sash_press_pos = None

        self.paned.bind("<ButtonPress-1>", _on_sash_press, add="+")

        self.scroll_frame.bind("<Configure>", lambda e: _refresh_scrollregion())
        self.canvas_checklist.bind("<Configure>", _on_checklist_canvas_configure)
        self.paned.bind("<ButtonRelease-1>", _on_sash_release)
        self.canvas_checklist.configure(yscrollcommand=self.sc_checklist.set)

        def _on_checklist_mw(event):
            self.canvas_checklist.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas_checklist.bind("<Enter>", lambda _: self.canvas_checklist.bind_all("<MouseWheel>", _on_checklist_mw))
        self.canvas_checklist.bind("<Leave>", lambda _: self.canvas_checklist.unbind_all("<MouseWheel>"))
        self.canvas_checklist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sc_checklist.pack(side=tk.RIGHT, fill=tk.Y)
        self._build_checklist()
        self.right = ttk.Frame(self.paned, padding="5")
        self.paned.add(self.right, weight=4)
        self.root.update_idletasks()
        try:
            self.paned.sashpos(0, self._pending_left_width)
        except Exception:
            pass
        def _on_paned_configure(event):
            try:
                target = self._pending_left_width
                current = self.paned.sashpos(0)
                if current < target:
                    self.paned.sashpos(0, target)
            except Exception:
                pass
        self.paned.bind("<Configure>", _on_paned_configure, add="+")
        if hasattr(self, 'canvas_widget') and self.canvas_widget:
            for cid in (getattr(self, '_cid_move', None), getattr(self, '_cid_leave', None)):
                if cid is not None:
                    try:
                        self.canvas_widget.mpl_disconnect(cid)
                    except Exception:
                        pass
            self._cid_move = None
            self._cid_leave = None
            try:
                self.canvas_widget.toolbar = None
            except Exception:
                pass
            try:
                self.canvas_widget.get_tk_widget().destroy()
            except Exception:
                pass
            self.canvas_widget = None

        if hasattr(self, 'fig') and self.fig:
            try:
                self.fig.canvas.toolbar = None
            except Exception:
                pass
            self.fig.clf()
            self.fig = None

        _t_init = self._get_theme()
        _legend_bg = _t_init.get("bg2", "#1e1e1e")
        _legend_fg = _t_init.get("fg", "#ffffff")
        _toolbar_bg = _t_init.get("bg", "#121212")

        toolbar_f = tk.Frame(self.right, bg=_toolbar_bg, highlightthickness=0, bd=0)
        toolbar_f.pack(side=tk.TOP, fill=tk.X)
        self._toolbar_f = toolbar_f

        _plot_container = tk.Frame(self.right, bg=_legend_bg,
                                   highlightthickness=0, bd=0)
        _plot_container.pack(fill=tk.BOTH, expand=True)
        _plot_container.grid_rowconfigure(0, weight=1)
        _plot_container.grid_columnconfigure(0, weight=1)
        _plot_container.grid_columnconfigure(1, weight=0)

        self._legend_panel = tk.Frame(_plot_container, width=185, bg=_legend_bg,
                                      highlightthickness=0, bd=0)
        self._legend_panel.grid(row=0, column=1, sticky='ns')
        self._legend_panel.pack_propagate(False)

        self._legend_title = tk.Label(self._legend_panel, text="Legend",
                                      font=('Segoe UI', 8, 'bold'), anchor='w',
                                      bg=_legend_bg, fg=_legend_fg)
        self._legend_title.pack(fill=tk.X, padx=4, pady=(4, 0))

        _leg_scroll_frame = tk.Frame(self._legend_panel, bg=_legend_bg,
                                     highlightthickness=0, bd=0)
        _leg_scroll_frame.pack(fill=tk.BOTH, expand=True)
        self._legend_scroll_frame = _leg_scroll_frame

        self._legend_canvas = tk.Canvas(_leg_scroll_frame, highlightthickness=0, bd=0,
                                        bg=_legend_bg)
        _leg_vsb = tk.Scrollbar(_leg_scroll_frame, orient='vertical',
                                command=self._legend_canvas.yview,
                                bg=_t_init.get("bg3","#2a2a2a"),
                                troughcolor=_t_init.get("bg2","#1e1e1e"),
                                activebackground=_t_init.get("accent","#1f6aa5"))
        self._legend_canvas.configure(yscrollcommand=_leg_vsb.set)
        _leg_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._legend_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._legend_vsb = _leg_vsb

        self._legend_inner = tk.Frame(self._legend_canvas)
        self._legend_inner_id = self._legend_canvas.create_window(
            (0, 0), window=self._legend_inner, anchor='nw')

        def _on_leg_configure(e):
            self._legend_canvas.configure(scrollregion=self._legend_canvas.bbox('all'))
            self._legend_canvas.itemconfig(self._legend_inner_id,
                                           width=self._legend_canvas.winfo_width())
        self._legend_inner.bind('<Configure>', _on_leg_configure)
        self._legend_canvas.bind('<Configure>', lambda e: self._legend_canvas.itemconfig(
            self._legend_inner_id, width=e.width))

        def _on_leg_scroll(e):
            self._legend_canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')
        self._legend_canvas.bind('<MouseWheel>', _on_leg_scroll)
        self._legend_inner.bind('<MouseWheel>', _on_leg_scroll)

        self.fig = Figure(figsize=(10, 6))
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=_plot_container)
        self._cid_move   = self.canvas_widget.mpl_connect('motion_notify_event', self._on_mouse_move)
        self._cid_leave  = self.canvas_widget.mpl_connect('axes_leave_event',    self._on_mouse_leave)
        self._cid_click  = self.canvas_widget.mpl_connect('button_press_event',  self._on_plot_click)
        self._cid_pick   = self.canvas_widget.mpl_connect('pick_event',          self._on_legend_pick)
        self._pinned_line = None

        self.toolbar = _NoHistoryToolbar(self.canvas_widget, toolbar_f, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=tk.LEFT)
        self._style_mpl_toolbar()

        self.canvas_widget.get_tk_widget().configure(
            highlightthickness=0, bd=0, bg=_t_init.get("bg", "#121212"))
        self.canvas_widget.get_tk_widget().grid(row=0, column=0, sticky='nsew')

    def _manual_update_check(self):
        """Called when the user clicks ⟳ - always gives feedback, respects ignore/disable via on_ignore/on_disable."""
        self.show_toast("Checking for updates...")
        check_for_updates(
            self.root,
            ignored_version="",
            updates_disabled=False,
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

        ui_order = ["Temperatures (°C)", "Utilization / Load (%)", "Clock Speeds (MHz)", "Power / Wattage (W)", "Voltage (V)", "Fan Speeds (RPM)", "Frame Times / Latency (ms)", "Frame Rate (FPS)"]
        self.sorted_cats = [c for c in ui_order if c in self.group_map] +\
                           sorted([c for c in self.group_map.keys() if c not in ui_order])

        for cat in self.sorted_cats:
            h = tk.Label(self.scroll_frame, text=f" {cat.upper()} ", font=('Segoe UI', 8, 'bold'), anchor="w")
            h.pack(fill=tk.X, pady=(8, 2))
            self.header_widgets[cat] = h
            for col in sorted(self.group_map[cat]):
                v = self.vars.get(col, tk.BooleanVar(value=False))
                self.vars[col] = v
                def _make_cb_cmd(col_name, var):
                    def _cmd():
                        pinned = getattr(self, '_pinned_line', None)
                        if pinned and pinned != col_name:

                            var.set(False)
                            self.show_toast(f'Unpin "{pinned[:30]}" first')
                            return
                        if pinned and pinned == col_name and not var.get():

                            self._pinned_line = None
                        self.update_plot()
                    return _cmd
                cb = ttk.Checkbutton(self.scroll_frame, text=col, variable=v,
                                     command=_make_cb_cmd(col, v),
                                     style="Alert.TCheckbutton" if self._is_critical(col) else "TCheckbutton")
                cb.pack(anchor=tk.W, padx=12)
                self.cb_widgets[col] = cb

    def _get_category(self, n: str) -> str:
        u = n.upper()
        if 'MS' in u or 'FRAME TIME' in u or 'LATENCY' in u or 'WAIT' in u: return "Frame Times / Latency (ms)"
        if 'FPS' in u or 'FRAME RATE' in u: return "Frame Rate (FPS)"
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
        _t = self._get_theme(); bg = _t["bg"]; fg = _t["fg"]; accent = _t["accent"]
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
                self.custom_groups[imported_name] = sensors
                self._save_config()
                self._refresh_group_buttons()
                self.show_toast(f"Imported: '{imported_name}'")
                return

            dialog = tk.Toplevel(self.root)
            dialog.title("Name Already Exists")
            dialog.resizable(False, False)
            dialog.grab_set()
            dialog.attributes("-topmost", True)

            try:
                is_dark = self.is_dark
            except Exception:
                is_dark = False
            _t = self._get_theme(); bg = _t["bg"]; fg = _t["fg"]; accent = _t["accent"]

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
        if not path:
            return
        self._load_csv_threaded(path, on_success=self._apply_new_csv)

    def _teardown(self):
        if self._sig_watcher_id:
            self.root.after_cancel(self._sig_watcher_id)
            self._sig_watcher_id = None

        if hasattr(self, 'canvas_widget') and self.canvas_widget:
            for cid in (getattr(self, '_cid_move', None), getattr(self, '_cid_leave', None), getattr(self, '_timeline_cid', None), getattr(self, '_timeline_mov_cid', None)):
                if cid is not None:
                    try:
                        self.canvas_widget.mpl_disconnect(cid)
                    except Exception:
                        pass
            self._cid_move = None
            self._cid_leave = None
            self._timeline_cid = None
            self._timeline_mov_cid = None

        def _clear_var(v):
            try:
                for mode, cbname in v.trace_info():
                    v.trace_remove(mode, cbname)
            except Exception:
                pass

        for v in getattr(self, 'vars', {}).values():
            _clear_var(v)
        self.vars = {}

        for attr in ('name_var', 'search_var', '_sig_badge_var'):
            v = getattr(self, attr, None)
            if v is not None:
                _clear_var(v)
                setattr(self, attr, None)

    def _apply_new_csv(self, new_analyzer):
        """Called on the main thread once a new CSV has loaded successfully."""
        self._teardown()
        self.analyzer = new_analyzer
        self.df = self.analyzer.df
        self._invalidate_x_cache()
        new_cols = set(self.df.columns)
        for col, var in list(self.vars.items()):
            if col not in new_cols:
                var.set(False)
        self.filter_active         = False
        self._sig_hits             = []
        self._sig_dirty            = True
        self._sig_timeline_x_vals  = None
                                                                      
        self.session_compare_active = False
        self.sessions               = []
        self._cmp_widget            = None
        self._cmp_fig               = None
        self._cmp_canvas            = None
        self._setup_ui()
        self._apply_theme_colors()
        self.update_plot()
        self.root.after(300, self._prompt_sensor_aliases)
        if self.debug_mode:
            self._open_debug_window()

    def _load_csv_threaded(self, path: str, on_success, on_error=None):
        """Show a spinner dialog, load the CSV in a background thread,
        then call on_success(analyzer) or on_error(exc) on the main thread."""
        import threading

        is_dark = self.is_dark
        _t = self._get_theme(); bg_dark = _t["bg"]; bg = _t["bg"]; fg = _t["fg"]; accent = _t["accent"]

        wait_win = tk.Toplevel(self.root)
        wait_win.title("Loading CSV")
        wait_win.resizable(False, False)
        wait_win.protocol("WM_DELETE_WINDOW", lambda: None)
        wait_win.configure(bg=bg_dark)
        self.root.update_idletasks()
        pw, ph = 340, 120
        rx = self.root.winfo_x() + (self.root.winfo_width()  // 2) - pw // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() // 2) - ph // 2
        wait_win.geometry(f"{pw}x{ph}+{rx}+{ry}")
        wait_win.transient(self.root)
        wait_win.grab_set()

        muted_fg = _t.get("bg3", "#888")
        outer = tk.Frame(wait_win, bg=accent, padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg=bg, padx=20, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        title_row = tk.Frame(inner, bg=bg)
        title_row.pack(anchor='w')
        tk.Label(title_row, text="📂  Loading CSV",
                 font=('Segoe UI', 11, 'bold'), bg=bg, fg=fg).pack(side=tk.LEFT)
        spin_var = tk.StringVar(value=" ⠋")
        tk.Label(title_row, textvariable=spin_var,
                 font=('Segoe UI', 11), bg=bg, fg=accent).pack(side=tk.LEFT, padx=(6, 0))

        fname = path.replace('\\', '/').split('/')[-1]
        tk.Label(inner, text=fname, font=('Segoe UI', 9), bg=bg,
                 fg=muted_fg, anchor='w').pack(fill=tk.X, pady=(6, 0))

        bar_frame = tk.Frame(inner, bg=bg)
        bar_frame.pack(fill=tk.X, pady=(8, 0))
        bar_bg = tk.Frame(bar_frame, bg=muted_fg, height=4, bd=0)
        bar_bg.pack(fill=tk.X)
        bar_fg = tk.Frame(bar_bg, bg=accent, height=4, bd=0)
        bar_fg.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        _bar_pos  = [0.0]
        _bar_dir  = [1]
        _bar_step = 0.06
        def _tick_bar():
            if not wait_win.winfo_exists():
                return
            _bar_pos[0] += _bar_step * _bar_dir[0]
            if _bar_pos[0] >= 0.85:
                _bar_dir[0] = -1
            elif _bar_pos[0] <= 0.0:
                _bar_dir[0] = 1
            bar_fg.place(relwidth=min(_bar_pos[0], 1.0))
            wait_win.after(40, _tick_bar)
        _tick_bar()

        _SPIN = [" ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏"]
        _si   = [0]
        def _tick_spin():
            if not wait_win.winfo_exists():
                return
            _si[0] = (_si[0] + 1) % len(_SPIN)
            spin_var.set(_SPIN[_si[0]])
            wait_win.after(80, _tick_spin)
        _tick_spin()

        def _close():
            if wait_win.winfo_exists():
                wait_win.grab_release()
                wait_win.destroy()

        def _worker():
            _tk_refs = [spin_var, wait_win, bar_fg, bar_bg, bar_frame, inner, outer]

            def _release_tk_refs():
                _tk_refs.clear()

            try:
                analyzer = TelemetryAnalyzer(path)
                analyzer.load()
                def _done():
                                                                             
                                                                             
                                                                             
                                                                         
                                                                    
                                                                           
                                                    
                    try:
                        on_success(analyzer)
                    finally:
                        _close()
                        _release_tk_refs()
                self.root.after(0, _done)
            except Exception as exc:
                _captured_exc = exc
                def _fail():
                    _close()
                    _release_tk_refs()
                    if on_error:
                        on_error(_captured_exc)
                    else:
                        messagebox.showerror("Load Error", str(_captured_exc))
                self.root.after(0, _fail)

        threading.Thread(target=_worker, daemon=True).start()

    def _clear_all(self):
        _prev = self.session_compare_active
        self.session_compare_active = False
        for v in self.vars.values():
            v.set(False)
        self.session_compare_active = _prev
        self.update_plot()
    def _render_composite_png(self, dpi=150):
        import io
        from PIL import Image, ImageGrab

        buf = io.BytesIO()
        self.fig.savefig(buf, format='png', dpi=dpi,
                         bbox_inches='tight',
                         facecolor=self.fig.get_facecolor())
        buf.seek(0)
        fig_img = Image.open(buf).convert('RGB')

        legend_img = None
        try:
            panel = self._legend_panel
            panel.update_idletasks()
            x = panel.winfo_rootx()
            y = panel.winfo_rooty()
            w = panel.winfo_width()
            h = panel.winfo_height()
            if w > 10 and h > 10:
                legend_img = ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert('RGB')
                legend_img = legend_img.resize(
                    (int(legend_img.width * dpi / 96),
                     int(legend_img.height * dpi / 96)),
                    Image.LANCZOS)
        except Exception:
            legend_img = None

        if legend_img is None:
            return fig_img

        total_w = fig_img.width + legend_img.width
        total_h = max(fig_img.height, legend_img.height)
        bg_col = tuple(int(self.fig.get_facecolor()[i] * 255) for i in range(3))
        composite = Image.new('RGB', (total_w, total_h), bg_col)
        composite.paste(fig_img, (0, 0))
        composite.paste(legend_img, (fig_img.width, 0))
        return composite

    def _export(self):
        f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if f:
            try:
                from PIL import Image
                img = self._render_composite_png(dpi=300)
                img.save(f)
            except ImportError:
                self.fig.savefig(f, dpi=300, bbox_inches='tight',
                                 facecolor=self.fig.get_facecolor())

    def _copy_png_to_clipboard(self):
        try:
            import io, sys, ctypes
            from PIL import Image

            img = self._render_composite_png(dpi=150)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)

            if sys.platform == 'win32':
                k32 = ctypes.windll.kernel32
                u32 = ctypes.windll.user32
                k32.GlobalAlloc.restype  = ctypes.c_void_p
                k32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
                k32.GlobalLock.restype   = ctypes.c_void_p
                k32.GlobalLock.argtypes  = [ctypes.c_void_p]
                k32.GlobalUnlock.argtypes = [ctypes.c_void_p]
                u32.SetClipboardData.restype  = ctypes.c_void_p
                u32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

                img = Image.open(buf).convert('RGB')
                output = io.BytesIO()
                img.save(output, 'BMP')

                data = output.getvalue()[14:]

                u32.OpenClipboard.argtypes = [ctypes.c_void_p]
                u32.OpenClipboard.restype  = ctypes.c_bool
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                import time as _time
                for _attempt in range(5):
                    if u32.OpenClipboard(hwnd):
                        break
                    _time.sleep(0.05)
                else:
                    self.show_toast('Clipboard locked – try again')
                    return
                u32.EmptyClipboard()
                h = k32.GlobalAlloc(0x0042, len(data))
                ptr = k32.GlobalLock(h)
                ctypes.memmove(ptr, data, len(data))
                k32.GlobalUnlock(h)
                u32.SetClipboardData(8, h)
                u32.CloseClipboard()
                self.show_toast("Chart copied to clipboard")
            else:
                self.show_toast("Clipboard copy is Windows-only; use 💾 PNG instead")
        except Exception as e:
            self.show_toast(f"Copy failed: {e}")

    def _clear_cursors(self):
        self._last_cursor_idx = -1
        for line in self.cursor_lines:
            try: line.remove()
            except: pass
        self.cursor_lines = []
        if self.cursor_text:
            try: self.cursor_text.remove()
            except: pass
            self.cursor_text = None
        if hasattr(self, '_line_annotation') and self._line_annotation:
            try: self._line_annotation.remove()
            except: pass
            self._line_annotation = None
        if hasattr(self, '_prev_highlight') and self._prev_highlight:
            try:
                self._prev_highlight.set_linewidth(self._prev_highlight_lw)
                self._prev_highlight.set_zorder(self._prev_highlight_z)
            except: pass
            self._prev_highlight = None

    def _on_mouse_leave(self, event):
        self._last_cursor_idx = -1
        self._clear_cursors()
        self.canvas_widget.draw_idle()

    def _update_tk_legend(self, entries):
        """Rebuild the Tkinter legend panel. entries = list of (label, color, col_name, is_header)."""
        if not hasattr(self, '_legend_inner'):
            return
        t = self._get_theme()
        bg     = t["bg"]
        bg2    = t["bg2"]
        bg3    = t["bg3"]
        fg     = t["fg"]
        accent = t["accent"]

        self._legend_panel.configure(bg=bg2)
        self._legend_title.configure(bg=bg2, fg=accent)

        if hasattr(self, '_legend_scroll_frame'):
            try: self._legend_scroll_frame.destroy()
            except Exception: pass

        scroll_f = tk.Frame(self._legend_panel, bg=bg2)
        scroll_f.pack(fill=tk.BOTH, expand=True)
        self._legend_scroll_frame = scroll_f

        self._legend_canvas = tk.Canvas(scroll_f, highlightthickness=0, bd=0, bg=bg2)
        vsb = tk.Scrollbar(scroll_f, orient='vertical', command=self._legend_canvas.yview,
                           bg=bg3, troughcolor=bg2, activebackground=accent)
        self._legend_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._legend_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._legend_vsb = vsb

        self._legend_inner = tk.Frame(self._legend_canvas, bg=bg2)
        self._legend_inner_id = self._legend_canvas.create_window(
            (0, 0), window=self._legend_inner, anchor='nw')

        def _on_leg_configure(e):
            self._legend_canvas.configure(scrollregion=self._legend_canvas.bbox('all'))
            w = self._legend_canvas.winfo_width()
            if w > 1:
                self._legend_canvas.itemconfig(self._legend_inner_id, width=w)
        self._legend_inner.bind('<Configure>', _on_leg_configure)
        self._legend_canvas.bind('<Configure>', lambda e: self._legend_canvas.itemconfig(
            self._legend_inner_id, width=e.width) if e.width > 1 else None)

        def _on_scroll(e):
            self._legend_canvas.yview_scroll(int(-1*(e.delta/120)), 'units')
        self._legend_canvas.bind('<MouseWheel>', _on_scroll)
        self._legend_inner.bind('<MouseWheel>', _on_scroll)

        pinned = getattr(self, '_pinned_line', None)

        for entry in entries:
            label, color, col_name, is_header = entry[0], entry[1], entry[2], entry[3]
            linestyle = entry[4] if len(entry) > 4 else '-'
            if is_header:
                hl = tk.Label(self._legend_inner, text=label, font=('Segoe UI', 8, 'bold'),
                              bg=bg2, fg=accent, anchor='w', padx=4)
                hl.pack(fill=tk.X, pady=(6, 1))
                hl.bind('<MouseWheel>', lambda e: self._legend_canvas.yview_scroll(
                    int(-1*(e.delta/120)), 'units'))
                tk.Frame(self._legend_inner, bg=bg3, height=1).pack(fill=tk.X, padx=4)
                continue

            is_pinned = (pinned == col_name)

            cell = tk.Frame(self._legend_inner, bg=bg2, cursor='hand2')
            cell.pack(fill=tk.X, padx=2, pady=1)

            row = tk.Frame(cell, bg=bg2)
            row.pack(fill=tk.X)

            SWATCH_W, SWATCH_H = 28, 12
            swatch = tk.Canvas(row, width=SWATCH_W, height=SWATCH_H,
                               bg=bg2, highlightthickness=0, bd=0)
            swatch.pack(side=tk.LEFT, padx=(4, 4), pady=3)

            _dash_map = {
                '-':   '',
                '--':  (4, 2),
                ':':   (1, 2),
                '-.':  (4, 2, 1, 2),
                'solid':      '',
                'dashed':     (4, 2),
                'dotted':     (1, 2),
                'dashdot':    (4, 2, 1, 2),
            }
            _dash = _dash_map.get(linestyle, '')
            mid_y = SWATCH_H // 2

            def _rgb_to_hex(col):
                if isinstance(col, str):
                    return col
                if isinstance(col, (tuple, list)) and len(col) >= 3:
                    return '#{:02x}{:02x}{:02x}'.format(
                        int(col[0] * 255) if col[0] <= 1.0 else int(col[0]),
                        int(col[1] * 255) if col[1] <= 1.0 else int(col[1]),
                        int(col[2] * 255) if col[2] <= 1.0 else int(col[2])
                    )
                return '#888888'

            _kw = dict(fill=_rgb_to_hex(color), width=2)
            if _dash:
                _kw['dash'] = _dash
            swatch.create_line(2, mid_y, SWATCH_W - 2, mid_y, **_kw)

            name_line, *stats_parts = label.split('\n')
            name_line = name_line.strip().lstrip('✓ ')
            lbl_text = ('📌 ' if is_pinned else '') + name_line
            lbl = tk.Label(row, text=lbl_text,
                           font=('Segoe UI', 8, 'bold' if is_pinned else 'normal'),
                           bg=bg2, fg=fg, anchor='w', wraplength=120, justify='left')
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            if stats_parts:
                stats_lbl = tk.Label(cell, text=stats_parts[0].strip(),
                                     font=('Segoe UI', 8, 'bold'), bg=bg2,
                                     fg=accent if is_pinned else fg,
                                     anchor='w', padx=20, wraplength=135, justify='left')
                stats_lbl.pack(fill=tk.X)

            hover_widgets = [cell, row, lbl] + ([stats_lbl] if stats_parts else [])

            _inside = [0]

            def _on_enter(e, ws=hover_widgets, counter=_inside, sw=swatch):
                counter[0] += 1
                for w in ws:
                    try: w.configure(bg=bg3)
                    except Exception: pass
                try: sw.configure(bg=bg3)
                except Exception: pass

            def _on_leave(e, ws=hover_widgets, counter=_inside, c=cell, sw=swatch):
                counter[0] -= 1
                def _maybe_reset():
                    if counter[0] <= 0:
                        counter[0] = 0
                        for w in ws:
                            try: w.configure(bg=bg2)
                            except Exception: pass
                        try: sw.configure(bg=bg2)
                        except Exception: pass
                c.after(20, _maybe_reset)

            def _on_click(e, cn=col_name):
                cur_pin = getattr(self, '_pinned_line', None)
                if cur_pin == cn:
                    self._pinned_line = None
                    self.show_toast('Unpinned')
                else:
                    self._pinned_line = cn
                    self.show_toast(f'Pinned: {cn[:40]}')
                self.update_plot()

            def _on_scroll(e, lc=self._legend_canvas):
                lc.yview_scroll(int(-1 * (e.delta / 120)), 'units')

            bind_widgets = [cell, row, swatch, lbl] + ([stats_lbl] if stats_parts else [])
            for w in bind_widgets:
                w.bind('<Enter>',      _on_enter)
                w.bind('<Leave>',      _on_leave)
                w.bind('<Button-1>',   _on_click)
                w.bind('<MouseWheel>', _on_scroll)

        _legend_canvas_ref   = self._legend_canvas
        _legend_inner_id_ref = self._legend_inner_id
        if not hasattr(self, '_legend_finalize_log'):
            self._legend_finalize_log = []
        _log = self._legend_finalize_log
        _log.clear()

        def _finalize_legend(retry=5):
            try:
                canvas   = _legend_canvas_ref
                inner_id = _legend_inner_id_ref
                if not canvas.winfo_exists():
                    _log.append(f"retry={retry}: canvas destroyed, giving up")
                    return
                w    = canvas.winfo_width()
                bbox = canvas.bbox('all')
                _log.append(f"retry={retry}: winfo_width={w}  bbox={bbox}  "
                            f"items={len(canvas.find_all())}  "
                            f"inner_children={len(self._legend_inner.winfo_children()) if hasattr(self,'_legend_inner') and self._legend_inner.winfo_exists() else '?'}")
                if bbox and w > 1 and bbox[3] > 1:
                    canvas.configure(scrollregion=bbox)
                    canvas.itemconfig(inner_id, width=w)
                    canvas.yview_moveto(0)
                    _log.append(f"retry={retry}: SUCCESS - scrollregion={bbox}  width={w}")
                elif bbox and w > 1 and bbox[3] <= 1:
                    canvas.configure(scrollregion=bbox)
                    canvas.itemconfig(inner_id, width=w)
                    canvas.yview_moveto(0)
                    _log.append(f"retry={retry}: SUCCESS (empty legend - no sensors selected)")
                elif retry > 0:
                    canvas.after(50, lambda: _finalize_legend(retry - 1))
                else:
                    _log.append(f"retry=0: FAILED - bbox={bbox}  width={w}")
            except Exception as _fe:
                _log.append(f"retry={retry}: EXCEPTION {_fe}")
        _legend_canvas_ref.after_idle(_finalize_legend)

    def _on_legend_pick(self, event):
        """Click a legend entry to pin/unpin that sensor."""
        artist = event.artist
        try:
            label = artist.get_label()
        except Exception:
            return
        if not label or label.startswith('_') or label.startswith('──'):
            return
        col_name = label.split('\n')[0].strip()

        col_name = col_name.lstrip(' ✓')
        if not col_name or col_name not in self.df.columns:
            return
        if self._pinned_line == col_name:
            self._pinned_line = None
            self.show_toast('Unpinned')
        else:
            self._pinned_line = col_name
            self.show_toast(f'Pinned: {col_name[:40]}')
        self._last_cursor_idx = -1
        self.update_plot()

    def _on_plot_click(self, event):
        """Left-click to pin a line; right-click to unpin."""
        if event.inaxes is None:
            return

        if event.button == 3:
            if self._pinned_line:
                self._pinned_line = None
                self.show_toast("Unpinned")
                self.update_plot()
            return
        if event.button != 1:
            return

        if event.inaxes is getattr(self, '_sig_timeline_ax', None):
            return
        plot_axes = [a for a in self.fig.axes if a is not getattr(self, '_sig_timeline_ax', None)]
        ax = event.inaxes if event.inaxes in plot_axes else None
        if ax is None or event.ydata is None:
            return
        try:
            ylim = ax.get_ylim()
            y_range = max(abs(ylim[1] - ylim[0]), 1e-9)

            x_vals = getattr(self, '_last_x_vals', None)
            if x_vals is not None and len(x_vals):
                idx = int(np.argmin(np.abs(x_vals - event.xdata)))
            else:
                idx = 0
            closest_line, closest_dist = None, float('inf')
            for line in ax.get_lines():
                lbl = line.get_label()
                if lbl.startswith('_') or lbl.startswith('REF:'):
                    continue
                ydata = line.get_ydata()
                if not len(ydata): continue
                yi = min(idx, len(ydata) - 1)
                nd = abs(float(ydata[yi]) - float(event.ydata)) / y_range
                if nd < closest_dist:
                    closest_dist, closest_line = nd, line
            if closest_line and closest_dist < 0.10:
                col_name = closest_line.get_label().split('\n')[0].strip()
                if self._pinned_line == col_name:

                    self._pinned_line = None
                    self.show_toast("Unpinned")
                else:
                    self._pinned_line = col_name
                    self.show_toast(f"Pinned: {col_name[:40]}")
                self.update_plot()
            else:
                if self._pinned_line:
                    self._pinned_line = None
                    self.update_plot()
        except Exception:
            pass

    def _on_mouse_move(self, event):
        if event.inaxes is None:
            self._on_mouse_leave(event)
            return
        try:
            fc = getattr(self, '_hover_fc', '#252525' if self.is_dark else 'white')
            tc = getattr(self, '_hover_tc', 'white' if self.is_dark else 'black')
            cursor_color = getattr(self, '_hover_cursor_color', 'white' if self.is_dark else 'gray')

            if self.heatmap_mode and hasattr(self, '_heatmap_sel') and self._heatmap_sel:
                x_vals = self._heatmap_x_vals
                idx = int(np.argmin(np.abs(x_vals - event.xdata)))
                sensor_idx = int(round(event.ydata))
                cache_key = (idx, sensor_idx)
                if cache_key == getattr(self, '_last_cursor_idx', None):
                    return
                self._last_cursor_idx = cache_key
                if 0 <= idx < len(x_vals) and 0 <= sensor_idx < len(self._heatmap_sel):
                    col = self._heatmap_sel[sensor_idx]
                    val = self._heatmap_matrix_raw[col][idx]
                    self._clear_cursors()
                    ax = event.inaxes
                    for a in self.fig.axes:
                        self.cursor_lines.append(a.axvline(x=x_vals[idx],
                            color=cursor_color, ls='--', alpha=0.5))
                    x_label = self._format_elapsed(x_vals[idx]) if self.time_mode else f"Rec: {idx}"
                    txt = f"{x_label}\n{col[:35]}: {val:.2f}"
                    if getattr(self, '_tooltip_enabled', True):
                        self.cursor_text = self.fig.text(
                            0.01, 0.99, txt, va='top', ha='left',
                            wrap=True,
                            bbox=dict(boxstyle='round', facecolor=fc, alpha=0.85, edgecolor='#555'),
                            fontsize=8, color=tc)
                        self.cursor_text._get_wrap_line_width = lambda: 160
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

            if idx == getattr(self, '_last_cursor_idx', -1):
                return
            self._last_cursor_idx = idx

            self._clear_cursors()
            plot_axes = [a for a in self.fig.axes if a is not getattr(self, '_sig_timeline_ax', None)]
            plot_x = x_vals[idx] if use_time else idx
            for a in self.fig.axes:
                self.cursor_lines.append(
                    a.axvline(x=plot_x, color=cursor_color, ls='--', alpha=0.5))

            sel  = [c for c, v in self.vars.items() if v.get() and c in self.df.columns]
            row  = self.df.iloc[idx]
            stats_cache = getattr(self, '_sensor_stats_cache', {})

            txt = f"Time: {self._format_elapsed(x_vals[idx])}\n" if use_time else f"Rec: {idx}\n"

            if self.delta_mode and len(sel) >= 2:
                d_val = abs(row[sel[0]] - row[sel[1]])
                txt += f"Δ Delta: {d_val:.2f}\n---\n"

            _pinned = getattr(self, '_pinned_line', None)
            display_sel = [_pinned] if _pinned and _pinned in sel else sel
            sensor_lines = []
            for c in display_sel:
                curr = row[c] if c in row.index else float('nan')
                s_min, s_max = stats_cache.get(c, (float('nan'), float('nan')))
                sensor_lines.append(f"{c}: {curr:.2f}  (min {s_min:.1f}  max {s_max:.1f})")
            if _pinned:
                sensor_lines.append("── click line to unpin ──")
            txt += "\n".join(sensor_lines)

            ax = event.inaxes if event.inaxes in plot_axes else (plot_axes[0] if plot_axes else event.inaxes)
            closest_line = None
            closest_dist = float('inf')
            _pinned = getattr(self, '_pinned_line', None)
            if not _pinned and ax and event.ydata is not None:
                ylim = ax.get_ylim()
                y_range = max(abs(ylim[1] - ylim[0]), 1e-9)
                for line in ax.get_lines():
                    lbl = line.get_label()
                    if lbl.startswith('_') or lbl.startswith('REF:'):
                        continue
                    ydata = line.get_ydata()
                    if len(ydata) == 0:
                        continue
                    try:
                        yi = min(idx, len(ydata) - 1)
                        norm_dist = abs(float(ydata[yi]) - float(event.ydata)) / y_range
                        if norm_dist < closest_dist:
                            closest_dist = norm_dist
                            closest_line = line
                    except Exception:
                        pass

            prev_hl   = getattr(self, '_prev_highlight', None)
            prev_dist = getattr(self, '_prev_highlight_dist', float('inf'))
            SWITCH_THRESHOLD = 0.08
            HYSTERESIS       = 0.70

            if closest_line and closest_dist < SWITCH_THRESHOLD:
                switch = (closest_line is not prev_hl and
                          (prev_hl is None or closest_dist < prev_dist * HYSTERESIS))
                if switch:

                    if prev_hl:
                        try:
                            prev_hl.set_linewidth(self._prev_highlight_lw)
                            prev_hl.set_zorder(self._prev_highlight_z)
                        except Exception: pass
                    self._prev_highlight_lw   = closest_line.get_linewidth()
                    self._prev_highlight_z    = closest_line.get_zorder()
                    self._prev_highlight_dist = closest_dist
                    closest_line.set_linewidth(self._prev_highlight_lw + 1.5)
                    closest_line.set_zorder(10)
                    self._prev_highlight = closest_line
                else:

                    self._prev_highlight_dist = closest_dist

                col_name = closest_line.get_label().split('\n')[0].strip()
                if col_name in self.df.columns:
                    curr = row[col_name] if col_name in row.index else float('nan')
                    s_min, s_max = stats_cache.get(col_name, (float('nan'), float('nan')))
                    ann_txt = f"{col_name}\nCurr: {curr:.2f}  Min: {s_min:.1f}  Max: {s_max:.1f}"
                    ann = getattr(self, '_line_annotation', None)
                    if ann is not None:

                        ann.set_text(ann_txt)
                        ann.xy = (plot_x, curr)
                    else:
                        self._line_annotation = ax.annotate(
                            ann_txt,
                            xy=(plot_x, curr),
                            xytext=(12, 12), textcoords='offset points',
                            fontsize=8, color=tc,
                            bbox=dict(boxstyle='round,pad=0.4', facecolor=fc, alpha=0.92,
                                      edgecolor=closest_line.get_color(), linewidth=1.5),
                            zorder=20, annotation_clip=False
                        )
            elif _pinned and _pinned in self.df.columns and ax:

                curr = row[_pinned] if _pinned in row.index else float('nan')
                s_min, s_max = stats_cache.get(_pinned, (float('nan'), float('nan')))
                ann_txt = f"{_pinned}\nCurr: {curr:.2f}  Min: {s_min:.1f}  Max: {s_max:.1f}"
                ann = getattr(self, '_line_annotation', None)
                if ann is not None:
                    ann.set_text(ann_txt)
                    ann.xy = (plot_x, curr)
                else:

                    pin_color = tc
                    for line in ax.get_lines():
                        if line.get_label().split('\n')[0].strip() == _pinned:
                            pin_color = line.get_color()
                            break
                    self._line_annotation = ax.annotate(
                        ann_txt,
                        xy=(plot_x, curr),
                        xytext=(12, 12), textcoords='offset points',
                        fontsize=8, color=tc,
                        bbox=dict(boxstyle='round,pad=0.4', facecolor=fc, alpha=0.92,
                                  edgecolor=pin_color, linewidth=1.5),
                        zorder=20, annotation_clip=False
                    )
            else:

                if prev_hl:
                    try:
                        prev_hl.set_linewidth(self._prev_highlight_lw)
                        prev_hl.set_zorder(self._prev_highlight_z)
                    except Exception: pass
                    self._prev_highlight      = None
                    self._prev_highlight_dist = float('inf')
                ann = getattr(self, '_line_annotation', None)
                if ann is not None:
                    try: ann.remove()
                    except Exception: pass
                    self._line_annotation = None

            if getattr(self, '_tooltip_enabled', True):
                self.cursor_text = self.fig.text(
                    0.01, 0.99, txt, va='top', ha='left',
                    wrap=True,
                    bbox=dict(boxstyle='round', facecolor=fc, alpha=0.8, edgecolor='#555'),
                    fontsize=8, color=tc)
                self.cursor_text._get_wrap_line_width = lambda: self.fig.get_figwidth() * self.fig.dpi * 0.20
            self.canvas_widget.draw_idle()
        except Exception:
            pass

    def _calc_timeline_rows(self, hits):
        if not hits:
            return 1
        entries = []
        for hit in hits:
            spans = hit.get('spans') or []
            if not spans:
                s, e = hit.get('start_idx'), hit.get('end_idx')
                spans = [(s, e)] if s is not None else []
            for i, span in enumerate(spans):
                x0 = span[0] if span else 0
                x1 = span[1] if span else x0
                entries.append((x0, x1, hit.get('name', '') if i == 0 else ''))
        if not entries:
            return 1
        total = max((x1 for _, x1, _ in entries), default=1)
        x_range = max(total, 1)
        CHAR_W = x_range * 0.012
        BAR_GAP = x_range * 0.003
        row_right = []
        for x0, x1, name in entries:
            if name:
                half_w = len(name[:20]) * CHAR_W / 2
                claimed = max(x1, (x0 + x1) / 2 + half_w)
            else:
                claimed = x1
            placed = False
            for i, rx in enumerate(row_right):
                if x0 > rx + BAR_GAP:
                    row_right[i] = claimed
                    placed = True
                    break
            if not placed:
                row_right.append(claimed)
        return max(1, len(row_right))

    def _sensors_for_sig(self, sig_name: str) -> set:
        cols = set(self.df.columns)
        def _any(*keywords):
            kw = [k.upper() for k in keywords]
            return {c for c in cols if any(k in c.upper() for k in kw)}
        def _cols(*keywords):
            kw = [k.upper() for k in keywords]
            return {c for c in cols if all(k in c.upper() for k in kw)}
        m = {
            "CPU Thermal Throttling": (
                _any("TDIE","TCTL","TJMAX","PROCHOT","THROTTL","CPU PACKAGE [","CPU PACKAGE TEMP","PACKAGE TEMP","CORE TEMP","CPU TEMP","CPU TEMPERATURE","CORE MAX","CORE DISTANCE","DISTANCE TO TJMAX","CPU HOT","THERMAL THROTTL","CPU DIE","CCD TEMP","CCD1","CCD2","IOD TEMP","CPU CCD","P-CORE","E-CORE","RING TEMP","PAKET","KERN") |
                _cols("CPU","POWER") | _cols("CORE","DISTANCE")
            ),
            "CPU Power Limit Reached": (
                _any("PL1","PL2","PL3","PL4","PPT","EDC","TDC","POWER LIMIT","THROTTL","PROCHOT","PACKAGE POWER LIMIT","CPU POWER LIMIT","TURBO POWER","POWER LIMIT EXCEEDED","IA LIMIT","GT LIMIT","RING LIMIT","RUNNING AVERAGE THERMAL","RAPL","PERFORMANCE LIMIT - POWER","PERFORMANCE LIMIT - THERMAL","CURRENT CDTP") |
                _cols("CPU","POWER") | _cols("CPU","PACKAGE","POWER") | _cols("IA","POWER")
            ),
            "CPU Bottleneck": _any("TOTAL CPU","CPU USAGE","CPU LOAD","CPU UTIL","CPU AUSLASTUNG","CPU BELASTUNG","GPU USAGE","GPU CORE LOAD","GPU LOAD","GPU AUSLASTUNG","GPU CORE USAGE","MAX CPU","CPU THREAD","THREAD USAGE"),
            "CPU Clock Stretching - Major": (_cols("EFFECTIVE","CLOCK") | _cols("CLOCK","PERF") | _cols("CPU","USAGE") | _cols("CPU","LOAD") | _any("TOTAL CPU USAGE","TOTAL CPU LOAD","AVERAGE EFFECTIVE","EFF CLOCK","T0 EFFECTIVE","T1 EFFECTIVE","CORE RATIO","BUS CLOCK")),
            "CPU Clock Stretching - Minor": (_cols("EFFECTIVE","CLOCK") | _cols("CLOCK","PERF") | _cols("CPU","USAGE") | _cols("CPU","LOAD") | _any("TOTAL CPU USAGE","TOTAL CPU LOAD","AVERAGE EFFECTIVE","EFF CLOCK","T0 EFFECTIVE","T1 EFFECTIVE")),
            "GPU Thermal Warning": _any("GPU TEMPERATURE","GPU TEMP [","GPU HOT","GPU HOTSPOT","HOT SPOT","GPU JUNCTION","GPU MEMORY JUNCTION","GPU THERMAL","THERMAL LIMIT","GPU EDGE","EDGE TEMP","GPU JUNCTION TEMP","GPU CORE TEMP","GPU DIODE","GPU TEMPERATUR"),
            "GPU Overheating (Hotspot)": (_any("GPU TEMPERATURE","GPU TEMP [","GPU HOT","GPU HOTSPOT","HOT SPOT","GPU JUNCTION","GPU MEMORY JUNCTION","GPU THERMAL","THERMAL LIMIT","GPU EDGE","EDGE TEMP","GPU CORE TEMP","GPU DIODE","GPU TEMPERATUR") | _cols("GPU","POWER") | _cols("GPU","CLOCK") | _cols("GPU","USAGE")),
            "GPU Driver TDR (Timeout)": (_cols("GPU","USAGE") | _cols("GPU","LOAD") | _cols("GPU","CLOCK") | _cols("GPU","FREQUENCY") | _any("GPU AUSLASTUNG","GPU TAKT","GPU CORE USAGE","GPU CORE CLOCK","GPU EFFECTIVE CLOCK","GPU CROSSBAR")),
            "GPU Power Limit Saturated": (_any("GPU POWER","GPU BOARD POWER","GPU PACKAGE POWER","TGP","TBP","GPU TGP","GPU TBP","GPU WATT","GPU LEISTUNG","PERFORMANCE LIMIT - POWER","PERFORMANCE LIMIT - THERMAL","PERFORMANCE LIMIT - UTILIZATION","PERFORMANCE LIMIT - RELIABILITY","PERFORMANCE LIMIT - MAX","PERFCAP","POWER LIMIT","PERF LIMIT","GPU INPUT POWER","GPU RAIL POWER","GPU 12VHPWR","NVVDD","FBVDD") | _cols("GPU","CLOCK") | _cols("GPU","USAGE")),
            "GPU Power Limit Oscillation": (_any("GPU POWER","GPU BOARD POWER","TGP","TBP","PERFORMANCE LIMIT - POWER","PERFCAP","POWER LIMIT","GPU WATT","GPU LEISTUNG","GPU INPUT POWER","NVVDD","FBVDD") | _cols("GPU","CLOCK")),
            "GPU VRAM Overflow Analysis": _any("VRAM","GPU MEMORY","D3D MEMORY","GPU MEM","MEMORY ALLOCATED","MEMORY AVAILABLE [MB","GPU D3D","DEDICATED VIDEO","VIDEO MEMORY","VIRTUAL MEMORY","GDDR","HBM","GPU MEMORY USAGE","GPU MEMORY LOAD","GPU MEMORY ALLOCATED","GPU MEMORY AVAILABLE","D3D MEMORY DEDICATED","D3D MEMORY DYNAMIC","SHARED MEMORY"),
            "VRAM Thermal Throttling": (_any("GPU MEMORY JUNCTION","MEMORY JUNCTION","VRAM TEMP","VRAM TEMPERATURE","GPU MEM TEMP","HBM TEMP","GDDR TEMP","GPU MEMORY TEMP","MEMORY TEMP") | _cols("GPU","MEMORY","CLOCK") | _cols("GPU","CLOCK")),
            "VRAM Swapping / System Memory Spillover": _any("GPU D3D MEMORY","D3D MEMORY DYNAMIC","D3D MEMORY DEDICATED","GPU MEMORY ALLOCATED","SHARED MEMORY","VIRTUAL MEMORY","PAGE FILE","GPU MEMORY AVAILABLE","DEDICATED VIDEO MEMORY"),
            "PSU +12V Rail Sag": (_any("+12V [V]","+12V VOLTAGE","12V RAIL","ATX 12V","EPS 12V","12V SUPPLY","VBUS 12","12V OUT","12 VOLT","VCC 12V","12VDC","+12.0V","12.000V","VCORE 12V","MAIN 12V") | _cols("GPU","POWER")),
            "PSU +5V Rail Unstable": _any("+5V [V]","+5V VOLTAGE","5V RAIL","ATX 5V","5V SUPPLY","5VSB","5V STANDBY","VBUS 5","5V OUT","5 VOLT","VCC 5V","5VDC","+5.0V","5.000V","MAIN 5V","+5VS","5V SB","VIN 5V","AVCC"),
            "PSU +3.3V Rail Unstable": _any("+3.3V [V]","+3.3V VOLTAGE","3.3V RAIL","3V3","3.3V SUPPLY","3.3V OUT","ATX 3.3","3.3 VOLT","3.3VDC","VCC 3.3","+3.3VS","3.3V SB","VDD 3.3","VDDA","AVDD","+3.30V","3.300V","3.3000V","VDD (SWA)","VDDQ (SWB)","VPP (SWC)","1.8V VOUT","1.0V VOUT","3VSB","3V SB","3.3VSB","VIN 3.3","+3V3","3V3 RAIL","3.3V VOLTAGE","3.3V SENSOR","VCC3","VCC 3","VCCIO"),
            "PSU Hardware Failure Indicators": (_any("+12V [V]","+12V VOLTAGE","12V RAIL","ATX 12V","EPS 12V") | _any("+5V [V]","+5V VOLTAGE","5V RAIL","ATX 5V") | _any("+3.3V [V]","+3.3V VOLTAGE","3.3V RAIL","3V3") | _any("POWER SUPPLY","HARDWARE LIMIT","SOFTWARE LIMIT","AVG. POWER (PL1)","BURST POWER (PL2)","CURRENT (PL4)","THROTTL","PERFORMANCE LIMIT") | _cols("GPU","USAGE") | _cols("GPU","CLOCK")),
            "Fan Stall Detected": (_any("FAN","RPM","PUMP","COOLER","FAN SPEED","FAN RPM","CPU FAN","GPU FAN","CHASSIS FAN","CASE FAN","SYS FAN","AIO PUMP","WATER PUMP","LüFTER","VENTILATEUR","CPU [RPM]","GPU [RPM]","FAN1","FAN2","FAN3") | _cols("CPU","TEMP") | _cols("GPU","TEMP")),
            "VRM Overheating": _any("VRM","MOSFET","CHOKE","MOS TEMP","PHASE TEMP","VCORE TEMP","CPU VRM","GPU VRM","SVI","VDDCR","VDDCR_SOC","POWER STAGE","PWM TEMP","PWMIC","DIGI+ VRM","ASUS VRM","VRM HOT","VRM TEMPERATURE","MOSFet","FET TEMP","IA VR","GT VR","SA VR","VR TEMP"),
            "System RAM Exhaustion": _any("PHYSICAL MEMORY","MEMORY USED","MEMORY LOAD","MEMORY AVAILABLE","RAM LOAD","RAM USAGE","PHYSICAL MEMORY USED","PHYSICAL MEMORY LOAD","PHYSICAL MEMORY AVAILABLE","MEMORY USAGE","RAM USED","RAM AVAILABLE","SPEICHER","ARBEITSSPEICHER"),
            "Virtual Memory Limit": _any("VIRTUAL MEMORY","PAGE FILE","COMMIT","PAGEFILE","SWAP","VIRTUAL MEMORY COMMITTED","VIRTUAL MEMORY AVAILABLE","VIRTUAL MEMORY LOAD","PAGE FILE USAGE","PAGE FILE TOTAL","COMMITTED BYTES","COMMIT LIMIT"),
            "Storage Thermal Critical": _any("DRIVE TEMP","SSD TEMP","NVME TEMP","HDD TEMP","DRIVE TEMPERATURE","DISK TEMP","DISK TEMPERATURE","M.2 TEMP","STORAGE TEMP","LAUFWERK TEMP","FESTPLATTE TEMP","TEMPERATURE [°C]","DRIVE TEMPERATURE [°C]","DRIVE TEMPERATURE 2","DRIVE TEMPERATURE 3","COMPOSITE TEMP","SENSOR 1 TEMP","SENSOR 2 TEMP"),
            "Storage Overheating": _any("DRIVE TEMP","SSD TEMP","NVME TEMP","HDD TEMP","DRIVE TEMPERATURE","DISK TEMP","M.2 TEMP","COMPOSITE TEMP","STORAGE TEMP","DRIVE TEMPERATURE 2","DRIVE TEMPERATURE 3","SENSOR 1 TEMP","SENSOR 2 TEMP"),
            "Storage Congestion": _any("READ RATE","WRITE RATE","READ ACTIVITY","WRITE ACTIVITY","TOTAL ACTIVITY","DRIVE ACTIVITY","DISK ACTIVITY","IO RATE","READ TOTAL","WRITE TOTAL","READ SPEED","WRITE SPEED","DISK SPEED","MB/S","READ [MB","WRITE [MB"),
            "Storage I/O Bottleneck / Hitching": _any("READ RATE","WRITE RATE","READ ACTIVITY","WRITE ACTIVITY","TOTAL ACTIVITY","READ SPEED","WRITE SPEED","IO RATE","FRAME TIME","FRAMETIME","GPU BUSY","CPU BUSY"),
            "S.M.A.R.T. Hardware Failure": _any("DRIVE FAIL","DRIVE WARN","DRIVE WARNING","DRIVE FAILURE","S.M.A.R.T","SMART","FAILURE [YES","WARNING [YES","REALLOCATED","PENDING SECTOR","UNCORRECTABLE","OFFLINE UNCORRECTABLE","CRC ERROR","ULTRA DMA CRC"),
            "SSD Lifespan Critical": _any("REMAINING LIFE","DRIVE HEALTH","WEAR LEVEL","AVAILABLE SPARE","DRIVE REMAINING","NAND ENDURANCE","MEDIA WEAROUT","PERCENT USED","PERCENT LIFETIME","TOTAL BYTES WRITTEN","TOTAL HOST WRITES","HOST WRITES","NAND WRITES","DRIVE REMAINING LIFE","SSD HEALTH","ENDURANCE REMAINING"),
            "SSD Wear Warning": _any("REMAINING LIFE","DRIVE HEALTH","WEAR LEVEL","AVAILABLE SPARE","NAND ENDURANCE","PERCENT USED","PERCENT LIFETIME","TOTAL HOST WRITES","HOST WRITES","DRIVE REMAINING LIFE","SSD HEALTH","ENDURANCE REMAINING"),
            "Micro-Stuttering Detected": _any("FRAME TIME","FRAMETIME","FPS","FRAME RATE","GPU BUSY","CPU BUSY","GPU WAIT","CPU WAIT","PRESENTED","DISPLAYED","ANIMATION ERROR","FRAME TIME PRESENTED","FRAME TIME DISPLAYED","FRAMERATE PRESENTED","FRAMERATE DISPLAYED","1% LOW","0.1% LOW","99TH","1ST PERCENTILE","LATENCY","RENDER TIME"),
            "Background Process Interference": _any("CPU USAGE","TOTAL CPU","CPU LOAD","CPU UTIL","GPU USAGE","GPU LOAD","GPU CORE LOAD","FRAME TIME","FRAMETIME","MAX CPU","CPU THREAD","THREAD USAGE","PROCESS CPU","CPU AUSLASTUNG"),
            "GPU Priority Conflict (Background App)": _any("FRAME TIME","FRAMETIME","GPU USAGE","GPU LOAD","GPU BUS","BUS LOAD","GPU WAIT","GPU BUSY","GPU CLOCK","FPS","GPU CORE LOAD","GPU D3D USAGE","GPU GRAPHICS USAGE","GPU COMPUTE USAGE","GPU VIDEO USAGE"),
            "GPU Engine Wait Bottleneck": _any("GPU WAIT","GPU BUSY","GPU WAIT (AVG)","GPU BUSY (AVG)","FRAME TIME","FRAMETIME","CPU WAIT","CPU BUSY","FPS","GPU WAIT [MS]","GPU BUSY [MS]","CPU WAIT [MS]","CPU BUSY [MS]","ANIMATION ERROR"),
            "Hardware (WHEA) Errors": _any("WHEA","HARDWARE ERROR","CORRECTABLE","NON-FATAL","FATAL ERROR","PCIe LANE","WINDOWS HARDWARE ERROR","MCE","MACHINE CHECK","CORRECTABLE ERROR COUNT","NON-FATAL ERROR COUNT","FATAL ERROR COUNT","WHEA ERROR","HARDWARE ERRORS","TOTAL ERRORS","UNSUPPORTED REQUEST"),
            "Chipset Thermal Throttling": _any("CHIPSET","PCH TEMP","PCH [","PCH TEMPERATURE","MOTHERBOARD [","MOTHERBOARD TEMP","NB TEMP","NORTHBRIDGE","SOUTHBRIDGE","PLATFORM CONTROLLER","PCH TEMPERATURE [","PCH TEMPERATURE2","PCH TEMPERATURE3","PCH TEMPERATURE4","SMU TEMP","SPD HUB"),
            "PCIe Bus Interface Chokepoint": _any("GPU BUS","BUS LOAD","PCIE LINK","PCIE SPEED","GPU USAGE","GPU CLOCK","FRAME TIME","PCIE LINK SPEED","PCIE BANDWIDTH","GPU BUS LOAD","GPU BUS INTERFACE","GPU PCIE","LINK SPEED","GT/S"),
            "PCIe Bus Signal Instability": _any("RECEIVER ERROR","REPLAY COUNT","REPLAY ROLLOVER","BAD TLP","BAD DLLP","RECOVERY COUNT","CORRECTABLE ERROR COUNT","NON-FATAL ERROR COUNT","FATAL ERROR COUNT","UNSUPPORTED REQUEST","PCIE LANE","LCRC ERROR","NAKS SENT","NAKS RECEIVED","PCI EXPRESS ERROR","PCIE ERROR"),
            "Kernel Driver Latency (DPC/ISR)": _any("DPC","SYSTEM INTERRUPT","LATENCY","FRAME TIME","FRAMETIME","CPU BUSY","CPU WAIT","DPC LATENCY","ISR LATENCY","INTERRUPT LATENCY","KERNEL LATENCY","DPC/ISR","DEFERRED PROCEDURE"),
            "Laptop Power Delivery Failure (Limp Mode)": (_any("BATTERY","CHARGE","DISCHARGE","AC ADAPTER","REMAINING CAPACITY","CHARGE LEVEL","CHARGE RATE","BATTERY VOLTAGE","BATTERY CAPACITY","CHARGE CURRENT","DISCHARGE RATE","WEAR LEVEL","FULL CHARGE CAPACITY","DESIGN CAPACITY","POWER SOURCE","AC/DC","PLUGGED IN","ON BATTERY","LAPTOP BATTERY","BATTERY REMAINING","BATTERY POWER","DISCHARGE CURRENT") | _cols("CPU","POWER") | _cols("GPU","POWER")),
            "Memory XMP/EXPO Profile Disabled": _any("MCLK","MEMORY CLOCK","DRAM CLOCK","RAM CLOCK","MEM FREQ","MEMORY FREQUENCY","DRAM FREQUENCY","RAM FREQUENCY","MEMORY SPEED","DRAM SPEED"),
            "Phantom Clock Cap": _any("GPU CLOCK","GPU CORE CLOCK","GPU EFFECTIVE CLOCK","GPU CROSSBAR","GPU VIDEO CLOCK","GPU MEMORY CLOCK","PERFORMANCE LIMIT","POWER LIMIT","THERMAL LIMIT","RELIABILITY VOLTAGE","OPERATING VOLTAGE","GPU BOOST CLOCK","BOOST CLOCK","GPU BASE CLOCK","BASE CLOCK","PERFCAP REASON","CLOCK CAP","CLOCK LIMIT"),
        }
        return m.get(sig_name, set()) & cols

    def _timeline_peak_idx(self, hit):
        """For hits without positional data, find the row index of the peak in relevant cols."""
        cols = [c for c in hit.get('cols', []) if c and c in self.df.columns]
        if not cols:
            return None
        try:
            peak_idx = int(self.df[cols[0]].idxmax())
            return peak_idx
        except Exception:
            return None

    def _draw_sig_timeline(self, ax, x_vals, hits):
        sev_colors = {'CRITICAL': '#e74c3c', 'WARNING': '#f39c12', 'INFO': '#3498db'}
        is_dark = self.is_dark
        bg2_color = self._get_theme()["bg2"]

        ax.set_facecolor(bg2_color)
        ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        n = len(x_vals)
        x_min, x_max = x_vals[0], x_vals[-1]
        x_range = max(x_max - x_min, 1e-9)

        self._sig_timeline_ax     = ax
        self._sig_timeline_x_vals = x_vals

        if not hits:
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(0, 1)
            ax.text(0.5, 0.5, 'No signatures triggered', ha='center', va='center',
                    fontsize=7, color='#4ec94e', transform=ax.transAxes)
            self._sig_timeline_hits = []
            return

        def _xi(idx):
            return x_vals[max(0, min(int(idx), n - 1))]

        def _fmt(xv):
            try:
                return self._format_elapsed(xv)
            except Exception:
                return f'{xv:.1f}'

        entries = []
        for hit in hits:
            spans = hit.get('spans') or []
            if not spans:
                s = hit.get('start_idx')
                e = hit.get('end_idx')
                spans = [(s, e)] if s is not None and e is not None else [None]
            for span_idx, span in enumerate(spans):
                if span is not None:
                    x0 = _xi(span[0])
                    x1 = _xi(span[1])
                    if x1 <= x0:
                        x1 = x0 + x_range * 0.005
                    has_span = True
                else:
                    peak = self._timeline_peak_idx(hit)
                    x0 = x1 = _xi(peak) if peak is not None else x_min + x_range * 0.5
                    has_span = False
                entries.append((hit, x0, x1, has_span, span_idx == 0))

        BAR_GAP = x_range * 0.003

        CHAR_WIDTH = x_range * 0.012

        def _label_budget(x0, x1, name):
            """Return (label_text, label_half_width) clipped to fit the span."""
            span_w = x1 - x0
            max_chars = max(6, int(span_w / CHAR_WIDTH)) if span_w > 0 else 20
            text = name[:max_chars] + ('...' if len(name) > max_chars else '')
            half_w = len(text) * CHAR_WIDTH / 2
            return text, half_w

        row_right = []
        entry_rows = []
        entry_labels = []

        for (hit, x0, x1, has_span, first_span) in entries:
            lbl_text, half_w = _label_budget(x0, x1, hit['name'])
            center = (x0 + x1) / 2
            claimed_right = max(x1, center + half_w)

            placed = False
            for i, rx in enumerate(row_right):
                if x0 > rx + BAR_GAP:
                    row_right[i] = claimed_right
                    entry_rows.append(i)
                    placed = True
                    break
            if not placed:
                entry_rows.append(len(row_right))
                row_right.append(claimed_right)

            entry_labels.append(lbl_text)

        n_rows = max(1, len(row_right))
        row_h  = 1.0 / n_rows

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(0, 1)

        hit_patches = []
        for (hit, x0, x1, has_span, first_span), row, lbl_text in zip(entries, entry_rows, entry_labels):
            color  = sev_colors.get(hit.get('severity', 'INFO'), '#3498db')
            y_bot  = 1.0 - (row + 1) * row_h + 0.02
            y_top  = 1.0 - row * row_h        - 0.02
            center = (x0 + x1) / 2

            if has_span:
                patch = ax.axvspan(x0, x1, ymin=y_bot, ymax=y_top,
                                   color=color, alpha=0.6, zorder=3)
                ax.plot([x0, x0], [y_bot, y_top], color=color, lw=1.5, alpha=0.9, zorder=4)
                ax.plot([x1, x1], [y_bot, y_top], color=color, lw=1.5, alpha=0.9, zorder=4)
            else:
                patch = ax.axvline(x0, ymin=y_bot, ymax=y_top,
                                   color=color, lw=2.5, alpha=0.85, zorder=3)

            if lbl_text:
                y_mid = (y_bot + y_top) / 2
                ax.text(center, y_mid, lbl_text,
                        ha='center', va='center', fontsize=6,
                        color='white', fontweight='bold', clip_on=True, zorder=5)

            hit_patches.append((patch, hit, center, y_bot, y_top))

        self._sig_timeline_hits = hit_patches

    def _on_timeline_motion(self, event):
        if event.inaxes is not getattr(self, '_sig_timeline_ax', None):
            if getattr(self, '_timeline_tooltip', None):
                self._timeline_tooltip.set_visible(False)
                self.canvas_widget.draw_idle()
            return
        if not getattr(self, '_sig_timeline_hits', None):
            return
        xv = getattr(self, '_sig_timeline_x_vals', None)
        if xv is None or len(xv) < 2:
            return
        xc, yc = event.xdata, event.ydata
        if xc is None or yc is None:
            return

        x_range = xv[-1] - xv[0]
        threshold = x_range * 0.06

        best, best_dist = None, float('inf')
        for entry in self._sig_timeline_hits:
            patch, hit, center, y_bot, y_top = entry
            if y_bot <= yc <= y_top:
                dist = abs(center - xc)
                if dist < best_dist:
                    best_dist, best = dist, entry

        ax = self._sig_timeline_ax
        if not hasattr(self, '_timeline_tooltip') or self._timeline_tooltip is None:
            self._timeline_tooltip = ax.annotate(
                '', xy=(0, 0), xytext=(8, 8), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5',
                          facecolor='#1a1a2e' if self.is_dark else '#fff',
                          edgecolor='#888', alpha=0.97),
                fontsize=7.5, color='white' if self.is_dark else 'black',
                zorder=10, visible=False, annotation_clip=False,
            )
        tt = self._timeline_tooltip

        if best and best_dist < threshold:
            patch, hit, center, y_bot, y_top = best
            icon = '[CRIT]' if hit['severity'] == 'CRITICAL' else '[WARN]' if hit['severity'] == 'WARNING' else '[INFO]'
            lines = [f"{icon}  {hit['name']}"]
            spans = hit.get('spans', [])
            if spans and getattr(self, '_sig_timeline_x_vals', None) is not None:
                xv = self._sig_timeline_x_vals
                x0 = xv[max(0, spans[0][0])]
                x1 = xv[min(len(xv) - 1, spans[-1][1])]
                dur = x1 - x0
                def _fe(v):
                    try: return self._format_elapsed(v)
                    except Exception: return f'{v:.1f}'
                lines.append(f"  {_fe(x0)}  →  {_fe(x1)}  ({_fe(dur)} duration)")
            for ev in hit.get('evidence', [])[:5]:
                lines.append(f"  • {ev}")
            if hit.get('cols'):
                lines.append(f"  Sensors: {', '.join(c[:35] for c in hit['cols'][:3])}")
            lines.append("  [click to select sensors]")
            tt.set_text('\n'.join(lines))
            tt.xy = (xc, yc)
            tt.set_visible(True)
        else:
            tt.set_visible(False)
        self.canvas_widget.draw_idle()

    def _on_timeline_click(self, event):
        if event.inaxes is not getattr(self, '_sig_timeline_ax', None):
            return
        if not getattr(self, '_sig_timeline_hits', None):
            return
        xc, yc = event.xdata, event.ydata
        if xc is None or yc is None:
            return

        best, best_dist = None, float('inf')
        for entry in self._sig_timeline_hits:
            patch, hit, center, y_bot, y_top = entry
            if y_bot <= yc <= y_top:
                dist = abs(center - xc)
                if dist < best_dist:
                    best_dist, best = dist, entry
        if best is None:
            return

        patch, hit, center, y_bot, y_top = best

        cols = self._sensors_for_sig(hit['name'])
        if cols:
            for v in self.vars.values():
                v.set(False)
            for col in cols:
                if col in self.vars:
                    self.vars[col].set(True)

        self.update_plot()
        self.show_toast(f"{hit['severity']}: {hit['name']}")

    def _launch_stratagem_hero(self):

        active_theme = self.custom_theme.get("active", "")
        if active_theme != "Helldivers 2":
            return

        STRATAGEMS = [
            ("Reinforce",               ["Up", "Down", "Right", "Left", "Up"]),
            ("SOS Beacon",              ["Up", "Down", "Right", "Up"]),
            ("Resupply",                ["Down", "Down", "Up", "Right"]),
            ("Eagle Airstrike",         ["Up", "Right", "Right"]),
            ("Eagle Cluster Bomb",      ["Up", "Right", "Down", "Down", "Right"]),
            ("Eagle Napalm Airstrike",  ["Up", "Right", "Down", "Right"]),
            ("Eagle 500KG Bomb",        ["Up", "Right", "Down", "Down", "Down"]),
            ("Eagle Strafing Run",      ["Up", "Right", "Right", "Down"]),
            ("Eagle Smoke Strike",      ["Up", "Right", "Up", "Down"]),
            ("Eagle Rearm",             ["Up", "Up", "Left", "Up", "Right"]),
            ("Orbital Gatling Barrage", ["Right", "Down", "Left", "Up", "Up"]),
            ("Orbital Airburst Strike", ["Right", "Right", "Right"]),
            ("Orbital Laser",           ["Right", "Down", "Up", "Right", "Down"]),
            ("Orbital Railcannon",      ["Right", "Up", "Down", "Down", "Right"]),
            ("Orbital Precision Strike",["Right", "Right", "Up"]),
            ("Orbital Gas Strike",      ["Right", "Right", "Down", "Right"]),
            ("Orbital EMS Strike",      ["Right", "Right", "Left", "Down"]),
            ("Orbital Walking Barrage", ["Right", "Down", "Right", "Down", "Right", "Down"]),
            ("Orbital 380MM Barrage",   ["Right", "Down", "Up", "Up", "Left", "Down", "Down"]),
            ("Orbital 120MM Barrage",   ["Right", "Right", "Down", "Left", "Right", "Down"]),
            ("Shield Generator Relay",  ["Down", "Down", "Left", "Right", "Left"]),
            ("Tesla Tower",             ["Down", "Right", "Up", "Left", "Down", "Right"]),
            ("Machine Gun Sentry",      ["Down", "Up", "Right", "Right", "Up"]),
            ("Gatling Sentry",          ["Down", "Up", "Left", "Up"]),
            ("Mortar Sentry",           ["Down", "Up", "Right", "Down"]),
            ("EMS Mortar Sentry",       ["Down", "Down", "Up", "Up", "Left"]),
            ("Autocannon Sentry",       ["Down", "Up", "Right", "Up", "Left", "Up"]),
            ("Rocket Sentry",           ["Down", "Up", "Left", "Right"]),
            ("Guard Dog Rover",         ["Down", "Up", "Left", "Up", "Right", "Right"]),
            ("Supply Pack",             ["Down", "Left", "Down", "Up", "Up", "Down"]),
            ("Jump Pack",               ["Down", "Up", "Up", "Down", "Up"]),
            ("Shield Generator Pack",   ["Down", "Up", "Left", "Right", "Down", "Up", "Left"]),
            ("Anti-Tank Mines",         ["Down", "Left", "Up", "Up"]),
            ("Incendiary Mines",        ["Down", "Left", "Left", "Down"]),
            ("Hellbomb",                ["Down", "Up", "Left", "Down", "Up", "Right", "Down", "Up"]),
            ("SEAF Artillery",          ["Right", "Up", "Up", "Down"]),
            ("Machine Gun",             ["Down", "Left", "Down", "Up", "Right"]),
            ("Autocannon",              ["Down", "Left", "Down", "Up", "Up", "Right"]),
            ("Recoilless Rifle",        ["Down", "Left", "Right", "Right", "Left"]),
            ("Expendable Anti-Tank",    ["Down", "Down", "Left", "Up", "Right"]),
            ("Spear",                   ["Down", "Down", "Up", "Down", "Down"]),
            ("Railgun",                 ["Right", "Down", "Left", "Up", "Up", "Right"]),
            ("Flamethrower",            ["Down", "Left", "Up", "Down", "Up"]),
            ("Stalwart",                ["Down", "Left", "Down", "Up", "Up", "Left"]),
            ("Laser Cannon",            ["Down", "Left", "Down", "Up", "Left"]),
            ("Arc Thrower",             ["Down", "Right", "Down", "Up", "Left", "Left"]),
            ("Quasar Cannon",           ["Down", "Down", "Up", "Left", "Right"]),
            ("Anti-Materiel Rifle",     ["Down", "Left", "Right", "Up", "Down"]),
        ]

        import random
        import time as _time
        import matplotlib.patches as _mpatches

        _t      = self._get_theme()
        bg      = _t["bg"]
        fg      = _t["fg"]
        accent  = _t["accent"]

        ARROW_DISPLAY = {"Up": "▲", "Down": "▼", "Left": "◄", "Right": "►"}
        GAME_DURATION = 45
        POINTS_PER_CORRECT = 100

        state = {
            "active":      True,
            "score":       0,
            "streak":      0,
            "best_streak": 0,
            "start_time":  _time.time(),
            "current":     None,
            "progress":    0,
            "flash":       None,
            "flash_until": 0.0,
            "done":        False,
        }

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(bg)
        self.fig.patch.set_facecolor(bg)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        def _next_stratagem():
            pool = [s for s in STRATAGEMS if s is not state["current"]]
            state["current"]  = random.choice(pool)
            state["progress"] = 0

        _next_stratagem()

        def _redraw():
            ax.clear()
            ax.set_facecolor(bg)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")

            now       = _time.time()
            elapsed   = now - state["start_time"]
            remaining = max(0.0, GAME_DURATION - elapsed)
            frac      = remaining / GAME_DURATION

            if state["done"]:
                ax.text(0.5, 0.65, "MISSION COMPLETE", ha="center", va="center",
                        fontsize=22, fontweight="bold", color="#f0c030",
                        transform=ax.transAxes)
                ax.text(0.5, 0.50, f"SCORE:  {state['score']}",
                        ha="center", va="center", fontsize=18, color=fg,
                        transform=ax.transAxes)
                ax.text(0.5, 0.38, f"Best Streak: {state['best_streak']}x",
                        ha="center", va="center", fontsize=12, color=accent,
                        transform=ax.transAxes)
                ax.text(0.5, 0.22, "Ctrl+H to play again   |   Esc to return to plot",
                        ha="center", va="center", fontsize=9, color="#888",
                        transform=ax.transAxes)
                self.canvas_widget.draw_idle()
                return

            name, seq = state["current"]
            prog      = state["progress"]
            flash     = state["flash"] if now < state["flash_until"] else None

            ax.text(0.5, 0.94, "STRATAGEM HERO",
                    ha="center", va="top", fontsize=16, fontweight="bold",
                    color="#f0c030", transform=ax.transAxes)

            bx, by, bw, bh = 0.10, 0.86, 0.80, 0.025
            ax.add_patch(_mpatches.FancyBboxPatch(
                (bx, by), bw, bh, boxstyle="round,pad=0.005",
                facecolor="#2a2a2a", edgecolor="#555", linewidth=1,
                transform=ax.transAxes, zorder=2))
            bar_color = "#4caf50" if frac > 0.40 else "#f0c030" if frac > 0.20 else "#e74c3c"
            if frac > 0:
                ax.add_patch(_mpatches.FancyBboxPatch(
                    (bx, by), bw * frac, bh, boxstyle="round,pad=0.005",
                    facecolor=bar_color, edgecolor="none",
                    transform=ax.transAxes, zorder=3))
            ax.text(bx + bw + 0.02, by + bh / 2, f"{remaining:.1f}s",
                    ha="left", va="center", fontsize=9, color=fg,
                    transform=ax.transAxes)

            ax.text(0.01, 0.97, f"Score: {state['score']}",
                    ha="left", va="top", fontsize=10, color=fg,
                    transform=ax.transAxes)
            if state["streak"] >= 2:
                ax.text(0.99, 0.97, f"{state['streak']}x streak",
                        ha="right", va="top", fontsize=10, color="#f0c030",
                        transform=ax.transAxes)

            name_color = "#4caf50" if flash == "good" else "#e74c3c" if flash == "bad" else fg
            ax.text(0.5, 0.72, name,
                    ha="center", va="center", fontsize=15, fontweight="bold",
                    color=name_color, transform=ax.transAxes)

            n       = len(seq)
            spacing = min(0.09, 0.70 / max(n, 1))
            start_x = 0.5 - spacing * (n - 1) / 2
            for i, arrow in enumerate(seq):
                x = start_x + i * spacing
                col = "#4caf50" if i < prog else "#f0c030" if i == prog else "#555555"
                ax.text(x, 0.55, ARROW_DISPLAY.get(arrow, "?"),
                        ha="center", va="center",
                        fontsize=max(14, 22 - n),
                        color=col, fontweight="bold",
                        transform=ax.transAxes)

            if prog < n:
                ax.text(0.5, 0.42, f"Press  {ARROW_DISPLAY[seq[prog]]}",
                        ha="center", va="center", fontsize=11, color="#888",
                        transform=ax.transAxes)

            ax.text(0.5, 0.04, "Esc — quit",
                    ha="center", va="bottom", fontsize=8, color="#555",
                    transform=ax.transAxes)

            self.canvas_widget.draw_idle()

        def _tick():
            if not state["active"]:
                return
            if _time.time() - state["start_time"] >= GAME_DURATION and not state["done"]:
                state["done"] = True
                _redraw()
                return
            _redraw()
            self.root.after(100, _tick)

        def _on_key(event):
            if not state["active"]:
                return
            key = event.keysym

            if key == "Escape":
                _quit()
                return

            if state["done"]:
                if key == "Escape":
                    _quit()
                return

            if key not in ("Up", "Down", "Left", "Right"):
                return

            name, seq = state["current"]
            prog      = state["progress"]

            if key == seq[prog]:
                state["progress"] += 1
                if state["progress"] == len(seq):
                    state["streak"] += 1
                    state["best_streak"] = max(state["best_streak"], state["streak"])
                    bonus = max(1, state["streak"])
                    state["score"]       += POINTS_PER_CORRECT * bonus
                    state["flash"]        = "good"
                    state["flash_until"]  = _time.time() + 0.35
                    _next_stratagem()
                else:
                    state["flash"] = None
            else:
                state["progress"]    = 0
                state["streak"]      = 0
                state["flash"]       = "bad"
                state["flash_until"] = _time.time() + 0.25

            _redraw()

        def _quit():
            state["active"] = False
            for k in _key_binds:
                try:
                    self.root.unbind(k)
                except Exception:
                    pass
            self.root.bind("<Control-h>", lambda e: self._launch_stratagem_hero())
            self.update_plot()

        _key_binds = ["<Up>", "<Down>", "<Left>", "<Right>", "<Escape>"]
        for k in _key_binds:
            self.root.bind(k, _on_key)

        _redraw()
        _tick()

    def update_plot(self):
        if self.session_compare_active:
            self._draw_session_compare()
            return
        self.fig.clear()
        self._clear_cursors()
        is_dark = self.is_dark
        _t         = self._get_theme()
        bg_color   = _t["bg"]
        bg2_color  = _t["bg2"]
        text_color = _t["fg"]
        grid_color = _t["bg3"]
        self.fig.patch.set_facecolor(bg_color)
        sel = [c for c, v in self.vars.items() if v.get() and c in self.df.columns]
        if getattr(self, '_pinned_line', None) not in sel:
            self._pinned_line = None

        if not getattr(self, '_sensor_stats_cache', {}):
            self._sensor_stats_cache = {
                c: (float(self.df[c].min()), float(self.df[c].max()))
                for c in self.df.columns if self.df[c].dtype.kind in 'f i'
            }

        self._hover_fc = _t["bg2"]
        self._hover_tc = _t["fg"]
        self._hover_cursor_color = 'white' if self.is_dark else 'gray'

        if self.heatmap_mode:
            if hasattr(self, '_legend_panel'):
                self._legend_panel.grid_remove()
            self._draw_heatmap(sel)
            return

        if hasattr(self, '_legend_panel'):
            self._legend_panel.grid(row=0, column=1, sticky='ns')
        x_vals, ts, use_time = self._get_x_axis()

        if len(x_vals) != len(self.df):
            self._invalidate_x_cache()
            x_vals, ts, use_time = self._get_x_axis()
        self._last_x_vals = x_vals
        ref_x = self._get_ref_x_axis()

        from matplotlib.gridspec import GridSpec
        if self._sig_hits and getattr(self, 'sig_timeline_enabled', True):
            sel_set = {c for c, v in self.vars.items() if v.get()}
            if sel_set:
                hits = [h for h in self._sig_hits
                        if self._sensors_for_sig(h['name']) & sel_set]
            else:
                hits = list(self._sig_hits)
        else:
            hits = []
        if hits:
            n_rows   = max(1, self._calc_timeline_rows(hits))
            tl_ratio = max(0.07, min(n_rows * 0.06, 0.28))
            gs = GridSpec(2, 1, figure=self.fig,
                          height_ratios=[tl_ratio, 1 - tl_ratio],
                          hspace=0.04)
            self._sig_timeline_ax = self.fig.add_subplot(gs[0])
            self._main_plot_gs    = gs[1]
        else:
            self._sig_timeline_ax = None
            self._main_plot_gs    = None

        def _fmt_xticks(ax):
            if not use_time:
                return
            def _fmt(val, _):
                return self._format_elapsed(val)
            import matplotlib.ticker as ticker
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(_fmt))
            ax.tick_params(axis='x', labelrotation=30)

        if self.delta_mode and self.multi_mode:
            ax = self.fig.add_subplot(self._main_plot_gs if self._main_plot_gs is not None else 111)
            ax.set_facecolor(bg2_color)
            ax.text(0.5, 0.5, "Turn off Multi Mode to use Delta",
                    ha='center', va='center', color='#ffcc00', fontsize=12, fontweight='bold')
            self.canvas_widget.draw_idle()
            return

        if not sel:
            self._update_tk_legend([])
            if self._sig_timeline_ax is not None and hits:
                self._draw_sig_timeline(self._sig_timeline_ax, x_vals, hits)
                if not hasattr(self, '_timeline_cid') or self._timeline_cid is None:
                    self._timeline_cid     = self.canvas_widget.mpl_connect('button_press_event', self._on_timeline_click)
                    self._timeline_mov_cid = self.canvas_widget.mpl_connect('motion_notify_event', self._on_timeline_motion)
                self._timeline_tooltip = None
            else:
                ax = self.fig.add_subplot(111)
                ax.set_facecolor(bg2_color)
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

        _tc    = self._get_theme()
        _base6 = [_tc.get(f"plot_c{i}", matplotlib.rcParams['axes.prop_cycle'].by_key()['color'][i % 10])
                  for i in range(6)]

        def _expand_palette(base, n):
            """Expand base colors to n maximally-distinguishable colors.
            Uses the Golomb ruler / golden-ratio hue spacing strategy:
            new hues are placed at the point maximally distant from all
            existing hues on the color wheel, then brightness is alternated
            to create a second dimension of separation."""
            import colorsys, math
            result = list(base)
            if n <= len(base):
                return result[:n]

            hls_base = []
            for c in base:
                try:
                    r = int(c[1:3],16)/255; g = int(c[3:5],16)/255; b = int(c[5:7],16)/255
                    hls_base.append(colorsys.rgb_to_hls(r, g, b))
                except Exception:
                    hls_base.append((0, 0.5, 0.7))

            avg_l = sum(v[1] for v in hls_base) / len(hls_base)
            avg_s = sum(v[2] for v in hls_base) / len(hls_base)
            used_hues = [h for h, l, s in hls_base]

            bright_levels = [
                min(0.82, avg_l + 0.22),
                max(0.28, avg_l - 0.18),
                min(0.90, avg_l + 0.35),
                max(0.18, avg_l - 0.30),
            ]

            def _min_angular_dist(h, existing):
                """Minimum angular distance from h to any hue in existing (0-1 scale)."""
                dists = [min(abs(h - e), 1 - abs(h - e)) for e in existing]
                return min(dists) if dists else 1.0

            extra_idx = 0
            while len(result) < n:

                best_h, best_dist = 0.0, -1.0

                for deg in range(360):
                    h = deg / 360.0
                    d = _min_angular_dist(h, used_hues)
                    if d > best_dist:
                        best_dist = d
                        best_h = h

                lv = bright_levels[extra_idx % len(bright_levels)]

                sv = min(1.0, max(0.35, avg_s + (0.08 if extra_idx % 2 == 0 else -0.08)))

                r2, g2, b2 = colorsys.hls_to_rgb(best_h, lv, sv)
                result.append(f"#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}")
                used_hues.append(best_h)
                extra_idx += 1

            return result
        num_sel = len(sel) if sel else 6
        colors = _expand_palette(_base6, max(num_sel, 6))

        if self.multi_mode:
            from matplotlib.gridspec import GridSpecFromSubplotSpec
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

            hspace     = min(0.6, max(0.15, 1.2 / num_plots))
            self._last_multi_hspace = hspace
            legend_fs  = max(8, 10 - num_plots // 5)
            tick_fs    = max(7, 9 - num_plots // 5)
            show_stats = num_plots <= 8

            _inner = GridSpecFromSubplotSpec(
                num_plots, 1,
                subplot_spec=self._main_plot_gs if self._main_plot_gs is not None else GridSpec(1, 1, figure=self.fig)[0],
                hspace=hspace
            )

            for i, cat_name in enumerate(active_cats):
                ax = self.fig.add_subplot(_inner[i], sharex=axes[0] if axes else None)
                axes.append(ax)
                ax.set_facecolor(bg2_color)
                if num_plots <= 5:
                    ax.set_ylabel(cat_name, color=text_color, fontsize=max(7, 9 - num_plots // 5),
                                  fontweight='bold', labelpad=2)

                for col_name in category_groups[cat_name]:
                    main_color = colors[color_idx % len(colors)]
                    if self.compare_mode and self.ref_df is not None and col_name in self.ref_df.columns:
                        ax.plot(ref_x, self.ref_df[col_name],
                                ls='--', lw=1, alpha=0.5, color=main_color, zorder=2,
                                label=f"REF: {col_name}")
                    series = self.df[col_name].dropna()
                    if show_stats:
                        stats = f"▼{series.min():.1f}  ~{series.mean():.1f}  ▲{series.max():.1f}"
                        label = f"{col_name}\n{stats}"
                    else:
                        label = col_name
                    _pinned = getattr(self, '_pinned_line', None)
                    _is_pin = (_pinned == col_name)
                    _alpha  = 1.0 if (_pinned is None or _is_pin) else 0.25
                    _lw     = 2.5 if _is_pin else 1.5
                    ax.plot(x_vals, self.df[col_name], label=label,
                            lw=_lw, color=main_color, zorder=4 if _is_pin else 3, alpha=_alpha)
                    _draw_spec_zones(ax, col_name)
                    color_idx += 1

                ax.grid(True, linestyle=':', alpha=0.4, color=grid_color)
                ax.tick_params(colors=text_color, labelsize=tick_fs)
                if num_plots > 5:
                    ax.yaxis.set_tick_params(labelleft=False)
                    ax.set_ylabel(cat_name, color=text_color,
                                  fontsize=max(7, 9 - num_plots // 5),
                                  fontweight='bold', labelpad=2, rotation=0,
                                  ha='right', va='center')
                _fmt_xticks(ax)

            for ax in axes[:-1]:
                for _lbl in ax.get_xticklabels(): _lbl.set_visible(False)

            _tk_legend_entries = []
            _line_color_map = {}
            for ax, cat_name in zip(axes, active_cats):
                h, lb = ax.get_legend_handles_labels()
                if not h: continue
                _tk_legend_entries.append((cat_name, None, None, True))
                for handle, label in zip(h, lb):
                    parts = label.split('\n')
                    col_name = parts[0].strip()
                    try: lcolor = handle.get_color()
                    except Exception: lcolor = '#888'
                    try: lstyle = handle.get_linestyle()
                    except Exception: lstyle = '-'
                    stats_str = parts[1] if len(parts) > 1 and show_stats else ''
                    full_lbl = col_name + ('\n' + stats_str if stats_str else '')
                    _tk_legend_entries.append((full_lbl, lcolor, col_name, False, lstyle))
            self._update_tk_legend(_tk_legend_entries)
            all_labels = [e[0] for e in _tk_legend_entries]
            eff_fs = legend_fs

            if self.compare_mode and self.ref_df is not None:
                diff_lines = []
                for col_name in sel:
                    if col_name not in self.ref_df.columns:
                        continue
                    cur = self.df[col_name].dropna()
                    ref = self.ref_df[col_name].dropna()
                    if cur.empty or ref.empty:
                        continue
                    d_avg = cur.mean() - ref.mean()
                    d_max = cur.max()  - ref.max()
                    d_min = cur.min()  - ref.min()
                    short = col_name[:32] + ('…' if len(col_name) > 32 else '')
                    def _fmt_d(v):
                        sign = '+' if v >= 0 else ''
                        return f"{sign}{v:.1f}"
                    diff_lines.append(
                        f"{short}\n"
                        f"  avg {_fmt_d(d_avg)}  max {_fmt_d(d_max)}  min {_fmt_d(d_min)}"
                    )
                if diff_lines:
                    panel_text = "Session vs Reference\n" + ("─" * 28) + "\n" + "\n".join(diff_lines)
                    box_bg = '#1a1a1a' if is_dark else '#f0f4f8'
                    self.fig.text(
                        0.825, 0.02, panel_text,
                        fontsize=7, color=text_color,
                        va='bottom', ha='left',
                        fontfamily='monospace',
                        bbox=dict(boxstyle='round,pad=0.5',
                                  facecolor=box_bg,
                                  edgecolor='#444' if is_dark else '#ccc',
                                  alpha=0.92),
                        transform=self.fig.transFigure,
                        clip_on=False,
                        zorder=10
                    )

        elif self.delta_mode and len(sel) >= 2:
            ax = self.fig.add_subplot(self._main_plot_gs if self._main_plot_gs is not None else 111)
            ax.set_facecolor(bg2_color)
            s1, s2 = self.df[sel[0]], self.df[sel[1]]
            delta = (s1 - s2).abs()

            if self.compare_mode and self.ref_df is not None and sel[0] in self.ref_df.columns and sel[1] in self.ref_df.columns:
                ref_delta = (self.ref_df[sel[0]] - self.ref_df[sel[1]]).abs()
                ax.plot(ref_x, ref_delta, color="#ffcc00", ls='--', alpha=0.5, lw=1, zorder=1,
                        label=f"REF: Δ ({sel[0]} - {sel[1]})")

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

            _tk_delta = []
            for line in ax.get_lines():
                lbl = line.get_label()
                if lbl.startswith('_'): continue
                parts = lbl.split('\n')
                col_name = parts[0].strip()
                try: lcolor = line.get_color()
                except Exception: lcolor = '#888'
                try: lstyle = line.get_linestyle()
                except Exception: lstyle = '-'
                full_lbl = col_name + ('\n' + parts[1] if len(parts) > 1 else '')
                _tk_delta.append((full_lbl, lcolor, col_name, False, lstyle))
            self._update_tk_legend(_tk_delta)
            all_labels = [e[0] for e in _tk_delta]
        else:
            legend_fs = max(9, 10 - len(sel) // 6)
            ax = self.fig.add_subplot(self._main_plot_gs if self._main_plot_gs is not None else 111)
            ax.set_facecolor(bg2_color)
            for i, col_name in enumerate(sel):
                main_color = colors[i % len(colors)]
                if self.compare_mode and self.ref_df is not None and col_name in self.ref_df.columns:
                    ref_s = self.ref_df[col_name].dropna()
                    ref_stats = f"Min: {ref_s.min():.1f}  Avg: {ref_s.mean():.1f}  Max: {ref_s.max():.1f}"
                    ax.plot(ref_x, self.ref_df[col_name],
                            ls='--', lw=1, alpha=0.5, color=main_color, zorder=2,
                            label=f"REF: {col_name}\n{ref_stats}")
                series = self.df[col_name].dropna()
                stats = f"▼{series.min():.1f}  ~{series.mean():.1f}  ▲{series.max():.1f}"
                _pinned = getattr(self, '_pinned_line', None)
                _is_pin = (_pinned == col_name)
                _alpha  = 1.0 if (_pinned is None or _is_pin) else 0.25
                _lw     = 2.5 if _is_pin else 1.5
                ax.plot(x_vals, self.df[col_name], label=f"{col_name}\n{stats}",
                        lw=_lw, color=main_color, zorder=4 if _is_pin else 3, alpha=_alpha)
                _draw_spec_zones(ax, col_name)

            ax.grid(True, linestyle=':', alpha=0.4, color=grid_color)
            ax.tick_params(colors=text_color, labelsize=8)
            _fmt_xticks(ax)

            _tk_single_entries = []
            for line in ax.get_lines():
                lbl = line.get_label()
                if lbl.startswith('_'): continue
                parts = lbl.split('\n')
                col_name = parts[0].strip()
                stats_str = parts[1] if len(parts) > 1 else ''
                try: lcolor = line.get_color()
                except Exception: lcolor = '#888'
                try: lstyle = line.get_linestyle()
                except Exception: lstyle = '-'
                full_lbl = col_name + ('\n' + stats_str if stats_str else '')
                _tk_single_entries.append((full_lbl, lcolor, col_name, False, lstyle))
            self._update_tk_legend(_tk_single_entries)
            all_labels = [e[0] for e in _tk_single_entries]

            if self.compare_mode and self.ref_df is not None:
                diff_lines = []
                for col_name in sel:
                    if col_name not in self.ref_df.columns:
                        continue
                    cur  = self.df[col_name].dropna()
                    ref  = self.ref_df[col_name].dropna()
                    if cur.empty or ref.empty:
                        continue
                    d_avg = cur.mean() - ref.mean()
                    d_max = cur.max()  - ref.max()
                    d_min = cur.min()  - ref.min()
                    short = col_name[:32] + ('…' if len(col_name) > 32 else '')
                    def _fmt_d(v):
                        sign = '+' if v >= 0 else ''
                        return f"{sign}{v:.1f}"
                    diff_lines.append(
                        f"{short}\n  avg {_fmt_d(d_avg)}  max {_fmt_d(d_max)}  min {_fmt_d(d_min)}"
                    )
                if diff_lines:
                    panel_text = "Session vs Reference\n" + ("─" * 28) + "\n" + "\n".join(diff_lines)
                    muted = '#888888'
                    pos_col  = '#4caf50' if is_dark else '#2e7d32'
                    neg_col  = '#ef5350' if is_dark else '#c62828'
                    box_bg   = '#1a1a1a' if is_dark else '#f0f4f8'
                    self.fig.text(
                        0.825, 0.02, panel_text,
                        fontsize=7, color=text_color,
                        va='bottom', ha='left',
                        fontfamily='monospace',
                        bbox=dict(boxstyle='round,pad=0.5',
                                  facecolor=box_bg,
                                  edgecolor='#444' if is_dark else '#ccc',
                                  alpha=0.92),
                        transform=self.fig.transFigure,
                        clip_on=False,
                        zorder=10
                    )

        if self._sig_timeline_ax is not None and hits:
            self._draw_sig_timeline(self._sig_timeline_ax, x_vals, hits)
        else:
            self._sig_timeline_hits = []
            self._sig_timeline_x_vals = x_vals

        if not hasattr(self, '_timeline_cid') or self._timeline_cid is None:
            self._timeline_cid     = self.canvas_widget.mpl_connect('button_press_event', self._on_timeline_click)
            self._timeline_mov_cid = self.canvas_widget.mpl_connect('motion_notify_event', self._on_timeline_motion)
        self._timeline_tooltip = None

        try:
            if not self.multi_mode:
                self.fig.tight_layout(h_pad=0.5)
        except Exception:
            pass
        if self.multi_mode:
            self.fig.subplots_adjust(left=0.12, right=0.98, hspace=getattr(self, '_last_multi_hspace', 0.3))
        else:
            self.fig.subplots_adjust(left=0.10, right=0.98)
        self.canvas_widget.draw_idle()

if __name__ == "__main__":
    import threading
    import sys, os



    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"ERRORX2.RESYNC.ERR.{CURRENT_VERSION}"
        )
    except Exception:
        pass

                           
                                                                             
                                                                             
                                                                              
                                                                             
                                                                              
                                                                            
                                                                               
                                                                             
                                                 
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)                          
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()                                   
    except Exception:
        pass

    root = tk.Tk()
    root.withdraw()




    try:
        if getattr(sys, 'frozen', False):
            _resolved_icon = sys.executable
        else:
            _p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icon.ico')
            _resolved_icon = _p if os.path.exists(_p) else None
    except Exception:
        _resolved_icon = None
    def _apply_icon(window):
        """Apply icon to window title bar. Safe to call multiple times."""
        if not _resolved_icon:
            return
        try:
            window.iconbitmap(_resolved_icon)
        except Exception:
            pass


    _apply_icon(root)


    root.bind("<Map>", lambda e: _apply_icon(root) if e.widget is root else None)


    if _resolved_icon:
        _orig_toplevel_init = tk.Toplevel.__init__
        def _patched_toplevel_init(self, *args, **kwargs):
            _orig_toplevel_init(self, *args, **kwargs)
            def _maybe_apply():
                try:
                    if self.winfo_exists() and self.title():
                        _apply_icon(self)
                except Exception:
                    pass
            self.after(10, _maybe_apply)
        tk.Toplevel.__init__ = _patched_toplevel_init

    path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if not path:
        root.destroy()
    else:
        splash = tk.Toplevel(root)
        splash.title("RESYNC.ERR")
        splash.resizable(False, False)
        splash.protocol("WM_DELETE_WINDOW", lambda: None)
        _st = load_theme(); _sa = _st.get("active","Dark (Default)"); _su = _st.get("user_themes",{}); _sc = _su.get(_sa, _DEFAULT_DARK_THEME if "Light" not in _sa else _DEFAULT_LIGHT_THEME)
        _sbg = _sc.get("bg","#121212"); _sfg = _sc.get("fg","#e0e0e0"); _sacc = _sc.get("accent","#1f6aa5")
        splash.configure(bg=_sbg)
        splash.geometry("340x120")
        splash.grab_set()

        outer = tk.Frame(splash, bg="#1f6aa5", padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg=_sbg, padx=20, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        title_row = tk.Frame(inner, bg=_sbg)
        title_row.pack(anchor='w')
        tk.Label(title_row, text="📂  Loading CSV",
                 font=('Segoe UI', 11, 'bold'), bg=_sbg, fg=_sacc).pack(side=tk.LEFT)
        spin_var = tk.StringVar(value=" ⠋")
        tk.Label(title_row, textvariable=spin_var,
                 font=('Segoe UI', 11), bg=_sbg, fg=_sacc).pack(side=tk.LEFT, padx=(6, 0))

        fname = path.replace('\\', '/').split('/')[-1]
        tk.Label(inner, text=fname, font=('Segoe UI', 9),
                 bg=_sbg, fg=_sfg, anchor='w').pack(fill=tk.X, pady=(6, 0))

        bar_frame = tk.Frame(inner, bg=_sbg)
        bar_frame.pack(fill=tk.X, pady=(8, 0))
        bar_bg = tk.Frame(bar_frame, bg="#2a2a2a", height=4, bd=0)
        bar_bg.pack(fill=tk.X)
        bar_fg = tk.Frame(bar_bg, bg="#1f6aa5", height=4, bd=0)
        bar_fg.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        _bar_pos = [0.0]
        _bar_dir = [1]
        def _tick_bar():
            if not splash.winfo_exists():
                return
            _bar_pos[0] += 0.06 * _bar_dir[0]
            if _bar_pos[0] >= 0.85:   _bar_dir[0] = -1
            elif _bar_pos[0] <= 0.0:  _bar_dir[0] = 1
            bar_fg.place(relwidth=min(_bar_pos[0], 1.0))
            splash.after(40, _tick_bar)
        _tick_bar()

        _SPIN = [" ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏"]
        _si   = [0]
        def _tick_spin():
            if not splash.winfo_exists():
                return
            _si[0] = (_si[0] + 1) % len(_SPIN)
            spin_var.set(_SPIN[_si[0]])
            splash.after(80, _tick_spin)
        _tick_spin()

        def _worker():
            _tk_refs = [spin_var, splash, bar_fg, bar_bg, bar_frame, inner, outer]
            try:
                a = TelemetryAnalyzer(path)
                a.load()
                refs = _tk_refs[:]
                def _done():
                    try:
                        app = TelemetryApp(root, a)
                        app.canvas_widget.draw()                            
                        root.update()                                                   
                    finally:
                        root.deiconify()
                        def _refix_sash():
                            try:
                                app.paned.sashpos(0, app._pending_left_width)
                            except Exception:
                                pass
                        root.after_idle(_refix_sash)
                        root.after(150, _refix_sash)
                        refs.clear()
                        splash.grab_release()
                        splash.destroy()
                    root.after(100, lambda: _apply_icon(root))
                root.after(0, _done)
            except Exception as exc:
                _captured_exc = exc
                refs = _tk_refs[:]
                def _fail():
                    refs.clear()
                    splash.grab_release()
                    splash.destroy()
                    messagebox.showerror("Error", str(_captured_exc))
                    root.destroy()
                root.after(0, _fail)
        threading.Thread(target=_worker, daemon=True).start()
        root.mainloop()
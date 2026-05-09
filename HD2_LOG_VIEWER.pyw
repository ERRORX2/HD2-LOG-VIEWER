import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
import matplotlib.cm as mcm
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
CURRENT_VERSION = "1.4.8"  # Bump 
GITHUB_REPO = "ERRORX2/HD2-LOG-VIEWER"


def save_config(groups_dict: Dict, is_dark: bool, multi_mode: bool = False, delta_mode: bool = False,
                ignored_version: str = "", updates_disabled: bool = False, time_mode: bool = False,
                thresholds: Dict = None, heatmap_mode: bool = False, disabled_sigs: list = None):
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
            "disabled_sigs": disabled_sigs or []
        }
    }
    try:
        with open(GROUPS_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except:
        pass

def load_config() -> Tuple[Dict, bool, bool, bool, str, bool, bool, Dict, bool, list]:
    if not Path(GROUPS_FILE).exists():
        return {}, False, False, False, "", False, False, {}, False, []
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
                        sets.get("disabled_sigs", []))
            return data if isinstance(data, dict) else {}, False, False, False, "", False, False, {}, False, []
    except:
        return {}, False, False, False, "", False, False, {}, False, []


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
        self.aliases: dict = {}           # canonical_key -> actual column name (user-confirmed)

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

        # Keep time_series in sync with df after row trimming
        if self.time_series is not None:
            self.time_series = self.time_series.iloc[:len(self.df)].reset_index(drop=True)
        self.df = self.df.reset_index(drop=True)
        self.aliases = self.load_aliases()

    def extract_hardware_names(self) -> dict:
        # -- Known HWiNFO type-tag prefixes ---------------------------------
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
            # Must start with a known HWiNFO type tag
            if not _KNOWN_TAGS.match(c):
                return False
            # Reject cells that look like numeric sensor readings
            # e.g. "12.34", "0", "Yes", "No", "100.0"
            if re.match(r'^-?\d+(\.\d+)?$', c):
                return False
            if c.upper() in ('YES', 'NO', 'N/A', 'OK', 'FAIL', 'WARNING'):
                return False
            # Reject if it ends with a unit bracket — that's a column header, not a device label
            # e.g. "CPU Package [°C]" — the real label rows have no unit suffixes
            if re.search(r'\[(°C|MHz|W|V|%|RPM|MB|GB|A|ms|FPS|x|T|GT/s)\]\s*$', c, re.IGNORECASE):
                return False
            # Must contain at least one letter after the tag separator
            if ': ' in c:
                _, device_part = c.split(': ', 1)
                if not re.search(r'[A-Za-z]', device_part):
                    return False
            return True

        # Read raw rows (all encodings to be safe)
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

        # -- Find the label row(s) -------------------------------------------
        # Score each row by the fraction of non-empty cells that are label cells.
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

        # Require at least 10% of non-empty cells to match AND at least 3 absolute hits
        # before we trust the row — prevents a stray sensor name triggering a false positive
        if best_score < 0.25 or not best_row:
            return {}
        if sum(1 for c in best_row if _is_label_cell(c)) < 3:
            return {}

        # -- Category rules (matched against the TYPE TAG, first match wins) -
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

        seen: dict = {}  # device_name -> category

        for cell in best_row:
            cell = cell.strip().strip('\ufeff')
            if not cell or not _is_label_cell(cell):
                continue

            if ': ' in cell:
                type_tag, device_part = cell.split(': ', 1)
                # Strip sub-type suffixes like ": DTS", ": Enhanced", ": C-State Residency"
                # These appear when HWiNFO groups sensors under a sub-category.
                # The real device name is everything up to the SECOND ": " if the remainder
                # looks like a sub-label (no spaces before it, or known suffix patterns).
                _SUBLABEL = re.compile(
                    r':\s*(DTS|Enhanced|C-State Residency|Performance Limit Reasons|'
                    r'Clocks?|Temperatures?|Voltages?|Powers?|Fan\s*Speeds?|'
                    r'Throttling|Usage|Utilization|Residency|Load|Misc\w*)\s*$',
                    re.IGNORECASE
                )
                device_part = _SUBLABEL.sub('', device_part).strip()
                # Also strip the "Brand: Model" GPU sub-label e.g. "AMD Radeon RX 6700 XT: Sapphire RX 6700 XT"
                # Keep the longer/more specific of the two sides
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

            # Deduplication: if we already have a name that is a prefix of this one
            # (or vice versa), keep the longer/more specific one.
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
                    continue  # existing is already more specific

            if device_name not in seen:
                seen[device_name] = cat

        # -- Build ordered result --------------------------------------------
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
         saved_thresholds, self.heatmap_mode, disabled_sigs_list) = load_config()
        self.disabled_sigs = set(disabled_sigs_list)

        self.vars = {}
        self.cb_widgets = {}
        self.header_widgets = {}
        self.group_map = {}
        self.cursor_lines = []
        self.cursor_text = None
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
            'DRIVE': 70.0,          # generic HWinfo "Drive Temperature" columns
            'TEMPERATURE': 70.0,    # bare "Temperature [°C]" fallback
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
            # Out-of-spec detection
            'memory_load_max': 95.0,       # Physical/GPU memory load %
            'drive_spare_min': 10.0,       # Available spare % floor
            'drive_life_min': 10.0,        # Remaining life % floor
            'vcore_droop_max': 0.3,        # Max Vcore swing (V)
            'clock_instability': 0.35,     # std/mean ratio threshold
            'throttle_threshold': 0.9,     # throttling flag sensitivity (0–1)
            # Signature-specific thresholds (used by _run_signatures)
            'sig_cpu_thermal_pct': 0.85,   # fraction of temp limit to trigger CPU thermal signature
            'sig_cpu_thermal_samples': 10, # consecutive samples required
            'sig_fan_stall_rpm': 100.0,    # RPM below which fan is considered stalled
            'sig_fan_min_spinning': 200.0, # min peak RPM for fan to be considered "has spun"
            'sig_fan_hot_cpu_c': 70.0,     # CPU temp above which a stalled fan is flagged
            'sig_fan_hot_gpu_c': 65.0,     # GPU temp above which a stalled fan is flagged
            'sig_drive_temp_max': 70.0,    # drive temp threshold for storage overheating signature
            'sig_vrm_temp_max': 105.0,     # VRM temp threshold for VRM overheating signature
            'sig_ram_exhaust_pct': 95.0,   # physical memory % for RAM exhaustion signature
            'sig_vram_overflow_pct': 98.0, # VRAM usage % for VRAM overflow signature
            'sig_cpu_bn_gpu_pct': 60.0,    # GPU usage below this → possible CPU bottleneck
            'sig_cpu_bn_cpu_pct': 85.0,    # CPU usage above this → possible CPU bottleneck
            'sig_cpu_bn_samples': 10,      # rolling window for bottleneck detection
            'sig_stutter_mult': 3.0,       # frametime spike = median * this multiplier
            'sig_stutter_min_hits': 5,     # minimum stutter events to flag
            'sig_tdr_clock_frac': 0.5,     # GPU clock fraction for TDR detection
            'sig_ppt_sat_pct': 0.98,       # fraction of PPT limit to consider saturated
            'sig_ppt_sat_samples': 15,     # sustained samples for PPT saturation
            'sig_clock_stretch_mhz': 500.0,# requested-vs-effective clock gap to flag stretching
            'sig_disk_busy_pct': 99.9,     # disk busy % threshold for congestion signature
            'sig_disk_busy_samples': 3,    # rolling window for disk congestion
            'sig_v12_lo': 11.4,            # +12V lower spec limit for signature
            'sig_v5_lo': 4.75,  'sig_v5_hi': 5.25,
            'sig_v33_lo': 3.14, 'sig_v33_hi': 3.47,
        }

        # Apply saved overrides on top of defaults
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
        # Signature-specific thresholds
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

        # Expose app reference so check_for_updates can call show_toast
        self.root._app_ref = self

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._setup_ui()
        self._apply_theme_colors()
        self.update_plot()
        self.root.after(300, self._prompt_sensor_aliases)  # after UI settles

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
        if self._sig_watcher_id:
            self.root.after_cancel(self._sig_watcher_id)
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

        # -- Temperature limits ------------------------------------------------
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

        # -- Voltage rails -----------------------------------------------------
        section("Voltage Rails — Safe Range (V)")
        range_row("+12V Rail",   "rail_12v_lo",   "rail_12v_hi",   *self.volt_rails['+12V'],  "V")
        range_row("+5V Rail",    "rail_5v_lo",    "rail_5v_hi",    *self.volt_rails['+5V'],   "V")
        range_row("+3.3V Rail",  "rail_33v_lo",   "rail_33v_hi",   *self.volt_rails['+3.3V'], "V")

        # -- Component voltages ------------------------------------------------
        section("Component Voltages")
        range_row("CPU Vcore",   "cpu_volt_lo", "cpu_volt_hi", *self.cpu_volt_range,  "V")
        range_row("DRAM Voltage","dram_volt_lo","dram_volt_hi",*self.dram_volt_range, "V")
        row("GPU Core Voltage max", "gpu_volt_max", self.gpu_volt_max, "V")

        # -- Power limits ------------------------------------------------------
        section("Power Draw Limits (W)")
        row("CPU max power",    "cpu_power_max",   self.cpu_power_max,   "W")
        row("GPU max power",    "gpu_power_max",   self.gpu_power_max,   "W")
        row("Total system max", "total_power_max", self.total_power_max, "W")

        # -- Frame / latency ---------------------------------------------------
        section("Frame Timing & Latency")
        row("Frame time spike (1% high)", "frametime_max_ms", self.frametime_max_ms, "ms")
        row("Min FPS (0.1% low)",         "fps_min",          self.fps_min,          "FPS")
        row("Latency max",                "latency_max_ms",   self.latency_max_ms,   "ms")

        # -- Misc --------------------------------------------------------------
        section("Miscellaneous")
        row("Fan stall threshold",          "fan_min_rpm",        self.fan_min_rpm,        "RPM")

        # -- Drive health ------------------------------------------------------
        section("Drive Health")
        row("Available spare min",          "drive_spare_min",    self.drive_spare_min,    "%")
        row("Remaining life min",           "drive_life_min",     self.drive_life_min,     "%")

        # -- Memory ------------------------------------------------------------
        section("Memory Load")
        row("RAM / VRAM load max",          "memory_load_max",    self.memory_load_max,    "%")

        # -- Stability ---------------------------------------------------------
        section("Stability Detection")
        row("Throttle sensitivity (0–1)",   "throttle_threshold", self.throttle_threshold, "")
        row("Vcore max droop",              "vcore_droop_max",    self.vcore_droop_max,    "V")
        row("Clock instability ratio",      "clock_instability",  self.clock_instability,  "std/mean")

        # -- Hardware Signature Thresholds -------------------------------------
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

        # -- Signature Enable / Disable ----------------------------------------
        section("Signature Enable / Disable")
        tk.Label(body, text="Uncheck a signature to exclude it from detection and reports.",
                 bg=bg, fg="#888", font=('Segoe UI', 8), wraplength=480,
                 justify='left').pack(anchor='w', padx=8, pady=(2, 6))

        _ALL_SIGNATURES = [
            # name                              default severity hint
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
            ("PSU Hardware Failure Indicators", "CRITICAL/WARNING"),
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
        ]

        _SEV_COLORS = {"CRITICAL": "#ff4d4d", "WARNING": "#f59e0b",
                       "INFO": "#38bdf8", "CRITICAL/WARNING": "#ff8c42"}
        sig_vars = {}   # name -> BooleanVar
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

        # Buttons 
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
                self.fan_min_rpm      = float(entries['fan_min_rpm'].get())
                self.drive_spare_min  = float(entries['drive_spare_min'].get())
                self.drive_life_min   = float(entries['drive_life_min'].get())
                self.memory_load_max  = float(entries['memory_load_max'].get())
                self.throttle_threshold = float(entries['throttle_threshold'].get())
                self.vcore_droop_max  = float(entries['vcore_droop_max'].get())
                self.clock_instability = float(entries['clock_instability'].get())

                # Signature thresholds
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

                # Apply signature enable/disable toggles
                self.disabled_sigs = {name for name, var in sig_vars.items() if not var.get()}

                # All parsed OK — save and update
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
                # Field mid-edit — silently ignore, just flag status
                status_var.set("⚠ Invalid value — fix before closing")
                status_lbl.config(fg="#e74c3c")

        # Bind live save to every entry var — depracted due to performance issues when rapidly changing values. Now only applied on button click.
        #def _on_trace(*_):
         #   _try_apply()

        #for var in entries.values():
         #   var.trace_add("write", _on_trace)

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
                # Reset checkboxes in dialog
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
        self.show_toast(f"Ignored v{version} — you'll be notified about future versions")

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
            # Signature thresholds
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
                    self.heatmap_mode, list(self.disabled_sigs))

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

        try:
            self.fig.tight_layout(h_pad=0.5)
        except Exception:
            pass
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
        accent = "#1f6aa5" if self.is_dark else "#3498db"
        hover_bg = "#252525" if self.is_dark else "#e9ecef"

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
    def _is_critical(self, col: str) -> bool:
        raw  = col.upper()
        name = raw.replace(' ', '')
        series = self.df[col].dropna()
        if series.empty:
            return False

        # -- Exclusions --------------------------------------------------------
        if any(x in raw for x in _EXCLUDE_RAW) or any(x in name for x in _EXCLUDE_NAME):
            return False

        # -- Frame timing / FPS ------------------------------------------------
        if 'FRAME TIME' in raw or 'FRAMETIME' in raw:
            if '1% HIGH' in raw and '0.1%' not in raw:
                return series.max() > self.frametime_max_ms
            return False

        if 'FRAMERATE' in raw or ' FPS' in raw or 'FRAMES PER SECOND' in raw:
            if '0.1%' in raw and 'LOW' in raw and 'PRESENTED' not in raw:
                return series.min() <= self.fps_min and series.max() > 0
            return False

        if 'LATENCY' in raw or 'RENDER TIME' in raw or 'PRESENT TIME' in raw \
                or 'GPU BUSY' in raw or 'CPU BUSY' in raw or 'DISPLAY LATENCY' in raw:
            return series.max() > self.latency_max_ms

        if '[MS]' in raw:
            return False

        # -- Throttling --------------------------------------------------------
        if any(x in raw for x in _THROTTLE_KW):
            return series.max() >= self.throttle_threshold

        # -- Yes/No binary flags -----------------------------------------------
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
                # -- Per-core / package throttling --
                'THERMAL THROTTL',
                'PACKAGE/RING THERMAL',
                'POWER LIMIT EXCEEDED',

                # -- Intel IA (CPU core) limit reasons --
                'IA: PROCHOT',
                'IA: THERMAL EVENT',
                'IA: RESIDENCY STATE REGULATION',
                'IA: RUNNING AVERAGE THERMAL LIMIT',
                'IA: VR THERMAL ALERT',
                'IA: VR TDC',
                'IA: PACKAGE-LEVEL RAPL',   # covers PL1 and PL2 PL3
                'IA: MAX TURBO LIMIT',
                'IA: TURBO ATTENUATION',
                'IA: THERMAL VELOCITY BOOST',
                'IA LIMIT REASONS',

                # -- Intel GT (iGPU) limit reasons --
                'GT: PROCHOT',
                'GT: THERMAL EVENT',
                'GT: DDR RAPL',
                'GT: RESIDENCY STATE REGULATION',
                'GT: RUNNING AVERAGE THERMAL LIMIT',
                'GT: VR THERMAL ALERT',
                'GT: VR TDC',
                'GT: MAX VR VOLTAGE',       # "GT: Max VR Voltage  ICCmax  PL4"
                'GT: DOMAIN-LEVEL PBM',
                'GT: PACKAGE-LEVEL RAPL',
                'GT: INEFFICIENT OPERATION',
                'GT: FUSES LIMIT',
                'GT LIMIT REASONS',

                # -- Intel Ring/LLC limit reasons --
                'RING: PROCHOT',
                'RING: THERMAL EVENT',
                'RING: DDR RAPL',
                'RING: RESIDENCY STATE REGULATION',
                'RING: RUNNING AVERAGE THERMAL LIMIT',
                'RING: VR THERMAL ALERT',
                'RING: VR TDC',
                'RING: MAX VR VOLTAGE',
                'RING: PACKAGE-LEVEL RAPL', # RING PL1 / PL2 PL3
                'RING LIMIT REASONS',

                # -- GPU NVIDIA performance limiters --
                'PERFORMANCE LIMIT - POWER',
                'PERFORMANCE LIMIT - THERMAL',
                'PERFORMANCE LIMIT - RELIABILITY VOLTAGE',
                'PERFORMANCE LIMIT - MAX OPERATING VOLTAGE',
                'PERFORMANCE LIMIT - UTILIZATION',
                'PERFORMANCE LIMIT - SLI',
                'GPU PERFORMANCE LIMITERS',

                # -- GPU NVIDIA throttle reasons --
                'AVG. POWER (PL1)',         # Avg. Power (PL1)
                'BURST POWER (PL2)',        # Burst Power (PL2)
                'CURRENT (PL4)',            # Current (PL4)
                'THERMAL',
                'POWER SUPPLY',
                'SOFTWARE LIMIT',
                'HARDWARE LIMIT',
                'GPU THROTTLE REASONS',

                # -- Drive warnings --
                'DRIVE WARNING', 'DRIVE WARN',

                # -- AMD --
                'PPT LIMIT', 'TDC LIMIT', 'EDC LIMIT',
                'SOC THROTTLE', 'GFX THROTTLE',
                'STAPM LIMIT', 'SLOW PPT', 'FAST PPT',
            )
            if any(k in raw for k in _WARN_THRESH):
                # Require >1% of samples to be active to filter single-sample noise
                return series.max() >= 1.0 and (series >= 1.0).mean() > 0.01

            return False

        # -- Total Errors ------------------------------------------------------
        if 'TOTAL ERRORS' in raw:
            return series.max() > 0

        # -- Drive health ------------------------------------------------------
        if 'AVAILABLE SPARE' in raw and '[%]' in raw:
            return series.min() < self.drive_spare_min

        if any(x in raw for x in _SMART_KW):
            return series.min() < self.drive_life_min

        # -- [%] columns -------------------------------------------------------
        if '[%]' in raw:
            if 'LIMIT' in raw:
                return False
            if ('MEMORY' in raw or 'RAM' in raw) and ('USAGE' in raw or 'LOAD' in raw):
                return series.max() >= self.memory_load_max
            if 'DECODE' in raw or 'ENCODE' in raw or 'VIDEO' in raw or 'MEDIA' in raw:
                return False

        # -- WHEA / hardware errors --------------------------------------------
        if any(x in raw for x in _WHEA_KW):
            return series.max() > 0

        # -- Drive / memory errors ---------------------------------------------
        if any(x in raw for x in _ERROR_KW):
            return series.max() > 0

        # -- Power draw --------------------------------------------------------
        if '[W]' in raw and 'STATIC' not in raw and 'LIMIT' not in raw and 'PPT' not in raw:
            if 'CPU' in raw and self._sustained(col, self.cpu_power_max, n_samples=5):
                return True
            if 'GPU' in raw and self._sustained(col, self.gpu_power_max, n_samples=5):
                return True
            if 'TOTAL' in raw and self._sustained(col, self.total_power_max, n_samples=5):
                return True

        # -- CPU PPT saturation ------------------------------------------------
        if 'CPU PPT' in raw and '[W]' in raw and 'LIMIT' not in raw:
            ppt_limit_col = next(
                (c for c in self.df.columns if 'PPT' in c.upper() and 'LIMIT' in c.upper()
                 and '[W]' in c.upper() and 'CPU' in c.upper()), None)
            if ppt_limit_col is not None:
                limit_val = self.df[ppt_limit_col].dropna().mean()
                if limit_val > 0 and series.mean() >= limit_val * 0.98:
                    return True

        # -- Voltage rails (+12V, +5V, +3.3V) --------------------------------
        for rail, (low, high) in self.volt_rails.items():
            if rail in raw:
                if any(x in raw for x in _RAIL_SKIP):
                    continue
                after = raw.split(rail)[-1]
                if 'INPUT' in after or 'PCIE' in after or 'HPWR' in after:
                    continue
                return series.min() < low or series.max() > high


        # -- CPU Vcore ---------------------------------------------------------
        # Only actual Vcore sensors — NOT per-core VID (handled separately below)
        if 'VCORE' in raw or 'CPU CORE VOLTAGE' in raw:
            lo, hi = self.cpu_volt_range
            out_of_range = series.min() < lo or series.max() > hi
            drooping = series.max() - series.min() > self.vcore_droop_max
            if out_of_range or drooping:
                return True

        # -- Per-core / aggregate VID ------------------------------------------
        # VID swing across cores is normal power management — do NOT apply droop.
        # Only flag if outside absolute safe voltage range.
        if 'VID' in raw and 'GPU' not in raw and 'VIDEO' not in raw:
            lo, hi = self.cpu_volt_range
            return series.min() < lo or series.max() > hi

        # -- DRAM voltage ------------------------------------------------------
        # Exclude GPU auxiliary rails (VDDCI_MEM, VDDIO, VDDCI etc.) —
        # these are GPU-side rails that run at lower voltages than system DRAM
        if ('DRAM VOLTAGE' in raw or 'DIMM VOLTAGE' in raw or 'MEMORY VOLTAGE' in raw
                or 'VDIMM' in raw or 'VDDQ' in raw):
            if 'GPU' in raw:
                return False
            lo, hi = self.dram_volt_range
            return series.min() < lo or series.max() > hi

        # -- GPU core voltage -------------------------------------------------
        if 'GPU CORE VOLTAGE' in raw and 'GFX' not in raw and 'VDDCR' not in raw:
            return series.max() > self.gpu_volt_max

        # -- Clock instability -------------------------------------------------
        if 'CPU CLOCK' in raw or 'GPU CLOCK' in raw or 'CORE CLOCK' in raw:
            if 'EFFECTIVE' not in raw and 'REQUESTED' not in raw \
                    and 'CORE #' not in raw and 'LIMIT' not in raw:
                if series.mean() > 100 and (series.std() / series.mean()) > self.clock_instability:
                    return True

        # -- Fan speeds -------------------------------------------------------
        # GPU fans use zero-RPM idle curves — going to 0 at idle is expected.
        # For GPU fans only flag if the fan never spun while GPU was very hot.
        # For all other fans flag if they were spinning then stalled.
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

        # -- Temperatures -----------------------------------------------------
        if any(x in name for x in _TEMP_TRIGGERS):
            matched_limit = None
            matched_len   = 0
            for key, limit in self.temp_limits.items():
                key_norm = key.upper().replace(' ', '')
                if key_norm in name and len(key_norm) > matched_len:
                    matched_limit = limit
                    matched_len   = len(key_norm)
            # 'TEMPERATURE' is a very short generic key — if a more specific
            # category keyword is also present, use its limit instead
            if matched_limit is not None and matched_len == len('TEMPERATURE'):
                for specific in ('CORE', 'GPU', 'HOTSPOT', 'TDIE', 'TCTL', 'CCD',
                                 'SSD', 'NVME', 'HDD', 'VRM', 'CHIPSET', 'SOCKET'):
                    if specific.replace(' ', '') in name:
                        matched_limit = self.temp_limits.get(specific, matched_limit)
                        break
            return self._sustained(col, matched_limit if matched_limit is not None else 90.0, n_samples=3)

        # -- Physical memory load ----------------------------------------------
        if 'PHYSICAL MEMORY' in raw and 'LOAD' in raw:
            return series.max() >= self.memory_load_max

        return False

    # -- Sustained spike helper ------------------------------------------------
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

    def _toggle_debug(self):
        """Ctrl+F8 — open/refresh the debug window."""
        self.debug_mode = not self.debug_mode
        flag = " [DEBUG]" if self.debug_mode else ""
        self.root.title(f"RESYNC.ERR v{CURRENT_VERSION} - {self.analyzer.path.name}{flag}")
        if self.debug_mode:
            self._open_debug_window()
        else:
            # Close the window if it's open
            if hasattr(self, '_debug_win') and self._debug_win and self._debug_win.winfo_exists():
                self._debug_win.destroy()
            self.show_toast("Debug mode OFF")

    def _open_debug_window(self):
        """Open (or refresh) the debug output window."""
        is_dark = self.is_dark
        bg      = "#0d0d0d" if is_dark else "#f8f9fa"
        bg2     = "#1a1a1a" if is_dark else "#ffffff"
        fg      = "#d4d4d4" if is_dark else "#212529"
        accent  = "#1f6aa5"
        fg_ok   = "#4ec94e"
        fg_miss = "#ff5555"
        fg_sec  = "#4f8ef7"
        fg_val  = "#f0c060"

        # If window already exists just refresh it
        if hasattr(self, '_debug_win') and self._debug_win and self._debug_win.winfo_exists():
            win = self._debug_win
            txt = self._debug_txt
            txt.config(state='normal')
            txt.delete('1.0', tk.END)
        else:
            win = tk.Toplevel(self.root)
            win.title("RESYNC.ERR — Debug Dump  [Ctrl+F8 to refresh / close]")
            win.geometry("860x700")
            win.minsize(600, 400)
            win.configure(bg=bg)
            win.transient(self.root)
            self._debug_win = win

            def _on_debug_close():
                self.debug_mode = False
                self.root.title(f"RESYNC.ERR v{CURRENT_VERSION} - {self.analyzer.path.name}")
                win.destroy()
            win.protocol("WM_DELETE_WINDOW", _on_debug_close)

            # Toolbar
            tb = tk.Frame(win, bg="#111" if is_dark else "#dee2e6", pady=4, padx=8)
            tb.pack(fill=tk.X)
            tk.Label(tb, text="🐛  Debug Dump", font=('Segoe UI', 10, 'bold'),
                     bg=tb['bg'], fg=accent).pack(side=tk.LEFT)
            ttk.Button(tb, text="⟳ Refresh", command=self._open_debug_window).pack(side=tk.RIGHT, padx=2)
            ttk.Button(tb, text="📋 Copy All", command=lambda: (
                win.clipboard_clear(),
                win.clipboard_append(txt.get('1.0', tk.END)),
                self.show_toast("Debug output copied to clipboard")
            )).pack(side=tk.RIGHT, padx=2)
            ttk.Button(tb, text="✕ Close", command=_on_debug_close).pack(side=tk.RIGHT, padx=2)

            # Text area
            frame = tk.Frame(win, bg=bg)
            frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
            txt = tk.Text(frame, bg=bg2, fg=fg, font=('Cascadia Code', 9) if is_dark else ('Consolas', 9),
                          wrap='none', relief='flat', padx=10, pady=8,
                          insertbackground=fg, selectbackground=accent)
            sb_y = ttk.Scrollbar(frame, orient='vertical',   command=txt.yview)
            sb_x = ttk.Scrollbar(frame, orient='horizontal',  command=txt.xview)
            txt.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
            sb_y.pack(side=tk.RIGHT,  fill=tk.Y)
            sb_x.pack(side=tk.BOTTOM, fill=tk.X)
            txt.pack(fill=tk.BOTH, expand=True)
            self._debug_txt = txt

            # Colour tags
            txt.tag_config('header',  foreground='#a78bfa', font=('Consolas', 9, 'bold'))
            txt.tag_config('section', foreground=fg_sec,    font=('Consolas', 9, 'bold'))
            txt.tag_config('ok',      foreground=fg_ok)
            txt.tag_config('miss',    foreground=fg_miss)
            txt.tag_config('val',     foreground=fg_val)
            txt.tag_config('crit',    foreground='#ff4d4d', font=('Consolas', 9, 'bold'))
            txt.tag_config('warn',    foreground='#f59e0b', font=('Consolas', 9, 'bold'))
            txt.tag_config('info',    foreground='#38bdf8')
            txt.tag_config('muted',   foreground='#555' if is_dark else '#999')

        # -- Build the dump into the text widget ----------------------------
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
            wl(SEP, 'section')
            wl(f"  {title}", 'section')
            wl(SEP, 'section')

        def mx(c):  return df[c].max()  if c and c in df.columns else None
        def avg(c): return df[c].mean() if c and c in df.columns else None

        wl('═' * 72, 'header')
        wl(f"  RESYNC.ERR v{CURRENT_VERSION}  —  Debug Dump", 'header')
        wl(f"  CSV     : {self.analyzer.path}", 'header')
        wl(f"  Rows    : {len(df):,}   Columns: {len(df.columns):,}", 'header')
        wl(f"  Disabled: {sorted(self.disabled_sigs) or 'none'}", 'header')
        wl('═' * 72, 'header')

        # -- CPU ------------------------------------------------------------
        cpu_temp      = self._col('TCTL') or self._col('TDIE') or self._col('CPU')
        cpu_clock     = self._col('KERN', 'TAKT') or self._col('CORE', 'CLOCK') or self._col('CLOCK')
        cpu_usage_col = self._col('CPU', 'USAGE') or self._col('CPU', 'UTIL') or self._col('CPU', 'LOAD') or self._col('TOTAL', 'CPU')
        cpu_power     = self._col('CPU', 'PACKAGE') or self._col('CPU', 'PPT') or self._col('CPU', 'POWER')
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

        # -- GPU ------------------------------------------------------------
        gpu_hotspot       = self._col_excl(('GPU', 'HOT'),  excl=('CPU', 'LIMIT')) or self._col_excl(('GPU', 'TEMP'), excl=('CPU',))
        gpu_usage_col     = self._col('GPU', 'USAGE') or self._col('GPU', 'LOAD')
        gpu_clock         = self._col('GPU', 'CLOCK') or self._col('GPU', 'FREQUENCY')
        gpu_power         = self._col('GPU', 'POWER')
        gpu_throttle      = self._col_excl(('GPU', 'THROTTL'), excl=('CPU',)) or self._col('PERFCAP')
        gpu_pwr_limit     = self._col('Performance Limit - Power [Yes/No]') or self._col('PERFCAP', 'PWR')
        gpu_eff_clock     = self._col('GPU Effective Clock [MHz]')
        gpu_mem_usage     = self._col('GPU', 'MEMORY', 'USAGE') or self._col('GPU', 'MEMORY', 'ALLOCATED')
        gpu_mem_dedicated = self._col('GPU D3D Memory Dedicated')
        gpu_mem_dynamic   = self._col('GPU D3D Memory Dynamic')
        gpu_bus_col       = self._col('GPU Bus Load') or self._col('Bus Load')
        vram_junc         = self._col('GPU Memory Junction Temperature [°C]')

        section("GPU COLUMNS")
        col("gpu_hotspot",        gpu_hotspot)
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

        if gpu_hotspot:
            section("GPU THERMAL VALUES")
            val("Max hotspot",   mx(gpu_hotspot))
            val("Mean hotspot",  avg(gpu_hotspot))
            val("Hotspot limit", self.temp_limits.get('GPU_HOTSPOT', 110.0))

        if gpu_clock and gpu_usage_col:
            section("GPU CLOCK / TDR VALUES")
            val("Max clock",  mx(gpu_clock))
            val("Min clock",  df[gpu_clock].min())
            val("Clock std",  df[gpu_clock].std())
            low_u  = df[gpu_usage_col] < 5
            stall  = (df[gpu_clock].rolling(3).std() < 1.0) & (df[gpu_clock] > 0)
            tdr_ev = (low_u & stall).rolling(5).sum() >= 3
            val("TDR candidate samples", int(tdr_ev.sum()), "d")

        # -- FRAME TIMING ---------------------------------------------------
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

        # -- STORAGE --------------------------------------------------------
        section("STORAGE COLUMNS")
        drive_t = [c for c in df.columns if 'TEMP' in c.upper()
                   and any(k in c.upper() for k in ['DRIVE','NVME','SSD','HDD'])]
        drive_h = [c for c in df.columns if any(k in c.upper()
                   for k in ['REMAINING LIFE','WEAR LEVEL','AVAILABLE SPARE'])]
        wl(f"  Drive temp cols   ({len(drive_t)}): {drive_t or MISS}")
        wl(f"  Drive health cols ({len(drive_h)}): {drive_h or MISS}")
        for c in drive_t:
            val(f"  Max {c[:35]}", mx(c))

        # -- FABRIC / MEMORY -------------------------------------------------
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

        # -- PSU RAILS ------------------------------------------------------
        section("PSU RAIL COLUMNS")

        _RAIL_EXCL = ['[W]', '[A]', 'POWER', 'CURRENT', 'WATT', 'VID', 'OFFSET',
                      'LIMIT', 'PPT', 'TDP', 'PCIE', 'INPUT', 'GPU', 'HPWR', 'VDDQ', 'FBVDD']

        def _find_rail(keywords, excl=_RAIL_EXCL):
            for c in df.columns:
                cu = c.upper()
                if '[V]' not in cu:
                    continue
                if any(e in cu for e in excl):
                    continue
                if any(k.upper() in cu for k in keywords):
                    return c
            return None

        rail_map = {
            '+12V':  _find_rail(['12V', '12 V', 'ATX 12', 'EPS 12']),
            '+5V':   _find_rail(['5V', '5 V', 'ATX 5', '5VSB', 'AVCC'],
                                excl=_RAIL_EXCL + ['12V', '3.3', '3V3']),
            '+3.3V': _safe_alias('rail_33v',
                                 _find_rail(['3.3V', '3V3', '3.3 V', 'VCC3', 'VCCIO',
                                             'VDDA', 'AVDD', 'VDD (SWA)', 'VDDQ', 'VPP'],
                                            excl=['[W]','[A]','POWER','CURRENT','GPU','12V','5V'])),
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

        def _safe_alias(key, *fallbacks):
            """Return alias or fallback column only if it exists in df.
            Supports list of aliases — tries each in order."""
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

        # PSU Yes/No flags
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
            wl("  No voltage rail columns found — PSU analysis unavailable.", 'muted')

        # -- SYSTEM ---------------------------------------------------------
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
            val("Max PCIe errors", mx(pcie_errors))

        # -- THRESHOLDS -----------------------------------------------------
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

        # -- VOLTAGE RAILS --------------------------------------------------
        section("VOLTAGE RAIL LIMITS  (active values)")
        for rail, (lo, hi) in self.volt_rails.items():
            d_lo, d_hi = self._default_volt_rails.get(rail, (lo, hi))
            modified = " ★" if abs(lo - d_lo) > 0.001 or abs(hi - d_hi) > 0.001 else ""
            w(f"       {rail:10s} = ")
            wl(f"{lo}V – {hi}V{modified}", 'val')

        # -- MISC THRESHOLDS ------------------------------------------------
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

        # -- FAN & COOLING COLUMNS ------------------------------------------
        section("FAN / COOLING COLUMNS")
        fan_cols = [c for c in df.columns if any(k in c.upper() for k in ['FAN','RPM','PUMP','COOLER'])]
        if fan_cols:
            for c in fan_cols[:10]:
                mn, av, mx2 = df[c].min(), df[c].mean(), df[c].max()
                w(f"  {c[:50]:50s}  ")
                wl(f"min={mn:.0f}  avg={av:.0f}  max={mx2:.0f}", 'val')
        else:
            wl(f"  {MISS}", 'miss')

        # -- VRM COLUMNS ----------------------------------------------------
        section("VRM / MOSFET COLUMNS")
        vrm_cols = [c for c in df.columns if any(k in c.upper()
                    for k in ['VRM','MOSFET','CHOKE','PHASE','MOS TEMP'])]
        if vrm_cols:
            for c in vrm_cols[:8]:
                w(f"  {c[:50]:50s}  ")
                wl(f"max={df[c].max():.1f}", 'val')
        else:
            wl(f"  {MISS}", 'miss')

        # -- BATTERY / LAPTOP COLUMNS ---------------------------------------
        section("BATTERY / LAPTOP COLUMNS")
        batt_cols = [c for c in df.columns if any(k in c.upper()
                     for k in ['BATTERY','CHARGE','DISCHARGE','AC ADAPTER','REMAINING CAPACITY'])]
        if batt_cols:
            for c in batt_cols[:8]:
                w(f"  {c[:50]:50s}  ")
                wl(f"min={df[c].min():.2f}  max={df[c].max():.2f}", 'val')
        else:
            wl("  No battery/laptop columns found — desktop system assumed.", 'muted')

        # -- OUT-OF-SPEC SENSOR SUMMARY -------------------------------------
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

        # -- COLUMN COVERAGE SCORE ------------------------------------------
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

        # -- SIGNATURE HITS -------------------------------------------------
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

        wl()
        wl('═' * 72, 'header')
        wl(f"  End of dump — Ctrl+F8 to refresh, ✕ to close", 'header')
        wl('═' * 72, 'header')

        txt.config(state='disabled')
        txt.see('1.0')

    def _run_debug_dump(self):
        """Legacy stub — debug output now goes to the in-app window via _open_debug_window()."""
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
            self.root.after(0, _done)

        def _tick():
            if self._sig_dirty and not self._sig_running:
                self._sig_dirty   = False
                self._sig_running = True
                threading.Thread(target=_worker, daemon=True).start()
            # Schedule next check in 3 seconds
            self._sig_watcher_id = self.root.after(3000, _tick)

        # Cancel any existing watcher before starting
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

        def add(name, severity, description, evidence):
            if name in self.disabled_sigs:
                return
            clean_ev = [str(e) for e in evidence if e and str(e).strip()]
            hits.append({
                'name': name, 
                'severity': severity,
                'description': description, 
                'evidence': clean_ev
            })

        # -- SENSOR MAPPING -----------------------------------------------------------

        def _a(key):
            """Return first valid user-confirmed alias column for key, else None.
            Supports multiple aliases per key (list) so different CSVs all resolve."""
            entry = self.analyzer.aliases.get(key)
            if not entry:
                return None
            candidates = entry if isinstance(entry, list) else [entry]
            return next((c for c in candidates
                         if c and c in df.columns), None)

        # -- CPU Metrics ---------------------------------------------------------------

        cpu_temp      = _a('cpu_temp') or self._col('TCTL') or self._col('TDIE') or self._col('PROZESSOR', 'TEMPERATUR') or self._col('TEMPERATUR') or self._col('CPU')
       #cpu_hotspot   = self._col('HOT', 'SPOT') or self._col('GPU', 'HOT')
        cpu_clock     = self._col('KERN', 'TAKT') or self._col('CORE', 'CLOCK') or self._col('CLOCK')
       #eff_clock     = self._col('CPU', 'EFF') or self._col('EFFIZIENZ') or self._col('EFFECTIVE')\
        cpu_usage_col = _a('cpu_usage') or self._col('CPU', 'AUSLASTUNG') or self._col('CPU', 'USAGE') or self._col('CPU', 'UTIL') or self._col('CPU', 'LOAD') or self._col('PROZESSOR') or self._col('TOTAL', 'CPU')
        cpu_power     = _a('cpu_power') or self._col('CPU-Gesamt-Leistungsaufnahme') or self._col('CPU', 'PACKAGE') or self._col('CPU', 'PPT') or self._col('CPU', 'POWER') or self._col('CPU Package Power')
        throttle      = self._col('THROTTLE') or self._col('PROCHOT')
        cpu_utility   = self._col('CPU USAGE') or self._col('CPU UTILIZATION') or self._col('CPU AUSLASTUNG') or self._col('TOTAL CPU USAGE')

        # GPU Metrics (Fixing the 45.8°C CPU mixup)
        gpu_hotspot   = _a('gpu_temp') or self._col_excl(('GPU', 'HOT'), excl=('CPU', 'LIMIT')) or self._col_excl(('GPU', 'TEMP'), excl=('CPU',))
        gpu_usage_col = _a('gpu_usage') or self._col('GPU', 'USAGE') or self._col('GPU', 'LOAD') or self._col('GPU', 'AUSLASTUNG') or self._col('GPU USAGE')
        gpu_clock     = _a('gpu_clock') or self._col('GPU', 'CLOCK') or self._col('GPU', 'FREQUENCY') or self._col('GPU', 'TAKT')
        gpu_throttle  = self._col_excl(('GPU', 'THROTTL'), excl=('CPU',)) or self._col('PERFCAP')
        gpu_power     = _a('gpu_power') or self._col('GPU', 'POWER') or self._col('BOARD', 'POWER') or self._col('TOTAL', 'BOARD') or self._col('TGP') or self._col('TBP') or self._col('ASIC') or self._col('NVVDD') or self._col('PCIe') or self._col('LEISTUNG') or self._col('EINGANGSLEISTUNG') or self._col('POWER')
        gpu_clk_col   = self._col('GPU Clock [MHz]')

        # GPU Electrical & Power Limits
        gpu_12v_input_v = self._col('GPU 12VHPWR Voltage') or self._col('GPU PCIe +12V Input Voltage') or self._col('GPU 12V Input Voltage')
        gpu_12v_input_w = self._col('GPU 12VHPWR Power') or self._col('GPU Power [W]') or self._col('GPU Board Power')
        gpu_pwr_limit   = self._col('Performance Limit - Power [Yes/No]') or self._col('PERFCAP', 'PWR')

        # GPU Memory & Bus
        gpu_mem_usage = self._col('GPU','MEMORY','USAGE') or self._col('GPU','MEMORY','ALLOCATED') or self._col('GPU','MEM','USAGE') or self._col('GPU','MEM','LOAD') or self._col('D3D','MEMORY') or self._col('VRAM','USAGE') or self._col('FRAMEBUFFER') or self._col('ADAPTER','MEMORY')
        vram_junction_temp = self._col('GPU Memory Junction Temperature [°C]')
        gpu_mem_dedicated = self._col('GPU D3D Memory Dedicated')
        gpu_mem_dynamic   = self._col('GPU D3D Memory Dynamic')
        gpu_bus_col       = self._col('GPU Bus Load') or self._col('Bus Load')

        # System & Performance
        is_laptop     = any(k in "".join(self.df.columns).upper() for k in ['BATTERY', 'CHARGE', 'AC ADAPTER', 'DISCHARGE', 'MOBILE', 'LAPTOP'])
        chipset_t     = _a('chipset_temp') or self._col('Chipset [°C]') or self._col('Motherboard [°C]') or self._col('PCH') or self._col('SMU')
        usb_v_col     = self._col('USB VCC') or self._col('USB Voltage')
        pcie_errors   = _a('pcie_errors') or self._col('PCI Express Error Counters (avg)')
        system_interrupts = _a('sys_interrupts') or self._col('System Interrupts') or self._col('DPC Latency')

        # Timing & Clocks
        ft_col        = _a('frame_time') or self._col('Frametime [ms]') or self._col('GPU Frametime') or self._col('Frame Time')
        gpu_busy_ms   = _a('gpu_busy') or self._col('GPU Busy (avg) [ms]') or self._col('GPU Busy')
        gpu_wait_ms   = _a('gpu_wait') or self._col('GPU Wait (avg) [ms]') or self._col('GPU Wait')
        gpu_eff_clock = self._col('GPU Effective Clock [MHz]')
        fclk_col = _a('fclk') or self._col('FCLK') or None
        uclk_col = _a('uclk') or next((c for c in df.columns if 'UCLK' in c), None)
        mclk_col = _a('mclk') or self._col('MCLK') or self._col('MEMORY CLOCK') or self._col('DRAM CLOCK') or None

        # -- Sensor Debug ---------------------------------------------------------------

        def mx(col): return df[col].max() if col and col in df.columns else 0
        def avg(col): return df[col].mean() if col and col in df.columns else 0

        # 1. CPU THERMAL THROTTLING
        
        if cpu_temp:
            limit = self.temp_limits.get('TDIE', 95.0)
            warn_threshold = limit * 0.85
            crit_threshold = limit * 0.92
            
            is_critical = self._sustained(cpu_temp, crit_threshold,
                                          n_samples=self.sig_cpu_thermal_samples)
            is_warning  = self._sustained(cpu_temp, warn_threshold,
                                          n_samples=self.sig_cpu_thermal_samples)

            if is_critical or is_warning:
                thr_active = throttle and mx(throttle) >= 1.0
                severity = "CRITICAL" if is_critical else "WARNING"
                add("CPU Thermal Throttling", severity,
                    "CPU is hitting its thermal ceiling. ADVICE: Check CPU cooler mounting, re-apply thermal paste, or ensure your AIO pump hasn't failed.",
                    [f"Peak Temp: {mx(cpu_temp):.1f}°C",
                     f"Limit: {limit:.0f}°C",
                     f"Throttling Flag: {'Active' if thr_active else 'Inactive'}"])
        
        # 2. GPU THERMALS (HOTSPOT & DELTA)
        if gpu_hotspot:
            hs_max = mx(gpu_hotspot)
            hs_limit = self.temp_limits.get('HOTSPOT', 95.0)
            
            # Identify the Edge temperature column
            gpu_edge = self._col_excl(('GPU', 'TEMP'), excl=('HOTSPOT', 'MEMORY', 'CPU'))
            
            # Calculate Delta (Hotspot - Edge)
            delta_val = 0
            if gpu_edge:
                # Calculate the maximum difference found in the logs
                delta_series = self.df[gpu_hotspot] - self.df[gpu_edge]
                delta_val = delta_series.max()
            
            # Evidence list: Always included to provide context
            evidence = [
                f"Hotspot Max: {hs_max:.1f}°C",
                f"Thermal Delta: {delta_val:.1f}°C"
            ]

            # 2a. CRITICAL: Absolute Temperature Over Limit
            if hs_max >= hs_limit:
                add("GPU Overheating (Hotspot)", "CRITICAL", 
                    "The GPU Hotspot is at dangerous levels. ADVICE: Immediately increase GPU fan curves in Afterburner and check for obstructed case airflow.",
                    evidence + [f"Hardware Limit: {hs_limit}°C"])
            
            # 2b. WARNING: High Temperature OR High Delta (Mounting Issue)
            elif hs_max > (hs_limit - 10) or delta_val >= 21.0:
                if delta_val >= 21.0:
                    msg = "High thermal delta detected. ADVICE: A gap over 21°C suggests poor mounting pressure or 'pump-out' of thermal paste. Consider re-pasting the GPU."
                else:
                    msg = "GPU Hotspot is approaching dangerous levels. ADVICE: Increase fan speeds or reduce the power limit."
                
                add("GPU Thermal Warning", "WARNING", msg, evidence)
            
        # 3. PSU +12V RAIL STABILITY
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
        
        # 4. GPU DRIVER TDR / CRASH
        
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
                    ]
                )
        
        # 5. MULTI-DRIVE OVERHEATING (ATTEMPT TO SCANS ALL DRIVES)
        drive_temps = [c for c in df.columns if 'TEMP' in c.upper() and any(k in c.upper() for k in ['DRIVE', 'NVME', 'SSD'])]

        for d_col in drive_temps:
            peak = mx(d_col)
            u_col = d_col.upper()
            
            # HDD detection.
            if any(k in u_col for k in ['HDD', 'HARD DRIVE', 'ST']): # 'ST' often starts Seagate HDD names
                crit_limit = 55.0  # HDDs should never cross 55C
                warn_limit = 45.0  # Performance/reliability drops at 45C
                drive_type = "HDD (Mechanical)"
            else:
                # Default to NVMe/SSD limits
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
        
        # 6. HARDWARE ERROR (WHEA)
        
        whea = self._col('WHEA')
        if whea and mx(whea) > 0:
            add("Hardware (WHEA) Errors", "CRITICAL", 
                "Windows detected physical hardware errors. ADVICE: This is often caused by unstable RAM (XMP/EXPO) or CPU undervolts. Revert to BIOS defaults.",
                [f"Total Errors: {int(mx(whea))}"])
        
        # 7. CPU POWER LIMIT THROTTLING
        
        ppt_limit = self._col('CPU', 'PPT', 'LIMIT')
        if cpu_power and ppt_limit and self._sustained(cpu_power, mx(ppt_limit)*self.sig_ppt_sat_pct,
                                                        self.sig_ppt_sat_samples):
            add("CPU Power Limit Reached", "WARNING", 
                "CPU performance is being capped by power limits. ADVICE: If temps are safe, you can increase 'PPT' or 'PL1/PL2' limits in BIOS.",
                [f"Power Sustained at: {avg(cpu_power):.1f}W"])
        
        # 8. FAN FAILURE / STALL (THERMAL-AWARE)
        
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
                    
                    if (is_stalled & is_hot).rolling(window=3).sum().max() >= 3:
                        add("Fan Stall Detected", "CRITICAL", 
                            f"Fan '{col}' stopped while components were hot. ADVICE: Check for cables blocking the fan blades or a failing motor.",
                            ["RPM hit 0 during load samples."])
                        break
        
        # 9. GPU VRAM OVERFLOW ANALYSIS (EVENT + DURATION BASED)
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
            # assume uniform sampling; if timestamp exists, use it instead
            if "Timestamp" in df.columns:
                df["Timestamp"] = pd.to_datetime(df["Timestamp"])
                df["_time_diff"] = df["Timestamp"].diff().dt.total_seconds().fillna(0)
                time_unit = "seconds"
            else:
                df["_time_diff"] = 1  # fallback = 1 sample = 1 unit
                time_unit = "samples"

            overflow_time = df["_time_diff"] * df["_overflow_state"]

            total_overflow_duration = overflow_time.sum()

            # per-event durations
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
                    ]
                )

            df.drop(columns=["_overflow_state", "_time_diff"], inplace=True, errors="ignore")
        
        # 10. S.M.A.R.T. & WEAR-LEVELING FAILURE (HIGH-SAFETY TIER)
        
        fail_cols = [c for c in df.columns if any(k in c.upper() for k in ['DRIVE', 'SSD', 'NVME']) 
                     and any(k in c.upper() for k in ['FAILURE', 'WARNING'])]
        
        life_cols = [c for c in df.columns if 'REMAINING LIFE' in c.upper() or 'DRIVE HEALTH' in c.upper()]

        # 1. Hardware Failure Flags (The "Red Alert")
        for f_col in fail_cols:
            if mx(f_col) >= 1.0:
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

        # 2. SSD Lifespan Exhaustion (The "Wear Alert")
        for l_col in life_cols:
            current_life = df[l_col].min()
            
            # Tier 1: CRITICAL - 5% or less (High Risk of Read-Only/Failure)
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
            
            # Tier 2: WARNING - 20% or less (Replacement Window)
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
        
        # 11. SYSTEM RAM EXHAUSTION
        
        ram_load = self._col('PHYSICAL', 'MEMORY', 'LOAD')
        if ram_load and mx(ram_load) > self.sig_ram_exhaust_pct:
            add("System RAM Exhaustion", "WARNING", 
                "Physical RAM is nearly full. ADVICE: Close browser tabs, Discord, or other background apps. Consider upgrading to 32GB RAM.", 
                [f"Max Load: {mx(ram_load):.1f}%", f"Threshold: {self.sig_ram_exhaust_pct}%"])
        
        # 12. VIRTUAL MEMORY (PAGE FILE) PRESSURE
        
        v_load = self._col('VIRTUAL', 'MEMORY', 'LOAD') or self._col('PAGE', 'FILE', 'USAGE')
        if v_load and mx(v_load) > 98:
            add("Virtual Memory Limit", "CRITICAL", 
                "The system 'Commit Limit' is full. ADVICE: Ensure your Windows Page File is set to 'System Managed' and your C: drive is not full.", 
                [f"Commit Charge: {mx(v_load):.1f}%"])
        
        # 13. CPU BOTTLENECK
        
        if gpu_usage_col and cpu_usage_col:
            bn = (df[gpu_usage_col] < self.sig_cpu_bn_gpu_pct) & (df[cpu_usage_col] > self.sig_cpu_bn_cpu_pct)
            if bn.rolling(window=self.sig_cpu_bn_samples).sum().max() >= self.sig_cpu_bn_samples:
                add("CPU Bottleneck", "WARNING", 
                    "CPU is maxed out while GPU is idling. ADVICE: Increase resolution/graphics settings to shift load to GPU, or close background apps.", 
                    [f"Avg GPU Usage during spike: {df.loc[bn, gpu_usage_col].mean():.1f}%",
                     f"Thresholds: GPU < {self.sig_cpu_bn_gpu_pct}%, CPU > {self.sig_cpu_bn_cpu_pct}%"])
        
        # 14. VRM OVERHEATING
        
        vrm_temp = self._col('VRM') or self._col('MOS')
        if vrm_temp and mx(vrm_temp) > self.sig_vrm_temp_max:
            add("VRM Overheating", "CRITICAL", 
                "Motherboard power delivery is too hot. ADVICE: Improve case airflow or add a small fan directed at the motherboard heatsinks.", 
                [f"Max: {mx(vrm_temp):.1f}°C", f"Threshold: {self.sig_vrm_temp_max}°C"])
        
        # 15. CPU CLOCK STRETCHING (ACTIVE-CORE VALIDATION)

        req_cols = [c for c in df.columns if 'Clock (perf #' in c]
        if req_cols:
            n_cores        = len(req_cols)
            per_core_ratios  = []
            per_core_active  = []   # boolean Series per core, True = core is active

            for i, req_col in enumerate(req_cols):
                t0_col = f"Core {i} T0 Effective Clock [MHz]"
                t1_col = f"Core {i} T1 Effective Clock [MHz]"

                req = df[req_col].replace(0, np.nan)

                # Only consider samples where the requested clock is meaningful
                # (above 300 MHz rules out C-state idle samples)
                valid_req = req > 300

                core_ratios  = []
                core_weights = []
                core_active  = pd.Series(False, index=df.index)

                for eff_col in [t0_col, t1_col]:
                    if eff_col not in df.columns:
                        continue
                    eff = df[eff_col]

                    # Active = effective clock is at least 35% of requested + 100 MHz
                    # Stricter than the old formula to avoid flagging genuine C-state exits
                    active = valid_req & (eff > (0.35 * req + 100))

                    ratio  = (eff / req).where(active)
                    # Use effective clock as weight so higher-frequency samples
                    # contribute more — avoids idle samples pulling the ratio down
                    weight = eff.where(active)

                    core_ratios.append(ratio)
                    core_weights.append(weight)
                    core_active = core_active | active

                if not core_ratios:
                    continue

                ratios  = pd.concat(core_ratios,  axis=1)
                weights = pd.concat(core_weights, axis=1)

                # Use median across T0/T1 threads to be robust against one thread being parked
                core_ratio  = ratios.median(axis=1)

                # Weight = fraction of threads that are active (0, 0.5, or 1.0)
                core_weight = ratios.notna().astype(float).mean(axis=1)

                # Require at least 3 of last 5 samples to show core as active
                # before we trust the ratio — avoids single-sample bursts
                stable_active = core_active.rolling(5, min_periods=3).sum() >= 3
                core_ratio  = core_ratio.where(stable_active)
                core_weight = core_weight.where(stable_active)

                per_core_ratios.append(core_ratio)
                per_core_active.append(core_active.astype(int))

            if per_core_ratios:
                all_ratios  = pd.concat(per_core_ratios, axis=1)
                all_active  = pd.concat(per_core_active, axis=1)

                # Weighted mean ratio across all cores
                # Weight columns are fraction-active (0–1), aligned with ratio NaN mask
                weight_mat   = all_ratios.notna().astype(float)
                weight_total = weight_mat.sum(axis=1).replace(0, np.nan)
                weighted_sum = (all_ratios.fillna(0) * weight_mat).sum(axis=1)
                mean_ratio   = (weighted_sum / weight_total).replace([np.inf, -np.inf], np.nan)

                # Per-core worst ratio (useful for evidence reporting)
                worst_core_ratio = all_ratios.min(axis=1)

                # Core pressure = fraction of cores that are active at each sample
                # Fix: use actual active flag sum / total cores (not notna which is always True)
                active_count  = all_active.sum(axis=1)
                core_pressure = (active_count / n_cores).rolling(5, min_periods=3).mean()

                # System load from total CPU usage if available
                system_load = df.get(
                    'Total CPU Usage [%]',
                    pd.Series(0.0, index=df.index)
                ).fillna(0)

                # valid_load: sample is under meaningful load via two signals
                sys_signal  = np.clip(system_load / 100.0, 0, 1)
                core_signal = np.clip(core_pressure.fillna(0), 0, 1)
                # Balanced 60/40 — core pressure is a direct signal, don't underweight it
                load_score  = 0.6 * sys_signal + 0.4 * core_signal
                valid_load  = load_score > 0.55

                # Transition filter: suppress detection during rapid load changes
                # (clock stretching during a load ramp is normal scheduler behavior)
                # Use a simple rolling std of load as the transition indicator —
                # more interpretable than the exponential decay that masked real events
                load_std       = system_load.rolling(5, min_periods=3).std().fillna(0)
                in_transition  = load_std > 15.0   # >15% std in a 5-sample window = ramp

                # Classification thresholds
                # major: effective clock is severely behind requested under load
                # minor: moderate deficit — could be thermal, power, or scheduling
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

                # Persistence filter: require the condition to hold for a sustained
                # window, not just a few samples — single rolling pass (no double smooth)
                major_event = major.rolling(8, min_periods=5).mean() > 0.55
                minor_event = minor.rolling(8, min_periods=5).mean() > 0.50

                # Per-core breakdown for evidence — which cores were worst
                core_avg_ratios = all_ratios.mean()
                worst_cores     = core_avg_ratios.nsmallest(3)

                if major_event.any():
                    avg_r     = mean_ratio[major_event].mean()
                    worst_r   = mean_ratio[major_event].min()
                    peak_load = system_load[major_event].max()
                    peak_pressure = core_pressure[major_event].max()

                    # Determine likely cause from other signals
                    cause_hints = []
                    cpu_temp_col = self._col('CPU', 'TEMP') or self._col('TDIE') or self._col('TCTL')
                    if cpu_temp_col:
                        peak_temp = df[cpu_temp_col][major_event].max()
                        t_limit   = self.temp_limits.get('TDIE', self.temp_limits.get('CORE', 95.0))
                        if peak_temp >= t_limit * 0.92:
                            cause_hints.append(f"CPU temp {peak_temp:.1f}°C near limit — likely thermal throttle")
                    ppt_col = self._col('CPU', 'PPT') or self._col('CPU', 'POWER')
                    ppt_lim_col = self._col('CPU', 'PPT', 'LIMIT') or self._col('CPU', 'POWER', 'LIMIT')
                    if ppt_col and ppt_lim_col:
                        ppt_ratio = df[ppt_col].mean() / (df[ppt_lim_col].mean() + 1e-9)
                        if ppt_ratio >= 0.95:
                            cause_hints.append("CPU PPT at limit — power throttling")
                    if not cause_hints:
                        cause_hints.append("No obvious thermal/power cause found — check for OS scheduler issues or BIOS power limits")

                    worst_core_strs = [
                        f"Core {c.split()[1] if 'Core' in str(c) else c}: avg ratio {v:.2f}"
                        for c, v in worst_cores.items() if not np.isnan(v)
                    ]

                    add(
                        name="CPU Clock Stretching — Major",
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
                        name="CPU Clock Stretching — Minor",
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

        # 16 & 16b. PSU SIGNATURES
        if not is_laptop:
            # 16. PSU +5V / +3.3V RAIL STABILITY
            
            for r_name, low, high in [('+5V', self.sig_v5_lo, self.sig_v5_hi),
                                       ('+3.3V', self.sig_v33_lo, self.sig_v33_hi)]:
                col = self._col(r_name)
                if col and (df[col].min() < low or df[col].max() > high):
                    add(f"PSU {r_name} Rail Unstable", "WARNING", 
                        f"Low-voltage rail {r_name} is out of spec. ADVICE: This can cause random USB disconnects or drive errors. Check PSU health.",
                        [f"Detected Range: {df[col].min():.2f}V - {df[col].max():.2f}V",
                         f"Spec: {low}V - {high}V"])
    
            # 16b. PSU HARDWARE FAILURE INDICATORS
    
            _psu_evidence = []
            _psu_severity_score = 0   # more signals = higher confidence
    
            # Signal A: +12V rail sag 
            v12_col = self._col('+12V')
            if v12_col:
                v12s = df[v12_col].dropna()
                sag_mask = v12s < self.sig_v12_lo
                sag_pct  = float(sag_mask.mean()) * 100
                if sag_pct > 5.0:
                    _psu_evidence.append(f"+12V sagging below {self.sig_v12_lo}V in {sag_pct:.1f}% of samples (min {v12s.min():.2f}V)")
                    _psu_severity_score += 2 if v12s.min() < 11.2 else 1
    
            # Signal B: +5V rail out of spec
            v5_col = self._col('+5V')
            if v5_col:
                v5s = df[v5_col].dropna()
                if v5s.min() < self.sig_v5_lo or v5s.max() > self.sig_v5_hi:
                    _psu_evidence.append(f"+5V rail out of spec: {v5s.min():.2f}V – {v5s.max():.2f}V (spec {self.sig_v5_lo}–{self.sig_v5_hi}V)")
                    _psu_severity_score += 1
    
            # Signal C: +3.3V rail out of spec
            v33_col = _a('rail_33v') or self._col('+3.3V')
            if v33_col:
                v33s = df[v33_col].dropna()
                if v33s.min() < self.sig_v33_lo or v33s.max() > self.sig_v33_hi:
                    _psu_evidence.append(f"+3.3V rail out of spec: {v33s.min():.2f}V – {v33s.max():.2f}V (spec {self.sig_v33_lo}–{self.sig_v33_hi}V)")
                    _psu_severity_score += 1
    
            # Signal D: Yes/No PSU-specific throttle flags triggered
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
    
            # Signal E: cross-rail correlation — multiple rails sagging simultaneously

            rails_sagging = sum([
                1 for col, lo in [(v12_col, self.sig_v12_lo),
                                   (v5_col, self.sig_v5_lo),
                                   (v33_col, self.sig_v33_lo)]
                if col and df[col].dropna().min() < lo
            ])
            if rails_sagging >= 2:
                _psu_evidence.append(f"{rails_sagging} rails simultaneously below spec — strong indicator of PSU output stage degradation")
                _psu_severity_score += 2
    
            # Signal F: high rail voltage ripple (std dev > 0.15V indicates cap degradation)
            for lbl, col in [('+12V', v12_col), ('+5V', v5_col), ('+3.3V', v33_col)]:
                if col:
                    ripple = df[col].dropna().std()
                    if ripple > 0.15:
                        _psu_evidence.append(f"{lbl} rail ripple/noise: σ={ripple:.3f}V (>0.15V suggests capacitor wear)")
                        _psu_severity_score += 1
    
            # Signal G: GPU TDR + 12V sag co-occurrence
            # A TDR immediately after a voltage drop is strong evidence of PSU failure
            if v12_col and gpu_usage_col and gpu_clock:
                sag_now  = df[v12_col] < self.sig_v12_lo
                low_gpu  = df[gpu_usage_col] < 5
                clk_dead = (df[gpu_clock].rolling(3).std() < 1.0) & (df[gpu_clock] > 0)
                co_occur = (sag_now & low_gpu & clk_dead).sum()
                if co_occur >= 3:
                    _psu_evidence.append(f"+12V sag coincides with GPU stall in {co_occur} samples — likely PSU-induced GPU crash")
                    _psu_severity_score += 2
    
            if _psu_severity_score >= 2 and _psu_evidence:
                sev = "CRITICAL" if _psu_severity_score >= 4 else "WARNING"
                add("PSU Hardware Failure Indicators", sev,
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
        
        # 18. STORAGE CONGESTION
        
        disk_busy = self._col('TOTAL', 'ACTIVE', 'TIME') or self._col('DISK', 'BUSY')
        if disk_busy and (df[disk_busy] >= self.sig_disk_busy_pct).rolling(
                window=self.sig_disk_busy_samples).sum().max() >= self.sig_disk_busy_samples:
            add("Storage Congestion", "INFO", 
                "System drive was 100% busy. ADVICE: Check for background Windows Updates or Antivirus scans that may be fighting the game for disk access.", 
                ["Persistent 100% disk usage detected.",
                 f"Threshold: {self.sig_disk_busy_pct}% for {self.sig_disk_busy_samples} samples"])

        # 19. PHANTOM THROTTLING (CLOCK CAP)

        if cpu_clock and cpu_usage_col:
            # If the CPU is pegged but the clock is stuck at 'idle' speeds (usually <1.0GHz)
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

        # 20. GPU POWER & TDP ANALYSIS (UNIVERSAL LAPTOP/DESKTOP)

        if gpu_pwr_limit and gpu_power:
            pwr_limit_active = df[gpu_pwr_limit] >= 1.0
            hit_pct = (pwr_limit_active.sum() / len(df)) * 100
            peak_watts = mx(gpu_power)
            avg_watts = avg(gpu_power)
            
            # Detect "Limp Mode"
            # GPU is power limiting.
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
                # Standard TDP Ceiling
                desc = f"The GPU reached its power limit (Peak: {peak_watts:.1f}W)."
                if is_laptop:
                    desc += " ADVICE: Ensure you are in 'Performance' mode and the original charger is connected."
                else:
                    desc += " ADVICE: If temps are safe, you can increase the Power Limit in Afterburner."

                add(
                    name="GPU Power Limit Saturated",
                    severity="WARNING",
                    description=desc,
                    evidence=[f"Average Load: {avg_watts:.1f}W", f"Limit Duration: {hit_pct:.1f}%"]
                )

        # 21. PCIe BUS INTERFACE MISMATCH (WIDTH/SPEED)

        pcie_width = self._col('GPU', 'PCIE', 'WIDTH')
        pcie_gen   = self._col('GPU', 'PCIE', 'GENERATION') or self._col('GPU', 'BUS', 'GEN')
        
        if pcie_width and pcie_gen:
            # We look for the maximum reached during the log (when the GPU is active)
            max_width = mx(pcie_width)
            max_gen   = mx(pcie_gen)
            
            # Logic: Most modern GPUs should be at x16. 
            # If it's stuck at x4 or x1 even under load, there's a physical/BIOS issue.
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

        # 22. BACKGROUND PROCESS INTERFERENCE (OS JITTER)

        # We look for high 'Total' CPU usage while the GPU is significantly under-loaded,
        # or spikes in CPU usage that don't correlate with GPU demand.
        if cpu_usage_col and gpu_usage_col:
            # Logic: If CPU is working hard (>70%) but GPU is bored (<40%), 
            # something else is fighting for the processor.
            os_jitter = (df[cpu_usage_col] > 70) & (df[gpu_usage_col] < 40)
            
            if os_jitter.rolling(window=self.sig_cpu_bn_samples).sum().max() >= self.sig_cpu_bn_samples:
                add(
                    name="Background Process Interference",
                    severity="INFO",
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

        # 23. GPU PRIORITY & HARDWARE ACCEL CONFLICT
        if ft_col and gpu_usage_col:
            
            rolling_avg_ft = df[ft_col].rolling(window=10, center=True).mean()
            df = df.assign(jitter_calc = df[ft_col] / rolling_avg_ft)
            
            is_stuttering = df['jitter_calc'] > 1.5
            stutter_count = is_stuttering.sum()
            
            if stutter_count > 3:
                stutter_indices = df[is_stuttering].index
                avg_gpu_load = df.loc[stutter_indices, gpu_usage_col].mean()
                
                # Check for the 'Bus Load' fingerprint (Background data movement)
                bus_activity = df.loc[stutter_indices, gpu_bus_col].max() if gpu_bus_col else 0
                
                # BRANCH: Hardware Acceleration Conflict

                if (avg_gpu_load < 92) or (bus_activity > 5.0):
                    usage_gap = 100 - avg_gpu_load
                    add(
                        name="GPU Priority Conflict (Background App)",
                        severity="WARNING" if usage_gap < 35 else "CRITICAL",
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
        # 24. VRAM SWAPPING (SHARED MEMORY OVERFLOW)

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
        # 25. CONNECTOR THERMAL RISK (MELTING/FIRE HAZARD)
        if gpu_12v_input_v and gpu_12v_input_w:
            
            high_load_mask = df[gpu_12v_input_w] > 300
            
            if high_load_mask.any():
                min_v = df.loc[high_load_mask, gpu_12v_input_v].min()
                max_w = df[gpu_12v_input_w].max()
                
                # Thresholds: 
                # 11.70V: Warning (High Resistance)
                # 11.50V: CRITICAL (Potential Melting Hazard)
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
        # 26. VRAM JUNCTION THERMAL THROTTLING

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

        # 27. PCIE LINK INTEGRITY (Silent Errors)

        if pcie_errors:
            total_pcie_errors = df[pcie_errors].sum()
            if total_pcie_errors > 0:
                add(
                    name="PCIe Bus Signal Instability",
                    severity="CRITICAL",
                    description=(
                        "Detected hardware-level PCIe errors. This is usually caused by a "
                        "faulty PCIe Riser cable, a loose GPU seating, or an unstable PCIe Gen 4/5 link."
                    ),
                    evidence=[f"Total PCIe Errors: {total_pcie_errors}", "ADVICE: Reseat GPU or replace Riser."]
                )

        # 28. GPU WAIT-STATE ANALYSIS (PresentMon Elite)
        if gpu_wait_ms and ft_col:
            # Calculate the percentage of the frame the GPU spent doing nothing
            df = df.assign(wait_ratio = df[gpu_wait_ms] / df[ft_col])
            
            # Threshold: If the GPU is waiting for >25% of the total frame time, 
            # it's an optimization or priority bottleneck.
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

                # 29. RYZEN FABRIC DESYNC (AMD ONLY)

        if fclk_col and uclk_col and mclk_col:

            f_med = df[fclk_col].median()
            u_med = df[uclk_col].median()
            m_med = df[mclk_col].median()

            # -----------------------------
            # PLATFORM DETECTION
            # -----------------------------
            is_ddr5 = m_med > 2400  # simple + reliable


            # -----------------------------
            # DDR5: CHECK UCLK vs MCLK
            # -----------------------------
            if is_ddr5:

                delta = (df[uclk_col] - df[mclk_col]).abs()

                # filter noise
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


            # -----------------------------
            # DDR4: CHECK FCLK vs UCLK
            # -----------------------------
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

        # 30. GPU POWER LIMIT OSCILLATION (SAWTOOTH STUTTER)

        if gpu_pwr_limit and gpu_clk_col:
            # Convert 'Yes/No' to 1/0 if necessary
            limit_active = df[gpu_pwr_limit].apply(lambda x: 1 if x == 'Yes' else 0)
            
            # Detect how many times it toggled on/off
            toggles = limit_active.diff().abs().sum()
            
            # If it toggles more than 5 times in a log, it's 'Ping-Ponging'
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
        # 31. KERNEL INTERRUPT / DPC LATENCY SPIKES

        if cpu_utility:
            
            usage_std = df[cpu_utility].std()
            
            if usage_std > 15: # High volatility in system response
                add(
                    name="Kernel Driver Latency (DPC/ISR)",
                    severity="WARNING",
                    description=(
                        "Detected high volatility in system utility. This usually indicates "
                        "a background driver (Wi-Fi, Audio, or USB) is causing micro-stutters."
                    ),
                    evidence=[
                        f"System Load Variance: {usage_std:.2f}%",
                        "ADVICE: Update network/audio drivers or disable unused USB controllers."
                    ]
                )

        # 32. DRIVE I/O CONGESTION / HITCHING

        drive_activity = self._col('Total Activity [%]') or self._col('Read Activity [%]')
        drive_warning  = self._col('Drive Warning [Yes/No]')

        if drive_activity:
            # If the drive is pinned at 100% for several samples, it's a bottleneck
            is_pinned = (df[drive_activity] > 98).sum() > 3
            
            if is_pinned or (drive_warning and (df[drive_warning] == 'Yes').any()):
                add(
                    name="Storage I/O Bottleneck / Hitching",
                    severity="CRITICAL" if (drive_warning and (df[drive_warning] == 'Yes').any()) else "WARNING",
                    description="The system drive is maxed out or reporting hardware warnings, causing asset-loading hitches.",
                    evidence=["Drive at 100% activity" if is_pinned else "Hardware Warning Flag Detected", 
                              "ADVICE: Check SSD health or move game to a faster drive."],
                )

        # 33. USB BUS STABILITY & CHIPSET THERMALS

        if usb_v_col or chipset_t:
            # Check for Chipset overheating (common on X570/X670 boards)
            if chipset_t and (df[chipset_t] > 80).any():
                add(
                    name="Chipset Thermal Throttling",
                    severity="WARNING",
                    description="Motherboard chipset is overheating. This often causes USB and NVMe dropouts.",
                    evidence=[f"Max Chipset Temp: {df[chipset_t].max():.1f}°C"],
                    advice="Ensure GPU isn't blocking chipset airflow."
                )
                
            # Check for USB Voltage Sag
            if usb_v_col:
                min_usb_v = df[usb_v_col].min()
                if min_usb_v < 4.75: # Standard USB 5V rail should stay above 4.75V
                    add(
                        name="USB Rail Voltage Sag",
                        severity="CRITICAL",
                        description="USB 5V rail dropped below safety limits. This causes peripheral disconnects.",
                        evidence=[f"Min USB Voltage: {min_usb_v:.2f}V"],
                        advice="Unplug non-essential USB devices or use a powered USB hub."
                    )
        
        return hits

    def _open_alias_manager(self):
        """Open the sensor alias manager — view, delete individual aliases, or clear all."""
        is_dark = self.is_dark
        bg   = "#121212" if is_dark else "#f8f9fa"
        bg2  = "#1e1e1e" if is_dark else "#ffffff"
        bg3  = "#2a2a2a" if is_dark else "#e9ecef"
        fg   = "#e0e0e0" if is_dark else "#212529"
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
            "fclk":        "Fabric Clock (FCLK) — AMD Ryzen",
            "uclk":        "Unified Memory Clock (UCLK) — AMD Ryzen",
            "mclk":        "Memory Clock (MCLK)",
            "gpu_busy":    "GPU Busy Time (PresentMon)",
            "gpu_wait":    "GPU Wait Time (PresentMon)",
            "chipset_temp":"Chipset Temperature",
            "pcie_errors": "PCIe Error Counters",
            "sys_interrupts": "System Interrupts / DPC Latency",
        }

        aliases = dict(self.analyzer.aliases)  # working copy

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

        outer = tk.Frame(dialog, bg=acc, padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg=bg, padx=14, pady=12)
        inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(inner, text="⚙  Sensor Alias Manager",
                 font=('Segoe UI', 12, 'bold'), bg=bg, fg=acc).pack(anchor='w')
        tk.Label(inner,
                 text="Click ✕ next to any alias to remove it. Changes apply immediately.",
                 font=('Segoe UI', 9), bg=bg, fg=muted).pack(anchor='w', pady=(2, 10))

        list_outer = tk.Frame(inner, bg=bg2, bd=1, relief='flat')
        list_outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(list_outer, bg=bg2, highlightthickness=0)
        sb = ttk.Scrollbar(list_outer, orient='vertical', command=canvas.yview)
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

        row_widgets = {}  # key -> list of row frames (one per alias entry)

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

                # Section header
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

                    # Capture loop variables
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

        # Bottom buttons
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

        # Critical Sensors
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
            ("fclk",          "Fabric Clock (FCLK) — AMD Ryzen",
             "Used for Ryzen fabric desync detection.\n"
             "Look for the Infinity Fabric clock speed in MHz (AMD systems only).\n"
             "Common names: FCLK [MHz]",
             self._col('FCLK'),
             lambda c: 'FCLK' in c.upper() and '[MHZ]' in c.upper()),
            ("uclk",          "Unified Memory Clock (UCLK) — AMD Ryzen",
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
            # Check if any existing alias for this key already works in current CSV
            entry = aliases.get(key)
            if entry:
                existing = entry if isinstance(entry, list) else [entry]
                if any(c in self.df.columns for c in existing):
                    continue  

            # Skip if auto-detect already found it
            if auto_result:
                continue

            # Build candidate list — exclude any already confirmed aliases
            already_known = set(entry if isinstance(entry, list) else ([entry] if entry else []))
            candidates = [c for c in df_cols
                          if filt(c) and c != self.analyzer.time_col
                          and c not in already_known]
            if not candidates:
                continue  # nothing to offer — skip silently

            # Show picker dialog
            chosen = self._sensor_picker_dialog(label, candidates, desc)
            if chosen:
                # Append to existing list — preserves all previous aliases
                existing_list = aliases.get(key, [])\
                    if isinstance(aliases.get(key), list) else \
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
        bg   = "#121212" if is_dark else "#f8f9fa"
        bg2  = "#1e1e1e" if is_dark else "#ffffff"
        bg3  = "#1a2a3a" if is_dark else "#e8f4fd"
        fg   = "#e0e0e0" if is_dark else "#212529"
        acc  = "#1f6aa5"

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

        # Description box
        if description:
            desc_frame = tk.Frame(inner, bg=bg3, padx=10, pady=8,
                                  highlightthickness=1,
                                  highlightbackground="#2a4a6a" if is_dark else "#b8d4ea")
            desc_frame.pack(fill=tk.X, pady=(0, 10))
            tk.Label(desc_frame, text="ℹ  What to look for:",
                     font=('Segoe UI', 8, 'bold'), bg=bg3,
                     fg="#4f8ef7", anchor='w').pack(anchor='w')
            tk.Label(desc_frame, text=description,
                     font=('Segoe UI', 8), bg=bg3,
                     fg="#a0c4e8" if is_dark else "#2a4a6a",
                     justify='left', anchor='w',
                     wraplength=pw - 60).pack(anchor='w', pady=(4, 0))

        # Scrollable list of radio buttons
        list_frame = tk.Frame(inner, bg=bg2, bd=1, relief='flat')
        list_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(list_frame, bg=bg2, highlightthickness=0,
                           height=min(len(candidates) * 28, 320))
        sb = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
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

        # Buttons
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
        bg      = "#121212" if is_dark else "#f8f9fa"
        fg      = "#e0e0e0" if is_dark else "#212529"
        accent  = "#1f6aa5" if is_dark else "#3498db"
        bg2     = "#1e1e1e" if is_dark else "#ffffff"

        # -- Spinner dialog while extract_hardware_names() runs -------------
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
            hw = self.analyzer.extract_hardware_names()
            self.root.after(0, lambda: _show_results(hw))

        def _show_results(hw):
            if wait_win.winfo_exists():
                wait_win.grab_release()
                wait_win.destroy()

            # -- Main hardware dialog ---------------------------------------
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

        # -- Wait dialog (non-blocking, stays alive via mainloop) -----------
        is_dark  = self.is_dark
        bg_dark  = "#121212" if is_dark else "#f8f9fa"

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

        # Title row with inline spinner
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

        # Progress bar
        bar_frame = tk.Frame(inner, bg=bg_dark)
        bar_frame.pack(fill=tk.X, pady=(8, 0))
        bar_bg = tk.Frame(bar_frame, bg="#2a2a2a" if is_dark else "#dee2e6", height=4, bd=0)
        bar_bg.pack(fill=tk.X)
        bar_fg = tk.Frame(bar_bg, bg="#1f6aa5", height=4, bd=0)
        bar_fg.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        # Braille spinner — runs purely on main thread via after(), costs nothing
        _SPIN_FRAMES = [" ⠋", " ⠙", " ⠹", " ⠸", " ⠼", " ⠴", " ⠦", " ⠧", " ⠇", " ⠏"]
        _spin_idx = [0]
        def _tick_spinner():
            if not wait_win.winfo_exists():
                return
            _spin_idx[0] = (_spin_idx[0] + 1) % len(_SPIN_FRAMES)
            spin_var.set(_SPIN_FRAMES[_spin_idx[0]])
            wait_win.after(80, _tick_spinner)
        _tick_spinner()

        # Thread-safe UI updaters via after()
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

        # -- All heavy work runs here, off the main thread ------------------
        def _generate():
            try:
                import matplotlib
                matplotlib.use('Agg')   # non-interactive PNG-only backend, safe off main thread
                import matplotlib.pyplot as _plt
                df   = self.df
                cols = list(df.columns)
                sel  = [c for c, v in self.vars.items() if v.get() and c in df.columns]
                x_vals, ts, use_time = self._get_x_axis()
                colors_cycle = _plt.rcParams['axes.prop_cycle'].by_key()['color']

                # helpers
                def _fig_to_b64(fig) -> str:
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
                    fig, ax = _plt.subplots(figsize=figsize)
                    fig.patch.set_facecolor('#1a1a2e')
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
                        import matplotlib.ticker as ticker
                        ax.xaxis.set_major_formatter(
                            ticker.FuncFormatter(lambda v, _: self._format_elapsed(v)))
                        ax.tick_params(axis='x', labelrotation=20)
                    fig.subplots_adjust(right=0.72)
                    b64 = _fig_to_b64(fig)
                    _plt.close(fig)
                    return _chart_html(b64, title)

                # 1. Selected sensors
                _set_status("Rendering selected sensor chart\u2026", 0.10)
                charts_selected_html = ""
                if sel:
                    charts_selected_html = _make_chart(
                        sel, "Selected Sensors",
                        figsize=(13, max(3.5, len(sel) * 0.35)))

                # 2. Category charts
                _set_status("Rendering category charts\u2026", 0.25)
                cat_charts_html = ""
                cat_groups: dict = {}
                # Units that make no sense on a shared chart — skip these columns
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

                # 3. PSU rail charts
                _set_status("Rendering PSU rail charts\u2026", 0.50)
                psu_charts_html = ""
                _RAIL_KEYWORDS = {
                    '+12V':  ['12V', '12 V'],
                    '+5V':   ['5V', '5 V'],
                    '+3.3V': ['3.3V', '3.3 V', '3V3'],
                }
                _RAIL_EXCL = ['[W]', '[A]', 'POWER', 'CURRENT', 'WATT',
                              'VID', 'OFFSET', 'LIMIT', 'PPT', 'TDP',
                              'PCIE', 'INPUT', 'GPU', 'HPWR', 'VDDQ', 'FBVDD']
                for rail_name, keywords in _RAIL_KEYWORDS.items():
                    rail_cols = []
                    for c in cols:
                        if c not in df.columns:
                            continue
                        cu = c.upper()
                        if '[V]' not in cu:
                            continue
                        if any(ex in cu for ex in _RAIL_EXCL):
                            continue
                        if any(k.upper() in cu for k in keywords):
                            rail_cols.append(c)
                    if not rail_cols:
                        continue
                    lo, hi = self.volt_rails.get(rail_name, (None, None))

                    def _make_rail_chart(rcols, rtitle, rlo, rhi):
                        fig, ax = _plt.subplots(figsize=(13, 3.5))
                        fig.patch.set_facecolor('#1a1a2e')
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
                            import matplotlib.ticker as ticker
                            ax.xaxis.set_major_formatter(
                                ticker.FuncFormatter(lambda v, _: self._format_elapsed(v)))
                            ax.tick_params(axis='x', labelrotation=20)
                        fig.subplots_adjust(right=0.72)
                        b64 = _fig_to_b64(fig)
                        _plt.close(fig)
                        return _chart_html(b64, rtitle)

                    spec_str = f"  |  Spec: {lo}V \u2013 {hi}V" if lo is not None else ""
                    psu_charts_html += _make_rail_chart(
                        rail_cols, f"PSU Rail: {rail_name}{spec_str}", lo, hi)

                # 4. Hardware info
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

                # 5. Metadata
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

                # 6. Per-sensor stats
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

                # 7. Signatures
                _set_status("Running signature analysis\u2026", 0.80)
                sigs = self._run_signatures()
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

                # 8. Out-of-spec sensors
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

                # 9. Assemble & write
                _set_status("Writing report file\u2026", 0.95)
                html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RESYNC.ERR Session Report \u2014 {csv_name}</title>
<style>
:root{{--bg:#0d0d1a;--bg2:#13132b;--bg3:#1a1a38;--accent:#4f8ef7;--accent2:#a78bfa;
      --text:#e2e8f0;--muted:#64748b;--border:#2d2d5a;--crit:#ff4d4d;--warn:#f59e0b;
      --info:#38bdf8;--good:#22c55e;--radius:10px;}}
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

        def _show(results):
            is_dark = self.is_dark
            bg     = "#121212" if is_dark else "#f8f9fa"
            fg     = "#e0e0e0" if is_dark else "#212529"
            accent = "#1f6aa5" if is_dark else "#3498db"

            dialog = tk.Toplevel(self.root)
            dialog.title("Hardware Failure Diagnosis")
            dialog.geometry("680x620")
            dialog.minsize(520, 400)
            dialog.grab_set()
            dialog.configure(bg=bg)

            self.root.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 340
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 310
            dialog.geometry(f"680x620+{x}+{y}")

            tk.Label(dialog, text="Hardware Failure Diagnosis",
                    font=('Segoe UI', 13, 'bold'),
                    bg=bg, fg=accent).pack(pady=(14, 2))

            tk.Label(dialog,
                    text=f"Analyzed {len(self.df)} samples — {len(results)} signature(s) detected",
                    font=('Segoe UI', 9),
                    bg=bg, fg="#888").pack(pady=(0, 10))

            outer = tk.Frame(dialog, bg=bg)
            outer.pack(fill=tk.BOTH, expand=True, padx=12)

            canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
            sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
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

                        # -- CPU ------------------------------------------------------
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

                        "CPU Clock Stretching — Major": (
                            _cols("EFFECTIVE", "CLOCK") |
                            _cols("CLOCK", "PERF") |
                            _cols("CPU", "USAGE") | _cols("CPU", "LOAD") |
                            _any("TOTAL CPU USAGE", "TOTAL CPU LOAD",
                                 "AVERAGE EFFECTIVE", "EFF CLOCK",
                                 "T0 EFFECTIVE", "T1 EFFECTIVE",
                                 "CORE RATIO", "BUS CLOCK")
                        ),

                        "CPU Clock Stretching — Minor": (
                            _cols("EFFECTIVE", "CLOCK") |
                            _cols("CLOCK", "PERF") |
                            _cols("CPU", "USAGE") | _cols("CPU", "LOAD") |
                            _any("TOTAL CPU USAGE", "TOTAL CPU LOAD",
                                 "AVERAGE EFFECTIVE", "EFF CLOCK",
                                 "T0 EFFECTIVE", "T1 EFFECTIVE")
                        ),

                        # -- GPU ------------------------------------------------------
                        "GPU Thermal Warning": (
                            _any("GPU TEMPERATURE", "GPU TEMP [",
                                 "GPU HOT", "GPU HOTSPOT", "HOT SPOT",
                                 "GPU JUNCTION", "GPU MEMORY JUNCTION",
                                 "GPU THERMAL", "THERMAL LIMIT",
                                 # AMD variants
                                 "GPU EDGE", "EDGE TEMP", "GPU JUNCTION TEMP",
                                 # NVIDIA variants
                                 "GPU CORE TEMP", "GPU DIODE",
                                 # German
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

                        # -- PSU RAILS -------------------------------------------------
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
                        # -- FANS / COOLING --------------------------------------------
                        "Fan Stall Detected": (
                            _any("FAN", "RPM", "PUMP", "COOLER",
                                 "FAN SPEED", "FAN RPM", "CPU FAN", "GPU FAN",
                                 "CHASSIS FAN", "CASE FAN", "SYS FAN",
                                 "AIO PUMP", "WATER PUMP",
                                 "LÜFTER", "VENTILATEUR",
                                 "CPU [RPM]", "GPU [RPM]", "FAN1", "FAN2", "FAN3") |
                            _cols("CPU", "TEMP") | _cols("GPU", "TEMP")
                        ),

                        # -- VRM -------------------------------------------------------
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

                        # -- MEMORY ---------------------------------------------------
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

                        # -- STORAGE --------------------------------------------------
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

                        # -- FRAME TIMING / PERFORMANCE --------------------------------
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

                        # -- SYSTEM / HARDWARE -----------------------------------------
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

                for r in results:

                    is_crit = r['severity'] == 'CRITICAL'
                    is_info = r.get('severity') == 'INFO'

                    card_bg   = "#2a0a0a" if (is_dark and is_crit) else \
                                "#1a2a1a" if (is_dark and not is_crit) else \
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

                    # "Select Relevant Sensors" button per signature card
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

            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

        # Use cached results if available and not dirty, otherwise re-run once
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

    def _setup_ui(self):
        flag = " [DEBUG]" if self.debug_mode else ""
        self.root.title(f"RESYNC.ERR v{CURRENT_VERSION} - {self.analyzer.path.name}{flag}")
        self.root.geometry("1600x950")
        self.root.minsize(1000, 700)
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.bind("<Control-F8>", lambda e: self._toggle_debug())

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

        # Diagnose button + live badge row
        _bg = "#121212" if self.is_dark else "#f8f9fa"
        diag_row = tk.Frame(search_f, bg=_bg)
        diag_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(diag_row, text="🔬 Diagnose Hardware Signatures",
                   command=self._open_diagnosis,
                   style="Action.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._sig_badge_var = tk.StringVar(value="⏳")
        self._sig_badge_lbl = None   # replaced by per-severity labels below

        # Per-severity badge labels
        self._badge_crit_lbl = tk.Label(diag_row, text="", font=('Segoe UI', 8, 'bold'),
                                         bg=_bg, fg="#ff4d4d", padx=3)
        self._badge_warn_lbl = tk.Label(diag_row, text="", font=('Segoe UI', 8, 'bold'),
                                         bg=_bg, fg="#f59e0b", padx=3)
        self._badge_info_lbl = tk.Label(diag_row, text="", font=('Segoe UI', 8, 'bold'),
                                         bg=_bg, fg="#38bdf8", padx=3)
        self._badge_ok_lbl   = tk.Label(diag_row, text="⏳", font=('Segoe UI', 8),
                                         bg=_bg, fg="#888", padx=3)

        self._badge_ok_lbl.pack(side=tk.RIGHT)
        self._badge_info_lbl.pack(side=tk.RIGHT)
        self._badge_warn_lbl.pack(side=tk.RIGHT)
        self._badge_crit_lbl.pack(side=tk.RIGHT)

        ttk.Button(search_f, text="🖥 View Detected Hardware", command=self._open_hardware_info).pack(fill=tk.X, pady=(0, 4))
        ttk.Button(search_f, text="⚙ Edit Detection Limits", command=self._open_limits_editor).pack(fill=tk.X, pady=(0, 8))

        # Start background watcher — marks dirty so first run fires immediately
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
        if not path:
            return
        self._load_csv_threaded(path, on_success=self._apply_new_csv)

    def _apply_new_csv(self, new_analyzer):
        """Called on the main thread once a new CSV has loaded successfully."""
        self.analyzer = new_analyzer
        self.df = self.analyzer.df
        new_cols = set(self.df.columns)
        for col, var in list(self.vars.items()):
            if col not in new_cols:
                var.set(False)
        self.filter_active = False
        self._sig_hits     = []
        self._sig_dirty    = True
        self._setup_ui()
        self._apply_theme_colors()
        self.update_plot()
        self.root.after(300, self._prompt_sensor_aliases)
        # Re-open debug window with fresh data if debug mode was active
        if self.debug_mode:
            self._open_debug_window()

    def _load_csv_threaded(self, path: str, on_success, on_error=None):
        """Show a spinner dialog, load the CSV in a background thread,
        then call on_success(analyzer) or on_error(exc) on the main thread."""
        import threading

        is_dark = self.is_dark
        bg_dark = "#121212" if is_dark else "#f8f9fa"

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

        outer = tk.Frame(wait_win, bg="#1f6aa5", padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg=bg_dark, padx=20, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        title_row = tk.Frame(inner, bg=bg_dark)
        title_row.pack(anchor='w')
        tk.Label(title_row, text="📂  Loading CSV",
                 font=('Segoe UI', 11, 'bold'), bg=bg_dark, fg="#4f8ef7").pack(side=tk.LEFT)
        spin_var = tk.StringVar(value=" ⠋")
        tk.Label(title_row, textvariable=spin_var,
                 font=('Segoe UI', 11), bg=bg_dark, fg="#1f6aa5").pack(side=tk.LEFT, padx=(6, 0))

        fname = path.replace('\\', '/').split('/')[-1]
        tk.Label(inner, text=fname, font=('Segoe UI', 9), bg=bg_dark,
                 fg="#888", anchor='w').pack(fill=tk.X, pady=(6, 0))

        bar_frame = tk.Frame(inner, bg=bg_dark)
        bar_frame.pack(fill=tk.X, pady=(8, 0))
        bar_bg = tk.Frame(bar_frame, bg="#2a2a2a" if is_dark else "#dee2e6", height=4, bd=0)
        bar_bg.pack(fill=tk.X)
        bar_fg = tk.Frame(bar_bg, bg="#1f6aa5", height=4, bd=0)
        bar_fg.place(x=0, y=0, relheight=1.0, relwidth=0.0)

        # Indeterminate bar — bounces back and forth
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
            try:
                analyzer = TelemetryAnalyzer(path)
                analyzer.load()
                def _done():
                    _close()
                    on_success(analyzer)
                self.root.after(0, _done)
            except Exception as exc:
                def _fail():
                    _close()
                    if on_error:
                        on_error(exc)
                    else:
                        messagebox.showerror("Load Error", str(exc))
                self.root.after(0, _fail)

        threading.Thread(target=_worker, daemon=True).start()


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

        try:
            self.fig.tight_layout(h_pad=0.5)
        except Exception:
            pass
        if self.multi_mode:
            self.fig.subplots_adjust(right=0.80)
        else:
            self.fig.subplots_adjust(right=0.82)
        self.canvas_widget.draw_idle()


if __name__ == "__main__":
    import threading
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if not path:
        root.destroy()
    else:
        # -- Startup loading spinner -------------------------------------
        splash = tk.Toplevel(root)
        splash.title("RESYNC.ERR")
        splash.resizable(False, False)
        splash.protocol("WM_DELETE_WINDOW", lambda: None)
        splash.configure(bg="#121212")
        splash.geometry("340x120")
        splash.grab_set()

        outer = tk.Frame(splash, bg="#1f6aa5", padx=2, pady=2)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg="#121212", padx=20, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        title_row = tk.Frame(inner, bg="#121212")
        title_row.pack(anchor='w')
        tk.Label(title_row, text="📂  Loading CSV",
                 font=('Segoe UI', 11, 'bold'), bg="#121212", fg="#4f8ef7").pack(side=tk.LEFT)
        spin_var = tk.StringVar(value=" ⠋")
        tk.Label(title_row, textvariable=spin_var,
                 font=('Segoe UI', 11), bg="#121212", fg="#1f6aa5").pack(side=tk.LEFT, padx=(6, 0))

        fname = path.replace('\\', '/').split('/')[-1]
        tk.Label(inner, text=fname, font=('Segoe UI', 9),
                 bg="#121212", fg="#888", anchor='w').pack(fill=tk.X, pady=(6, 0))

        bar_frame = tk.Frame(inner, bg="#121212")
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
            try:
                a = TelemetryAnalyzer(path)
                a.load()
                def _done():
                    splash.grab_release()
                    splash.destroy()
                    root.deiconify()
                    TelemetryApp(root, a)
                root.after(0, _done)
            except Exception as exc:
                def _fail():
                    splash.grab_release()
                    splash.destroy()
                    messagebox.showerror("Error", str(exc))
                    root.destroy()
                root.after(0, _fail)

        threading.Thread(target=_worker, daemon=True).start()
        root.mainloop()
![HD2 Log Viewer Logo](assets/icon.ico) 
# HD2 LOG VIEWER
![Build Status](https://github.com/ERRORX2/HD2-LOG-VIEWER/actions/workflows/build.yml/badge.svg)
![Latest Release](https://img.shields.io/github/v/release/ERRORX2/HD2-LOG-VIEWER?color=blue&label=Latest%20Version)

> Professional-grade telemetry analysis for high-frequency hardware logs. Load a HWiNFO64 or MangoHud CSV, and turn thousands of sensor rows into an interactive chart, a 44-detector failure-scan, and a shareable diagnosis 

| | |
|---|---|
| **Input formats** | HWiNFO64 CSV (best), MangoHud CSV, generic CSV (auto separator + encoding sniffing: UTF-8 / Latin-1 / CP1252) |
| **Platforms** | Windows EXE, Linux (Arch/CachyOS tested), any OS with Python 3.12+ and Tkinter |
| **Core deps** | pandas ≥ 1.3, numpy ≥ 1.21, matplotlib ≥ 3.4 (+ optional Pillow, psutil, scipy) |
| **Config files** | `groups.json`, `sensor_aliases.json`, `theme.json`, `custom_sig.json` - all plain JSON, all portable |
---

## 🚀 Installation & Deployment

### 📦 Option 1: Latest Windows Release (Recommended for Most Users)

<!-- LATEST_RELEASE_START -->
### 🚀 Latest Windows Release: v1.7.6 (2026-09-21)

- Download: [release_release_v1.7.6.zip](https://github.com/ERRORX2/HD2-LOG-VIEWER/releases/download/v1.7.6/release_v1.7.6.zip)

### 🔐 Integrity

<details>

<summary>Cryptographic Hashes</summary>

* EXE SHA256: `6AF4649401B500999A5AC621BD7140415F9F3082C24121A095D2CF3DFD13F01D`
* Groups JSON SHA256: `0CDF44A34045CACD79EFC608A3A2312BDB903DEC5ADB0E30BE4343439878BAB3`
* Manifest SHA256: `35DD54F1F2004FF1C3B24B51BDE76F43D50E773A46C7CCC7E880DAB6BD39A2C6`
* ZIP SHA256: `D65FF0B71000408118CED06F3B6DB6CCEDE50E62FC60CA15ABA3662C3FDD02B8`

</details>
<!-- LATEST_RELEASE_END -->

1. Download the **[Latest Release](../../releases/latest)**.
2. Download the `HD2_LOG_VIEWER_latest.zip` archive.
3. **Extract the ZIP fully** to a folder of your choice.
4. Run `HD2_LOG_VIEWER.exe`.

*Ensure `groups.json` stays in the same folder as the EXE to load your presets.*

---

### 🛠️ Option 2: Running on Linux (Arch/CachyOS)

```bash
sudo pacman -S git python tk python-pandas python-matplotlib python-numpy python-pillow python-pip python-psutil
git clone https://github.com/ERRORX2/HD2-LOG-VIEWER.git
cd HD2-LOG-VIEWER && python HD2_LOG_VIEWER.pyw
```

---

### 🛠️ Option 3: Running from Source (For Developers)

```bash
git clone https://github.com/ERRORX2/HD2-LOG-VIEWER.git
cd HD2-LOG-VIEWER
pip install -r requirements.txt
pythonw HD2_LOG_VIEWER.pyw    # python on Linux
```

---

## 📖 Usage

**1 · Load.** Pick a CSV - a themed splash parses it in the background. The app flags logging gaps > 2.5 s (row ranges, missing time, usability verdict), trims crash-corrupted trailing rows, asks you to confirm any sensor column it can't auto-detect (and remembers your answer forever), then identifies the hardware in the log across 13 categories. **New CSV** swaps logs without a restart.

**2 · Explore.** Sensors are grouped into categories (Temps, Load, Clocks, Power, Voltage, Fans, Frametimes, FPS + GPU/CPU/Other fallbacks) with live search and a one-click **🚨 Out-of-Spec** filter. Pick a view:

| Mode | What it does |
|---|---|
| **Multi-Plot** | One subplot per sensor category, side-by-side, no scale overlap |
| **Heatmap** | View multiple sensors at once, shows known thersholds of sensors in severity bands depending on the selected theme. |
| **Δ Delta** | Absolute difference of the first two selected sensors, both sources + delta annotated with Min/Avg/Max |
| **Time** | X-axis switches from polling ticks to real elapsed time when a timestamp column exists |

**3 · Diagnose.** **🔬 Diagnose Hardware Signatures** runs 44 detectors and shows severity-tagged cards with plain-English explanations, evidence values, and one-click jumps to the relevant chart. A background scan keeps the sidebar's Critical/Warning/Info badges live, and a narrative engine summarizes the causal relationships between findings. **📋 Copy Discord Summary** turns it all into a paste-ready report.

---

## 🔬 Detection Coverage (44 detectors)

| Domain | Signatures include |
|---|---|
| 🌡️ **Thermal & Cooling** | CPU thermal throttling (sustained + spike), GPU hotspot overheat with near-limit early warning and edge↔hotspot delta (paste pump-out / mounting pressure), VRAM junction throttling, VRM/MOSFET overheating, chipset/PCH throttling, fan stall under load, drive thermal throttling (separate HDD/SSD thresholds) |
| ⚡ **Power & Voltage** | CPU clock stretching major/minor (effective-vs-requested ratio, AMD Ryzen + Intel P/E-core naming), PPT/PL1/PL2 saturation, GPU power-limit saturation + oscillation, 12VHPWR connector drop (melting/fire risk), +12V sag & ripple, multi-rail OOS (+12V/+5V/+3.3V), PSU degradation cross-scoring, laptop limp-mode, phantom clock cap |
| 🧬 **Memory & Fabric** | RAM exhaustion, pagefile/virtual-memory overflow, VRAM spillover to system RAM, Ryzen FCLK/UCLK desync (1:1 / 1:2 / invalid states), XMP/EXPO disabled, memory controller mismatch |
| 🧩 **System & OS** | WHEA errors, GPU TDR patterns (+ INFO-tier "unverified stall at log start" when evidence is inconclusive), CPU bottleneck, background process interference, GPU priority conflicts, engine-wait bottleneck (PresentMon), median-relative micro-stutter, DPC/ISR latency, PCIe chokepoint + signal instability |
| 💾 **Storage & I/O** | I/O bottleneck + hitching + sustained 100% activity (WARNING/INFO tiers), NVMe/SSD thermal throttling, S.M.A.R.T. failure flags, SSD lifespan/wear, pagefile overuse, USB rail sag |
| 🧪 **Meta & Platform** | Sensor alias validation, crash-truncation cleanup, locale-aware parsing (comma decimals, German Yes/No, multi-encoding), plus your own custom signatures |

**Custom Signature Wizard:** build your own detectors - Simple or Advanced mode, min/max value gates, excluded sensors, trigger modes, count-based severity thresholds, custom description/advice text, built-in Reference and Examples, and a **🧪 Test** button that runs your rule against the current log before you save it. Stored in `custom_sig.json`, editable and deletable at any time.

---

## ⌨️ Shortcuts & Tools

| Input | Action |
|---|---|
| `Ctrl+C` | Copy current chart (+ legend) to clipboard - Windows, needs Pillow |
| `Ctrl+F8` | Debug dump: ~45 sections of engine internals (column resolution, per-signature status, keyword matching, PSU/fabric analysis, active thresholds & aliases) with search, match-jumping, problems-only filter, copy-all and save |
| Chart click / right-click | Pin nearest line / unpin |
| Legend row click | Pin / unpin that sensor |
| Signature Timeline marker click (enable in settings) | Auto-select that signature's sensors |

---

## 🎨 Theming & Settings

* **21 built-in themes** - Dark, Light, Slate, Teal, Forest Green, Crimson, Steel, Lime, Violet, Lavender, Cobalt, Neon Blue, Sand, Monochrome, **Helldivers 2**, Cathode, Garnet, Glacier, Vaporwave, Bunker, Stingray Analyzer.
* **Theme editor** - background, surface, border, text, accent + secondary, 6 plot-line colors, 6 heatmap band colors; import/export as JSON; everything persists across sessions.
* **Limits editor** - every threshold in one place: per-component temperature limits, rail safe ranges, component voltages, power caps, frame-time/latency limits, fan stall thresholds, drive health, memory load, stability ratios, 20+ signature sensitivity parameters, and the PSU rail specs. One-click reset to defaults.
* **Signature controls** - enable/disable individual detectors (23 of the 44 currently exposed; full coverage on the roadmap).
* **Updates** - silent startup check; view release page, ignore one version, or opt out entirely; manual **⟳ Check for Updates** in the About dialog (updates are not automatic, they are just to notify you about a new release).

## 🗂️ Files It Writes

| File | Purpose |
|---|---|
| `groups.json` | Saved sensor presets (selection + view mode) - shareable via clipboard |
| `sensor_aliases.json` | Your confirmed sensor-column mappings (multiple per sensor) |
| `theme.json` | Active theme + custom user themes |
| `custom_sig.json` | Your custom signatures |

---

## ⚖️ License

MIT License - Developed for the hardware enthusiast and troubleshooting community.

















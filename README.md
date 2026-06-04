![HD2 Log Viewer Logo](assets/icon.ico) 
# HD2 LOG VIEWER
![Build Status](https://github.com/ERRORX2/HD2-LOG-VIEWER/actions/workflows/build.yml/badge.svg)
![Latest Release](https://img.shields.io/github/v/release/ERRORX2/HD2-LOG-VIEWER?color=blue&label=Latest%20Version)

**HD2 LOG VIEWER** is a professional-grade telemetry utility designed for high-frequency hardware log analysis. Optimized for stability testing, thermal diagnostics, and hardware troubleshooting, it provides an interactive interface for visualizing and diagnosing data from **HWiNFO64**, **GPU-Z**, and **MSI Afterburner**.

---

## 🚀 Installation & Deployment

### 📦 Option 1: Latest Windows Release (Recommended for Most Users)
1. Go to the **[Latest Release](../../releases/latest)** page.
2. Download the `HD2_LOG_VIEWER_latest.zip` archive.
3. **Extract the ZIP fully** to a folder of your choice.
4. Run `HD2_LOG_VIEWER.exe`.

*Ensure `groups.json` stays in the same folder as the EXE to load your presets.*

### 🔐 Integrity

<details>

<summary>Cryptographic Hashes</summary>
  
* EXE SHA256: ``9415D1DF015BB47B031CEE051EF44E612E7A68054B9DDE42942A375AA1356E2E``
* Groups JSON SHA256: ``3AFEBEF1816D52DF9849EA545282A25887A6B0016D655836E4C7E3C1CAFD1A92``
* Manifest SHA256: ``E4417B7A2949E5F74921DBF22F416095701BDBA3B6FADB2DA9DF3155981F94FF``
* ZIP SHA256: ``536732E450F946CFDB4D41709891060EA800923DA7B3205C66F72880E4AFDAAB``

</details>

---

### 🛠️ Option 2: Running on Linux (Arch/CachyOS)
1. Install dependencies 
```sudo pacman -S git python tk python-pandas python-matplotlib python-numpy python-pip```
2. git clone ``https://github.com/ERRORX2/HD2-LOG-VIEWER.git``
3. cd ``HD2-LOG-VIEWER``
4. python ``HD2_LOG_VIEWER.pyw``

---

### 🛠️ Option 3: Running from Source (For Developers)

**Prerequisites:**
* Python 3.12
* pip

1. git clone ``https://github.com/ERRORX2/HD2-LOG-VIEWER.git``
2. cd ``HD2-LOG-VIEWER``
3. pip install ``pandas matplotlib numpy``
4. pythonw ``HD2_LOG_VIEWER.pyw``

---

## 📖 Usage

1. **Load a Log:** Launch the app and select your HWiNFO64 CSV. A spinner dialog loads it in the background.
2. **Select Sensors:** Use the categorized sidebar to toggle sensors, or apply a saved preset. Use the search box to filter by name.
3. **Analyze:** Hover over the chart for a live synchronized readout. Use Multi-Plot, Heatmap, Delta, or Time mode to change the view.
4. **Diagnose:** Click **🔬 Diagnose Hardware Signatures** to run the full analysis and review any findings. Use **📋 Copy Discord Summary** to share results instantly.
5. **Save Presets:** Type a name and click Save to store the current sensor selection. Share it via the clipboard icon next to each preset.
6. **Export:** Save a PNG of the current chart or generate a full HTML report for offline sharing or archiving.

---

## 🛠️ Core Features

### 📊 Visualization
* **Multi-Plot Mode:** Split sensors into categorized subplots - temperatures, clocks, voltages, utilization - for side-by-side comparison without overlap.
* **Heatmap Mode:** Color-coded stress visualization across all selected sensors simultaneously, using absolute thresholds for known sensor types and per-sensor normalization as fallback.
* **Δ Delta Mode:** Graph the absolute difference between sensor values over time - useful for tracking GPU core vs. hotspot spread or VRM thermal delta.
* **Time Mode:** Switch the X-axis between raw polling ticks and actual elapsed time when a timestamp column is detected.
* **Interactive Tooltip:** Hover over any point on the chart for a synchronized readout of all plotted sensors at that exact moment.
* **Signal Event Timeline:** A dedicated timeline strip below the chart marks where hardware anomalies were detected. Click any marker to jump directly to that moment and see what triggered it.
* **Chart Export:** Save the current view as a high-resolution PNG (300 DPI) including the full sensor legend, or copy it directly to the clipboard with `Ctrl+C`.

### 🔍 Sensor Management
* **Categorized Sensor List:** Sensors are automatically sorted into groups - Temperatures, Utilization, Clocks, Power, Voltage, Fan Speeds - for fast navigation across large logs.
* **Live Search:** Filter the sensor list in real time by typing; results update instantly.
* **Out-of-Spec Filter:** One click hides all normal sensors and shows only those currently reading outside safe thresholds, highlighted in the list.
* **Sensor Alias System:** Permanently rename ambiguous or hardware-specific sensor columns so they are correctly identified across any future log file from the same machine.
* **Preset Groups:** Save any combination of selected sensors as a named preset. Apply, rename, delete, or share presets via clipboard - paste a shared preset from another user directly into the app.

### 🔬 Diagnostics
* **Hardware Failure Diagnosis:** Runs a full signature scan and presents findings as severity-tagged cards (Critical / Warning / Info) with plain-English descriptions, evidence values, and one-click sensor selection to jump straight to the relevant chart.
* **Session Summary Narrative:** Automatically generates a plain-English paragraph summarizing the most significant findings and any causal relationships between issues detected.
* **Discord Summary Copy:** Copies a compact, formatted summary of the session narrative and all detected signals - including severity and evidence - ready to paste directly into Discord or a support ticket.
* **Real-Time Signature Badges:** The sidebar shows a live count of critical, warning, and info signals as soon as the scan completes in the background, without opening the diagnosis window.
* **Out-of-Spec Detection:** Independently flags individual sensors that exceed configured thresholds, separate from the full signature engine.
* **Detected Hardware View:** Parses the CSV label rows to identify and display the actual hardware devices present in the log - CPU, GPU, storage drives, network adapters, and more - grouped by category.

### 🔁 Session Comparison
* **Reference Baseline:** Pin the current session as a reference, then load a second CSV to compare directly against it.
* **Overlay Mode:** Draws both sessions on the same axes so differences in thermals, clocks, or power are immediately visible.
* **Delta Summary Panel:** Shows avg/max/min differences between the current and reference session for every selected sensor, displayed as an annotated panel on the chart.
* **Swap Reference:** Swap the current and reference sessions without reloading either file.

### 📄 Reporting
* **HTML Report Export:** Generates a fully self-contained HTML report including detected hardware, session summary, all signature findings, out-of-spec sensors, per-sensor charts (selected and by category), PSU rail voltages, and a full statistics table. No internet connection required to view.

### 🎨 Theming
* **14 Built-in Themes:** Dark (Default), Light (Default), Slate, Teal, Forest Green, Crimson, Steel, Lime, Violet, Lavender, Cobalt, Neon Blue, Sand, Monochrome, and the Helldivers 2 theme.
* **Theme Editor:** Customize any theme's background, surface, border, text, accent, plot line colors, and heatmap band colors using a color picker. Save as a named user theme.
* **Import / Export Themes:** Share themes as `.json` files. Import a theme file and it is immediately available in the editor.
* **Persistent Theme:** The active theme and all customizations are saved and restored between sessions.

### ⚙️ Settings & Configuration
* **Limits Editor:** Configure every detection threshold - temperature limits per component type, voltage rail safe ranges, power maximums, fan stall thresholds, frametime limits, and all signature-specific sensitivity parameters.
* **Signature Controls:** Enable or disable individual signatures from the settings panel. The signal timeline and badge counts update accordingly.
* **Tooltip Toggle:** Enable or disable the hover tooltip from the top bar without restarting.
* **Crash Recovery:** Automatically trims corrupted or zeroed rows commonly left at the end of logs after crashes or hard resets.
* **Update Notifications:** Checks for new releases silently on startup. If an update is found, you can open the release page, ignore that specific version, or disable future notifications. A manual check is available via the ⟳ button at any time.
* **Debug Dump:** A hidden developer panel (`Ctrl+F8`) shows all resolved sensor columns, detected values, fabric clock ratios, PSU rail analysis, and internal state - useful for diagnosing why a signature did or did not fire.

---

## 🔬 Diagnostics Engine

HD2 LOG VIEWER includes an advanced signature detection system that analyzes system behavior across thermals, power delivery, memory stability, storage performance, and OS-level scheduling.

### 🧠 Detection Coverage

**🌡️ Thermal & Cooling**
* CPU thermal throttling and sustained temperature stress
* GPU hotspot and edge-to-hotspot delta analysis
* VRAM junction temperature throttling
* VRM and MOSFET overheating
* Chipset / PCH thermal throttling
* Fan stall detection during active load

**⚡ Power & Voltage**
* CPU clock stretching (major and minor) - effective vs. requested clock ratio analysis per core
* GPU power limit saturation and oscillation
* PSU +12V rail sag and ripple analysis
* Multi-rail voltage out-of-spec detection (+12V, +5V, +3.3V)
* Laptop power delivery failure / limp mode detection
* Phantom GPU clock cap detection

**🧬 Memory & Fabric**
* System RAM exhaustion and virtual memory / pagefile overflow
* VRAM overflow with spillover into system memory
* Ryzen FCLK/UCLK fabric desync (DDR4 and DDR5 modes)
* Memory XMP/EXPO profile disabled detection
* Memory controller clock mismatch

**🧩 System & OS**
* Hardware (WHEA) errors
* GPU driver TDR / timeout pattern detection
* CPU bottleneck (GPU idle while CPU saturated)
* Background process CPU interference
* GPU priority conflict from background applications
* GPU engine wait bottleneck (PresentMon frame data)
* Kernel driver / DPC latency spikes
* PCIe bus interface chokepoint and signal instability

**💾 Storage & I/O**
* Drive I/O bottleneck and sustained 100% activity
* NVMe and SSD thermal throttling
* S.M.A.R.T. hardware failure flags
* SSD lifespan critical and wear warnings
* Pagefile overuse

**🧪 Meta & Platform**
* Sensor alias validation and auto-detection prompting
* Log row integrity and crash-truncation cleanup
* USB rail voltage sag

---

## 🛡️ Security & Transparency

Because this utility is packaged using PyInstaller, some antivirus engines may flag the executable as a false positive.

Previously, automated VirusTotal scanning was integrated into the CI pipeline. This has been removed for the following technical and operational reasons:

- **Binary size constraints:** The compiled executable is large due to bundled dependencies, which makes repeated API uploads inefficient and prone to request failures or rate limiting.
- **API cost / quota limitations:** Continuous scanning of every build consumes VirusTotal API quota. For a free and frequently built project, this introduces unnecessary operational cost.
- **CI overhead:** Uploading and polling external scan results significantly increases build time without affecting runtime functionality or binary correctness.

### 🔍 Current security model

- Each release includes a **SHA256 checksum** for integrity verification of the distributed archive.
- The project is built deterministically via **GitHub Actions**, with artifacts generated directly from source.
- Manual VirusTotal scans may still be performed selectively on major releases when required.

This approach prioritizes build stability, reproducibility, and cost efficiency while maintaining basic integrity validation.

---


## ⚖️ License

MIT License - Developed for the hardware enthusiast and troubleshooting community.

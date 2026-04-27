
# HD2 LOG VIEWER

![Build Status](https://github.com/ERRORX2/HD2-LOG-VIEWER/actions/workflows/build.yml/badge.svg)
![Latest Release](https://img.shields.io/github/v/release/ERRORX2/HD2-LOG-VIEWER?color=blue&label=Latest%20Version)

**HD2 LOG VIEWER** is a professional-grade telemetry utility designed for high-frequency hardware log analysis. Optimized for stability testing and thermal diagnostics, it provides an interactive interface for visualizing data from **HWinfo64**, **GPU-Z**, and **MSI Afterburner**.

---

## 🚀 Installation & Deployment
<!-- LATEST_RELEASE_START -->
### 🚀 Latest Release: v1.3.4 (2026-04-26)

- Download: [release_release_v1.3.4.zip](https://github.com/ERRORX2/HD2-LOG-VIEWER/releases/download/v1.3.4/release_v1.3.4.zip)
- SHA256: 55BDC8B4FABB44BD70AD0E985A561C71D13BE98F2447B3BE163088A078FA218B
- VirusTotal: MANUAL SCAN | https://www.virustotal.com/gui/file/55bdc8b4fabb44bd70ad0e985a561c71d13be98f2447b3be163088a078fa218b?nocache=1
<!-- LATEST_RELEASE_END -->

### 📦 Option 1: Compiled Executable (Recommended for Users)
1. Go to the **[Latest Release](../../releases/latest)** page.
2. Download the `HD2_LOG_VIEWER_latest.zip` archive.
3. **Extract the ZIP fully** to a folder of your choice.
4. Run `HD2_LOG_VIEWER.exe`.

*Ensure `groups.json` stays in the same folder as the EXE to load your presets.*

---

### 🛠️ Option 2: Running from Source (For Developers)

**Prerequisites:**
* Python 3.10+
* pip

```bash
git clone https://github.com/ERRORX2/HD2-LOG-VIEWER.git
cd HD2-LOG-VIEWER
pip install pandas matplotlib numpy
pythonw HD2_LOG_VIEWER.pyw
````

---

## 🛡️ Security & Transparency

Because this utility is bundled using PyInstaller, some antivirus engines may flag it as a false positive.

* **Automatic Scanning:** Every release is scanned via VirusTotal during build
* **Integrity:** SHA256 hashes are provided for verification

---

## 🛠️ Core Functionality

* **📊 Multi-Plot Mode:** Categorized subplots for Temperatures, Clocks, and Voltages.
* **Δ Delta Analysis:** Graph absolute differences (e.g., GPU Core vs. Hotspot).
* **🔍 Comparison Engine:** Overlay live data against a reference baseline.
* **🔬 Signature-Based Diagnostics:** Cross-system hardware anomaly detection engine.
* **🚨 Intelligent Diagnostics:** Automatic flagging of thermal throttling and voltage sag.
* **🌗 Adaptive UI:** Full Dark and Light mode support.
* **🔔 Update Notifications:** Automatic update checks on startup with options to ignore a specific version or disable notifications entirely.
* **🕒 Time Mode:** Switch the graph between raw data ticks and actual time (H:MM:SS).
* **📋 Preset Management:** Save sensor groups, rename them with the pencil icon, and share them via clipboard.
* **🌡️ Heatmap Mode:** Dynamic color-coded stress mapping (Green/Yellow/Red).
* **⚙️ Limits Editor:** Fully customizable threshold engine—fine-tune thermal and voltage "Danger Zones" for your specific hardware.
* **🧹 Crash Recovery:** Smart data cleaning that automatically trims corrupted/zeroed rows typically found at the end of logs after a system crash.

---

## 🔬 Diagnostics Engine

HD2 LOG VIEWER includes an advanced signature detection system that analyzes system behavior across thermals, power delivery, memory stability, storage performance, and OS-level scheduling.

### 🧠 Detection Coverage

The engine monitors multiple layers of system behavior:

#### 🌡️ Thermal & Cooling Stability

* CPU thermal throttling
* GPU hotspot deltas
* VRAM and VRM temperature stress
* Chipset and CCD thermal imbalance

#### ⚡ Power & Voltage Behavior

* Clock stretching and performance loss under load
* GPU power limit oscillation
* Voltage reliability limits

#### 🧬 Memory & Fabric Integrity

* RAM saturation and memory controller load
* VRAM swapping and memory pressure
* Ryzen fabric synchronization (FCLK/UCLK behavior)

#### 🧩 System & OS-Level Stability

* WHEA hardware errors
* Kernel/DPC latency spikes
* CPU core parking under load
* Background process CPU spikes

#### 💾 Storage & I/O Performance

* SSD congestion and sustained 100% I/O usage
* SMART health monitoring
* Pagefile overuse and memory leak detection

#### 🧪 Meta Diagnostics

* Sensor integrity validation
* Log stability and data consistency checks

---

### 🎯 Purpose

* Detect early system instability before failure occurs
* Identify hidden performance bottlenecks
* Correlate hardware behavior across multiple subsystems
* Expose issues not visible through single-metric monitoring

---

## 📖 Usage Instructions

1. **Import Data:** Click "New CSV" and select your log.
2. **Toggle Sensors:** Select specific hardware metrics from the sidebar.
3. **Analyze:** Hover over any graph point for synchronized data readout across all plots.
4. **Save Presets:** Use the "Groups" menu to save current sensor selections for future logs.
5. **Updates:** On startup the app silently checks for new releases. If one is found you can open the release page, ignore that specific version, or disable future notifications entirely. You can also manually check anytime via the ⟳ button in the top bar.

---

## ⚖️ License

MIT License - Developed for the hardware enthusiast community.


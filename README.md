
# HD2 LOG VIEWER

![Build Status](https://github.com/ERRORX2/HD2-LOG-VIEWER/actions/workflows/build.yml/badge.svg)
![Latest Release](https://img.shields.io/github/v/release/ERRORX2/HD2-LOG-VIEWER?color=blue&label=Latest%20Version)

**HD2 LOG VIEWER** is a professional-grade telemetry utility designed for high-frequency hardware log analysis. Optimized for stability testing and thermal diagnostics, it provides an interactive interface for visualizing data from **HWinfo64**, **GPU-Z**, and **MSI Afterburner**.

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

## 🚀 Installation & Deployment
<!-- LATEST_RELEASE_START -->
### 🚀 Latest Release: v1.4.7 (2026-05-07)

- Download: [release_release_v1.4.7.zip](https://github.com/ERRORX2/HD2-LOG-VIEWER/releases/download/v1.4.7/release_v1.4.7.zip)

### 🔐 Integrity

- EXE SHA256: 60A3AF0C16E3F20847DB73D1563A35FA8C04521AE591F7149DC6CB8F743E9750
- Groups JSON SHA256: 23D61C23D4E5D605D1CAB518647C0BB5BAE026AE86D3B9E065ACEA67FE11F1D4
- Manifest SHA256: E0572F44B27C8B9F808673E7D9C4D4752359FA08BAA7C0FB9FFBC7A67540B97B
- ZIP SHA256: 608EC825D115C9BBA331B88D047FDEAA5AA0CC65053BE8B90F148CE48E0CF2C0
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

## 🛠️ Core Functionality

* **📊 Multi-Plot Mode:** Categorized subplots for temperatures, clocks, voltages, and utilization metrics.
* **🧠 Sensor Alias System:** Persistent user-configurable sensor aliasing improves automatic sensor matching across differently formatted CSV logs.
* **Δ Delta Analysis:** Graph absolute differences between related sensors (for example GPU Core vs. Hotspot).
* **🔍 Comparison Engine:** Overlay live telemetry data against a reference baseline.
* **📄 HTML Report Export:** Generate structured HTML reports from analyzed logs for sharing, archiving, and offline review.
* **🔬 Signature-Based Diagnostics:** Detects hardware instability patterns across thermals, power delivery, memory, storage, and OS behavior.
* **🚨 Automated Diagnostics:** Flags thermal throttling, voltage instability, PSU sag, and related hardware anomalies.
* **🌗 Adaptive UI:** Full dark and light mode support.
* **🔔 Update Notifications:** Automatic update checks on startup with ignore-version and disable options.
* **🕒 Time Mode:** Switch graphs between raw polling ticks and actual elapsed time.
* **📋 Preset Management:** Save, rename, organize, and share sensor groups.
* **🌡️ Heatmap Mode:** Dynamic color-coded stress visualization.
* **⚙️ Limits Editor:** Customizable threshold system for thermal and voltage warning zones.
* **🧹 Crash Recovery:** Automatically trims corrupted or zeroed rows commonly left at the end of logs after crashes or hard resets.

---

## 🔬 Diagnostics Engine

HD2 LOG VIEWER includes an advanced signature detection system that analyzes system behavior across thermals, power delivery, memory stability, storage performance, and OS-level scheduling.

### 🧠 Detection Coverage

The engine monitors multiple layers of system behavior:

🌡️ Thermal & Cooling Stability

* CPU thermal throttling
* GPU hotspot deltas
* VRAM and VRM temperature stress
* Chipset and CCD thermal imbalance

⚡ Power & Voltage Behavior

* Clock stretching and performance loss under load
* GPU power limit oscillation
* Voltage reliability limits
* Multi-rail voltage sag detection
* PSU ripple and transient instability analysis

🧬 Memory & Fabric Integrity

* RAM saturation and memory controller load
* VRAM swapping and memory pressure
* Ryzen fabric synchronization (FCLK/UCLK behavior)

🧩 System & OS-Level Stability

* WHEA hardware errors
* Kernel and DPC latency spikes
* CPU core parking under load
* Background process CPU spikes

💾 Storage & I/O Performance

* SSD congestion and sustained 100% I/O usage
* SMART health monitoring
* Pagefile overuse and memory leak detection

🧪 Meta Diagnostics

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










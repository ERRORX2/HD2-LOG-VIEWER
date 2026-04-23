# HD2 LOG VIEWER

![Build Status](https://github.com/ERRORX2/HD2-LOG-VIEWER/actions/workflows/build.yml/badge.svg)
![Latest Release](https://img.shields.io/github/v/release/ERRORX2/HD2-LOG-VIEWER?color=blue&label=Latest%20Version)

**HD2 LOG VIEWER** is a professional-grade telemetry utility designed for high-frequency hardware log analysis. Optimized for stability testing and thermal diagnostics, it provides an interactive interface for visualizing data from **HWinfo64**, **GPU-Z**, and **MSI Afterburner**.

---

## 🚀 Installation & Deployment
<!-- LATEST_RELEASE_START -->
<!-- LATEST_RELEASE_END -->
### 📦 Option 1: Compiled Executable (Recommended for Users)
1.  Go to the **[Latest Release](../../releases/latest)** page.
2.  Download the `HD2_LOG_VIEWER_latest.zip` archive.
3.  **Extract the ZIP fully** to a folder of your choice.
4.  Run `HD2_LOG_VIEWER.exe`.
    * *Note: Ensure `groups.json` stays in the same folder as the EXE to load your presets.*

### 🛠️ Option 2: Running from Source (For Developers)
**Prerequisites:**
* Python 3.10 or higher.
* `pip` (Python Package Index).

**Setup Steps:**
1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/ERRORX2/HD2-LOG-VIEWER.git](https://github.com/ERRORX2/HD2-LOG-VIEWER.git)
    cd HD2-LOG-VIEWER
    ```
2.  **Install Required Libraries:**
    ```bash
    pip install pandas matplotlib numpy
    ```
3.  **Launch the Application:**
    ```bash
    pythonw HD2_LOG_VIEWER.pyw
    ```

---

## 🛡️ Security & Transparency
Because this utility is bundled using PyInstaller, some antivirus engines may flag the executable as a "False Positive." 
* **Automatic Scanning:** Every release is scanned via the VirusTotal API during the build process.
* **Integrity:** You can view the scan report link in the Latest Release section above.

---

## 🛠️ Core Functionality
* **📊 Multi-Plot Mode:** Categorized subplots for Temperatures, Clocks, and Voltages.
* **Δ Delta Analysis:** Graph absolute differences (e.g., GPU Core vs. Hotspot).
* **🔍 Comparison Engine:** Overlay live data against a reference baseline.
* **🚨 Intelligent Diagnostics:** Automatic flagging of thermal throttling and voltage sag.
* **🌗 Adaptive UI:** Full Dark and Light mode support.

---

## 📖 Usage Instructions
1.  **Import Data:** Click "New CSV" and select your log.
2.  **Toggle Sensors:** Select specific hardware metrics from the sidebar.
3.  **Analyze:** Hover over any graph point for synchronized data readout across all plots.
4.  **Save Presets:** Use the "Groups" menu to save current sensor selections for future logs.

---

## ⚖️ License
MIT License - Developed for the hardware enthusiast community.
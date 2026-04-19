# HD2 LOG VIEWER

**HD2 LOG VIEWER** is a specialized telemetry analysis utility designed for high-frequency hardware log parsing. Built for stability testing and performance tuning, it provides a streamlined interface for visualizing data from HWinfo64, GPU-Z, and MSI Afterburner.

---

## 🛠️ Core Functionality

* **Automated Sensor Mapping:** Intelligently parses CSV headers to categorize sensors by hardware component (CPU, GPU, VRM, etc.).
* **Out-of-Spec Detection:** Automatically flags sensor data that exceeds defined thermal or voltage thresholds.
* **Preset Management:** Save and load custom sensor groups via `groups.json` for consistent benchmarking across different sessions.
* **High-Resolution Visualization:** Multi-axis graphing with interactive cursor logic for precise data point analysis.
* **Stateless Execution:** Standard windowed operation with no console persistence.

---

## 🚀 Installation & Deployment

### For End Users (Windows)
1.  Navigate to the **Releases** section of this repository.
2.  Download the `HD2_LOG_VIEWER_v.zip` package.
3.  Extract the contents. Ensure `HD2_LOG_VIEWER.exe` and `groups.json` remain in the same directory.
4.  Run the executable.

### For Developers (Source)
To audit the source or run in a localized Python environment:
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPO.git](https://github.com/YOUR_USERNAME/YOUR_REPO.git)
    ```
2.  **Install dependencies:**
    ```bash
    pip install pandas matplotlib seaborn
    ```
3.  **Execute via Python Windowed launcher:**
    ```bash
    python HD2_LOG_VIEWER.pyw
    ```

---

## 📖 Usage Instructions

1.  **Import Data:** Click "Import CSV" and select your telemetry log.
2.  **Toggle Sensors:** Use the sidebar to select the specific hardware metrics you wish to overlay.
3.  **Isolate Alerts:** Use the alert filter to jump to timestamps where hardware exceeded safe operating parameters.
4.  **Documentation:** Use the "Export PNG" feature to save the current graph state for troubleshooting logs or sharing with others.

---

## ⚙️ Technical Specifications

* **Framework:** Tkinter
* **Data Handling:** Pandas / NumPy
* **Plotting Engine:** Matplotlib (TkAgg)
* **Build Pipeline:** GitHub Actions / PyInstaller

---

## ⚖️ License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

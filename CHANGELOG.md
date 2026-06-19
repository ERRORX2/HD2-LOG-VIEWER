# Change Log


## v1.6 (2026-06-07)

✨ New Features

📊 Session Compare - Complete Rework

* Multi-Session Overlay: Compare up to 6 CSV sessions side-by-side on a single chart. Sessions are shown as colored chips with a remove button. Add sessions from any CSV at any time without reloading.
* Uses Normal Sensor Checklist: Sensor selection is now driven by the existing left-panel checklist - no separate dropdown. All selected sensors are compared simultaneously across all loaded sessions.
* Multi-Mode Support: When Multi mode is active, each selected sensor gets its own subplot in the compare view, all sharing a time axis. Green/red diff shading (better/worse vs S1) applies per pane.
* Normalized Chart Mode: Scales every session to 0-100% of its own range for shape comparison across sensors with different value scales (e.g. comparing two runs at different power targets).
* Full Stats Table: The stats table now shows every selected sensor - not just the first. Each sensor gets a divider row followed by one session row each, with Min, Avg, Max, P1, P95, P99, σ, Δ Avg, and Δ% columns. Best values highlighted green (▲), worst red (▼).
* Sessions Persist Across Toggle: Closing and re-opening Session Compare restores all previously loaded sessions. Sessions are only cleared when a new CSV is loaded via the New CSV button.
* Ctrl+C Copies Chart and Table: Ctrl+C in compare mode composites the matplotlib chart and the stats table into a single image and copies it to the clipboard. Reverts to normal plot copy on exit.
* Export Report with Loading Bar: One chart is generated per sensor, each with green/red diff shading between S1 and S2.

🗑️ Removed

* Old Reference Compare System: The Set Ref, Ref CSV, Compare ON/OFF, and Swap buttons have been removed from the UI. Session Compare supersedes the old single-reference system with support for up to 6 sessions, a dedicated stats table, and a proper chart layout.

💡 Notes

* Keep groups.json and theme.json when updating to preserve your custom sensor presets, aliases, themes, and saved configurations.
* Session Compare is accessible via the 📊 Session Compare button in the View Settings panel.

## v1.5.9.2 (2026-06-04) 

✨ New Features

* MangoHud CSV Support: The viewer can now load MangoHud log files in addition to HWiNFO64 CSVs. MangoHud columns are automatically mapped to display names with units (e.g. gpu_temp > GPU Temperature [°C]) so all existing features - signatures, heatmap, presets, HTML report, and time axis - work without any changes.
* MangoHud Debug Info: When a MangoHud CSV is loaded, the debug window now shows a dedicated section with the parsed system info block (CPU, GPU, RAM, OS, kernel, driver) and a full column resolution table showing which sensors were found and their min/avg/max values.
* MangoHud Hardware Detection: "View Detected Hardware" correctly parses the MangoHud system info header and displays CPU, GPU, RAM, OS, and kernel information.

🐛 Bug Fixes

* X-Axis Length Mismatch Crash: Fixed a ValueError where loading a shorter CSV after a longer one could cause a shape mismatch between x-axis values and sensor data, crashing the plot. The x-axis cache is now invalidated after the new dataframe is assigned, and a safety guard in update_plot force-reinvalidates if a mismatch is ever detected.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* MangoHud support covers frame timing, CPU/GPU load, temperatures, clocks, power, and VRAM metrics.
* Keep groups.json when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.9 (2026-06-02)

🐛 Bug Fixes

* Diagnosis Window Blocking: The Hardware Failure Diagnosis window no longer blocks interaction with the main window — both can now be used simultaneously.
* Diagnosis Window Minimize: The Hardware Failure Diagnosis window can now be minimized and resized like a normal window.
* Diagnosis Window Singleton: Clicking "Diagnose Hardware Signatures" while the window is already open will now bring it to the front instead of opening a duplicate window.
* Diagnosis Window Restore: If the Diagnosis window is minimized and the button is clicked again, it will now correctly restore and focus the existing window.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.8 (2026-05-22)

🐛 Bug Fixes

* Signal Timeline Crash: Fixed an IndexError that could occur when opening the Hardware Failure Diagnosis window on certain logs, caused by a typo in the span index clamping logic.
* Session Stale Data Crash: Fixed a crash that could occur when loading a second shorter CSV after a longer one, where leftover timeline data from the previous session could cause out-of-bounds index access.
* Timeline Tooltip Safety: Added null guards to the timeline tooltip to handle the cleared state safely when switching between sessions.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.7 (2026-05-21)

🖥️ UI & Reporting

* Discord Summary Copy: Added a "Copy Discord Summary" button to the Hardware Failure Diagnosis window. Copies the session summary narrative followed by a condensed signal list with severity emojis, signal names, and full evidence bullets. Falls back to a clean all-clear message when no signatures are detected.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.6 (2026-05-20)

🖥️ UI & Reporting

* Plot Export Fixes: Fixed a bug where exporting charts via PNG or copying them directly to the clipboard (Ctrl+C) would cut off and exclude the sensor legend from the final picture.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.5 (2026-05-20)

🔬 Hardware Detection & Signatures

* Smarter Sensor Matching: Improved how the app finds your CPU data (temperature, usage, and power). It now uses strict filters to ignore wrong or overlapping sensor names, making sure it reads the correct data.
* Better Overheating Detection: The app now checks for instant temperature spikes alongside long-term high heat. If your CPU hits a dangerous peak temperature even for a moment, it will now correctly flag it as a warning or critical issue.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.4 (2026-05-19)

🛡️ Stability & Bug Fixes

* Signature Engine Crash Fix: Fixed a critical issue where the signature analyzer could encounter an unhandled exception and crash the application under specific data conditions.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep groups.json when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.3 (2026-05-18)

⚡ Performance & Optimization

* X-Axis Data Caching: Added an internal cache (_x_axis_cache) for x-axis value calculations to eliminate redundant processing, automatically invalidating the cache only when a new CSV is loaded or the time mode is toggled.
* Sensor Stats Cache: Optimized the _sensor_stats_cache lookup engine to calculate statistics for all numeric columns on the first build and cache the results, preventing expensive recomputations on every plot update.
  - Redundant Call Elimination: Streamlined rendering overhead by removing a duplicate theme retrieval call inside the plot update pipeline, reusing the existing theme state dictionary instead.

🎨 Bug Fixes & Export Improvements

* HTML Report Layout Restore: Fixed a structural bug in exported HTML reports by restoring the critical CSS :root styling variables (--text, --muted, --border, etc.) that were accidentally truncated during a previous code cleanup.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep groups.json when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.2 (2026-05-18)

📊 Interactive Legend & UI Focus

* Legend Cleanup & Deselection: Fixed an issue where the sidebar legend frame would completely break or fail to clear out and disappear from view when all active sensors were deselected.
* Pinned State Reset: Fixed a bug where a pinned sensor line's name would get stuck in the legend list after that sensor was unselected, ensuring it now safely resets.

🧠 Enhanced Debug System

* Diagnostic View Overhaul: Expanded the internal debugger output to actively track live application statistics, including process RAM usage via psutil, exact CSV file sizes in megabytes, active theme variables, sensor selection counts, UI configuration flags, and data cache boundaries.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.5.1 (2026-05-17)

🎨 Custom Theme Engine

* Theme Editor: Added a fully featured UI panel to customize application backgrounds, foregrounds, accent colors, plot lines, and heatmap ranges.
* Built-in Presets: Supplied 13 unique theme choices.
* Theme Portability: Added support for creating, saving, renaming, and sharing custom setups via a standalone theme.json configuration file.

📊 Interactive Visualization Layer

* Custom Side-Panel Legend: Replaced the default Matplotlib legend with a scrollable, Tkinter-backed interactive side panel.
* Line Pinning & Focus: Added the ability to click legend entries or graph lines to "pin" a specific data series, highlighting it while fading out the background data.
* Dynamic Hover Highlights: Implemented reactive line-thickening effects when hovering mouse pointers over legend elements.
* Color Expansion Palette: Introduced an HSL color expansion algorithm to automatically generate visually distinct, high-contrast colors when rendering more than 6 simultaneous data tracks.
* On-Plot Annotations: Integrated floating, color-matched text labels that map current data values directly to the cursor position on hover.

🛠️ Code Refactoring & Polish

* Centralized Theme Architecture: Replaced scattered, hardcoded conditional color logic across multiple UI view modules with a single theme utility system.
* Configuration State Integrity: Updated state tracking models to ensure the new tooltip preferences cleanly save across app sessions.

💡 Notes

* Keep ``groups.json`` when updating to preserve your custom sensor presets, aliases, and saved configurations.


## v1.5.0 (2026-05-15)

🧠 Diagnostic Narrative Engine

* Session Summary: Added a human-readable analysis section to the top of reports that translates technical sensor data into plain-English insights.
* Root Cause Mapping: Added intelligence to link related events, such as explicitly connecting performance drops to detected hardware limits or cooling failures.
* Weighted Severity: Added a dynamic scoring system that adjusts the tone and urgency of the summary based on the criticality of detected issues.

📈 Timeline Layout Engine

* Greedy Row Packing: Overhauled the timeline layout with a new algorithm that intelligently stacks overlapping events into vertical rows to maximize space and maintain readability.
* Adaptive Labeling: Added "Label Budgeting" to automatically truncate or hide text based on the available horizontal space, preventing label collisions on short-duration events.

🔬 Hardware Detection & Signatures

* Severity Rebalancing: Updated signature severity ratings across the engine to better inform users of critical vs. non-critical hardware events.
* XMP/EXPO Validation: Added a new signature to detect if high-performance memory is misconfigured and running at stock JEDEC speeds.
* Refined PSU Analysis: Added improved logic and updated descriptions for PSU rail instability hits to provide better troubleshooting context.

🖥️ UI & Reporting

* Narrative Integration: Added a dedicated summary box to HTML exports to highlight key findings immediately upon opening a report.
* Enhanced Tooltips: Added direct evidence strings from the analysis engine to timeline tooltips for better data transparency.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve your custom sensor presets, aliases, and saved configurations.

## v1.4.11 (2026-05-14)

🆕 Interactive Signature Timeline

* Added a new interactive signature timeline above the main plot.
* Stacked event rows prevent overlap and improve readability.
* Added begin/end timestamps directly on event bars.
* Added hover tooltips with signature evidence and related sensor details.
* Clicking timeline events automatically selects relevant sensors.
    
* Timeline filtering is automatic:
  - All events are shown when no sensors are selected.
  - Only relevant events are shown when sensors are selected.

* Added a persistent Settings toggle to enable or disable the timeline entirely.
* Timeline hides automatically when disabled or when no matching events exist.

🔬 Signature System

* Signature events now support multiple independent occurrences on the timeline.
* Added gap-merging logic to prevent brief drops from splitting a single event into multiple fragments.
* Signature processing can now automatically derive event ranges directly from sensor data.

* Added explicit event masking for:
  - CPU throttling
  - TDR detection
  - VRAM overflow
  - Bottlenecks
  - Fan stalls
  - RAM exhaustion

🖥️ Multi-Mode Rendering & UI

* Improved multi-plot layout scaling with adaptive spacing, fonts, and label truncation.
* Added a unified figure legend with category headers for cleaner compare-mode rendering.
* Improved compare-mode reference line handling across all plot modes.
* Hidden Y-axis labels automatically when using large subplot counts to reduce overlap.
* Renamed Edit Detection Limits to Settings for improved clarity.

⚡ Stability & Performance

* Improved rendering performance by reducing unnecessary cursor redraws.
* Optimized subplot layout generation and spacing behavior.
* Reworked off-thread rendering to improve stability and reduce Matplotlib-related crashes.
* Fixed additional widget and canvas cleanup issues related to repeated reloads.
* Added additional safeguards for Python 3.13 cross-thread cleanup behavior.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve custom sensor presets, sensor aliases, and timeline settings.

## v1.4.10 (2026-05-12)

CSV Swapping & UI

* In-Memory Swap: Instantly exchange Main and Reference logs without reloading files. UI, plots, and analysis now update dynamically.
* Refined Layout: Moved the Swap button to the reference row; it now activates only when a reference is loaded.

UX Enhancements

* Copy to Clipboard: Added Ctrl+C support to copy the current plot as a PNG (Windows native).
* Snappier Startup: Optimized imports and internal logic for faster app initialization.

Stability & Memory

* Leak Fixes: Implemented a new _teardown system to properly clear widgets and memory when opening new logs.
* Thread Safety: Added guards to prevent crashes during resource cleanup and UI rebuilds.

💡 Note: Keep ``groups.json`` when updating to preserve your custom sensor presets.

## v1.4.9 (2026-05-10)

⚡ PSU Rail Detection & Analysis

* Reworked PSU rail detection to use value-based matching for improved accuracy and compatibility.
* Added helper functions for more reliable voltage sensor selection across diagnostics and reports.
* Improved out-of-spec detection for PSU instability and related hardware failures.

🔬 Signature System

* Improved signature threshold handling for more consistent loading, saving, and application behavior.
* Refined signature detection logic and related diagnostic processing.

🖥️ UI & Reports

* Improved alias management UI and related dialogs.
* Refined report formatting and general UI behavior for better readability.

⚙️ Internal Changes

* Cleaned up redundant code and performed general refactoring.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve custom sensor presets and sensor alias

## v1.4.8 (2026-05-09)

🧠 Sensor Detection & Aliasing

* Expanded the sensor alias system with more sensor keys and improved auto-detection.
* Improved sensor matching across different CSV formats and naming schemes.
* Added better handling and guidance for unresolved sensors during CSV loading.

⚡ PSU Analysis

* Improved PSU rail detection for better compatibility and accuracy.
* Refined voltage rail analysis and related diagnostic behavior.

🖥️ Diagnostics & UI

* Added a background signature watcher for live diagnostic monitoring.
* Added live signature status badges to the UI.
* Improved the sensor picker dialog with descriptions and general UI tweaks.

⚙️ Internal Changes

* Removed obsolete ``__SKIP__`` logic.
* Refactored related processing code.
* General cleanup and refactoring.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve custom sensor presets and sensor aliases.

## v1.4.7 (2026-05-07)

🧠 Sensor Detection & Aliasing

* Added persistent user-configurable sensor aliasing to improve automatic sensor matching across different CSV formats and naming schemes.
* Added alias management UI for viewing, editing, and maintaining custom sensor mappings.
* Added prompts for unresolved or unknown sensors to improve column detection reliability.
* Expanded sensor detection keyword coverage and refined matching behavior for improved hardware identification.

⚡ PSU Failure Analysis

* Enhanced PSU-related diagnostics with additional ripple and voltage instability checks.
* Added multi-rail voltage sag detection for improved identification of transient power delivery issues.
* Added new PSU failure indicators and warning heuristics to improve report accuracy.

⚙️ Processing & Logic

* Improved Yes/No flag handling and normalization logic during sensor processing.
* Refined internal detection behavior and analysis thresholds across multiple signature types.

💡 Notes

* The signature system does not yet fully support the new sensor alias matching system and may not detect aliased sensors correctly in all cases. Full integration is planned for a future update, likely in the next release.
* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep ``groups.json`` when updating to preserve custom sensor presets and sensor aliases.

## v1.4.6 (2026-05-05)

🧠 Signature Detection & Processing

* Expanded _sensors_for_signature keyword lists to improve coverage of hardware events and sensor types.
* Improved critical/warning detection by adding additional keywords and refining threshold handling.
* Updated Yes/No column handling by mapping values to ``1.0 / 0.0`` and excluding them from numeric processing.

⚙️ Signature Controls & Debugging

* Added a "Signature Enable / Disable" section in settings, with disabled states persisted in configuration.
* Added debug mode (Ctrl + F8) with an in-app diagnostics window and signature hit summary.
* Added a "Select Relevant Sensors" button inside signature cards in the results dialog.

💡 Notes

* Hardware-specific categorization and detailed grouping require HWiNFO64 logs with a valid label row.
* Keep groups.json when updating to preserve custom sensor presets.

## v1.4.5 (2026-05-03)

📄 New Feature: Threaded Progress Dialogs

* Background Processing: Refactored heavy operations—including Hardware Info retrieval, HTML exports, and CSV loading—to run on dedicated background threads.
* Enhanced UI Responsiveness: Introduced modern progress spinners and dialogs to ensure the interface remains fully interactive during long-running tasks.
* Refined Report Logic: Upgraded the internal logic for Charts and Reports to improve data accuracy and rendering speed.

🎨 Visual Integration

* Unified Icon Sets: Expanded and standardized the application’s icon library for a more consistent and professional aesthetic.
* Refined UI Elements: Polished the diagnostic reporting interface for better visual clarity.

## v1.4.4 (2026-05-02)

📄 New Feature: HTML Session Reports

* HTML Export Engine: Added _export_html_report to generate a fully self-contained HTML session report, including hardware details, per-sensor stats, signature hits, and embedded charts.
* UI Integration: Introduced a 📄 HTML Report button to the bottom button bar for quick access.
* Zero Dependencies: All CSS, metadata, and charts are embedded directly into the .html file—no external image files or internet connection required.
* Diagnostic Summary: Features severity badges (🔴/🟡/✅), linked Table of Contents, and color-coded cards for diagnostic signature hits.

💡 Notes

* Compatibility: Reports can be generated from any CSV the program supports.
* Hardware Detection: Hardware specifications and categorized groupings within the report require HWiNFO64 logs with a valid label row.
* Settings: Keep your groups.json file when updating to preserve your custom sensor presets.

## v1.4.3 (2026-05-02)

✨ New Features

* Hardware Viewer: Added a 🖥 View Detected Hardware button. Opens a categorized dialog (CPU, GPU, Storage, etc.) with a 📋 Copy All export function.
  - Note: This feature is strictly compatible with HWiNFO64 logs.

🔬 Hardware Detection & Parsing

* Dynamic Row Detection: The parser now scans the entire file for the HWiNFO label row instead of assuming row 2.
* Categorization Rewrite: Switched from keyword matching to native HWiNFO type-tags (dGPU, iGPU, DDR5 DIMM, etc.) for more accurate grouping.
* Name Cleaning:
 - Stripped redundant telemetry suffixes (e.g., : C-State Residency, : Enhanced).
 - De-duplicated hardware prefixes and resolved Brand: Model naming conflicts.
* False-Positive Hardening:
 - Raised row confidence threshold to 25% with a 3-hit minimum.
 - Improved _is_label_cell logic to filter out numeric readings, binary flags (Yes/No), and unit headers ([°C], [MHz]).

🛠️ UI & Bug Fixes

* Sidebar Layout: Fixed an issue where tall sensor lists pushed action buttons off-screen; New CSV, Clear, and Export are now anchored to the panel bottom.
* UI Cleanup: Removed temporary analysis columns from final output to reduce clutter.

💡 Notes

* Compatibility: Detection and categorization features are designed specifically for HWiNFO64 CSV output.
* Settings: Keep your groups.json file when updating to preserve custom presets.

## v1.4.2 (2026-05-02)

* Fixed and improved VRAM overflow detection by switching to an event-based model with duration tracking
* Improved spill detection accuracy using trend + persistence filtering
* Added basic PCIe bus load correlation during VRAM spill events
* Cleaned up temporary analysis columns after processing

## v1.4.1 (2026-04-29)

🔬 Clock Stretching Detection Overhaul (V2)

The CPU diagnostic engine has been fundamentally rebuilt to identify performance loss that traditional average-based sensors miss.

* Per-Core Precision: The engine now evaluates clock behavior on an individual core basis rather than using global averages, catching instability in specific "weak" cores.
* Weighted Effective Clock Logic: * Introduced a Core Pressure metric to distinguish between idle cores and cores actively failing to hit frequency targets under load.
 - Added a Transition Filter to suppress false positives during rapid frequency shifts (e.g., entering/exiting boost states).
* Intelligent Root-Cause Correlation: The engine now cross-references clock stretching with thermal and power signatures (PPT/TDC/EDC) to identify the root cause (e.g., "Thermal Throttling" vs. "Power Limit Saturation").
* Dynamic Severity Tiering: * Major (CRITICAL): Significant, sustained stretching indicating severe instability or cooling failure.
 - Minor (WARNING): Intermittent stretching typical of aggressive PBO limits or "soft" power throttling.

🔬 Advanced Fabric & Memory Diagnostics

A complete rewrite of the synchronization engine, moving beyond simple ratio checks to platform-aware clock analysis.

* Platform-Specific Detection (DDR4 vs. DDR5): Automatically distinguishes between architectures to apply correct synchronization logic (e.g., FCLK/UCLK/MCLK relationships).
* Memory Controller Desync (UCLK/MCLK): New diagnostic specifically targeting DDR5/AM5 platforms to detect when the memory controller falls out of sync, causing increased latency.
* Infinity Fabric (FCLK) Ratio Evaluator: * Added detection for "High Latency Mode" (1:2 ratio) vs. "Optimal" (1:1).
 - New "Invalid/Misreported" state to flag potential sensor or BIOS reporting errors.
* Noise Filtering: Implemented a delta-masking system to ignore transient sensor jitter and "clock drift," ensuring only real synchronization issues are flagged.

🧠 Engine Improvements & Stability

* Dynamic Severity Scaling: Bottleneck detections (CPU/Disk) now scale from INFO to WARNING based on the actual intensity of the impact rather than a fixed state.
* Enhanced Evidence Reporting: Diagnostic logs now include granular data: Target vs. Effective ratios, Desync duration, and System load pressure.
* Optimized Analysis Pipeline: Streamlined the evaluation of rolling samples and CSV parsing to reduce CPU overhead during long-duration log analysis.
* Signal Stabilization: Improved logic for "Background Process Interference" to ensure alerts only trigger on sustained interference that actually affects performance.

🛠️ System & Security Changes

* Hardened Release Pipeline: * Full SHA256 Integrity Chain: Implemented a cryptographic chain of trust (EXE → Manifest → ZIP) to ensure file authenticity.
* Deterministic Builds: Standardized the build environment to ensure that the artifacts generated are consistent and verifiable.
* Structured Manifests: Each release now ships with a detailed manifest.json and build_info.json.
* Automated Documentation: The build pipeline now automatically updates the repository README with latest release links and security hashes.
* UI Fix: Hover behavior for elements now correctly follows the active UI theme instead of defaulting to white styling.

📦 Integrity & Verification

* Reproducible Artifacts: Built via GitHub Actions with a verifiable commit history.
* Checksums: SHA256 hashes are provided for all core components within the release archive to prevent file tampering.

💡 Notes

* Preserve Settings: Ensure you keep your existing groups.json file when updating to preserve custom presets.
* Data Requirements: To utilize the new Clock Stretching V2 logic, ensure your logs include per-core clock and effective clock sensors (available in HWiNFO64).
* Compatibility: If you see "CRITICAL" flags for Fabric clocks on older platforms, verify your BIOS is correctly reporting FCLK/UCLK values.

## v1.4.0 (2026-04-27)

🔬 Signature-Based Diagnostics Expansion
Introduced a major diagnostic overhaul with a new multi-layer signature detection system covering thermal, power, memory, storage, and OS-level behavior anomalies.

This includes detection for:

* CPU thermal throttling
* GPU hotspot delta instability
* VRAM / VRM thermal stress
* Clock stretching and performance degradation
* GPU power limit oscillation
* Memory pressure and VRAM swapping
* RAM controller saturation
* PCIe link degradation
* WHEA hardware errors
* Kernel / DPC latency spikes
* Storage I/O congestion and SMART degradation
* Pagefile overuse and memory exhaustion patterns

🧠 Engine Improvements

* Unified signature evaluation pipeline for cross-sensor correlation
* Improved detection consistency across long-duration logs
* Reduced false negatives in borderline thermal and power cases

🖱️ UI Improvements

* Fixed hover behavior for UI elements to properly follow the active theme instead of defaulting to white styling
* Added new "Detect Signatures" button for manual triggering of the diagnostic engine

⚡ Performance & Stability

* Optimized log parsing and analysis pipeline for lower CPU overhead
* Improved handling of large CSV datasets
* Reduced analysis lag during multi-plot rendering

🛠️ System Changes

* Removed automated VirusTotal CI scanning due to API cost, file size constraints, and CI overhead
* Replaced external scan dependency with SHA256-based integrity verification
* Updated release pipeline to improve build stability and speed

📦 Integrity

* Each release now ships with SHA256 checksum for archive verification
* Builds are fully reproducible via GitHub Actions

💡 Notes

* Ensure you keep your existing groups.json file when updating to preserve custom presets
* Signature detection behavior may vary depending on sensor availability in logs


## v1.3.4 (2026-04-26)

Expanded Monitoring: New detection for Drive Failure, Warning, Total Errors, and Available Spare [%].

New Editor Fields: Added editable thresholds for Drive Health, Memory Load, and Stability sensitivity.

Changed & Fixed
⚡ Performance Boost: Refactored core logic to significantly reduce CPU usage during log analysis.

🛠️ Logic Fixes: Fixed Vcore droop detection and improved generic drive sensor naming.

📉 Threshold Tuning: Raised generic drive limit to 70°C to reduce false alerts.

💡 Note
Important: Ensure you keep your existing groups.json file when updating so you do not lose your custom presets. The file will automatically update with the new sensor fields upon first launch.

## v1.3.3 (2026-04-25)

### Added
🌡️ Heatmap Mode: New view mapping sensor data to Green/Yellow/Red bands for instant stress diagnostics.

⚙️ Limits Editor: Custom UI to set your own "Danger Zones" for Temps, Voltages, and Power limits.

💾 Live-Save: Settings now save and validate instantly as you type in the editor.

Changed & Fixed
🧹 Crash Recovery: Enhanced logic to auto-trim "garbage" zero-rows from logs after a system crash.

📂 Encoding Support: Improved handling of UTF-8, Latin-1, and mixed decimal separators (, vs .).

💡 Note: Your existing presets will migrate automatically. Saving new limits will update your groups.json to the latest format.

## v1.3.1

### Added:

- Preset Renaming: Added a new pencil icon to the dashboard allowing users to rename existing sensor groups without having to recreate them.

- Collision Detection: Implemented a check to prevent accidental overwrites; the app now notifies you if a preset name already exists during a rename or import.

- Time Mode Toggle: Added the ability to switch the X-axis from raw data ticks to human-readable elapsed time (H:MM:SS) via a new "🕒 Time" button.

- Automatic Time Detection: The analyzer now intelligently scans logs for common timestamp or elapsed time headers to calculate session duration.

### Fixed
- Empty Row Filtering: Improved the "Smart Trim" logic to better handle and remove trailing empty or zeroed-out rows from CSV logs, resulting in cleaner graph starts/ends.

## v1.3

GitHub Update System
Added an integrated update checker that queries the GitHub API for new releases.

Implemented "Skip Version" logic to silence notifications for specific updates.

Added a global toggle to disable update checks for users preferring a static environment.

Configuration and Persistence (groups.json)
Migrated application state management to groups.json. The application now preserves Dark Mode, Multi-Plot, and Delta-Mode settings across sessions.

Improved configuration parsing to allow for non-destructive updates. When running a new executable version, the application will automatically inject missing settings keys into your existing groups.json while leaving your custom sensor presets intact.

Refined the "Import from Clipboard" function to streamline the process of adding externally shared sensor groups into the local configuration file.

System Improvements
Optimized UI responsiveness when filtering large sensor lists.

Standardized CSV ingestion to handle varied encoding formats and delimiters across different telemetry tools more reliably.

Understanding groups.json
The groups.json file serves as the central database for your personalized experience. It is divided into two primary sections:

Groups: This section stores your custom sensor presets. When you select specific sensors and save them with a name, the list of column headers is recorded here. This allows you to quickly switch between different diagnostic views (e.g., "Thermal Stress" vs. "Power Delivery").

Settings: This section tracks your UI preferences and update logic. It records whether you prefer Dark Mode and which visualization modes (Multi or Delta) were active when the program was last closed. It also stores the "skipped_version" string to ensure you are not prompted for updates you have already declined.

Deployment Note: To update the application, replace only the .exe file. As long as groups.json remains in the application directory, your data and preferences will be migrated to the new version format upon the first launch.

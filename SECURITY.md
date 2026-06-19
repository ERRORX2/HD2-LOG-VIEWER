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

# Universal Video Downloader - Executables

## Built Files

### GUI Version (Recommended)
- **File**: `UniversalVideoDownloader.exe`
- **Description**: Full-featured GUI application with drag & drop, dark mode, batch downloads, etc.
- **Size**: ~65MB (includes all dependencies)
- **Platforms**: Windows 64-bit

### CLI Version
- **File**: `UniversalVideoDownloader_CLI.exe`  
- **Description**: Command-line interface for automation and scripting
- **Size**: ~54MB (includes all dependencies)
- **Platforms**: Windows 64-bit

## Usage

### GUI Version
Simply double-click `UniversalVideoDownloader.exe` to launch the application.

### CLI Version
Run from command prompt:
```cmd
UniversalVideoDownloader_CLI.exe --help
UniversalVideoDownloader_CLI.exe -u "https://youtube.com/watch?v=VIDEO_ID"
```

## System Requirements
- Windows 10/11 (64-bit)
- No additional software required (all dependencies included)

## Notes
- Both executables are portable (no installation required)
- First launch may take a few seconds as dependencies are unpacked
- Antivirus software may flag the executables initially (this is normal for PyInstaller builds)

## Creating Executables for Other Platforms

### For Mac (.app or .dmg)
Run on macOS with Python and dependencies installed:
```bash
pyinstaller --onefile --windowed --name=UniversalVideoDownloader downloader_gui.py
```

### For Linux (.AppImage)
Run on Linux with Python and dependencies installed:
```bash
pyinstaller --onefile --name=UniversalVideoDownloader downloader_gui.py
```
Then package as AppImage using available tools.

## Build Information
- Built with: PyInstaller 6.15.0
- Python Version: 3.13.6
- Build Date: $(date)
- Dependencies: yt-dlp, PyQt5, requests, and others
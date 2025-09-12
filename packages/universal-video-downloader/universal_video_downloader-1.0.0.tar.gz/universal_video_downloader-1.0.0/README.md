# Universal Video Downloader

Download videos and audio from YouTube, TikTok, Instagram, Facebook, X (Twitter), Reddit, Vimeo, DailyMotion, and more — fast, private, and organized.

## Features

- 🚀 Batch downloads & playlists
- 🎵 MP3 extraction with metadata
- 📅 Scheduler & tray/background mode
- 🛡️ Proxy & cookies for private content
- 🎨 Modern cross-platform GUI (Windows, Mac, Linux)
- 🌓 Dark mode & drag-and-drop support
- 🔄 Update checker
- 📝 Subtitle and audio extraction
- ☁️ Upload to cloud storage (Pro)
- 🆓 Free and Pro versions

## Download Options

### 1. Pre-built Executables (Recommended)
Download the latest release for your platform:

- [Windows GUI (.exe)](https://github.com/Aarif5856/UniversalVideoDownloader/releases/latest/download/UniversalVideoDownloader.exe)
- [Windows CLI (.exe)](https://github.com/Aarif5856/UniversalVideoDownloader/releases/latest/download/UniversalVideoDownloader_CLI.exe)

### 2. Portable ZIP Package
- [Portable ZIP](https://github.com/Aarif5856/UniversalVideoDownloader/releases/latest/download/UniversalVideoDownloader_v1.0.0_Portable.zip) - No installation required

### 3. Python Package (pip install)
```bash
pip install universal-video-downloader
uvd --help
```

## Windows Security Warning ⚠️
Windows may flag executables as suspicious (false positive). This is common with PyInstaller builds.
- **Safe to use**: Our code is open source and verified
- **VirusTotal scan**: Upload to https://www.virustotal.com for verification
- **Add exclusion**: In Windows Defender if needed

## Usage

### GUI Version
Simply double-click the executable to launch the application with full interface.

### CLI Version
```cmd
# Basic download
UniversalVideoDownloader_CLI.exe -u "https://youtube.com/watch?v=VIDEO_ID"

# With options
UniversalVideoDownloader_CLI.exe -u "URL" --format mp4 --quality 720p
```

### Python Package
```bash
# GUI
uvd-gui

# CLI
uvd -u "VIDEO_URL"
```

## Installation Guide

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed installation instructions for all platforms.

## System Requirements
- Windows 10/11 (64-bit)
- No additional software required for executables
- Python 3.8+ required for pip installation

## Screenshots

![App Screenshot](screenshot.png)

## FAQ

**Q: What platforms are supported?**  
A: YouTube, TikTok, Instagram, Facebook, X, Reddit, Vimeo, DailyMotion, and more.

**Q: Is it free?**  
A: Yes! The Free version covers most features. Upgrade to Pro for advanced options.

**Q: How do I report bugs or request features?**  
A: Open an issue on GitHub or contact support.

**Q: Why does Windows flag this as a virus?**  
A: This is a false positive common with PyInstaller. The code is open source and safe.

## Development

### Build from Source
```bash
git clone https://github.com/Aarif5856/UniversalVideoDownloader.git
cd UniversalVideoDownloader
pip install -r requirements.txt
python downloader_gui.py
```

### Create Executables
```bash
pip install pyinstaller
pyinstaller --onefile --windowed downloader_gui.py
```

## License

MIT License

## Support

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/Aarif5856/UniversalVideoDownloader/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Aarif5856/UniversalVideoDownloader/discussions)

---

© 2025 Universal Video Downloader. All rights reserved.
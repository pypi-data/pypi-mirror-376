#!/usr/bin/env python3
"""
Build script to create executables for Universal Video Downloader
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔨 {description}")
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    # Get the current directory
    current_dir = Path(__file__).parent
    os.chdir(current_dir)
    
    print("🚀 Building Universal Video Downloader executables...")
    
    # Python executable path
    python_exe = "C:/Users/USER/downloder/.venv/Scripts/python.exe"
    pyinstaller_exe = "C:/Users/USER/downloder/.venv/Scripts/pyinstaller.exe"
    
    # Build GUI version (main executable)
    gui_cmd = [
        pyinstaller_exe,
        "--onefile",
        "--windowed",
        "--name=UniversalVideoDownloader",
        "--icon=NONE",  # We'll add an icon later
        "--add-data=*.py;.",
        "--hidden-import=PyQt5",
        "--hidden-import=yt_dlp",
        "--hidden-import=requests",
        "--hidden-import=tkinterdnd2",
        "downloader_gui.py"
    ]
    
    if not run_command(gui_cmd, "Building GUI executable"):
        return False
    
    # Build CLI version
    cli_cmd = [
        pyinstaller_exe,
        "--onefile",
        "--name=UniversalVideoDownloader_CLI",
        "--icon=NONE",
        "--hidden-import=yt_dlp",
        "--hidden-import=requests",
        "downloader.py"
    ]
    
    if not run_command(cli_cmd, "Building CLI executable"):
        return False
    
    print("\n🎉 Build completed successfully!")
    print("\nExecutables created:")
    print("📁 dist/UniversalVideoDownloader.exe - GUI version")
    print("📁 dist/UniversalVideoDownloader_CLI.exe - CLI version")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
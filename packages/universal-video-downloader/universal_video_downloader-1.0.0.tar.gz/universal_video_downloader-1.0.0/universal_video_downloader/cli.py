
"""
TikTok, Instagram, YouTube & Facebook Downloader Script
Requirements: yt-dlp
Usage:
    python downloader.py <video_url>
    python downloader.py --batch <urls.txt>
Supports TikTok, Instagram, YouTube, Facebook, and many other platforms supported by yt-dlp
Features:
    - Batch download from text file
    - Format selection
    - Progress bar
    - Error logging
    - Simple GUI (Tkinter)
"""

import sys
import os
import threading
import time
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog


DOWNLOAD_DIR = "downloads"
ERROR_LOG = "error_log.txt"

def ensure_download_dir():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

def log_error(url, error):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{url}: {error}\n")

def download_video(url, format_code=None, show_progress=True, proxy=None, subtitles=False, audio=False, cookies=None):
    ensure_download_dir()
    # Auto file naming: {platform}/{creator}/{title}.{ext}
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(extractor)s/%(uploader)s/%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook] if show_progress else [],
        'ignoreerrors': True,
        'noplaylist': False,
    }
    if format_code:
        ydl_opts['format'] = format_code
    if proxy:
        ydl_opts['proxy'] = proxy
    if subtitles:
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True
        ydl_opts['subtitlesformat'] = 'srt'
    if audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }, {
            'key': 'FFmpegMetadata',
        }]
    if cookies:
        ydl_opts['cookiefile'] = cookies
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Downloaded: {url}")
    except DownloadError as e:
        print(f"Failed to download: {url}\nError: {e}")
        log_error(url, str(e))
    except Exception as e:
        print(f"Failed to download: {url}\nError: {e}")
        log_error(url, str(e))

def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total:
            percent = downloaded / total * 100
            print(f"Progress: {percent:.2f}%", end='\r')
    elif d['status'] == 'finished':
        print("Download finished.            ")

class DownloadQueue:
    def __init__(self, urls, format_code=None, proxy=None, threads=1):
        self.urls = urls
        self.format_code = format_code
        self.proxy = proxy
        self.threads = threads
        self.paused = threading.Event()
        self.paused.set()  # Not paused initially
        self.stopped = False

    def pause(self):
        self.paused.clear()

    def resume(self):
        self.paused.set()

    def stop(self):
        self.stopped = True
        self.paused.set()

    def worker(self, url):
        while not self.paused.is_set():
            time.sleep(0.1)
        if self.stopped:
            return
        download_video(url, self.format_code, proxy=self.proxy)

    def run(self):
        import concurrent.futures
        if self.threads > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
                executor.map(self.worker, self.urls)
        else:
            for url in self.urls:
                if self.stopped:
                    break
                self.worker(url)

def batch_download(file_path, format_code=None, proxy=None, threads=1, queue_control=False):
    with open(file_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    if queue_control:
        queue = DownloadQueue(urls, format_code, proxy, threads)
        t = threading.Thread(target=queue.run)
        t.start()
        print("Batch download started. Type 'pause', 'resume', or 'stop' to control.")
        while t.is_alive():
            cmd = input().strip().lower()
            if cmd == 'pause':
                queue.pause()
                print("Paused.")
            elif cmd == 'resume':
                queue.resume()
                print("Resumed.")
            elif cmd == 'stop':
                queue.stop()
                print("Stopped.")
                break
        t.join()
    else:
        queue = DownloadQueue(urls, format_code, proxy, threads)
        queue.run()


def main():
    import argparse
    import time
    import requests
    parser = argparse.ArgumentParser(description="Universal Video Downloader")
    parser.add_argument("url", nargs="?", help="Video URL to download (single video, playlist, channel, or profile)")
    parser.add_argument("--batch", help="Path to text file with URLs (one per line)")
    parser.add_argument("--format", help="Format code (e.g. best, worst, 22, 18, etc.)")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    parser.add_argument("--proxy", help="Proxy URL (e.g. socks5://127.0.0.1:1080)")
    parser.add_argument("--threads", type=int, default=1, help="Number of concurrent downloads for batch mode")
    parser.add_argument("--queue", action="store_true", help="Enable queue control for batch downloads (pause/resume/stop)")
    parser.add_argument("--subtitles", action="store_true", help="Download subtitles/captions if available")
    parser.add_argument("--audio", action="store_true", help="Extract audio as MP3 with metadata")
    parser.add_argument("--cookies", help="Path to cookies.txt file for private video downloads")
    parser.add_argument("--schedule", help="Schedule download at time (HH:MM, 24h format)")
    parser.add_argument("--check-update", action="store_true", help="Check for new version")
    parser.add_argument("--gui", action="store_true", help="Launch GUI")
    args = parser.parse_args()

    VERSION = "1.0.0"
    UPDATE_URL = "https://api.github.com/repos/yourusername/yourrepo/releases/latest"

    def check_update():
        try:
            resp = requests.get(UPDATE_URL, timeout=5)
            if resp.status_code == 200:
                latest = resp.json()["tag_name"]
                if latest != VERSION:
                    print(f"New version available: {latest}. Download at https://github.com/yourusername/yourrepo")
                else:
                    print("You are using the latest version.")
            else:
                print("Could not check for updates.")
        except Exception:
            print("Could not check for updates.")

    def wait_until_schedule(schedule_time):
        now = time.localtime()
        target = time.strptime(schedule_time, "%H:%M")
        target_sec = target.tm_hour * 3600 + target.tm_min * 60
        now_sec = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
        wait_sec = target_sec - now_sec
        if wait_sec < 0:
            wait_sec += 24 * 3600  # Next day
        print(f"Scheduled download in {wait_sec//60} min {wait_sec%60} sec...")
        time.sleep(wait_sec)

    if args.check_update:
        check_update()
        return

    if args.gui:
        launch_gui()
        return

    if args.schedule:
        wait_until_schedule(args.schedule)

    if args.batch:
        batch_download(args.batch, args.format, proxy=args.proxy, threads=args.threads, queue_control=args.queue)
    elif args.url:
        download_video(args.url, args.format, not args.no_progress, proxy=args.proxy, subtitles=args.subtitles, audio=args.audio, cookies=args.cookies)
    else:
        print("Usage: python downloader.py <video_url> [--format <code>] [--batch <file>] [--proxy <url>] [--threads <n>] [--queue] [--subtitles] [--audio] [--cookies <file>] [--schedule HH:MM] [--check-update] [--gui]")

def launch_gui():
    def start_download():
        url = url_entry.get()
        format_code = format_entry.get()
        if url:
            download_video(url, format_code)
            messagebox.showinfo("Done", "Download finished!")
        else:
            messagebox.showerror("Error", "Please enter a video URL.")

    def start_batch():
        file_path = filedialog.askopenfilename(title="Select URL text file", filetypes=[("Text Files", "*.txt")])
        format_code = format_entry.get()
        if file_path:
            batch_download(file_path, format_code)
            messagebox.showinfo("Done", "Batch download finished!")

    def on_drop(event):
        # Drag & drop support for URLs
        url = event.data.strip()
        url_entry.delete(0, tk.END)
        url_entry.insert(0, url)

    # Basic dark mode
    root = tk.Tk()
    root.title("Universal Video Downloader")
    root.geometry("400x220")
    root.configure(bg="#222")

    label_fg = "#fff"
    entry_bg = "#333"
    entry_fg = "#fff"
    button_bg = "#444"
    button_fg = "#fff"

    tk.Label(root, text="Video URL:", bg="#222", fg=label_fg).pack()
    url_entry = tk.Entry(root, width=50, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    url_entry.pack()

    # Drag & drop support (Windows only, requires tkdnd)
    try:
        import tkinterdnd2 as tkdnd
        dnd_root = tkdnd.TkinterDnD.Tk()
        url_entry.drop_target_register(tkdnd.DND_TEXT)
        url_entry.dnd_bind('<<Drop>>', on_drop)
    except ImportError:
        pass  # tkdnd not installed, skip drag & drop

    tk.Label(root, text="Format code (optional):", bg="#222", fg=label_fg).pack()
    format_entry = tk.Entry(root, width=20, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    format_entry.pack()

    tk.Button(root, text="Download", command=start_download, bg=button_bg, fg=button_fg).pack(pady=5)
    tk.Button(root, text="Batch Download", command=start_batch, bg=button_bg, fg=button_fg).pack(pady=5)

    tk.Label(root, text="Drag & drop a URL into the box above.", bg="#222", fg=label_fg).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()

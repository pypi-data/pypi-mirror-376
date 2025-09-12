import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

DOWNLOAD_DIR = "downloads"

class DownloaderThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, url, format_code=None, proxy=None, subtitles=False, audio=False):
        super().__init__()
        self.url = url
        self.format_code = format_code
        self.proxy = proxy
        self.subtitles = subtitles
        self.audio = audio

    def run(self):
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(extractor)s/%(uploader)s/%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'ignoreerrors': True,
            'noplaylist': False,
        }
        if self.format_code:
            ydl_opts['format'] = self.format_code
        if self.proxy:
            ydl_opts['proxy'] = self.proxy
        if self.subtitles:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitlesformat'] = 'srt'
        if self.audio:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }, {
                'key': 'FFmpegMetadata',
            }]
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit(f"Downloaded: {self.url}")
        except DownloadError as e:
            self.error.emit(f"Failed: {self.url}\nError: {e}")
        except Exception as e:
            self.error.emit(f"Failed: {self.url}\nError: {e}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total * 100
                self.progress.emit(f"Progress: {percent:.2f}%")
        elif d['status'] == 'finished':
            self.progress.emit("Download finished.")

class DownloaderApp(QtWidgets.QWidget):
    VERSION = "1.0.0"
    UPDATE_URL = "https://api.github.com/repos/yourusername/yourrepo/releases/latest"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Video Downloader (PyQt)")
        self.setGeometry(100, 100, 500, 260)
        self.setAcceptDrops(True)
        self.init_ui()
        self.set_dark_mode()
        self.thread = None
        self.tray_icon = None
        self.create_tray_icon()
        self.check_update()
    def check_update(self):
        import requests
        try:
            resp = requests.get(self.UPDATE_URL, timeout=5)
            if resp.status_code == 200:
                latest = resp.json()["tag_name"]
                if latest != self.VERSION:
                    QtWidgets.QMessageBox.information(self, "Update Available", f"New version: {latest}. Download at https://github.com/yourusername/yourrepo")
            # else: silent if up-to-date or error
        except Exception:
            pass

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        self.url_label = QtWidgets.QLabel("Video URL:")
        self.url_entry = QtWidgets.QLineEdit()
        self.url_entry.setPlaceholderText("Paste or drag & drop a video URL here")
        self.format_label = QtWidgets.QLabel("Format code (optional):")
        self.format_entry = QtWidgets.QLineEdit()
        self.format_entry.setPlaceholderText("e.g. best, worst, 22, 18")
        self.subtitles_checkbox = QtWidgets.QCheckBox("Download subtitles/captions (.srt)")
        self.audio_checkbox = QtWidgets.QCheckBox("Extract audio as MP3 with metadata")
        self.schedule_label = QtWidgets.QLabel("Schedule (HH:MM, 24h):")
        self.schedule_entry = QtWidgets.QLineEdit()
        self.schedule_entry.setPlaceholderText("Leave blank for immediate download")
        self.download_btn = QtWidgets.QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        self.progress_label = QtWidgets.QLabel("")
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_entry)
        layout.addWidget(self.format_label)
        layout.addWidget(self.format_entry)
        layout.addWidget(self.subtitles_checkbox)
        layout.addWidget(self.audio_checkbox)
        layout.addWidget(self.schedule_label)
        layout.addWidget(self.schedule_entry)
        layout.addWidget(self.download_btn)
        layout.addWidget(self.progress_label)
        self.setLayout(layout)

    def create_tray_icon(self):
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        tray_menu = QtWidgets.QMenu()
        show_action = tray_menu.addAction("Show")
        exit_action = tray_menu.addAction("Exit")
        show_action.triggered.connect(self.show_window)
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.show_window()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Universal Video Downloader",
            "Running in background. Click tray icon to restore.",
            QtWidgets.QSystemTrayIcon.Information,
            2000
        )

    def set_dark_mode(self):
        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(34, 34, 34))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(51, 51, 51))
        dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(68, 68, 68))
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(255, 255, 255))
        self.setPalette(dark_palette)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        url = event.mimeData().text().strip()
        self.url_entry.setText(url)

    def start_download(self):
        import time
        url = self.url_entry.text().strip()
        format_code = self.format_entry.text().strip()
        subtitles = self.subtitles_checkbox.isChecked()
        audio = self.audio_checkbox.isChecked()
        schedule_time = self.schedule_entry.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter a video URL.")
            return
        if schedule_time:
            now = time.localtime()
            try:
                target = time.strptime(schedule_time, "%H:%M")
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Error", "Invalid time format. Use HH:MM (24h)")
                return
            target_sec = target.tm_hour * 3600 + target.tm_min * 60
            now_sec = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
            wait_sec = target_sec - now_sec
            if wait_sec < 0:
                wait_sec += 24 * 3600
            self.progress_label.setText(f"Scheduled download in {wait_sec//60} min {wait_sec%60} sec...")
            QtWidgets.QApplication.processEvents()
            time.sleep(wait_sec)
        self.download_btn.setEnabled(False)
        self.progress_label.setText("Starting download...")
        self.thread = DownloaderThread(url, format_code, subtitles=subtitles, audio=audio)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.download_finished)
        self.thread.error.connect(self.download_error)
        self.thread.start()

    def update_progress(self, msg):
        self.progress_label.setText(msg)

    def download_finished(self, msg):
        self.progress_label.setText(msg)
        self.download_btn.setEnabled(True)

    def download_error(self, msg):
        self.progress_label.setText(msg)
        self.download_btn.setEnabled(True)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DownloaderApp()
    window.show()
    sys.exit(app.exec_())

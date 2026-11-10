#!/usr/bin/env python3
"""Instagram Like Bot v2 - GUI (PyQt5) dan CLI.

GUI : python3 main.py
CLI : python3 main.py --cli -u USERNAME -t python,linux [--max-likes 20] [--headless]
      (password dibaca dari env IG_PASSWORD, atau diminta secara tersembunyi)
"""
import argparse
import getpass
import os
import sys
import threading

from scraper import InstagramBot, parse_hashtags


def run_cli(args) -> int:
    tags = parse_hashtags(args.tags or "")
    if not args.username or not tags:
        print("Butuh --username dan --tags yang valid.", file=sys.stderr)
        return 2
    password = os.environ.get("IG_PASSWORD") or getpass.getpass("Password Instagram: ")
    stop = threading.Event()
    bot = InstagramBot(args.username, password, headless=args.headless,
                       max_likes=args.max_likes, stop_event=stop)
    try:
        bot.run(tags)
    except KeyboardInterrupt:
        stop.set()
        print("\nDihentikan (Ctrl+C).")
    return 0


def run_gui() -> int:
    from PyQt5 import QtCore, QtWidgets

    class Worker(QtCore.QThread):
        log = QtCore.pyqtSignal(str)

        def __init__(self, user, pwd, tags, max_likes, headless):
            super().__init__()
            self.stop_event = threading.Event()
            self.bot = InstagramBot(user, pwd, headless=headless, max_likes=max_likes,
                                    log=self.log.emit, stop_event=self.stop_event)
            self.tags = tags

        def run(self):
            self.bot.run(self.tags)

    class Window(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.worker = None
            self.setWindowTitle("Instagram Like Bot v2")
            self.resize(560, 480)
            self.username = QtWidgets.QLineEdit()
            self.password = QtWidgets.QLineEdit()
            self.password.setEchoMode(QtWidgets.QLineEdit.Password)
            self.hashtags = QtWidgets.QLineEdit()
            self.hashtags.setPlaceholderText("python, linux, kalilinux")
            self.max_likes = QtWidgets.QSpinBox()
            self.max_likes.setRange(1, 200)
            self.max_likes.setValue(30)
            self.headless = QtWidgets.QCheckBox("Headless (tanpa jendela browser)")
            self.start_btn = QtWidgets.QPushButton("Start")
            self.stop_btn = QtWidgets.QPushButton("Stop")
            self.stop_btn.setEnabled(False)
            self.output = QtWidgets.QPlainTextEdit()
            self.output.setReadOnly(True)

            form = QtWidgets.QFormLayout()
            form.addRow("Username", self.username)
            form.addRow("Password", self.password)
            form.addRow("Hashtag", self.hashtags)
            form.addRow("Maks. like", self.max_likes)
            form.addRow("", self.headless)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.start_btn)
            row.addWidget(self.stop_btn)
            layout = QtWidgets.QVBoxLayout(self)
            layout.addLayout(form)
            layout.addLayout(row)
            layout.addWidget(self.output)
            self.start_btn.clicked.connect(self.start)
            self.stop_btn.clicked.connect(self.stop)

        def append(self, text):
            self.output.appendPlainText(text)

        def start(self):
            user, pwd = self.username.text().strip(), self.password.text()
            tags = parse_hashtags(self.hashtags.text())
            if not user or not pwd or not tags:
                self.append("Isi username, password, dan minimal satu hashtag valid.")
                return
            self.worker = Worker(user, pwd, tags, self.max_likes.value(),
                                 self.headless.isChecked())
            self.worker.log.connect(self.append)
            self.worker.finished.connect(self.done)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.worker.start()

        def stop(self):
            if self.worker:
                self.worker.stop_event.set()
                self.append("Menghentikan...")

        def done(self):
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

        def closeEvent(self, event):
            if self.worker and self.worker.isRunning():
                self.worker.stop_event.set()
                self.worker.wait(8000)
            event.accept()

    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    win.show()
    return app.exec_()


def main() -> int:
    p = argparse.ArgumentParser(description="Instagram hashtag like bot")
    p.add_argument("--cli", action="store_true", help="mode terminal tanpa GUI")
    p.add_argument("-u", "--username")
    p.add_argument("-t", "--tags", help="hashtag dipisah koma, mis. python,linux")
    p.add_argument("--max-likes", type=int, default=30)
    p.add_argument("--headless", action="store_true")
    args = p.parse_args()
    return run_cli(args) if args.cli else run_gui()


if __name__ == "__main__":
    sys.exit(main())

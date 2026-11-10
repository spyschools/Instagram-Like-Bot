"""Mesin bot: like postingan Instagram berdasarkan hashtag (Selenium 4 + Firefox)."""
from __future__ import annotations

import random
import re
import threading
import time
from typing import Callable, Iterable, List, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE = "https://www.instagram.com"
HASHTAG_RE = re.compile(r"^\w{1,100}$", re.UNICODE)

# Selector berbasis aria-label (jauh lebih stabil daripada class CSS acak).
# Bahasa browser dipaksa ke en-US; "Suka" disertakan sebagai cadangan (Indonesia).
LIKE_XPATH = ("//*[local-name()='svg'][@aria-label='Like' or @aria-label='Suka']"
              "/ancestor::*[@role='button'][1]")
UNLIKE_XPATH = ("//*[local-name()='svg'][@aria-label='Unlike' "
                "or @aria-label='Batal Suka']")
POPUP_XPATH = ("//button[normalize-space()='Not now' or normalize-space()='Not Now' "
               "or normalize-space()='Nanti Saja' or normalize-space()='Lain Kali' "
               "or contains(., 'Decline optional cookies') "
               "or contains(., 'Tolak cookie opsional')]")
BLOCK_MARKERS = ("action blocked", "try again later",
                 "tindakan diblokir", "coba lagi nanti")


class BotStopped(Exception):
    """Dihentikan oleh pengguna."""


class BotError(Exception):
    """Kesalahan yang tidak bisa dilanjutkan (login gagal, akun dibatasi, dll)."""


def parse_hashtags(text: str) -> List[str]:
    """'#python, linux  ai' -> ['python', 'linux', 'ai'] (hanya karakter aman)."""
    tags = []
    for raw in re.split(r"[,\s]+", text or ""):
        tag = raw.strip().lstrip("#")
        if tag and HASHTAG_RE.match(tag) and tag not in tags:
            tags.append(tag)
    return tags


class InstagramBot:
    def __init__(self, username: str, password: str, *, headless: bool = False,
                 max_likes: int = 30, min_delay: float = 5.0, max_delay: float = 12.0,
                 log: Callable[[str], None] = print,
                 stop_event: Optional[threading.Event] = None):
        self.username = username
        self._password = password
        self.headless = headless
        self.max_likes = max_likes
        self.min_delay = min_delay
        self.max_delay = max(max_delay, min_delay)
        self.log = log
        self.stop_event = stop_event or threading.Event()
        self.driver: Optional[webdriver.Firefox] = None
        self.likes = 0

    # ---------- util ----------
    def _check_stop(self) -> None:
        if self.stop_event.is_set():
            raise BotStopped()

    def _sleep(self, a: float, b: Optional[float] = None) -> None:
        end = time.time() + (random.uniform(a, b) if b else a)
        while time.time() < end:
            self._check_stop()
            time.sleep(0.25)

    def _pause(self) -> None:
        self._sleep(self.min_delay, self.max_delay)

    def _dismiss_popups(self) -> None:
        for btn in self.driver.find_elements(By.XPATH, POPUP_XPATH)[:2]:
            try:
                btn.click()
                self._sleep(1, 2)
            except WebDriverException:
                pass

    def _is_blocked(self) -> bool:
        try:
            text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        except WebDriverException:
            return False
        return any(m in text for m in BLOCK_MARKERS)

    # ---------- browser ----------
    def start(self) -> None:
        opts = Options()
        if self.headless:
            opts.add_argument("-headless")
        opts.set_preference("intl.accept_languages", "en-US, en")
        opts.set_preference("dom.webdriver.enabled", True)
        self.log("Membuka Firefox...")
        self.driver = webdriver.Firefox(options=opts)  # geckodriver via Selenium Manager
        self.driver.set_window_size(1100, 900)

    def close(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
            self.driver = None

    # ---------- aksi ----------
    def login(self) -> None:
        d = self.driver
        d.get(f"{BASE}/accounts/login/")
        self._sleep(3, 5)
        self._dismiss_popups()
        wait = WebDriverWait(d, 20)
        try:
            user = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        except TimeoutException:
            raise BotError("Form login tidak ditemukan (halaman berubah / diblokir).")
        pwd = d.find_element(By.NAME, "password")
        user.clear()
        user.send_keys(self.username)
        self._sleep(1, 2)
        pwd.clear()
        pwd.send_keys(self._password)
        self._sleep(1, 2)
        pwd.send_keys(Keys.ENTER)

        deadline = time.time() + 20
        while "/accounts/login" in d.current_url and time.time() < deadline:
            self._sleep(1)
        if any(k in d.current_url for k in ("challenge", "two_factor", "suspended")):
            if self.headless:
                raise BotError("Instagram meminta verifikasi/2FA. Jalankan tanpa --headless.")
            self.log("Verifikasi/2FA diminta. Selesaikan manual di jendela Firefox (maks 2 menit)...")
            end = time.time() + 120
            while any(k in d.current_url for k in ("challenge", "two_factor")) and time.time() < end:
                self._sleep(2)
        if "/accounts/login" in d.current_url:
            raise BotError("Login gagal. Periksa username/password.")
        self._sleep(2, 4)
        self._dismiss_popups()
        self._dismiss_popups()
        self.log(f"Login berhasil sebagai {self.username}")

    def _collect_posts(self, tag: str) -> List[str]:
        d = self.driver
        d.get(f"{BASE}/explore/tags/{tag}/")
        try:
            WebDriverWait(d, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/p/']")))
        except TimeoutException:
            self.log(f"#{tag}: tidak ada postingan ditemukan.")
            return []
        for _ in range(3):
            d.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            self._sleep(2, 4)
        hrefs = [a.get_attribute("href") for a in
                 d.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")]
        return list(dict.fromkeys(h for h in hrefs if h))

    def like_hashtag(self, tag: str) -> None:
        self.log(f"Mencari postingan #{tag} ...")
        posts = self._collect_posts(tag)
        self.log(f"#{tag}: {len(posts)} postingan ditemukan.")
        for url in posts:
            self._check_stop()
            if self.likes >= self.max_likes:
                return
            self.driver.get(url)
            self._sleep(3, 5)
            if self._is_blocked():
                raise BotError("Instagram membatasi aksi (Action Blocked). "
                               "Berhenti dulu; coba lagi setelah beberapa jam.")
            if self.driver.find_elements(By.XPATH, UNLIKE_XPATH):
                continue  # sudah di-like
            try:
                btn = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, LIKE_XPATH)))
                btn.click()
            except (TimeoutException, WebDriverException):
                self.log("Tombol like tidak ditemukan, lewati.")
                continue
            self.likes += 1
            self.log(f"[{self.likes}/{self.max_likes}] Liked: {url}")
            self._pause()

    def run(self, hashtags: Iterable[str]) -> None:
        try:
            self.start()
            self.login()
            for tag in hashtags:
                if self.likes >= self.max_likes:
                    break
                self.like_hashtag(tag)
            self.log(f"Selesai. Total like: {self.likes}")
        except BotStopped:
            self.log("Dihentikan oleh pengguna.")
        except BotError as e:
            self.log(f"ERROR: {e}")
        except WebDriverException as e:
            self.log(f"ERROR browser: {str(e).splitlines()[0]}")
        finally:
            self.close()

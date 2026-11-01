"""
Copyright (c) 2026 amthruster-dev. All rights reserved.

Spoty Ad X v3 - no login needed (Windows, no terminal window).
Reads Spoty's "now playing" info from Windows media controls + window titles.
Install:  pip install pycaw psutil comtypes
Run:      double-click ad_muter.pyw
"""
import base64
import ctypes
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
import traceback
from ctypes import wintypes
from tkinter import filedialog, scrolledtext

import comtypes
import psutil
from pycaw.pycaw import AudioUtilities

AD_TITLES = {"advertisement", "\u2014", "\u2013", "-"}
IDLE_TITLES = {"spotify", "spotify free", "spotify premium"}
JUNK_PREFIXES = ("gdi+", "default ime", "msctfime", "chrome legacy")


def main_titles(wtitles):
    return [t for t in wtitles if not t.lower().startswith(JUNK_PREFIXES)]

TERMS = (
    'Use this app at your own risk. It is provided "as is", without warranty of any kind. The developer (amthruster-dev) is not responsible or liable for any damages, losses, or legal issues arising from downloading, installing, or using this app, including problems with your Spotify account or its terms of service, damage to your device, or audio that is muted or not muted by mistake.'
    "\n\n"
    "This app is not affiliated with, endorsed by, or sponsored by Spotify. It only reads what is already shown on your device (the Spotify window title on Windows, the Spotify notification on Android). It does not block or skip ads and does not access your Spotify account. On Android it sets the phone's media volume to 0 during an ad and restores it afterward. Using it may go against the terms of the services you use, and you are responsible for following the laws and terms that apply to you."
    "\n\n"
    'By installing or using this app you accept these terms.'
)

PS_SCRIPT = r"""
$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($op, $type) {
  $m = $asTask.MakeGenericMethod($type)
  $t = $m.Invoke($null, @($op))
  $t.Wait(-1) | Out-Null
  $t.Result
}
$null = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime]
$null = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties, Windows.Media.Control, ContentType=WindowsRuntime]
$mgr = Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
while ($true) {
  $out = 'NONE'
  try {
    foreach ($s in $mgr.GetSessions()) {
      if ($s.SourceAppUserModelId -match 'Spotify') {
        $p = Await ($s.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
        $out = $p.Title + '|' + $p.Artist
      }
    }
  } catch { $out = 'ERR' }
  [Console]::Out.WriteLine($out)
  [Console]::Out.Flush()
  Start-Sleep -Milliseconds 600
}
"""

user32 = ctypes.windll.user32
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def window_titles():
    pids = {p.pid for p in psutil.process_iter(["name"])
            if (p.info["name"] or "").lower() == "spotify.exe"}
    titles = []

    def cb(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids:
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                titles.append(buf.value.strip())
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    return bool(pids), titles


def master_volume():
    dev = AudioUtilities.GetSpeakers()
    if hasattr(dev, "EndpointVolume"):
        return dev.EndpointVolume
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import IAudioEndpointVolume
    iface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return ctypes.cast(iface, ctypes.POINTER(IAudioEndpointVolume))


def apply_mute(mode, mute):
    if mode == "master":
        master_volume().SetMute(1 if mute else 0, None)
        return True
    found = False
    for s in AudioUtilities.GetAllSessions():
        if s.Process and s.Process.name().lower() == "spotify.exe":
            s.SimpleAudioVolume.SetMute(1 if mute else 0, None)
            found = True
    return found


class Worker(threading.Thread):
    def __init__(self, q):
        super().__init__(daemon=True)
        self.q = q
        self.enabled = True
        self.mode = "spotify"
        self.muted = False
        self.test_until = 0
        self.media = "NONE"  # latest line from PowerShell

    def start_ps(self):
        enc = base64.b64encode(PS_SCRIPT.encode("utf-16-le")).decode()
        proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
            creationflags=0x08000000)  # CREATE_NO_WINDOW

        def reader():
            for raw in proc.stdout:
                self.media = raw.decode("utf-8", "replace").strip()

        threading.Thread(target=reader, daemon=True).start()
        self.proc = proc

    def run(self):
        comtypes.CoInitialize()
        self.start_ps()
        while True:
            try:
                running, wtitles = window_titles()
                media = self.media
                title, artist = "", ""
                if "|" in media:
                    title, artist = media.rsplit("|", 1)
                self.q.put(("info", running, media, wtitles))

                if time.time() < self.test_until:
                    if not self.muted:
                        apply_mute(self.mode, True)
                        self.muted = True
                        self.q.put(("log", "TEST: muted for 3 seconds"))
                    time.sleep(0.3)
                    continue

                ad_media = bool(title or artist) and (
                    title.lower() in AD_TITLES or artist.lower() == "spotify")
                main = main_titles(wtitles)
                # Music always shows "Artist - Song". Anything else (except idle) is an ad.
                ad_window = (running and bool(main)
                             and not any(" - " in t for t in main)
                             and not all(t.lower() in IDLE_TITLES for t in main))
                is_ad = self.enabled and running and (ad_media or bool(ad_window))

                if is_ad != self.muted:
                    if apply_mute(self.mode, is_ad):
                        self.muted = is_ad
                        self.q.put(("log", "AD detected - muted" if is_ad else "Music - unmuted"))
                        if is_ad:
                            self.q.put(("ad",))
                    else:
                        self.q.put(("log", "No audio target found to mute"))

                if not self.enabled:
                    self.q.put(("state", "paused"))
                elif not running:
                    self.q.put(("state", "idle"))
                else:
                    self.q.put(("state", "ad" if self.muted else "music"))
            except Exception:
                self.q.put(("log", traceback.format_exc()))
            time.sleep(0.4)


class App(tk.Tk):
    COLORS = {"music": "#1db954", "ad": "#e22134", "idle": "#777777", "paused": "#777777"}
    TEXT = {"music": "Playing music", "ad": "AD - MUTED", "idle": "Spoty not running",
            "paused": "Stopped"}

    def __init__(self):
        super().__init__()
        self.title("Spoty Ad X")
        try:
            base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            self.iconbitmap(os.path.join(base, "icon.ico"))
        except Exception:
            pass
        self.geometry("460x500")
        self.configure(bg="#121212")
        self.ads = 0
        self.records = []
        self.last_info = None
        self.q = queue.Queue()
        self.worker = Worker(self.q)

        self.status = tk.Label(self, text="Starting...", font=("Segoe UI", 20, "bold"),
                               fg="white", bg="#777777", pady=14)
        self.status.pack(fill="x")

        box = tk.Frame(self, bg="#121212")
        box.pack(fill="x", padx=14, pady=8)
        self.l_proc = self._row(box, "Spoty app")
        self.l_media = self._row(box, "Windows now playing")
        self.l_titles = self._row(box, "Window titles")
        self.l_count = self._row(box, "Ads muted")
        self.l_count.config(text="0")

        btns = tk.Frame(self, bg="#121212")
        btns.pack(pady=8)
        self.btn = tk.Button(btns, text="Stop", width=12, command=self.toggle)
        self.btn.pack(side="left", padx=4)
        tk.Button(btns, text="Test mute (3s)", width=14,
                  command=lambda: setattr(self.worker, "test_until", time.time() + 3)).pack(side="left", padx=4)
        tk.Button(btns, text="Download log", width=14, command=self.save_log).pack(side="left", padx=4)

        tk.Label(self, text="(c) 2026 amthruster-dev. All rights reserved.", fg="#777777",
                 bg="#121212", font=("Segoe UI", 8)).pack(side="bottom", pady=(0, 4))
        link = tk.Label(self, text="Disclaimer & terms of use", fg="#6ea8fe", bg="#121212",
                        font=("Segoe UI", 9, "underline"), cursor="hand2")
        link.pack(side="bottom")
        link.bind("<Button-1>", lambda e: self.show_terms())
        self.logbox = scrolledtext.ScrolledText(self, height=10, bg="#1e1e1e", fg="#dddddd",
                                                font=("Consolas", 9), state="disabled")
        self.logbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.worker.start()
        self.after(250, self.poll)

    def _row(self, parent, name):
        f = tk.Frame(parent, bg="#121212")
        f.pack(fill="x", pady=1)
        tk.Label(f, text=name + ":", width=20, anchor="w", fg="#999999", bg="#121212").pack(side="left")
        v = tk.Label(f, text="-", anchor="w", justify="left", wraplength=250, fg="white", bg="#121212")
        v.pack(side="left")
        return v

    def show_terms(self):
        win = tk.Toplevel(self)
        win.title("Disclaimer & terms of use")
        win.configure(bg="#121212")
        win.geometry("440x400")
        tk.Label(win, text=TERMS, justify="left", wraplength=410, fg="#dddddd", bg="#121212",
                 font=("Segoe UI", 9)).pack(padx=14, pady=14, anchor="w")
        tk.Button(win, text="Close", width=12, command=win.destroy).pack(pady=(0, 12))

    def toggle(self):
        self.worker.enabled = not self.worker.enabled
        self.btn.config(text="Stop" if self.worker.enabled else "Start")

    def save_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="spoty_muter_log.txt",
            filetypes=[("Text file", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.records) + "\n")
            self.log(f"Log saved: {path}")

    def log(self, msg):
        self.records.append(time.strftime("%Y-%m-%d %H:%M:%S  EVENT  ") + msg)
        self.logbox.config(state="normal")
        self.logbox.insert("end", time.strftime("%H:%M:%S  ") + msg + "\n")
        self.logbox.see("end")
        self.logbox.config(state="disabled")

    def poll(self):
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == "state":
                    self.status.config(text=self.TEXT[m[1]], bg=self.COLORS[m[1]])
                elif m[0] == "info":
                    _, running, media, wt = m
                    snap = (running, media, tuple(wt))
                    if snap != self.last_info:
                        self.last_info = snap
                        self.records.append(
                            time.strftime("%Y-%m-%d %H:%M:%S  DATA   ")
                            + f"spoty_running={running} | windows_media={media!r} | window_titles={wt}")
                    self.l_proc.config(text="Found" if running else "NOT running",
                                       fg="#1db954" if running else "#e22134")
                    self.l_media.config(text=media.replace("|", "  |  "))
                    self.l_titles.config(text=" | ".join(wt) if wt else "none")
                elif m[0] == "log":
                    self.log(m[1])
                elif m[0] == "ad":
                    self.ads += 1
                    self.l_count.config(text=str(self.ads))
        except queue.Empty:
            pass
        self.after(250, self.poll)


if __name__ == "__main__":
    App().mainloop()

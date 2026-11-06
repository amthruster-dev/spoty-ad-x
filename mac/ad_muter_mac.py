"""
Copyright (c) 2026 amthruster-dev. All rights reserved.

Spoty Ad X (macOS) - no login needed.
Reads Spoty's state through its AppleScript interface and mutes only Spoty during ads.
"""
import queue
import subprocess
import threading
import time
import tkinter as tk
import traceback
from tkinter import filedialog, scrolledtext

TERMS = (
    'Use this app at your own risk. It is provided "as is", without warranty of any kind. The developer (amthruster-dev) is not responsible or liable for any damages, losses, or legal issues arising from downloading, installing, or using this app, including problems with your Spotify account or its terms of service, damage to your device, or audio that is muted or not muted by mistake.'
    "\n\n"
    "This app is not affiliated with, endorsed by, or sponsored by Spotify. It only reads what the Spotify app already reports on your Mac (the current track). It does not block or skip ads and does not access your Spotify account. During an ad it sets Spotify's own volume to 0 and restores it afterward. Using it may go against the terms of the services you use, and you are responsible for following the laws and terms that apply to you."
    "\n\n"
    "By installing or using this app you accept these terms."
)

SCRIPT = '''
if application "Spotify" is running then
  tell application "Spotify"
    try
      set st to player state as string
      set u to spotify url of current track
      set n to name of current track
      set a to artist of current track
      set v to sound volume
      return "RUN|" & st & "|" & u & "|" & n & "|" & a & "|" & v
    on error
      return "RUN|none|||| " & (sound volume)
    end try
  end tell
else
  return "OFF"
end if
'''


def osa(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=8)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "osascript failed")
    return r.stdout.strip()


def read_state():
    out = osa(SCRIPT)
    if out == "OFF":
        return {"running": False}
    p = out.split("|")
    p += [""] * (6 - len(p))
    try:
        vol = int(p[5].strip())
    except ValueError:
        vol = 50
    return {"running": True, "state": p[1], "url": p[2], "name": p[3], "artist": p[4], "vol": vol}


def set_volume(v):
    osa(f'tell application "Spotify" to set sound volume to {int(v)}')


def is_ad(s):
    if not s.get("running") or s.get("state") != "playing":
        return False
    return (s["url"].startswith("spotify:ad:") or s["name"].strip().lower() == "advertisement"
            or s["artist"].strip().lower() == "spotify" and not s["url"].startswith("spotify:track:"))


class Worker(threading.Thread):
    def __init__(self, q):
        super().__init__(daemon=True)
        self.q = q
        self.enabled = True
        self.muted = False
        self.saved = 50
        self.test_until = 0

    def run(self):
        while True:
            try:
                s = read_state()
                self.q.put(("info", s))
                test = time.time() < self.test_until
                want = s.get("running") and (test or (self.enabled and is_ad(s)))
                if want and not self.muted:
                    self.saved = s["vol"] if s["vol"] > 0 else self.saved
                    set_volume(0)
                    self.muted = True
                    self.q.put(("log", "TEST: muted for 3 seconds" if test else "AD detected - muted"))
                    if not test:
                        self.q.put(("ad",))
                elif self.muted and not want:
                    if s.get("running"):
                        set_volume(self.saved)
                    self.muted = False
                    self.q.put(("log", "Music - unmuted"))
                elif self.muted and s.get("running") and s["vol"] != 0:
                    set_volume(0)  # Spotify re-raised volume mid-ad
                if not self.enabled:
                    self.q.put(("state", "paused"))
                elif not s.get("running"):
                    self.q.put(("state", "idle"))
                else:
                    self.q.put(("state", "ad" if self.muted else "music"))
            except Exception:
                self.q.put(("log", traceback.format_exc()))
                time.sleep(1)
            time.sleep(0.4)


class App(tk.Tk):
    COLORS = {"music": "#1db954", "ad": "#e22134", "idle": "#777777", "paused": "#777777"}
    TEXT = {"music": "Playing music", "ad": "AD - MUTED", "idle": "Spoty not running",
            "paused": "Stopped"}

    def __init__(self):
        super().__init__()
        self.title("Spoty Ad X")
        self.geometry("460x520")
        self.configure(bg="#121212")
        self.ads = 0
        self.records = []
        self.last_info = None
        self.q = queue.Queue()
        self.worker = Worker(self.q)

        self.status = tk.Label(self, text="Starting...", font=("Helvetica", 20, "bold"),
                               fg="white", bg="#777777", pady=14)
        self.status.pack(fill="x")

        box = tk.Frame(self, bg="#121212")
        box.pack(fill="x", padx=14, pady=8)
        self.l_proc = self._row(box, "Spoty app")
        self.l_media = self._row(box, "Now playing")
        self.l_count = self._row(box, "Ads muted")
        self.l_count.config(text="0")

        btns = tk.Frame(self, bg="#121212")
        btns.pack(pady=8)
        self.btn = tk.Button(btns, text="Stop", width=10, command=self.toggle)
        self.btn.pack(side="left", padx=4)
        tk.Button(btns, text="Test mute (3s)", width=13,
                  command=lambda: setattr(self.worker, "test_until", time.time() + 3)).pack(side="left", padx=4)
        tk.Button(btns, text="Download log", width=12, command=self.save_log).pack(side="left", padx=4)

        tk.Label(self, text="(c) 2026 amthruster-dev. All rights reserved.", fg="#777777",
                 bg="#121212", font=("Helvetica", 9)).pack(side="bottom", pady=(0, 4))
        link = tk.Label(self, text="Disclaimer & terms of use", fg="#6ea8fe", bg="#121212",
                        font=("Helvetica", 10, "underline"), cursor="pointinghand")
        link.pack(side="bottom")
        link.bind("<Button-1>", lambda e: self.show_terms())
        self.logbox = scrolledtext.ScrolledText(self, height=10, bg="#1e1e1e", fg="#dddddd",
                                                font=("Menlo", 10), state="disabled")
        self.logbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.worker.start()
        self.after(250, self.poll)

    def on_close(self):
        try:
            if self.worker.muted:
                set_volume(self.worker.saved)
        except Exception:
            pass
        self.destroy()

    def _row(self, parent, name):
        f = tk.Frame(parent, bg="#121212")
        f.pack(fill="x", pady=1)
        tk.Label(f, text=name + ":", width=14, anchor="w", fg="#999999", bg="#121212").pack(side="left")
        v = tk.Label(f, text="-", anchor="w", justify="left", wraplength=290, fg="white", bg="#121212")
        v.pack(side="left")
        return v

    def show_terms(self):
        win = tk.Toplevel(self)
        win.title("Disclaimer & terms of use")
        win.configure(bg="#121212")
        win.geometry("440x420")
        tk.Label(win, text=TERMS, justify="left", wraplength=410, fg="#dddddd", bg="#121212",
                 font=("Helvetica", 11)).pack(padx=14, pady=14, anchor="w")
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
                    s = m[1]
                    if s != self.last_info:
                        self.last_info = s
                        self.records.append(time.strftime("%Y-%m-%d %H:%M:%S  DATA   ") + repr(s))
                    run = s.get("running")
                    self.l_proc.config(text="Found" if run else "NOT running",
                                       fg="#1db954" if run else "#e22134")
                    self.l_media.config(text=(f"{s['artist']} - {s['name']}" if s.get("name") else "-")
                                        + (f"  [{s['state']}]" if run else ""))
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

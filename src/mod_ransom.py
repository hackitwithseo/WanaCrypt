def f_old_wall():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
        v, _ = winreg.QueryValueEx(k, "Wallpaper")
        winreg.CloseKey(k)
        return v
    except Exception:
        return ""


def f_set_wall(path):
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
        return True
    except Exception:
        return False


def f_wall_image(path):
    from PIL import Image, ImageDraw, ImageFont
    u = ctypes.windll.user32
    w, h = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    im = Image.new("RGB", (w, h), (12, 12, 16))
    d = ImageDraw.Draw(im)
    try:
        big = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", int(h * 0.075))
        mid = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", int(h * 0.026))
        sml = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", int(h * 0.017))
    except Exception:
        big = mid = sml = ImageFont.load_default()
    red = (255, 40, 40)
    d.text((w // 2, int(h * 0.16)), "OOPS!", font=big, fill=red, anchor="mm")
    d.text((w // 2, int(h * 0.26)), "Your files have been encrypted!", font=mid, fill=(240, 240, 240), anchor="mm")
    box_w, box_h = int(w * 0.62), int(h * 0.42)
    x0, y0 = (w - box_w) // 2, int(h * 0.34)
    d.rectangle([x0, y0, x0 + box_w, y0 + box_h], outline=red, width=3)
    lines = [
        "What happened to my computer?",
        "Your important files are encrypted. Photos, documents, videos, databases,",
        "and other files are no longer accessible. A simulation only - nothing is",
        "actually encrypted, the popup is theatre.",
        "",
        "Can I recover my files?",
        "Sure. But you have limited time. If the timer runs out the price doubles.",
        "",
        "How do I pay?",
        "Send 300 USD worth of Bitcoin to the address in the window, then press",
        "the Decrypt button. The counter below is fake, the wallpaper is real.",
    ]
    y = y0 + int(h * 0.03)
    for ln in lines:
        d.text((x0 + int(w * 0.03), y), ln, font=sml, fill=(200, 200, 205))
        y += int(h * 0.032)
    d.text((w // 2, y0 + box_h - int(h * 0.04)),
           "BTC  13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94", font=mid, fill=(255, 210, 60), anchor="mm")
    im.save(path)


def f_ransom_on():
    G["ransom_on"] = True
    if not G.get("old_wall"):
        G["old_wall"] = f_old_wall()
    wall = os.path.join(f_appdir(), "wall.bmp")
    try:
        f_wall_image(wall)
        f_set_wall(wall)
    except Exception as e:
        f_log("run.log", "wallpaper: " + repr(e))
    try:
        ctypes.windll.user32.MessageBeep(0x30)
    except Exception:
        pass
    if not G.get("popup_open"):
        G["popup_open"] = True
        threading.Thread(target=f_popup, daemon=True).start()
    f_queue({"t": "ransom", "on": True})


def f_ransom_off():
    G["ransom_on"] = False
    G["popup_open"] = False
    old = G.get("old_wall") or ""
    if old and os.path.exists(old):
        f_set_wall(old)
    f_queue({"t": "ransom", "on": False})


def f_popup():
    import tkinter as tk
    try:
        root = tk.Tk()
    except Exception as e:
        G["popup_open"] = False
        f_log("run.log", "popup tk: " + repr(e))
        return
    root.title("Wana Decrypt0r 2.0")
    root.configure(bg="#0b0b0e")
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    head = tk.Frame(root, bg="#7b0f0f", height=64)
    head.pack(fill="x")
    tk.Label(head, text="  Wana Decrypt0r 2.0", bg="#7b0f0f", fg="#ffffff",
             font=("Segoe UI", 20, "bold")).pack(side="left", pady=12)
    tk.Label(head, text="Ooops, your files have been encrypted!  ",
             bg="#7b0f0f", fg="#ffd7d7", font=("Segoe UI", 12)).pack(side="right", pady=18)
    body = tk.Frame(root, bg="#0b0b0e")
    body.pack(fill="both", expand=True, padx=40, pady=18)
    txt = ("What Happened to My Computer?\n"
           "Your important files are encrypted. Many of your documents, photos, videos, databases and\n"
           "other files are no longer accessible because they have been encrypted.\n"
           "(Simulation: no real encryption. Files are fine.)\n\n"
           "Can I Recover My Files?\n"
           "Sure. We guarantee that you can recover all your files safely and easily.\n"
           "But you have not so enough time. You can decrypt some of your files for free.\n\n"
           "How Do I Pay?\n"
           "Send 300 USD worth of Bitcoin to:  13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94\n"
           "Then press Decrypt. Payment is not checked - it always succeeds.\n")
    tk.Label(body, text=txt, bg="#0b0b0e", fg="#d7d7dd", justify="left",
             font=("Consolas", 11)).pack(anchor="w")
    timer = tk.Label(body, text="", bg="#0b0b0e", fg="#ff4d4d", font=("Consolas", 15, "bold"))
    timer.pack(anchor="w", pady=10)
    counter = tk.Label(body, text="", bg="#0b0b0e", fg="#ffd24d", font=("Consolas", 11))
    counter.pack(anchor="w")
    bar = tk.Frame(body, bg="#1a1a20", height=22)
    bar.pack(fill="x", pady=14)
    fill = tk.Frame(bar, bg="#8a1010", width=0, height=22)
    fill.place(x=0, y=0)
    btnrow = tk.Frame(body, bg="#0b0b0e")
    btnrow.pack(anchor="w", pady=6)
    dead = datetime.now() + timedelta(days=CFG["ransom_days"])

    def tick():
        s = int((dead - datetime.now()).total_seconds())
        if s < 0:
            s = 0
        timer.config(text="Time left:  %dd %02dh %02dm %02ds" % (s // 86400, s % 86400 // 3600,
                                                                 s % 3600 // 60, s % 60))
        root.after(1000, tick)

    n = random.randint(300, 900)

    def cnt():
        nonlocal n
        n += random.randint(0, 9)
        counter.config(text="Files encrypted (simulated):  %d" % n)
        root.after(700, cnt)

    def decrypt():
        p = 0

        def step():
            nonlocal p
            p += random.randint(2, 7)
            if p >= 100:
                fill.config(width=bar.winfo_width())
                tk.Label(body, text="All your files have been decrypted (simulated).",
                         bg="#0b0b0e", fg="#4dff88", font=("Consolas", 12, "bold")).pack(anchor="w")
                return
            fill.config(width=int(bar.winfo_width() * p / 100))
            root.after(120, step)
        step()

    def close():
        G["popup_open"] = False
        root.destroy()

    tk.Button(btnrow, text="Decrypt", command=decrypt, bg="#8a1010", fg="white",
              font=("Segoe UI", 11, "bold"), padx=26, pady=6, relief="flat").pack(side="left", padx=(0, 10))
    tk.Button(btnrow, text="Close window", command=close, bg="#22222a", fg="#cccccc",
              font=("Segoe UI", 10), padx=18, pady=6, relief="flat").pack(side="left")
    tk.Label(root, text=" fake ransomware - wallpaper stays until you disable it ",
             bg="#0b0b0e", fg="#5b5b66", font=("Consolas", 9)).pack(side="bottom", pady=6)
    tick()
    cnt()
    root.protocol("WM_DELETE_WINDOW", close)
    root.mainloop()
    G["popup_open"] = False

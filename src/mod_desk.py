def f_monitor():
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)


def f_lock():
    ctypes.windll.user32.LockWorkStation()


def f_beep():
    ctypes.windll.kernel32.Beep(900, 400)


def f_volume(a):
    u = ctypes.windll.user32
    code = {"mute": 0xAD, "down": 0xAE, "up": 0xAF}.get(a, 0xAD)
    n = 1 if a == "mute" else 5
    for _ in range(n):
        u.keybd_event(code, 0, 0, 0)
        u.keybd_event(code, 0, 2, 0)
        time.sleep(0.03)


def f_speak(t):
    t = t.replace("'", "")
    subprocess.Popen(["powershell", "-NoProfile", "-Command",
                      "Add-Type -AssemblyName System.Speech;(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('" + t + "')"],
                     creationflags=0x08000000)


def f_open(a):
    try:
        os.startfile(a)
    except Exception:
        subprocess.Popen(["cmd", "/c", "start", "", a], creationflags=0x08000000)


def f_setclip(t):
    try:
        u = ctypes.windll.user32
        k = ctypes.windll.kernel32
        u.OpenClipboard(None)
        u.EmptyClipboard()
        buf = ctypes.create_unicode_buffer(t)
        h = k.GlobalAlloc(0x0042, ctypes.sizeof(buf))
        p = k.GlobalLock(h)
        ctypes.memmove(p, buf, ctypes.sizeof(buf))
        k.GlobalUnlock(h)
        u.SetClipboardData(13, h)
        u.CloseClipboard()
        return True
    except Exception:
        return False

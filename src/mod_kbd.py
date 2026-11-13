def f_kbd_on():
    G["kbd"] = True
    return "keyboard attached"


def f_kbd_off():
    G["kbd"] = False
    return "keyboard detached"


def f_kbdkey(vk):
    if not G.get("kbd"):
        return
    try:
        vk = int(vk)
    except Exception:
        return
    u = ctypes.windll.user32
    scan = u.MapVirtualKeyW(vk, 0)
    u.keybd_event(vk, scan, 0, 0)
    u.keybd_event(vk, scan, 2, 0)
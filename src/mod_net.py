def f_key():
    return bytes.fromhex(CFG["psk"])


def f_enc(data):
    nonce = os.urandom(12)
    c = AES.new(f_key(), AES.MODE_GCM, nonce=nonce)
    ct, tag = c.encrypt_and_digest(zlib.compress(data, 6))
    return struct.pack(">I", len(nonce) + len(ct) + 16) + nonce + ct + tag


def f_recvn(s, n):
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf


def f_close():
    with g_lock:
        s = g_conn.get("s")
        g_conn["s"] = None
    try:
        if s:
            s.close()
    except Exception:
        pass


def f_send(hdr, blob=b""):
    with g_lock:
        s = g_conn.get("s")
        if not s:
            return False
        try:
            s.sendall(f_enc(json.dumps(hdr).encode() + b"\n" + blob))
            return True
        except Exception as e:
            f_log("net.log", "send fail: " + repr(e))
            f_close()
            return False


def f_online():
    return g_conn.get("s") is not None


def f_read(s):
    ln = struct.unpack(">I", f_recvn(s, 4))[0]
    if ln > 80 * 1024 * 1024:
        raise ValueError("frame too big")
    d = f_recvn(s, ln)
    c = AES.new(f_key(), AES.MODE_GCM, nonce=d[:12])
    raw = zlib.decompress(c.decrypt_and_verify(d[12:-16], d[-16:]))
    h, _, blob = raw.partition(b"\n")
    return json.loads(h), blob


def f_flush():
    while True:
        try:
            hdr, blob = g_out.get_nowait()
        except queue.Empty:
            return
        if not f_send(hdr, blob):
            g_out.put((hdr, blob))
            return


def f_queue(hdr, blob=b""):
    if not f_send(hdr, blob):
        if g_out.qsize() < 3000:
            g_out.put((hdr, blob))


def f_net():
    while G.get("run"):
        try:
            f_log("net.log", "connecting " + str(CFG["host"]) + ":" + str(CFG["port"]))
            s = socket.create_connection((CFG["host"], int(CFG["port"])), timeout=12)
            s.settimeout(180)
            if CFG.get("tls"):
                s = ssl._create_unverified_context().wrap_socket(s)
            with g_lock:
                g_conn["s"] = s
            f_log("net.log", "connected")
            f_send({"t": "hello", **f_hello()})
            f_flush()
            while G.get("run"):
                hdr, blob = f_read(s)
                threading.Thread(target=f_dispatch, args=(hdr, blob), daemon=True).start()
        except Exception as e:
            f_log("net.log", "fail: " + repr(e))
        f_close()
        time.sleep(random.randint(*CFG["retry"]))


def f_beat():
    while G.get("run"):
        try:
            hb = f_hello()
            hb["t"] = "hb"
            f_send(hb)
        except Exception as e:
            f_log("net.log", "beat: " + repr(e))
        time.sleep(CFG["hb"])

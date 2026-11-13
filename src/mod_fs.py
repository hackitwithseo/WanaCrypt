def f_ls(p):
    p = p or os.environ.get("USERPROFILE", "C:\\")
    try:
        out = []
        for n in sorted(os.listdir(p))[:800]:
            f = os.path.join(p, n)
            try:
                if os.path.isdir(f):
                    out.append("<DIR>  " + n)
                else:
                    out.append(f"{os.path.getsize(f):>10}  {n}")
            except Exception:
                out.append("?????  " + n)
        return "\n".join(out) or "(empty)"
    except Exception as e:
        return str(e)


def f_hash(p):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for c in iter(lambda: fh.read(65536), b""):
                h.update(c)
        return h.hexdigest() + "  " + p
    except Exception as e:
        return str(e)


def f_find(name, root=None):
    root = root or os.environ.get("USERPROFILE", "C:\\")
    hits = []
    for r, d, fs in os.walk(root):
        for f in fs:
            if name.lower() in f.lower():
                hits.append(os.path.join(r, f))
                if len(hits) > 400:
                    return "\n".join(hits)
    return "\n".join(hits) or "(none)"


def f_zipdir(p):
    p = p or os.environ.get("USERPROFILE", "C:\\")
    tmp = os.path.join(tempfile.gettempdir(), "z" + str(int(time.time())))
    shutil.make_archive(tmp, "zip", p)
    data = open(tmp + ".zip", "rb").read()
    os.remove(tmp + ".zip")
    return data, os.path.basename(p.rstrip("\\")) + ".zip"

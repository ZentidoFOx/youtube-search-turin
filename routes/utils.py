import re

def _parse_views(text):
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None

def _pick_thumbs(thumbnails):
    if not thumbnails:
        return None, None, None
    try:
        thumbs = [t for t in thumbnails if isinstance(t, dict)]
        if not thumbs:
            return None, None, None
        thumbs = sorted(thumbs, key=lambda t: (t.get("width") or 0, t.get("height") or 0))
        if len(thumbs) == 1:
            u = thumbs[0].get("url")
            if isinstance(u, str):
                m = re.search(r"/vi/([^/]+)/", u)
                vid = m.group(1) if m else None
                if vid and ("hq720" in u or "sddefault" in u or "maxresdefault" in u):
                    base = f"https://i.ytimg.com/vi/{vid}"
                    d = f"{base}/default.jpg"
                    m2 = f"{base}/mqdefault.jpg"
                    h = f"{base}/hqdefault.jpg"
                    return d, m2, h
                d = u.replace("/hqdefault", "/default").replace("/mqdefault", "/default")
                m = u.replace("/hqdefault", "/mqdefault").replace("/default", "/mqdefault")
                h = u.replace("/mqdefault", "/hqdefault").replace("/default", "/hqdefault")
                return d, m, h
            return None, None, None
        low = thumbs[0].get("url")
        mid = thumbs[len(thumbs)//2].get("url")
        high = thumbs[-1].get("url")
        return (low if isinstance(low, str) else None), (mid if isinstance(mid, str) else None), (high if isinstance(high, str) else None)
    except Exception:
        return None, None, None

def _duration_text(info):
    def fmt(secs):
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    if not isinstance(info, dict):
        return None

    d = info.get("duration")
    if isinstance(d, str) and d.strip():
        return d.strip()
    if isinstance(d, dict):
        txt = d.get("text")
        if isinstance(txt, str) and txt.strip():
            return txt.strip()
        st = d.get("secondsText")
        if st is not None:
            try:
                secs = int(str(st).strip())
                return fmt(secs)
            except Exception:
                pass

    ls = info.get("lengthSeconds")
    if ls is not None:
        try:
            secs = int(ls)
            return fmt(secs)
        except Exception:
            pass

    acc = info.get("accessibility")
    if isinstance(acc, dict):
        acc_dur = acc.get("duration")
        if isinstance(acc_dur, str):
            m = re.search(r"(?:(\d+)\s*hours?)?.*?(?:(\d+)\s*minutes?)?.*?(?:(\d+)\s*seconds?)?", acc_dur, re.IGNORECASE)
            if m:
                h = int(m.group(1) or 0)
                mi = int(m.group(2) or 0)
                s = int(m.group(3) or 0)
                secs = h*3600 + mi*60 + s
                if secs > 0:
                    return fmt(secs)

    ds = info.get("durationSeconds")
    if ds is not None:
        try:
            secs = int(ds)
            return fmt(secs)
        except Exception:
            pass

    return None

def _duration_seconds(info):
    if not isinstance(info, dict):
        return None
    d = info.get("duration")
    if isinstance(d, dict):
        st = d.get("secondsText")
        if st is not None:
            try:
                return int(str(st).strip())
            except Exception:
                pass
    ls = info.get("lengthSeconds")
    if ls is not None:
        try:
            return int(ls)
        except Exception:
            pass
    ds = info.get("durationSeconds")
    if ds is not None:
        try:
            return int(ds)
        except Exception:
            pass
    txt = _duration_text(info)
    if isinstance(txt, str) and txt:
        parts = txt.split(":")
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            pass
    return None

def _estimate_mp3_sizes(seconds, bitrates=(192, 256, 320)):
    if seconds is None:
        return None
    res = {}
    for br in bitrates:
        try:
            mb = (seconds * br * 1000 / 8) / (1024 * 1024)
            res[str(br)] = round(mb, 2)
        except Exception:
            res[str(br)] = None
    return res

def _view_count_from_info(info):
    v = info.get("viewCount") if isinstance(info, dict) else None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        digits = "".join(ch for ch in v if ch.isdigit())
        return int(digits) if digits else None
    if isinstance(v, dict):
        text = v.get("text")
        if isinstance(text, str):
            digits = "".join(ch for ch in text if ch.isdigit())
            return int(digits) if digits else None
    return None

def _sanitize_filename(name: str):
    if not isinstance(name, str) or not name.strip():
        return "untitled"
    s = name.strip()
    s = re.sub(r"[\\/:*?\"<>|]", "_", s)
    s = re.sub(r"\s+", " ", s)
    return s[:180]

def _format_entry(f, video_id):
    size = f.get("filesize") or f.get("filesize_approx")
    typ = "audio" if (f.get("vcodec") in (None, "none")) else "video"
    return {
        "id": f.get("format_id"),
        "ext": f.get("ext"),
        "type": typ,
        "height": f.get("height"),
        "width": f.get("width"),
        "fps": f.get("fps"),
        "vcodec": f.get("vcodec"),
        "acodec": f.get("acodec"),
        "abr": f.get("abr"),
        "tbr": f.get("tbr"),
        "size": size,
        "note": f.get("format_note"),
        "downloadUrl": f"/download?id={video_id}&format={f.get('format_id')}"
    }

def _format_entry_direct(f):
    size = f.get("filesize") or f.get("filesize_approx")
    return {
        "id": f.get("format_id"),
        "ext": f.get("ext"),
        "height": f.get("height"),
        "width": f.get("width"),
        "fps": f.get("fps"),
        "vcodec": f.get("vcodec"),
        "acodec": f.get("acodec"),
        "abr": f.get("abr"),
        "tbr": f.get("tbr"),
        "size": size,
        "note": f.get("format_note"),
        "directUrl": f.get("url")
    }
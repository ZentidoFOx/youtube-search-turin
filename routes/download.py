import os
from flask import Blueprint, request, jsonify, send_from_directory
import yt_dlp
from .utils import _sanitize_filename, _format_entry, _format_entry_direct

bp = Blueprint("download", __name__)

@bp.get("/download")
def download_video():
    video_id = request.args.get("id", type=str)
    fmt_id = request.args.get("format", type=str)
    formt = request.args.get("formt", type=str)
    client = request.args.get("client", type=str)
    browser = request.args.get("browser", type=str)
    profile = request.args.get("profile", type=str)
    ffmpeg_loc = request.args.get("ffmpeg", type=str)
    mp4_flag = request.args.get("mp4", type=str)
    if not video_id:
        return jsonify({"error": "missing id"}), 400
    url = f"https://www.youtube.com/watch?v={video_id}"
    if (fmt_id and fmt_id.lower() == "mp3") or (formt and formt.lower() == "mp3"):
        base = request.host_url.rstrip("/")
        options = [
            {"quality": 192, "url": f"{base}/download/mp3?id={video_id}&quality=192"},
            {"quality": 256, "url": f"{base}/download/mp3?id={video_id}&quality=256"},
            {"quality": 320, "url": f"{base}/download/mp3?id={video_id}&quality=320"},
        ]
        return jsonify({"id": video_id, "mp3": options})
    if (fmt_id and fmt_id.lower() == "mp4") or (formt and formt.lower() == "mp4"):
        try:
            base_opts = {"quiet": True, "noplaylist": True, "retries": 3, "geo_bypass": True, "http_headers": {"User-Agent": "Mozilla/5.0"}}
            if client:
                base_opts["extractor_args"] = {"youtube": {"player_client": [client]}}
            if browser:
                base_opts["cookiesfrombrowser"] = browser if not profile else (browser, profile)
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            return jsonify({"error": str(e), "id": video_id}), 502
        formats = info.get("formats", [])
        mp4s = [f for f in formats if (f.get("ext") == "mp4" and f.get("format_id") and f.get("vcodec") not in (None, "none") and f.get("acodec") not in (None, "none") and f.get("url") and f.get("height"))]
        mp4s.sort(key=lambda f: f.get("height") or 0)
        picks = []
        if mp4s:
            picks.append(mp4s[0])
            picks.append(mp4s[len(mp4s)//2])
            picks.append(mp4s[-1])
        seen = set()
        options = []
        for f in picks:
            fid = f.get("format_id")
            if fid in seen:
                continue
            seen.add(fid)
            options.append({
                "quality": f"{f.get('height')}p",
                "url": f.get("url"),
                "downloadUrl": f"/download?id={video_id}&format={fid}&mp4=1"
            })
        return jsonify({
            "id": video_id,
            "title": info.get("title"),
            "mp4": options
        })
    if not fmt_id:
        try:
            base_opts = {"quiet": True, "noplaylist": True, "retries": 3, "geo_bypass": True, "http_headers": {"User-Agent": "Mozilla/5.0"}}
            if client:
                base_opts["extractor_args"] = {"youtube": {"player_client": [client]}}
            if browser:
                base_opts["cookiesfrombrowser"] = browser if not profile else (browser, profile)
            with yt_dlp.YoutubeDL(base_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            return jsonify({"error": str(e), "id": video_id}), 502
        formats = info.get("formats", [])
        items = [_format_entry(f, video_id) for f in formats if f.get("format_id")]
        return jsonify({
            "id": video_id,
            "title": info.get("title"),
            "formats": items,
            "bestDownloadUrl": f"/download?id={video_id}&format=best"
        })
    os.makedirs("downloads", exist_ok=True)
    outtmpl = os.path.join("downloads", "%(id)s-%(format_id)s.%(ext)s")
    fmt_expr = fmt_id
    if fmt_id == "best":
        fmt_expr = "bestvideo*+bestaudio/best"
    if fmt_id == "best_mp4":
        fmt_expr = "bestvideo*+bestaudio/best[ext=mp4]/best[ext=mp4]/best"
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": fmt_expr,
        "noplaylist": True,
        "quiet": True,
        "retries": 3,
        "geo_bypass": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }
    if not mp4_flag:
        ydl_opts["prefer_ffmpeg"] = True
        ydl_opts["merge_output_format"] = "mp4"
    if client:
        ydl_opts["extractor_args"] = {"youtube": {"player_client": [client]}}
    if browser:
        ydl_opts["cookiesfrombrowser"] = browser if not profile else (browser, profile)
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
    except Exception as e:
        if not client:
            try:
                ydl_opts["extractor_args"] = {"youtube": {"player_client": ["android"]}}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filepath = ydl.prepare_filename(info)
            except Exception as e2:
                return jsonify({"error": f"{str(e)} | {str(e2)}", "id": video_id, "format": fmt_id}), 502
    filename = os.path.basename(filepath)
    return jsonify({
        "id": video_id,
        "format": fmt_id,
        "file": filename,
        "downloadUrl": f"/files/{filename}",
        "title": info.get("title")
    })

@bp.get("/files/<path:filename>")
def serve_file(filename: str):
    return send_from_directory("downloads", filename, as_attachment=True)

@bp.get("/download/mp3")
def download_mp3():
    video_id = request.args.get("id", type=str)
    quality = request.args.get("quality", default=192, type=int)
    client = request.args.get("client", type=str)
    browser = request.args.get("browser", type=str)
    profile = request.args.get("profile", type=str)
    ffmpeg_loc = request.args.get("ffmpeg", type=str)
    if not video_id:
        return jsonify({"error": "missing id"}), 400
    url = f"https://www.youtube.com/watch?v={video_id}"
    os.makedirs("downloads", exist_ok=True)
    outtmpl = os.path.join("downloads", "%(title)s.%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "retries": 3,
        "geo_bypass": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
        "restrictfilenames": True,
        "windowsfilenames": True,
        "force_overwrites": True,
        "prefer_ffmpeg": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": str(quality),
        }],
    }
    if client:
        ydl_opts["extractor_args"] = {"youtube": {"player_client": [client]}}
    if browser:
        ydl_opts["cookiesfrombrowser"] = browser if not profile else (browser, profile)
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            safe_title = _sanitize_filename(info.get("title") or video_id)
            filepath = os.path.join("downloads", f"{safe_title}.mp3")
    except Exception as e:
        try:
            ydl_opts["extractor_args"] = {"youtube": {"player_client": ["android"]}}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                base = ydl.prepare_filename(info)
                filepath = os.path.splitext(base)[0] + ".mp3"
        except Exception as e2:
            return jsonify({"error": f"{str(e)} | {str(e2)}", "id": video_id}), 502
    filename = os.path.basename(filepath)
    return jsonify({
        "id": video_id,
        "file": filename,
        "downloadUrl": f"/files/{filename}",
        "title": info.get("title"),
        "quality": quality
    })
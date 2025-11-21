import os
import yt_dlp
from flask import Blueprint, request, jsonify
from .utils import _pick_thumbs, _duration_text, _view_count_from_info, _duration_seconds, _estimate_mp3_sizes

bp = Blueprint("info", __name__)

 

@bp.get("/info")
def video_info_query():
    video_id = request.args.get("id", type=str)
    if not video_id:
        return jsonify({"error": "missing id"}), 400
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    info = None
    errs = []
    
    # Use yt-dlp to extract video information
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        errs.append(f"yt-dlp failed: {str(e)}")
        return jsonify({"error": " | ".join(errs) or "failed to fetch video info", "id": video_id}), 502
    
    if info is None:
        return jsonify({"error": "failed to extract video info", "id": video_id}), 502
    # Extract thumbnails
    thumbs_src = info.get("thumbnails") or []
    td, tm, th = _pick_thumbs(thumbs_src)
    
    # Extract duration in seconds
    duration_secs = info.get("duration")
    if not isinstance(duration_secs, int):
        duration_secs = None
    
    # Format duration as string (HH:MM:SS or MM:SS)
    duration_str = None
    if duration_secs:
        h = duration_secs // 3600
        m = (duration_secs % 3600) // 60
        s = duration_secs % 60
        duration_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    
    # Safely extract values
    title = info.get("title")
    if not isinstance(title, str):
        title = None
    
    description = info.get("description")
    if not isinstance(description, str):
        description = None
    
    upload_date = info.get("upload_date")
    if upload_date and isinstance(upload_date, str):
        # Convert YYYYMMDD to ISO format
        if len(upload_date) == 8:
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    else:
        upload_date = None
    
    view_count = info.get("view_count")
    if not isinstance(view_count, int):
        view_count = None
    
    category = info.get("categories")
    if isinstance(category, list) and category:
        category = category[0]
    elif not isinstance(category, str):
        category = None
    
    result = {
        "id": video_id,
        "title": title,
        "description": description,
        "duration": duration_str,
        "thumbDefault": td,
        "thumbMedium": tm,
        "thumbHigh": th,
        "uploadDate": upload_date,
        "viewCount": view_count,
        "category": category,
        "estimatedMp3SizeMB": _estimate_mp3_sizes(duration_secs)
    }
    return jsonify(result)
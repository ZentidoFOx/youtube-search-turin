import os
from flask import Blueprint, request, jsonify
from youtubesearchpython import Video, ResultMode
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
    
    # First try: Video.get() with get_upload_date=True (gets both info & formats, includes uploadDate)
    try:
        info = Video.get(url, mode=ResultMode.json, get_upload_date=True)
    except Exception as e:
        errs.append(f"Video.get failed: {str(e)}")
    
    # Second try: Video.getInfo() (gets only info, uses HTML parsing for better data)
    if info is None:
        try:
            info = Video.getInfo(url, mode=ResultMode.json)
        except Exception as e2:
            errs.append(f"Video.getInfo failed: {str(e2)}")
    
    # If both methods failed, return error
    if info is None:
        return jsonify({"error": " | ".join(errs) or "failed to fetch video info", "id": video_id}), 502
    thumbs_src = info.get("thumbnails") or info.get("videoThumbnails") or []
    td, tm, th = _pick_thumbs(thumbs_src)
    secs = _duration_seconds(info)
    
    # Extract category - try multiple possible fields
    category = info.get("category")
    if not category:
        category = info.get("microformat", {}).get("videoDetails", {}).get("category")
    if not category:
        category = info.get("videoDetails", {}).get("category")
    
    # Safely extract values, ensuring no None concatenation
    title = info.get("title")
    if not isinstance(title, str):
        title = None
    
    description = info.get("description") or info.get("shortDescription")
    if not isinstance(description, str):
        description = None
    
    duration = _duration_text(info)
    if not isinstance(duration, str):
        duration = None
    
    upload_date = info.get("uploadDate") or info.get("publishDate") or info.get("publishedTime") or info.get("dateText")
    if not isinstance(upload_date, str):
        upload_date = None
    
    result = {
        "id": video_id,
        "title": title,
        "description": description,
        "duration": duration,
        "thumbDefault": td,
        "thumbMedium": tm,
        "thumbHigh": th,
        "uploadDate": upload_date,
        "viewCount": _view_count_from_info(info),
        "category": category,
        "estimatedMp3SizeMB": _estimate_mp3_sizes(secs)
    }
    return jsonify(result)
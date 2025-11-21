import os
from flask import Blueprint, request, jsonify
from youtubesearchpython import VideosSearch, Video, ResultMode
from .utils import _pick_thumbs, _duration_text, _view_count_from_info, _parse_views, _duration_seconds, _estimate_mp3_sizes

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
    if info is None:
        try:
            data = VideosSearch(video_id, limit=1).result()
            item = None
            if isinstance(data, dict):
                items = data.get("result") or []
                if isinstance(items, list) and items:
                    item = items[0]
            if item:
                thumbs_src = item.get("thumbnails") or []
                td, tm, th = _pick_thumbs(thumbs_src)
                secs = _duration_seconds(item)
                
                # Extract description from descriptionSnippet
                description = None
                ds = item.get("descriptionSnippet")
                if isinstance(ds, list) and ds:
                    try:
                        description = " ".join(s.get("text") for s in ds if isinstance(s, dict) and s.get("text"))
                    except Exception:
                        pass
                
                # Extract uploadDate from publishedTime
                upload_date = item.get("publishedTime")
                
                result = {
                    "id": video_id,
                    "title": item.get("title"),
                    "description": description,
                    "duration": _duration_text(item),
                    "thumbDefault": td,
                    "thumbMedium": tm,
                    "thumbHigh": th,
                    "uploadDate": upload_date,
                    "viewCount": _parse_views((item.get("viewCount") or {}).get("text")),
                    "category": None,
                    "estimatedMp3SizeMB": _estimate_mp3_sizes(secs)
                }
                return jsonify(result)
        except Exception as e3:
            errs.append(str(e3))
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
    
    result = {
        "id": video_id,
        "title": info.get("title"),
        "description": info.get("description") or info.get("shortDescription"),
        "duration": _duration_text(info),
        "thumbDefault": td,
        "thumbMedium": tm,
        "thumbHigh": th,
        "uploadDate": info.get("uploadDate") or info.get("publishDate") or info.get("publishedTime") or info.get("dateText"),
        "viewCount": _view_count_from_info(info),
        "category": category,
        "estimatedMp3SizeMB": _estimate_mp3_sizes(secs)
    }
    if result["description"] is None or result["category"] is None or result["uploadDate"] is None or (result["thumbDefault"] is None and result["thumbMedium"] is None and result["thumbHigh"] is None):
        try:
            data = VideosSearch(video_id, limit=1).result()
            item = None
            if isinstance(data, dict):
                items = data.get("result") or []
                if isinstance(items, list) and items:
                    item = items[0]
            if item:
                if result["description"] is None:
                    ds = item.get("descriptionSnippet")
                    if isinstance(ds, list) and ds:
                        try:
                            result["description"] = " ".join(s.get("text") for s in ds if isinstance(s, dict) and s.get("text"))
                        except Exception:
                            pass
                if result["uploadDate"] is None:
                    pt = item.get("publishedTime")
                    if isinstance(pt, str) and pt:
                        result["uploadDate"] = pt
                if result["thumbDefault"] is None and result["thumbMedium"] is None and result["thumbHigh"] is None:
                    tsrc = item.get("thumbnails") or []
                    td2, tm2, th2 = _pick_thumbs(tsrc)
                    result["thumbDefault"] = td2
                    result["thumbMedium"] = tm2
                    result["thumbHigh"] = th2
        except Exception:
            pass
    return jsonify(result)
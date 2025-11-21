import os
from flask import Blueprint, request, jsonify
from youtubesearchpython import VideosSearch, Video, ResultMode
from .utils import _pick_thumbs, _duration_text, _view_count_from_info, _parse_views, _duration_seconds, _estimate_mp3_sizes

bp = Blueprint("info", __name__)

@bp.get("/search/videos")
def search_videos():
    q = request.args.get("q", type=str)
    limit = request.args.get("limit", default=5, type=int)
    if not q:
        return jsonify({"error": "missing q"}), 400
    try:
        last_err = None
        for lim in [limit, 10, 5]:
            try:
                search = VideosSearch(q, limit=lim)
                data = search.result()
                if not isinstance(data, dict):
                    last_err = "invalid search response"
                    continue
                items = data.get("result") or []
                if not isinstance(items, list) or not items:
                    last_err = "empty search result"
                    continue
                videos = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    thumb_default, thumb_medium, thumb_high = _pick_thumbs(item.get("thumbnails") or [])
                    vc = item.get("viewCount")
                    vc_text = vc.get("text") if isinstance(vc, dict) else (str(vc) if vc is not None else None)
                    videos.append({
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "thumbDefault": thumb_default,
                        "thumbMedium": thumb_medium,
                        "thumbHigh": thumb_high,
                        "channelTitle": (item.get("channel") or {}).get("name"),
                        "channelId": (item.get("channel") or {}).get("id"),
                        "publishedAt": item.get("publishedTime"),
                        "duration": item.get("duration"),
                        "viewCount": _parse_views(vc_text)
                    })
                return jsonify({"videos": videos})
            except Exception as e:
                last_err = str(e)
                continue
        return jsonify({"error": last_err or "search failed", "q": q, "limit": limit}), 502
    except Exception as e:
        return jsonify({"error": str(e), "q": q, "limit": limit}), 502

@bp.get("/info")
def video_info_query():
    video_id = request.args.get("id", type=str)
    if not video_id:
        return jsonify({"error": "missing id"}), 400
    url = f"https://www.youtube.com/watch?v={video_id}"
    info = None
    errs = []
    try:
        info = Video.getInfo(url, mode=ResultMode.json)
    except Exception as e:
        errs.append(str(e))
        try:
            info = Video.get(url, mode=ResultMode.json)
        except Exception as e2:
            errs.append(str(e2))
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
                result = {
                    "id": video_id,
                    "title": item.get("title"),
                    "description": None,
                    "duration": _duration_text(item),
                    "thumbDefault": td,
                    "thumbMedium": tm,
                    "thumbHigh": th,
                    "uploadDate": None,
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
    result = {
        "id": video_id,
        "title": info.get("title"),
        "description": info.get("description"),
        "duration": _duration_text(info),
        "thumbDefault": td,
        "thumbMedium": tm,
        "thumbHigh": th,
        "uploadDate": info.get("uploadDate") or info.get("publishDate"),
        "viewCount": _view_count_from_info(info),
        "category": info.get("category"),
        "estimatedMp3SizeMB": _estimate_mp3_sizes(secs)
    }
    return jsonify(result)
from flask import Blueprint, request, jsonify
from youtubesearchpython import VideosSearch
from .utils import _pick_thumbs, _parse_views

bp = Blueprint("search", __name__)

@bp.route("/search/videos", methods=["GET", "POST"])
def search_videos():
    q = request.args.get("q", type=str)
    if not q and request.is_json:
        q = (request.get_json(silent=True) or {}).get("q")
    if not q:
        q = request.form.get("q")
    limit = request.args.get("limit", default=5, type=int)
    if (limit is None) and request.is_json:
        lv = (request.get_json(silent=True) or {}).get("limit")
        try:
            limit = int(lv) if lv is not None else 5
        except Exception:
            limit = 5
    if limit is None:
        lv = request.form.get("limit")
        try:
            limit = int(lv) if lv is not None else 5
        except Exception:
            limit = 5
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
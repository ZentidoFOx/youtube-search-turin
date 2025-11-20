from flask import Flask, request, jsonify
import os
from youtubesearchpython import VideosSearch

app = Flask(__name__)

def _parse_views(text):
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None

def _pick_thumbs(thumbnails):
    if not thumbnails:
        return None, None, None
    thumbs = sorted(thumbnails, key=lambda t: t.get("width", 0))
    low = thumbs[0]
    mid = thumbs[len(thumbs)//2]
    high = thumbs[-1]
    return low.get("url"), mid.get("url"), high.get("url")

@app.get("/")
def root():
    return jsonify({"status": "ok"})

@app.get("/search/videos")
def search_videos():
    q = request.args.get("q", type=str)
    limit = request.args.get("limit", default=5, type=int)
    if not q:
        return jsonify({"error": "missing q"}), 400
    search = VideosSearch(q, limit=limit)
    data = search.result()
    items = data.get("result", [])
    videos = []
    for item in items:
        thumb_default, thumb_medium, thumb_high = _pick_thumbs(item.get("thumbnails") or [])
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
            "viewCount": _parse_views((item.get("viewCount") or {}).get("text"))
        })
    return jsonify({"videos": videos})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
from flask import Flask, jsonify
import os
from routes.info import bp as info_bp
from routes.ui import bp as ui_bp
from routes.search import bp as search_bp

app = Flask(__name__)

@app.get("/")
def root():
    return jsonify({"status": "ok"})

app.register_blueprint(info_bp)
app.register_blueprint(ui_bp)
app.register_blueprint(search_bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

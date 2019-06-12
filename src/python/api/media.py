from flask import Blueprint, send_file, jsonify, send_from_directory
from io import BytesIO

from ..shared import Config

api_media = Blueprint("media", __name__, url_prefix="/api/media")


@api_media.route("/<int:media_id>")
def r_media(media_id: int):
    db = Config.DB
    name, b = db.conn.execute("""
    SELECT name, data
    FROM media 
    WHERE id = ?
    """, (media_id,)).fetchone()

    return send_file(BytesIO(b), attachment_filename=name)


@api_media.route("/<path:p>")
def r_media_serve(p: str):
    return send_from_directory(Config.MEDIA_FOLDER, p)


@api_media.route("/", methods=["POST"])
def r_media_path():
    return jsonify({
        "path": str(Config.MEDIA_FOLDER)
    })

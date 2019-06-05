from flask import Blueprint, request, jsonify
from flask_socketio import send
from uuid import uuid4
import json

from ..shared import Config
from ..engine.anki import Anki

api_io = Blueprint("io", __name__, url_prefix="/api/io")
ws_io = Blueprint("ws_io", __name__, url_prefix="/api/io")

ANKI_FILENAME = dict()


@api_io.route("/anki/import", methods=["POST"])
def r_anki_import():
    f = request.files["apkg"]
    f_id = str(uuid4())
    ANKI_FILENAME[f_id] = f.filename
    f.save(str(Config.UPLOAD_FOLDER.joinpath(f"{f_id}.apkg")))

    return jsonify({
        "id": f_id
    })


def r_anki_progress(f_id):
    try:
        filename = ANKI_FILENAME[f_id]

        anki = Anki(str(Config.UPLOAD_FOLDER.joinpath(f"{f_id}.apkg")), filename,
                    lambda x: send(x))
        anki.export(Config.DB)
    except Exception as e:
        send({
            "error": str(e)
        })
        raise


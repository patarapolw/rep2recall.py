from flask import Blueprint, request, jsonify, send_file, g
from flask_socketio import send
from uuid import uuid4
from werkzeug.utils import secure_filename
from gevent import sleep

from ..shared import Config
from ..engine.anki import Anki
from ..engine.db import Db
from ..engine.search import mongo_filter

api_io = Blueprint("io", __name__, url_prefix="/api/io")

FILE_ID_TO_NAME = dict()


@api_io.route("/import", methods=["POST"])
def r_import():
    f = request.files["file"]
    f_id = str(uuid4())
    FILE_ID_TO_NAME[f_id] = f.filename
    f.save(str(Config.UPLOAD_FOLDER.joinpath(f_id)))

    return jsonify({
        "id": f_id
    })


def r_import_progress(msg):
    try:
        filename = FILE_ID_TO_NAME[msg["id"]]
        if msg["type"] == ".apkg":
            anki = Anki(str(Config.UPLOAD_FOLDER.joinpath(msg["id"])), filename,
                        lambda x: (send(x), sleep(1)))
            anki.export(Config.DB)
        elif msg["type"] == ".r2r":
            import_db = Db(str(Config.UPLOAD_FOLDER.joinpath(msg["id"])))
            Config.DB.insertMany(import_db.getAll())
        else:
            raise ValueError(f"Invalid file type {msg['type']}")

        send(dict())
    except Exception as e:
        send({
            "error": str(e)
        })
        raise


@api_io.route("/export")
def r_export():
    def _clean_deck(item):
        if request.args.get("reset"):
            item.pop("srsLevel")
            item.pop("nextReview")
            item.pop("stat")
            return item
        else:
            return item

    deck = request.args.get("deck")
    filename = str(Config.UPLOAD_FOLDER.joinpath(str(uuid4())))
    new_file = Db(str(Config.UPLOAD_FOLDER.joinpath(filename)))
    db = Config.DB

    new_file.insertMany(list(map(_clean_deck, filter(mongo_filter({"$or": [
        {"deck": deck},
        {"deck": {"$startswith": f"{deck}/"}}
    ]}), db.getAll()))))

    new_file.close()

    return send_file(filename, attachment_filename=f"{secure_filename(deck)}.r2r", as_attachment=True, cache_timeout=-1)

from flask import Blueprint, request, Response, jsonify
import sqlite3

from ..shared import Config
from ..engine.search import mongo_filter, sorter
from ..engine.util import anki_mustache

api_editor = Blueprint("editor", __name__, url_prefix="/api/editor")


@api_editor.route("/", methods=["POST", "PUT", "DELETE"])
def r_editor():
    r = request.json
    db = Config.DB

    if request.method == "POST":
        offset = r.get("offset", 0)
        all_data = sorted(filter(mongo_filter(r["q"]), db.get_all()),
                          key=sorter(r.get("sortBy", "deck"), r.get("desc", False)))
        return jsonify({
            "data": list(map(_editor_entry_post_process, all_data[offset: offset + r.get("limit", 10)])),
            "count": len(all_data)
        })

    elif request.method == "PUT":
        try:
            if r.get("create"):
                if isinstance(r["create"], list):
                    c_ids = db.insert_many(r["create"])
                    return jsonify({
                        "ids": c_ids
                    })
                else:
                    c_id = db.insert_many([r["create"]])[0]
                    return jsonify({
                        "id": c_id
                    })

            if r.get("update"):
                if r.get("ids"):
                    db.update_many(r["ids"], r["update"])
                else:
                    db.update(r["id"], r["update"])

            return jsonify({"error": None})
        except sqlite3.Error as e:
            return jsonify({"error": str(e)})

    elif request.method == "DELETE":
        if r.get("ids"):
            db.delete_many(r["ids"])
        else:
            db.delete(r["id"])

        return jsonify({"error": None})

    return Response(status=404)


@api_editor.route("/editTags", methods=["PUT"])
def r_editor_edit_tags():
    d = request.json
    Config.DB.edit_tags(d["ids"], d["tags"], d["isAdd"])

    return jsonify({"error": None})


def _editor_entry_post_process(c: dict) -> dict:
    if c["front"].startswith("@md5\n"):
        data = c.get("data", dict())
        c["front"] = anki_mustache(c["tFront"], data)
        c["back"] = anki_mustache(c["tBack"], data, c["tFront"])

    return c

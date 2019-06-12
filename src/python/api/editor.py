from flask import Blueprint, request, Response, jsonify

from ..shared import Config
from ..engine.search import mongo_filter, sorter, parse_query

api_editor = Blueprint("editor", __name__, url_prefix="/api/editor")


@api_editor.route("/", methods=["POST", "PUT", "DELETE"])
def r_editor():
    r = request.json
    db = Config.DB

    if request.method == "POST":
        if r.get("cond"):
            cond, sort_by, desc = r["cond"], None, None
        else:
            cond, sort_by, desc = parse_query(r["q"])

        if sort_by is None:
            sort_by = r.get("sortBy", "deck")

        if desc is None:
            desc = r.get("desc", False)

        offset = r.get("offset", 0)
        all_data = sorted(filter(mongo_filter(cond), db.get_all()),
                          key=sorter(sort_by, desc))
        return jsonify({
            "data": all_data[offset: offset + r.get("limit", 10)],
            "count": len(all_data)
        })

    elif request.method == "PUT":
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

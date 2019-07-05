from flask import Blueprint, request, Response, jsonify
from random import shuffle

from ..shared import Config
from ..engine.search import mongo_filter, sorter, SearchParser
from ..engine.util import ankiMustache

api_editor = Blueprint("editor", __name__, url_prefix="/api/editor")


@api_editor.route("/", methods=["POST", "PUT", "DELETE"])
def r_editor():
    r = request.json
    db = Config.DB

    if request.method == "POST":
        parser = SearchParser()

        cond = r.get("cond")
        if cond is None:
            cond = parser.parse(r["q"]).cond
        if cond is None:
            cond = dict()

        sort_by = parser.sort_by
        desc = parser.desc
        is_ = parser.is_

        if sort_by is None:
            sort_by = r.get("sortBy", "deck")

        if desc is None:
            desc = r.get("desc", False)

        if is_ == "duplicate":
            sort_by = "front"

            counter = dict()
            for data in db.getAll():
                if data.get("tFront"):
                    counter.setdefault(ankiMustache(data["tFront"], data.get("data", dict())), []).append(data)
                else:
                    counter.setdefault(data["front"], []).append(data)

            all_data = []
            for v in counter.values():
                if len(v) > 1:
                    all_data.extend(v)
        elif is_ == "distinct":
            distinct_set = set()
            all_data = []
            for data in db.getAll():
                key = data.get("key", data["front"])
                if key not in distinct_set:
                    all_data.append(data)
                    distinct_set.add(key)
        else:
            all_data = db.getAll()

        if is_ == "distinct":
            sort_by = "random"

        if sort_by == "random":
            all_data = list(filter(mongo_filter(cond), all_data))
            shuffle(all_data)
        else:
            all_data = sorted(filter(mongo_filter(cond), all_data),
                              key=sorter(sort_by, desc))

        offset = r.get("offset", 0)

        return jsonify({
            "data": all_data[offset: offset + r.get("limit", 10)],
            "count": len(all_data)
        })

    elif request.method == "PUT":
        if r.get("create"):
            if isinstance(r["create"], list):
                c_ids = db.insertMany(r["create"])
                return jsonify({
                    "ids": c_ids
                })
            else:
                c_id = db.insertMany([r["create"]])[0]
                return jsonify({
                    "id": c_id
                })

        if r.get("update"):
            if r.get("ids"):
                db.updateMany(r["ids"], r["update"])
            else:
                db.update(r["id"], r["update"])

        return jsonify({"error": None})

    elif request.method == "DELETE":
        if r.get("ids"):
            db.deleteMany(r["ids"])
        else:
            db.delete(r["id"])

        return jsonify({"error": None})

    return Response(status=404)


@api_editor.route("/addTags", methods=["PUT"])
def r_editor_add_tags():
    d = request.json
    Config.DB.addTags(d["ids"], d["tags"])

    return jsonify({"error": None})


@api_editor.route("/removeTags", methods=["DELETE"])
def r_editor_remove_tags():
    d = request.json
    Config.DB.removeTags(d["ids"], d["tags"])

    return jsonify({"error": None})

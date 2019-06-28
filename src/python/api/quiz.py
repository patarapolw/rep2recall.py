from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import List

from ..shared import Config
from ..engine.search import SearchParser, parse_timedelta
from ..engine.typing import ICondOptions, IParserResult

api_quiz = Blueprint("quiz", __name__, url_prefix="/api/quiz")


@api_quiz.route("/treeview", methods=["POST"])
def r_quiz_treeview():
    def _recurse_parse_data(_data: List[dict], _deck: List[str], _depth: int = 0):
        do_loop = True

        while _depth < len(_deck) - 1:
            for c in _data:
                if c["name"] == _deck[_depth]:
                    c["children"] = c.get("children", [])
                    _recurse_parse_data(c["children"], _deck, _depth + 1)
                    do_loop = False
                    break

            _depth += 1

            if not do_loop:
                break

        if do_loop and _depth == len(_deck) - 1:
            full_name = "/".join(deck)
            deck_items = [d for d in all_items if d["deck"].startswith(full_name)]

            _data.append({
                "name": _deck[_depth],
                "fullName": full_name,
                "isOpen": _depth < 2,
                "stat": {
                    "new": len([d for d in deck_items if not d.get("nextReview")]),
                    "leech": len([d for d in deck_items if d.get("srsLevel") == 0]),
                    "due": len([d for d in deck_items if d.get("nextReview") and
                                datetime.fromisoformat(d["nextReview"]) < now])
                }
            })

    db = Config.DB
    all_items = db.parseCond(SearchParser().parse(request.json["q"]), ICondOptions(
        fields=["deck", "nextReview", "srsLevel"]
    )).data
    now = datetime.now()

    deck_list = sorted(set(d["deck"] for d in all_items))
    deck_with_subdecks = []

    for d in deck_list:
        deck = d.split("/")
        for i, _ in enumerate(deck):
            subdeck = "/".join(deck[:i + 1])
            if subdeck not in deck_with_subdecks:
                deck_with_subdecks.append(subdeck)

    full_data = []
    for d in deck_with_subdecks:
        deck = d.split("/")
        _recurse_parse_data(full_data, deck)

    return jsonify(full_data)


@api_quiz.route("/", methods=["POST"])
def r_quiz_build():
    r = request.json
    and_cond = [SearchParser().parse(r["q"]).cond]

    if r.get("deck"):
        and_cond.append({"$or": [
            {"deck": {"$startswith": r["deck"] + "/"}},
            {"deck": r["deck"]}
        ]})

    if r.get("type") != "all":
        type_ = r.get("type")
        if type_ == "due":
            and_cond.append({"nextReview": {"$lte": str(datetime.now())}})
        elif type_ == "leech":
            and_cond.append({"srsLevel": 0})
        elif type_ == "new":
            and_cond.append({"nextReview": {"$exists": False}})
        else:
            and_cond.append({"$or": [
                {"nextReview": {"$exists": False}},
                {"nextReview": {"$lte": str(datetime.now())}}
            ]})

    if r.get("due"):
        and_cond.append({"nextReview": {"$lte": str(datetime.now() + parse_timedelta(r["due"]))}})
    elif r.get("type") != "all":
        and_cond.append({"$or": [
            {"nextReview": {"$exists": False}},
            {"nextReview": {"$lte": str(datetime.now())}}
        ]})

    db = Config.DB
    all_items = db.parseCond(IParserResult(cond={"$and": and_cond}), ICondOptions(fields=["id"])).data

    return jsonify({"ids": [c["id"] for c in all_items]})


@api_quiz.route("/render", methods=["POST"])
def r_quiz_render():
    db = Config.DB
    c = db.render(request.json["id"])

    return jsonify(c)


@api_quiz.route("/right", methods=["PUT"])
def r_quiz_right():
    card_id = request.json["id"]
    db = Config.DB
    db.markRight(card_id)

    return jsonify({"error": None})


@api_quiz.route("/wrong", methods=["PUT"])
def r_quiz_wrong():
    card_id = request.json["id"]
    db = Config.DB
    db.markWrong(card_id)

    return jsonify({"error": None})

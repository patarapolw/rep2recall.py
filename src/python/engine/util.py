import re
from typing import List


def anki_mustache(s: str, d: List[dict] = None, front: str = "") -> str:
    if d is None:
        d = []

    s = s.replace("{{FrontSide}}", front.replace("@html\n", ""))

    keys = set()
    for item in d:
        keys.add(item["key"])
        s = re.sub(r"{{(\S+:)?%s}}" % re.escape(item["key"]), re.sub("^@[^\n]+\n", "", item["value"], flags=re.MULTILINE), s)

    s = re.sub(r"{{#(\S+)}}(.*){{\1}}", lambda m: m[2] if m[1] in keys else "", s, flags=re.DOTALL)
    s = re.sub(r"{{[^}]+}}", "", s)

    return "@rendered\n" + s

import re


def anki_mustache(s: str, d: dict, front: str = "") -> str:
    s = s.replace("{{FrontSide}}", front.replace("@html\n", ""))

    for k, v in d.items():
        s = re.sub(r"{{(\S+:)?%s}}" % re.escape(k), re.sub("^@[^\n]+\n", "", v, flags=re.MULTILINE), s)

    s = re.sub(r"{{#(\S+)}}(.*){{\1}}", lambda m: m[2] if m[1] in d.keys() else "", s, flags=re.DOTALL)
    s = re.sub(r"{{[^}]+}}", "", s)

    return "@rendered\n" + s

from src.python.engine.util import anki_mustache


def test_anki_mustache():
    assert anki_mustache("{{Simplified}}", {
        "Simplified": "Hello"
    }) == "Hello"

from ..python.engine.search import mongo_filter, shlex_split


def test_mongo_filter():
    print(list(filter(mongo_filter({"tag": {"$startswith": "h"}}), [{"tag": ["hanzi"], "extra": "x"}, {"tag": "sth"}])))


def test_shlex_split():
    print(shlex_split("a>=b", {">="}, True))

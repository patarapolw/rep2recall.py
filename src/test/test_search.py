from ..python.engine.search import mongo_filter


def test_mongo_filter():
    print(list(filter(mongo_filter({"tag": {"$startswith": "h"}}), [{"tag": ["hanzi"], "extra": "x"}, {"tag": "sth"}])))

from ..python.engine.search import mongo_filter


def test_mongo_filter():
    print(list(filter(mongo_filter({"$and": []}), [{"x": "Hanzi"}])))

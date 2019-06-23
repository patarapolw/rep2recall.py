from ..python.engine.search import SearchParser


def test_search_empty():
    print(SearchParser().parse(""))


def test_search1():
    print(SearchParser().parse("is:leech OR is:due"))
    print(SearchParser().parse("is:leech is:due"))
    print(SearchParser().parse("is:leech OR (is:due is:random)"))

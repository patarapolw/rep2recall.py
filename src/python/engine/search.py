from typing import Set, List, Tuple
from datetime import datetime, timedelta
import re
from typing import Union, Callable, Any
import math
import functools

ANY_OF = {"template", "front", "mnemonic", "entry", "deck", "tag"}
IS_DATE = {"created", "modified", "nextReview"}
IS_STRING = {"template", "front", "back", "mnemonic", "deck", "tag", "entry"}


def parse_query(s: str) -> Tuple[dict, Any, Any]:
    sort_by = None
    desc = None

    s = remove_brackets(s)
    if " OR " in s:
        return {"$or": [parse_query(t)[0] for t in shlex_split(s, {" OR "})]}, None, None

    tokens = shlex_split(s, {" "})
    token_result = []

    for t in tokens:
        expr_str = t[1:] if t[0] == "-" else t
        expr = shlex_split(expr_str, {':', '>', '>=', '<', '<=', '=', '~'}, True)

        pre_result = None

        if len(expr) == 1:
            or_cond = []
            for a in ANY_OF:
                if a in IS_STRING:
                    or_cond.append({a: {"$regex": re.escape(expr[0])}})
                else:
                    or_cond.append({a: expr[0]})

            or_cond.append({"@*": {"$regex": re.escape(expr[0])}})

            pre_result = {"$or": or_cond}

        elif len(expr) == 3:
            k, o, v = expr

            if k == "sortBy":
                o = "="

            if k == "is":
                if v == "due":
                    k = "nextReview"
                    o = "<="
                    v = str(datetime.now())
                elif v == "leech":
                    k = "srsLevel"
                    o = "="
                    v = 0
                elif v == "new":
                    k = "nextReview"
                    v = "NULL"
                elif v == "marked":
                    k = "tag"
                    o = "="
                    v = "marked"
            elif k == "due":
                k = "nextReview"
                o = "<="

            if v == "NULL":
                pre_result = {"$or": [
                    {k: ""},
                    {k: {"$exists": False}}
                ]}
            else:
                if k in IS_DATE:
                    try:
                        v = str(datetime.now() + parse_timedelta(v))
                        if o == ":":
                            if k == "nextReview":
                                o = "<="
                            else:
                                o = ">="
                    except ValueError:
                        pass

                if o == ":":
                    if isinstance(v, str) or k in IS_STRING:
                        v = {"$regex": re.escape(str(v))}
                elif o == "~":
                    v = {"$regex": str(v)}
                elif o == ">=":
                    v = {"$gte": v}
                elif o == ">":
                    v = {"$gt": v}
                elif o == "<=":
                    v = {"$lte": v}
                elif o == "<":
                    v = {"$lt": v}

                pre_result = {k: v}

        if pre_result is None:
            raise ValueError("Invalid query string")

        if tuple(pre_result.keys())[0] == "sortBy":
            sort_by = tuple(pre_result.values())[0]
            desc = (t[0] == "-")
        else:
            token_result.append({"$not": pre_result} if t[0] == "-" else pre_result)

    return {"$and": token_result}, sort_by, desc


def mongo_filter(cond: Union[str, dict]) -> Callable[[dict], bool]:
    if isinstance(cond, str):
        return mongo_filter(parse_query(cond)[0])

    def inner_filter(item: dict) -> bool:
        for k, v in cond.items():
            if k[0] == "$":
                if k == "$and":
                    return all(mongo_filter(x)(item) for x in v)
                elif k == "$or":
                    return any(mongo_filter(x)(item) for x in v)
                elif k == "$not":
                    return not mongo_filter(v)(item)
            else:
                item_k = dot_getter(item, k)

                if isinstance(v, dict) and any(k0[0] == "$" for k0 in v.keys()):
                    return _mongo_compare(item_k, v)
                elif isinstance(item_k, list):
                    if v not in item_k:
                        return False
                elif item_k != v:
                    return False

        return True

    return inner_filter


def parse_timedelta(s: str) -> timedelta:
    if s == "NOW":
        return timedelta()

    m = re.search("([-+]?\\d+)(\\S*)", s)
    if m:
        if m[2] in {"m", "min"}:
            return timedelta(minutes=int(m[1]))
        elif m[2] in {"h", "hr"}:
            return timedelta(hours=int(m[1]))
        elif m[2] in {"d"}:
            return timedelta(days=int(m[1]))
        elif m[2] in {"w", "wk"}:
            return timedelta(weeks=int(m[1]))
        elif m[2] in {"M", "mo"}:
            return timedelta(days=30 * int(m[1]))
        elif m[2] in {"y", "yr"}:
            return timedelta(days=365 * int(m[1]))

    raise ValueError("Invalid timedelta value")


def sorter(sort_by: str, desc: bool) -> Callable[[Any], bool]:
    def pre_cmp(a, b):
        m = _sort_convert(a)
        n = _sort_convert(b)

        if isinstance(m, (float, int, str)):
            if type(m) == type(n):
                return 1 if m > n else 0 if m == n else -1
            elif isinstance(m, str):
                return 1
            else:
                return -1
        else:
            return 0

    return functools.cmp_to_key(lambda x, y: -pre_cmp(dot_getter(x, sort_by, False), dot_getter(y, sort_by, False))
        if desc else pre_cmp(dot_getter(x, sort_by, False), dot_getter(y, sort_by, False)))


def dot_getter(d: dict, k: str, get_data: bool = True) -> Any:
    if k[0] == "@":
        return data_getter(d, k[1:])

    v = d

    for kn in k.split("."):
        if isinstance(v, dict):
            if kn == "*":
                v = list(v.values())
            else:
                v = v.get(kn, dict())
        elif isinstance(v, list):
            try:
                v = v[int(kn)]
            except (IndexError, ValueError):
                v = None
                break
        else:
            break

    if isinstance(v, dict) and len(v) == 0:
        v = None

    if get_data and k not in {"nextReview", "srsLevel"}:
        data = data_getter(d, k)
        if data is not None:
            if v is not None:
                if isinstance(data, list):
                    if isinstance(v, list):
                        v = [*v, *data]
                    elif v is not None:
                        v = [v, *data]
                    else:
                        v = data
                else:
                    if isinstance(v, list):
                        v = [*v, data]
                    elif v is not None:
                        v = [v, data]
                    else:
                        v = data
            else:
                v = data

    return v


def data_getter(d: dict, k: str) -> Union[str, None]:
    k = k.lower()

    try:
        if k == "*":
            return [v0["value"] for v0 in d["data"] if not v0["value"].startswith("@nosearch\n")]
        else:
            for v0 in d["data"]:
                if v0["key"].lower() == k:
                    return v0["value"]
    except AttributeError:
        pass

    return None


def shlex_split(s: str, split_token: Set[str], keep_splitter: bool = False) -> List[str]:
    s = remove_brackets(s)

    tokens = []

    new_token = ""
    in_quote = False
    in_bracket = False
    to_skip = 0

    for i, c in enumerate(s):
        if c == '"' and (i == 0 or (i > 0 and s[i - 1] != "\\")):
            in_quote = not in_quote
            to_skip += 1

        elif not in_bracket and c == "(" and (i == 0 or (i > 0 and s[i - 1] != "\\")):
            in_bracket = True
            to_skip += 1

        if not in_quote and not in_bracket:
            for t in split_token:
                if s[i: i + len(t)] == t and (i == 0 or (i > 0 and s[i - 1] != "\\")):
                    if new_token:
                        tokens.append(new_token)
                        new_token = ""

                    if keep_splitter:
                        tokens.append(t)

                    to_skip = len(t)
                    break

        else:
            if in_bracket and c == ")" and (i == 0 or (i > 0 and s[i - 1] != "\\")):
                in_bracket = False
                to_skip += 1

        if to_skip > 0:
            to_skip -= 1
            continue

        new_token += c

    if new_token:
        tokens.append(new_token)

    return tokens


def remove_brackets(s: str) -> str:
    if len(s) >=2 and s[0] == "(" and s[-1] == ")":
        return s[1:-1]

    return s


def _mongo_compare(v, v_obj: dict) -> bool:
    for op, v0 in v_obj.items():
        try:
            if op == "$regex":
                if isinstance(v, list):
                    return any(re.search(str(v0), str(b), flags=re.IGNORECASE) for b in v)
                else:
                    return re.search(str(v0), str(v), flags=re.IGNORECASE) is not None
            elif op == "$substr":
                if isinstance(v, list):
                    return any(str(v0) in str(b) for b in v)
                else:
                    return str(v0) in str(v)
            elif op == "$startswith":
                if isinstance(v, list):
                    return any(str(b).startswith(str(v0)) for b in v)
                else:
                    return str(v).startswith(str(v0))
            elif op == "$exists":
                return (v is not None) == v0
            else:
                try:
                    _v = int(v)
                    _v0 = int(v0)
                    v, v0 = _v, _v0
                except ValueError:
                    pass

                if op == "$gte":
                    return v >= v0
                elif op == "$gt":
                    return v > v0
                elif op == "$lte":
                    return v <= v0
                elif op == "$lt":
                    return v < v0
        except TypeError:
            pass

    return False


def _sort_convert(x) -> Union[float, str]:
    if x is None:
        return -math.inf
    elif isinstance(x, bool):
        return math.inf if x else -math.inf
    elif isinstance(x, int):
        return float(x)

    return str(x)

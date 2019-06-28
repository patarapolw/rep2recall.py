from typing import List, Union, Optional
from easydict import EasyDict
import dataclasses as dc


class IDataSocket(EasyDict):
    key: str
    value: Union[str, dict]


class IStreak(EasyDict):
    right: int = 0
    wrong: int = 0


class IStat(EasyDict):
    streak: IStreak


class IEntry(EasyDict):
    front: str = ""
    deck: str = ""
    id: Optional[int]
    back: Optional[str]
    mnemonic: Optional[str]
    tag: Optional[List[str]]
    srsLevel: Optional[int]
    nextReview: Optional[str]
    created: Optional[str]
    modified: Optional[str]
    stat: Optional[IStat]
    template: Optional[str]
    model: Optional[str]
    tFront: Optional[str]
    tBack: Optional[str]
    css: Optional[str]
    js: Optional[str]
    key: Optional[str]
    data: Optional[List[IDataSocket]]
    source: Optional[str]
    sH: Optional[str]
    sCreated: Optional[str]


class ICondOptions(EasyDict):
    offset: int = 0
    limit: Optional[int] = None
    sortBy: str = None
    desc: bool = False
    fields: Optional[List[str]] = None


class IPagedOutput(EasyDict):
    data: List[dict]
    count: int


@dc.dataclass
class IParserResult:
    cond: dict
    is_: set = dc.field(default_factory=set)
    sortBy: str = "deck"
    desc: bool = False

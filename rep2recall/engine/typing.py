from typing import List, Union
import dataclasses as dc


@dc.dataclass
class IDataSocket:
    key: str
    value: Union[str, dict]


@dc.dataclass
class IStreak:
    right: int = 0
    wrong: int = 0


@dc.dataclass
class IStat:
    streak: IStreak = dc.field(default_factory=IStreak)


@dc.dataclass
class IEntry:
    front: str
    deck: str
    id: int = None
    back: str = None
    mnemonic: str = None
    tag: List[str] = dc.field(default_factory=list)
    srsLevel: int = None
    nextReview: str = None
    created: str = None
    modified: str = None
    stat: IStat = dc.field(default_factory=IStat)
    template: str = None
    model: str = None
    tFront: str = None
    tBack: str = None
    css: str = None
    js: str = None
    key: str = None
    data: List[IDataSocket] = dc.field(default_factory=list)
    source: str = None
    sH: str = None
    sCreated: str = None


@dc.dataclass
class ICondOptions:
    offset: int = 0
    limit: int = None
    sortBy: str = None
    desc: bool = False
    fields: List[str] = dc.field(default_factory=list)


@dc.dataclass
class IPagedOutput:
    data: List[dict]
    count: int


@dc.dataclass
class IParserResult:
    cond: dict
    is_: set = dc.field(default_factory=set)
    sortBy: str = "deck"
    desc: bool = False

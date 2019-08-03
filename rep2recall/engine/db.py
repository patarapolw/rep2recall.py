import sqlite3
from typing import List, Iterable, Optional, Union
import json
from datetime import datetime
import hashlib
import dataclasses as dc

from .typing import IEntry, IStat, IStreak, ICondOptions, IParserResult, IPagedOutput
from .util import ankiMustache
from .quiz import srsMap, getNextReview, repeatReview
from .search import mongo_filter, sorter


class Db:
    def __init__(self, filename: str):
        self.conn = sqlite3.connect(filename, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS deck (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    VARCHAR UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        VARCHAR NOT NULL /* NOT UNIQUE */,
            h           VARCHAR UNIQUE,
            created     VARCHAR NOT NULL
        );
        CREATE TABLE IF NOT EXISTS template (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sourceId    INTEGER REFERENCES source(id),
            name        VARCHAR,
            model       VARCHAR,
            front       VARCHAR NOT NULL,
            back        VARCHAR,
            css         VARCHAR,
            js          VARCHAR,
            UNIQUE (sourceId, name, model)
        );
        CREATE TABLE IF NOT EXISTS note (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sourceId    INTEGER REFERENCES source(id),
            key         VARCHAR,
            data        VARCHAR NOT NULL /* JSON */,
            UNIQUE (sourceId, key)
        );
        CREATE TABLE IF NOT EXISTS media (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sourceId    INTEGER REFERENCES source(id),
            name        VARCHAR NOT NULL,
            data        BLOB NOT NULL,
            h           VARCHAR NOT NULL
        );
        CREATE TABLE IF NOT EXISTS card (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            deckId      INTEGER NOT NULL REFERENCES deck(id),
            templateId  INTEGER REFERENCES template(id),
            noteId      INTEGER REFERENCES note(id),
            front       VARCHAR NOT NULL,
            back        VARCHAR,
            mnemonic    VARCHAR,
            srsLevel    INTEGER,
            nextReview  VARCHAR,
            /* tag */
            created     VARCHAR,
            modified    VARCHAR,
            stat        VARCHAR
        );
        CREATE TABLE IF NOT EXISTS tag (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    VARCHAR UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cardTag (
            cardId  INTEGER NOT NULL REFERENCES card(id) ON DELETE CASCADE,
            tagId   INTEGER NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
            PRIMARY KEY (cardId, tagId)
        );
        """)

    def close(self):
        try:
            self.conn.commit()
            self.conn.close()
        except sqlite3.Error:
            pass

    def insertMany(self, entries: List[IEntry]) -> List[int]:
        entries = [IEntry(**self.transformCreateOrUpdate(None, u)) for u in entries]

        deckNameToId = dict()
        for deck in set(e.deck for e in entries):
            deckNameToId[deck] = self.getOrCreateDeck(deck)

        sourceHToId = dict()
        sourceSet = set()
        for e in entries:
            if e.sH and e.sH not in sourceSet:
                self.conn.execute("""
                INSERT INTO source (name, created, h)
                VALUES (?, ?, ?)
                ON CONFLICT DO NOTHING
                """, (e.source, e.sCreated, e.sH))

                sourceHToId[e.sH] = self.conn.execute("""
                SELECT id FROM source
                WHERE h = ?
                """, (e.sH,)).fetchone()[0]

                sourceSet.add(e.sH)

        templateKeyToId = dict()
        for e in entries:
            if e.tFront and e.template and e.model:
                if e.tFront:
                    self.conn.execute("""
                    INSERT INTO template (name, model, front, back, css, js, sourceId)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT DO NOTHING
                    """, (
                        e.template,
                        e.model,
                        e.tFront,
                        e.tBack,
                        e.css,
                        e.js,
                        sourceHToId.get(e.sH)
                    ))

                    templateKeyToId[f"{e.template}\x1f{e.model}"] = self.conn.execute("""
                    SELECT id FROM template
                    WHERE
                        sourceId = ? AND
                        name = ? AND
                        model = ?
                    """, (sourceHToId.get(e.sH), e.template, e.model)).fetchone()[0]

        noteKeyToId = dict()
        for e in entries:
            if e.data and e.key:
                try:
                    noteId = self.conn.execute("""
                    INSERT INTO note (sourceId, key, data)
                    VALUES (?, ?, ?)
                    """, (
                        sourceHToId.get(e.sH),
                        e.key,
                        json.dumps(e.data, ensure_ascii=False)
                    )).lastrowid
                except sqlite3.Error:
                    noteId = self.conn.execute("""
                    SELECT id FROM note
                    WHERE
                        sourceId = ? AND
                        key = ?
                    """, (sourceHToId.get(e.sH), e.key)).fetchone()[0]

                noteKeyToId[e.key] = noteId

        now = str(datetime.now())
        cardIds = []
        for e in entries:
            cardId = int(self.conn.execute("""
            INSERT INTO card
            (front, back, mnemonic, nextReview, deckId, noteId, templateId, created, srsLevel, stat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                e.front,
                e.back,
                e.mnemonic,
                e.nextReview,
                deckNameToId.get(e.deck),
                noteKeyToId.get(e.key),
                templateKeyToId.get(f"{e.template}\x1f{e.model}"),
                now,
                e.srsLevel,
                json.dumps(dc.asdict(e.stat), ensure_ascii=False)
            )).lastrowid)

            if e.tag:
                for t in e.tag:
                    self.conn.execute("""
                    INSERT INTO tag (name)
                    VALUES (?)
                    ON CONFLICT DO NOTHING
                    """, (t,))

                    self.conn.execute("""
                    INSERT INTO cardTag (cardId, tagId)
                    VALUES (
                        ?,
                        (SELECT id FROM tag WHERE name = ?)
                    )
                    ON CONFLICT DO NOTHING
                    """, (cardId, t))

            cardIds.append(cardId)

        self.conn.commit()

        return cardIds

    def getAll(self) -> List[dict]:
        c = self.conn.execute("""
        SELECT
            c.id AS id,
            c.front AS front,
            c.back AS back,
            mnemonic,
            /* tag */
            srsLevel,
            nextReview,
            d.name AS deck,
            c.created AS created,
            modified,
            t.name AS template,
            t.model AS model,
            t.front AS tFront,
            t.back AS tBack,
            css,
            js,
            n.key AS "key",
            n.data AS data,
            s.name AS source,
            s.h AS sourceH,
            s.created AS sourceCreated,
            stat
        FROM card AS c
        INNER JOIN deck AS d ON d.id = deckId
        LEFT JOIN template AS t ON t.id = templateId
        LEFT JOIN note AS n ON n.id = noteId
        LEFT JOIN source AS s ON s.id = n.sourceId
        """)

        items = []
        for r in c:
            item = dict(r)
            item["tag"] = [x[0] for x in self.conn.execute("""
            SELECT name
            FROM tag
            INNER JOIN cardTag AS ct ON ct.tagId = tag.id
            WHERE ct.cardId = ?
            """, (item["id"],))]
            item["data"] = json.loads(item["data"] if item["data"] else "null")
            item["stat"] = json.loads(item["stat"] if item["stat"] else "null")
            items.append(item)

        return items

    def getOrCreateDeck(self, name: str) -> int:
        self.conn.execute("""
        INSERT INTO deck (name)
        VALUES (?)
        ON CONFLICT DO NOTHING
        """, (name,))

        return self.conn.execute("""
        SELECT id FROM deck
        WHERE name = ?
        """, (name,)).fetchone()[0]

    def transformCreateOrUpdate(self, cId: Optional[int] = None, u: Union[dict, IEntry] = None) -> dict:
        if u is None:
            u = dict()

        data = None
        front = None

        if u.get("front", "").startswith("@template\n"):
            if data is None:
                if cId is not None:
                    data = self.getData(cId)
                else:
                    data = u.get("data", list())
            u["tFront"] = u.pop("front")[len("@template\n"):]

        if u.get("tFront"):
            front = ankiMustache(u["tFront"], data)
            u["front"] = "@md5\n" + hashlib.md5(front.encode()).hexdigest()

        if u.get("back", "").startswith("@template\n"):
            u["tBack"] = u.pop("back")[len("@template\n"):]
            if front is None:
                if cId is not None:
                    front = self.getFront(cId)
                else:
                    front = ""

        if u.get("tBack"):
            back = ankiMustache(u["tBack"], data, front)
            u["back"] = "@md5\n" + hashlib.md5(back.encode()).hexdigest()

        return u

    def update(self, cId: int, u: dict = None, doCommit: bool = True):
        if u is None:
            u = dict()

        u = self.transformCreateOrUpdate(cId, u)
        u["modified"] = str(datetime.now())

        for k, v in u.items():
            if k == "deck":
                deckId = self.getOrCreateDeck(v)
                self.conn.execute("""
                UPDATE card
                SET deckId = ?
                WHERE id = ?
                """, (deckId, cId))
            elif k in {
                "nextReview", "created", "modified",
                "front", "back", "mnemonic", "srsLevel"
            }:
                if not isinstance(v, (str, int, float)):
                    v = str(v)

                self.conn.execute(f"""
                UPDATE card
                SET {k} = ?
                WHERE id = ?
                """, (v, cId))
            elif k in {"css", "js"}:
                self.conn.execute(f"""
                UPDATE template
                SET {k} = ?
                WHERE template.id = (
                    SELECT templateId FROM card WHERE card.id = ?
                )
                """, (v, cId))
            elif k in {"tFront", "tBack"}:
                self.conn.execute(f"""
                UPDATE template
                SET {k[1:].lower()} = ?
                WHERE template.id = (
                    SELECT templateId FROM card WHERE card.id = ?
                )
                """, (v, cId))
            elif k == "tag":
                prevTags = self.getTags(cId)
                self.addTags(cId, [t for t in v if t not in prevTags], False, prevTags)
                self.removeTags(cId, [t for t in prevTags if t not in v], False, prevTags)
            elif k == "stat":
                v = json.dumps(v, ensure_ascii=False)
                self.conn.execute(f"""
                UPDATE card
                SET stat = ?
                WHERE id = ?
                """, (v, cId))
            elif k == "data":
                data = self.getData(cId)

                for vn in v:
                    isNew = True
                    for i, d in enumerate(data):
                        if d["key"] == vn["key"]:
                            data[i]["value"] = vn["value"]
                            isNew = False
                            break

                    if isNew:
                        data.append(vn)

                if self.conn.execute("""
                SELECT noteId FROM card WHERE card.id = ?
                """, (cId,)).fetchone() is None:

                    noteId = self.conn.execute("""
                    INSERT INTO note (data)
                    VALUES (?)
                    """, (json.dumps(data, ensure_ascii=False)))

                    self.conn.execute("""
                    UPDATE card
                    SET noteId = ?
                    WHERE id = ?
                    """, (noteId, cId))
                else:
                    self.conn.execute("""
                    UPDATE note
                    SET data = ?
                    WHERE note.id = (
                        SELECT noteId FROM card WHERE card.id = ?
                    )
                    """, (json.dumps(data, ensure_ascii=False), cId))

        if doCommit:
            self.conn.commit()

    def updateMany(self, cIds: List[int], u: dict = None):
        if u is None:
            u = dict()

        for cId in cIds:
            self.update(cId, u, False)

        self.conn.commit()

    def getFront(self, cId: int) -> str:
        front = self.conn.execute("""
        SELECT front FROM card WHERE id = ?
        """, (cId,)).fetchone()[0]

        if front.startswith("@md5\n"):
            tFront, data = self.conn.execute("""
            SELECT t.front, data
            FROM card AS c
            LEFT JOIN template AS t ON t.id = templateId
            LEFT JOIN note AS n ON n.id = noteId
            WHERE c.id = ?
            """, (cId,)).fetchone()

            if tFront and data:
                data = json.loads(data)
                front = ankiMustache(tFront, data)

        return front

    def getData(self, cId: int) -> List[dict]:
        return json.loads(self.conn.execute("""
        SELECT data FROM note
        WHERE note.id = (SELECT noteId FROM card WHERE card.id = ?)
        """, (cId,)).fetchone()[0])

    def delete(self, cId: int):
        self.conn.execute("""
        DELETE FROM card
        WHERE id = ?
        """, (cId,))
        self.conn.commit()

    def deleteMany(self, cIds: List[int]):
        self.conn.execute(f"""
        DELETE FROM card
        WHERE id IN ({",".join(["?"] * len(cIds))})
        """, cIds)
        self.conn.commit()

    def getTags(self, cId: int):
        return set(c[0] for c in self.conn.execute("""
        SELECT name
        FROM tag AS t
        INNER JOIN cardTag AS ct ON ct.tagId = t.id
        INNER JOIN card AS c ON ct.cardId = c.id
        WHERE c.id = ?
        """, (cId,)))

    def addTags(self, cId: int, tags: Iterable[str], doCommit: bool = True, prevTags: Iterable[str] = None):
        if prevTags is None:
            prevTags = []

        for t in tags:
            if t not in prevTags:
                self.conn.execute("""
                INSERT INTO tag (name)
                VALUES (?)
                ON CONFLICT DO NOTHING
                """, (t,))

                self.conn.execute("""
                INSERT INTO cardTag (cardId, tagId)
                VALUES (
                    ?,
                    (SELECT tag.id FROM tag WHERE tag.name = ?)
                )
                ON CONFLICT DO NOTHING
                """, (cId, t))

        self.update(cId, None, False)

        if doCommit:
            self.conn.commit()

    def removeTags(self, cId: int, tags: Iterable[str], doCommit: bool = True, prevTags: Iterable[str] = None):
        if prevTags is None:
            prevTags = []

        for t in prevTags:
            if t in tags:
                self.conn.execute("""
                DELETE FROM cardTag
                WHERE
                    cardId = ? AND
                    tagId = (SELECT id FROM tag WHERE name = ?)
                """, (cId, t))

        self.update(cId, None, False)

        if doCommit:
            self.conn.commit()

    def parseCond(self, cond: IParserResult, options: ICondOptions = None) -> IPagedOutput:
        def _filter_fields(entry: dict) -> dict:
            if options.fields is None:
                return entry

            output = dict()
            for k, v in entry.items():
                if k in options.fields:
                    output[k] = v

            return output

        sortBy = None
        if cond.sortBy:
            sortBy = cond.sortBy
        elif options.sortBy:
            sortBy = options.sortBy

        if sortBy:
            if cond.desc is not None:
                desc = cond.desc
            else:
                desc = options.desc

            sortKey = sorter(sortBy, desc)
        else:
            sortKey = None

        allCards = sorted((c for c in self.getAll() if mongo_filter(cond.cond)(c)), key=sortKey)
        if options.limit:
            endPoint = options.offset + options.limit
        else:
            endPoint = None

        return IPagedOutput(
            data=[_filter_fields(c) for c in allCards[options.offset: endPoint]],
            count=len(allCards)
        )

    def render(self, cardId: int) -> dict:
        c = dict(self.conn.execute("""
        SELECT
            c.front AS front,
            c.back AS back,
            mnemonic,
            t.name AS template,
            t.model AS model,
            t.front AS tFront,
            t.back AS tBack,
            css,
            js,
            n.data AS data
        FROM card AS c
        LEFT JOIN template AS t ON t.id = templateId
        LEFT JOIN note AS n ON n.id = noteId
        WHERE c.id = ?
        """, (cardId,)).fetchone())

        c["data"] = json.loads(c["data"] if c["data"] else "null")

        if c["front"].startswith("@md5\n"):
            c["front"] = ankiMustache(c.get("tFront", ""), c.get("data", list()))

        if c["back"] and c["back"].startswith("@md5\n"):
            c["back"] = ankiMustache(c.get("tBack", ""), c.get("data", list()), c["front"])

        return c

    def markRight(self, cardId: int):
        return self._updateCard(+1, cardId)

    def markWrong(self, cardId: int):
        return self._updateCard(-1, cardId)

    def _updateCard(self, dSrsLevel: int, cardId: int):
        srsLevel, stat = self.conn.execute("""
        SELECT srsLevel, stat FROM card WHERE id = ?""", (cardId,)).fetchone()

        if stat is None:
            stat = IStat(
                streak=IStreak(right=0, wrong=0)
            )
        else:
            stat = EasyDict(**json.loads(stat))

        if srsLevel is None:
            srsLevel = 0

        if dSrsLevel > 0:
            stat["streak"]["right"] = stat.setdefault("streak", dict()).setdefault("right", 0) + 1
        elif dSrsLevel < 0:
            stat["streak"]["wrong"] = stat.setdefault("streak", dict()).setdefault("wrong", 0) + 1

        srsLevel += dSrsLevel

        if srsLevel >= len(srsMap):
            srsLevel = len(srsMap) - 1

        if srsLevel < 0:
            srsLevel = 0

        if dSrsLevel > 0:
            nextReview = getNextReview(srsLevel)
        else:
            nextReview = repeatReview()

        self.update(cardId, {
            "srsLevel": srsLevel,
            "stat": stat,
            "nextReview": nextReview
        })

import sqlite3
from typing import List, Iterable, Optional
import json
from datetime import datetime
import hashlib
from .util import anki_mustache


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

    def insert_many(self, entries: List[dict]) -> List[int]:
        entries = list(map(lambda u: self.transform_create_or_update(None, u), entries))

        decks = list(set(map(lambda x: x["deck"], entries)))
        deck_ids = list(map(self.get_or_create_deck, decks))

        source_id = None
        source_set = set()
        for t in filter(lambda x: x.get("sourceH"), entries):
            source_h = t.get("sourceH")
            if source_h not in source_set:
                self.conn.execute("""
                INSERT INTO source (name, created, h)
                VALUES (?, ?, ?)
                ON CONFLICT DO NOTHING
                """, (t["source"], t["sourceCreated"], source_h))

                source_id = self.conn.execute("""
                SELECT id FROM source
                WHERE h = ?
                """, (source_h,)).fetchone()[0]

                source_set.add(source_h)

        templates = []
        for t in filter(lambda x: x.get("tFront"), entries):
            source_id = t.get("sourceId", source_id)
            templates.append(f"{t.get('template', 'template')}\x1f{t.get('model', 'model')}")

            if t.get("tFront"):
                self.conn.execute("""
                INSERT INTO template (name, model, front, back, css, js, sourceId)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """, (
                    t.get("template"),
                    t.get("model"),
                    t["tFront"],
                    t.get("tBack"),
                    t.get("css"),
                    t.get("js"),
                    source_id
                ))

        templates = list(set(templates))
        template_ids = []
        for t in templates:
            name, model = t.split("\x1f")
            template_ids.append(self.conn.execute("""
            SELECT id FROM template
            WHERE
                sourceId = ? AND
                name = ? AND
                model = ?
            """, (source_id, name, model)).fetchone()[0])

        note_ids = []
        for e in entries:
            if e.get("data"):
                try:
                    note_id = self.conn.execute("""
                    INSERT INTO note (sourceId, key, data)
                    VALUES (?, ?, ?)
                    """, (
                        source_id,
                        e.get("key"),
                        json.dumps(e["data"], ensure_ascii=False)
                    )).lastrowid
                except sqlite3.Error:
                    note_id = self.conn.execute("""
                    SELECT id FROM note
                    WHERE
                        sourceId = ? AND
                        key = ?
                    """, (source_id, e.get("key"))).fetchone()[0]
                note_ids.append(note_id)
            else:
                note_ids.append(None)

        now = str(datetime.now())
        card_ids = []
        for i, e in enumerate(entries):
            card_id = int(self.conn.execute("""
            INSERT INTO card
            (front, back, mnemonic, nextReview, deckId, noteId, templateId, created, srsLevel)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                e["front"],
                e.get("back"),
                e.get("mnemonic"),
                e.get("nextReview"),
                deck_ids[decks.index(e["deck"])],
                note_ids[i],
                template_ids[templates.index(f"{e['template']}\x1f{e['model']}")]
                if e.get("model") and e.get("template") else None,
                now,
                e.get("srsLevel")
            )).lastrowid)

            if e.get("tag"):
                for t in e["tag"]:
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
                    """, (card_id, t))

            card_ids.append(card_id)

        self.conn.commit()

        return card_ids

    def get_all(self) -> List[dict]:
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
            item["data"] = json.loads(item["data"] if item["data"] else "[]")
            item["stat"] = json.loads(item["stat"] if item["stat"] else "{}")
            items.append(item)

        return items

    def get_or_create_deck(self, name: str) -> int:
        self.conn.execute("""
        INSERT INTO deck (name)
        VALUES (?)
        ON CONFLICT DO NOTHING
        """, (name,))

        return self.conn.execute("""
        SELECT id FROM deck
        WHERE name = ?
        """, (name,)).fetchone()[0]

    def transform_create_or_update(self, c_id: Optional[int] = None, u: dict = None) -> dict:
        if u is None:
            u = dict()

        data = None
        front = None

        if u.get("front", "").startswith("@template\n"):
            if data is None:
                if c_id is not None:
                    data = self.get_data(c_id)
                else:
                    data = u.get("data", dict())
            u["tFront"] = u.pop("front")[len("@template\n"):]

        if u.get("tFront"):
            front = anki_mustache(u["tFront"], data)
            u["front"] = "@md5\n" + hashlib.md5(front.encode()).hexdigest()

        if u.get("back", "").startswith("@template\n"):
            u["tBack"] = u.pop("back")[len("@template\n"):]
            if front is None:
                if c_id is not None:
                    front = self.get_front(c_id)
                else:
                    front = ""

        if u.get("tBack"):
            back = anki_mustache(u["tBack"], data, front)
            u["back"] = "@md5\n" + hashlib.md5(back.encode()).hexdigest()

        return u

    def update(self, c_id: int, u: dict = None, commit: bool = True):
        if u is None:
            u = dict()

        u = self.transform_create_or_update(c_id, u)
        u["modified"] = str(datetime.now())

        for k, v in u.items():
            if k == "deck":
                deck_id = self.get_or_create_deck(v)
                self.conn.execute("""
                UPDATE card
                SET deckId = ?
                WHERE id = ?
                """, (deck_id, c_id))
            elif k in {
                "nextReview", "created", "modified",
                "front", "back", "mnemonic", "srsLevel"
            }:
                self.conn.execute(f"""
                UPDATE card
                SET {k} = ?
                WHERE id = ?
                """, (v, c_id))
            elif k in {"css", "js"}:
                self.conn.execute(f"""
                UPDATE template
                SET {k} = ?
                WHERE template.id = (
                    SELECT templateId FROM card WHERE card.id = ?
                )
                """, (v, c_id))
            elif k in {"tFront", "tBack"}:
                self.conn.execute(f"""
                UPDATE template
                SET {k[1:].lower()} = ?
                WHERE template.id = (
                    SELECT templateId FROM card WHERE card.id = ?
                )
                """, (v, c_id))
            elif k == "tag":
                prev_tags = self.get_tags(c_id)
                self.edit_tags([c_id], set(v) - prev_tags, True, False)
                self.edit_tags([c_id], prev_tags - set(v), False, False)
            elif k == "data":
                data = self.get_data(c_id)

                for vn in v:
                    assert isinstance(vn, dict)

                    is_new = True
                    for i, d in enumerate(data):
                        if d["key"] == vn["key"]:
                            data[i]["value"] = vn["value"]
                            is_new = False
                            break

                    if is_new:
                        data.append(vn)

                if self.conn.execute("""
                SELECT noteId FROM card WHERE card.id = ?
                """, (c_id,)).fetchone() is None:

                    note_id = self.conn.execute("""
                    INSERT INTO note (data)
                    VALUES (?)
                    """, (json.dumps(data, ensure_ascii=False)))

                    self.conn.execute("""
                    UPDATE card
                    SET noteId = ?
                    WHERE id = ?
                    """, (note_id, c_id))
                else:
                    self.conn.execute("""
                    UPDATE note
                    SET data = ?
                    WHERE note.id = (
                        SELECT noteId FROM card WHERE card.id = ?
                    )
                    """, (json.dumps(data, ensure_ascii=False), c_id))

        if commit:
            self.conn.commit()

    def update_many(self, c_ids: List[int], u: dict = None):
        if u is None:
            u = dict()

        for c_id in c_ids:
            self.update(c_id, u, False)

        self.conn.commit()

    def get_front(self, c_id: int) -> str:
        front = self.conn.execute("""
        SELECT front FROM card WHERE id = ?
        """, (c_id,)).fetchone()[0]

        if front.startswith("@md5\n"):
            t_front, data = self.conn.execute("""
            SELECT t.front, data
            FROM card AS c
            LEFT JOIN template AS t ON t.id = templateId
            LEFT JOIN note AS n ON n.id = noteId
            WHERE c.id = ?
            """, (c_id,)).fetchone()

            if t_front and data:
                data = json.loads(data)
                front = anki_mustache(t_front, data)

        return front

    def get_data(self, c_id: int) -> List[dict]:
        return json.loads(self.conn.execute("""
        SELECT data FROM note
        WHERE note.id = (SELECT noteId FROM card WHERE card.id = ?)
        """, (c_id,)).fetchone()[0])

    def delete(self, c_id: int):
        self.conn.execute("""
        DELETE FROM card
        WHERE id = ?
        """, (c_id,))
        self.conn.commit()

    def delete_many(self, c_ids: List[int]):
        self.conn.execute(f"""
        DELETE FROM card
        WHERE id IN ({",".join(["?"] * len(c_ids))})
        """, c_ids)
        self.conn.commit()

    def get_tags(self, c_id):
        return set(c[0] for c in self.conn.execute("""
        SELECT name
        FROM tag AS t
        INNER JOIN cardTag AS ct ON ct.tagId = t.id
        INNER JOIN card AS c ON ct.cardId = c.id
        WHERE c.id = ?
        """, (c_id,)))

    def edit_tags(self, c_ids: List[int], tags: Iterable[str], is_add: bool, commit: bool = True):
        for c_id in c_ids:
            prev_tags = self.get_tags(c_id)

            if is_add:
                updated_tags = set(tags) - prev_tags

                for t in sorted(updated_tags):
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
                    """, (c_id, t))
            else:
                updated_tags = prev_tags - set(tags)

                for t in sorted(updated_tags):
                    self.conn.execute("""
                    DELETE FROM cardTag
                    WHERE
                        cardId = ? AND
                        tagId = (SELECT id FROM tag WHERE name = ?)
                    """, (c_id, t))

            self.update(c_id, None, False)

        if commit:
            self.conn.commit()

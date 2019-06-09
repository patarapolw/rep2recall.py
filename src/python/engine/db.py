import sqlite3
from typing import List
import json
from datetime import datetime


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
            name        VARCHAR NOT NULL,
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
            key         VARCHAR NOT NULL,
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
            front       VARCHAR UNIQUE NOT NULL,
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
        for t in filter(lambda x: x["model"] and x["template"], entries):
            source_id = t.get("sourceId", source_id)
            templates.append(f"{t['template']}\x1f{t['model']}")

            if t.get("tFront"):
                self.conn.execute("""
                INSERT INTO template (name, model, front, back, css, js, sourceId)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """, (
                    t["template"],
                    t["model"],
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
            if e["entry"]:
                self.conn.execute("""
                INSERT INTO note (sourceId, key, data)
                VALUES (?, ?, ?)
                ON CONFLICT DO NOTHING
                """, (
                    source_id,
                    e["entry"],
                    json.dumps(e["data"], ensure_ascii=False)
                ))
                note_id = self.conn.execute("""
                SELECT id FROM note
                WHERE
                    sourceId = ? AND
                    key = ?
                """, (source_id, e["entry"])).fetchone()[0]
                note_ids.append(note_id)
            else:
                note_ids.append(None)

        now = str(datetime.now())
        card_ids = []
        for i, e in enumerate(entries):
            card_id = int(self.conn.execute("""
            INSERT INTO card
            (front, back, mnemonic, nextReview, deckId, noteId, templateId, created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                e["front"],
                e.get("back"),
                e.get("mnemonic"),
                e.get("nextReview"),
                deck_ids[decks.index(e["deck"])],
                note_ids[i],
                template_ids[templates.index(f"{e['template']}\x1f{e['model']}")]
                if e.get("model") and e.get("template") else None,
                now
            )).lastrowid)

            if e["tag"]:
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
            n.key AS entry,
            n.data AS data,
            s.name AS source,
            s.h AS sourceH,
            s.created AS sourceCreated,
            stat
        FROM card AS c
        INNER JOIN deck AS d ON d.id = deckId
        JOIN template AS t ON t.id = templateId
        JOIN note AS n ON n.id = noteId
        JOIN source AS s ON s.id = n.sourceId
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
            item["data"] = json.loads(item["data"] if item["data"] else "{}")
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

    def update(self, c_id: int, u: dict):
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
            elif k == "tag":
                for tag_name in v:
                    self.conn.execute("""
                    INSERT INTO tag (name)
                    VALUES (?)
                    ON CONFLICT DO NOTHING
                    """, (tag_name,))

                    self.conn.execute("""
                    INSERT INTO cardTag (cardId, tagId)
                    VALUES (
                        ?,
                        (SELECT tag.id FROM tag WHERE tag.name = ?)
                    )
                    ON CONFLICT DO NOTHING
                    """, (c_id, tag_name))
            elif k == "data":
                data = json.loads(self.conn.execute("""
                SELECT data FROM note
                WHERE note.id = (SELECT noteId FROM card WHERE card.id = ?)
                """, (c_id,)).fetchone()[0])

                self.conn.execute("""
                UPDATE note
                SET data = ?
                WHERE note.id = (
                    SELECT noteId FROM card WHERE card.id = ?
                )
                """, (json.dumps({**data, **v}, ensure_ascii=False), c_id))

        self.conn.commit()

    def update_many(self, c_ids: List[int], u: dict):
        for k, v in u.items():
            if k == "deck":
                deck_id = self.get_or_create_deck(v)
                self.conn.execute(f"""
                UPDATE card
                SET deckId = ?
                WHERE id IN ({",".join(["?"] * len(c_ids))})
                """, (deck_id, *c_ids))
            elif k in {
                "nextReview", "created", "modified",
                "front", "back", "mnemonic", "srsLevel"
            }:
                self.conn.execute(f"""
                UPDATE card
                SET {k} = ?
                WHERE id IN ({",".join(["?"] * len(c_ids))})
                """, (v, *c_ids))

        self.conn.commit()

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

    def edit_tags(self, c_ids: List[int], tags: List[str], is_add: bool):
        for c_id in c_ids:
            prev_tags = set(c[0] for c in self.conn.execute("""
            SELECT name
            FROM tag AS t
            INNER JOIN cardTag AS ct ON ct.tagId = t.id
            INNER JOIN card AS c ON ct.cardId = c.id
            WHERE c.id = ?
            """, (c_id,)))

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
                    DELETE FROM cardTag AS ct
                    INNER JOIN tag AS t WHERE t.id = ct.tagId
                    WHERE
                        cardId = ? AND
                        t.name = ?
                    """, (c_id, t))

        self.conn.commit()

from psycopg2 import pool, sql
import psycopg2
import hashlib
import random
from collections import Counter
import logging
from functools import partial, wraps
from collections import defaultdict
import time
import inspect
import heapq
from operator import itemgetter

from typing import Dict, Optional, Iterable, Dict, List

import ankipan_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

random.seed(42)

N_CONNS = 20

def with_pool_cursor(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        conn = self.get_safe_conn()
        try:
            with conn.cursor() as cur:
                return func(self, cur, *args, **kwargs)
        finally:
            self.db_pool.putconn(conn)
    return wrapper

def with_conditional_pool_conn(func):
    sig = inspect.signature(func)
    has_conn = 'conn' in sig.parameters

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not has_conn:
            return func(self, *args, **kwargs)

        try:
            bound = sig.bind_partial(self, *args, **kwargs)
        except TypeError:
            return func(self, *args, **kwargs)

        already_has_conn = ('conn' in bound.arguments) and (bound.arguments['conn'] is not None)
        if already_has_conn:
            return func(self, *args, **kwargs)

        conn = self.get_safe_conn()
        try:
            call_kwargs = {k: v for k, v in bound.arguments.items() if k != 'self'}
            call_kwargs['conn'] = conn
            return func(self, **call_kwargs)
        finally:
            self.db_pool.putconn(conn)
    return wrapper

class DBManager:
    def __init__(self, lang):
        logger.info("DBManager initializing...")
        if any(i is None for i in ankipan_db.db_config.values()):
            raise RuntimeError('Invalid .env file')
        self.db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=N_CONNS,
            options=f"-c search_path={lang}",
            **ankipan_db.db_config,
        )
        self.lang = lang

    def get_safe_conn(self, max_attempts=N_CONNS + 1, delay=0.05):
        last = None
        backoff = delay
        for _ in range(max_attempts):
            conn = self.db_pool.getconn()
            returned = False
            try:
                if getattr(conn, "closed", 0):
                    raise psycopg2.InterfaceError("connection already closed")
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                return conn
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                last = e
                try:
                    self.db_pool.putconn(conn, close=True)
                    returned = True
                except Exception:
                    pass
                time.sleep(backoff)
                backoff = min(backoff * 2, 0.5)
                continue
            except Exception:
                try:
                    self.db_pool.putconn(conn)
                    returned = True
                except Exception:
                    pass
                raise
            finally:
                if not returned and False:
                    self.db_pool.putconn(conn)
        raise last

    @with_pool_cursor
    def get_segments_for_lemmas(self,
                                cur,
                                relative_source_paths: list[str],
                                lemmas: list[str],
                                source_category_name: str,
                                native_lang,
                                n_sentences: int = 8,
                                k_root: int = 5,
                                stride: int = 1) -> dict:
        """Return sentence-context for lemmas."""

        cur.execute("SELECT id FROM sources WHERE name=%s AND nesting_level=0", (source_category_name,))
        source_category_id_unary_list = cur.fetchone()

        if not source_category_id_unary_list:
            raise RuntimeError(f'Source Category "{source_category_name}" not defined in db')
        source_category_id = source_category_id_unary_list[0]

        lemmas = list(set(lemmas))
        path_ids: list[int] = []
        for p in relative_source_paths:
            parts = [source_category_name] + [i for i in p.strip("/").split("/") if i]
            cur.execute(f"SELECT {self.lang}.source_id_from_path(VARIADIC %s)", (parts,))
            path_ids.append(cur.fetchone()[0])

        sql = f"""
        WITH roots AS (
            SELECT * FROM UNNEST(%s::int[]) AS r(root_id)
        ),
        target_sources AS (
            SELECT sd.id
            FROM   roots
            CROSS  JOIN LATERAL source_descendants(roots.root_id) sd
        ),
        raw AS (
            SELECT
                l.lemma,
                (ts.source_id = ANY(SELECT id FROM target_sources)) AS in_target,
                r.root_name,
                src.name AS source_name,
                ts.id          AS ts_id,
                w.word,
                ts.index       AS ts_index,
                ts.source_id   AS match_source_id,
                ROW_NUMBER() OVER (
                    PARTITION BY l.lemma,
                                (ts.source_id = ANY (SELECT id FROM target_sources)),
                                r.root_name
                    ORDER BY random()
                ) AS rn_root
            FROM   lemmas l
            JOIN   words  w   ON w.lemma_id = l.id
            JOIN   words_in_text_segments wits ON wits.word_id = w.id
            JOIN   text_segments ts ON ts.id = wits.text_segment_id
            JOIN   source_root_lookup r ON r.id = ts.source_id
            JOIN   sources src ON src.id = ts.source_id
            WHERE  l.lemma = ANY(%s) AND src.id = ANY(SELECT id FROM source_descendants(%s))
        ),
        raw_limited AS (               -- cap per root for diversity
            SELECT * FROM raw
            WHERE  rn_root <= %s
        ),
        counts AS (                    -- rows per lemma inside/outside specified prioritized example sentence sources
            SELECT lemma,
                COUNT(*) FILTER (WHERE in_target)     AS inside_total,
                COUNT(*) FILTER (WHERE NOT in_target) AS outside_total
            FROM   raw_limited
            GROUP  BY lemma
        ),
        quota AS (
            SELECT lemma,
                LEAST(%s / 2, inside_total)                        AS q_in,
                LEAST(%s - LEAST(%s / 2, inside_total),
                        outside_total)                               AS q_out
            FROM   counts
        ),
        matches AS (                   -- enforce ≈50/50 quota
            SELECT *
            FROM (
                SELECT rl.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY rl.lemma, rl.in_target
                        ORDER BY random()
                    ) AS rn_side
                FROM   raw_limited rl
            ) rl
            JOIN quota q USING (lemma)
            WHERE (rl.in_target AND rn_side <= q.q_in)
            OR (NOT rl.in_target AND rn_side <= q.q_out)
        )
        SELECT
            m.lemma,
            lvl1.name   AS lvl1_name,
            m.source_name,
            m.word,
            m.in_target,
            ctx.text,
            ctx.start_s,
            ctx.end_s,
            ctx.index - m.ts_index AS rel_index
        FROM matches m
        JOIN LATERAL (
                WITH RECURSIVE up AS (
                    SELECT s.id, s.parent_id, s.name, s.nesting_level
                    FROM   sources s
                    WHERE  s.id = m.match_source_id        -- start at the match
                UNION ALL
                    SELECT p.id, p.parent_id, p.name, p.nesting_level
                    FROM sources p
                    JOIN up u ON p.id = u.parent_id
                )
                SELECT name
                FROM   up
                WHERE  nesting_level = 1
                LIMIT  1
            ) lvl1 ON TRUE
        CROSS JOIN LATERAL (
            SELECT *
            FROM   text_segments ctx
            WHERE  ctx.source_id = m.match_source_id
            AND  ctx.index BETWEEN m.ts_index - %s AND m.ts_index + %s
            ORDER  BY ctx.index
        ) ctx
        ORDER  BY m.lemma, m.root_name, m.ts_id, ctx.index;
        """

        cur.execute(
            sql,(path_ids,
                lemmas,
                source_category_id,
                k_root,
                n_sentences, n_sentences, n_sentences,
                stride, stride))
        rows = cur.fetchall()

        result = {}
        for (lemma, source_root_name, source_name, word,
            in_target, text, start_s, end_s, rel_index) in rows:
            entry_type = "entries_from_known_sources" if in_target else "entries_from_unknown_sources"

            if not result.get(lemma, {}).get(entry_type, {}).get(source_root_name, {}).get(source_name):
                result.setdefault(lemma, {}).setdefault(entry_type, {}).setdefault(source_root_name, {}).setdefault(source_name, []).append({
                    "word": word,
                    'text_segments': [text],
                    'main_index': 0 if rel_index==0 else None,
                    "start_s": start_s,
                    "end_s": end_s,
                })
            else:
                result[lemma][entry_type][source_root_name][source_name][-1]['text_segments'].append(text)
                if rel_index==0:
                    result[lemma][entry_type][source_root_name][source_name][-1]['main_index'] = len(result[lemma][entry_type][source_root_name][source_name][-1]['text_segments'])-1
                result[lemma][entry_type][source_root_name][source_name][-1]['end_s'] = end_s

        # fetch cached translations (new loop because we need all text segments to fetch cached entry)
        for lemma, entries in result.items():
            for entry_type, source_data in entries.items():
                for source_root_name, sources in source_data.items():
                    for source_name, source_results in sources.items():
                        for i, source_result in enumerate(source_results):
                            cur.execute("SELECT translation from translations WHERE hash=%s AND lang = %s",
                                        (hashlib.sha256((' '.join(source_result['text_segments'])).encode("utf-8")).hexdigest(),native_lang))
                            translation_raw = cur.fetchone()
                            if translation_raw:
                                result[lemma][entry_type][source_root_name][source_name][i]['translation'] = translation_raw[0]
        return result

    def cache_translations(self, translations_by_text_segments, native_lang):
        rows = [(hashlib.sha256(o.encode("utf-8")).hexdigest(), t, native_lang) for o, t in translations_by_text_segments.items()]
        conn = self.get_safe_conn()
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO translations (hash, translation, lang)
                VALUES (%s, %s, %s)
                ON CONFLICT (hash) DO NOTHING
                """, rows)
        conn.commit()
        self.db_pool.putconn(conn)

    @with_pool_cursor
    def get_available_sources(self, cur, source_category_names: list[str] | None = None) -> dict[str, dict]:
        if source_category_names:
            cur.execute("SELECT id from sources WHERE name=%s AND nesting_level=0", (source_category_names,))
            root_ids = [id[0] for id in cur.fetchall()]
            if not root_ids:
                raise RuntimeError(
                    f'Source category name(s) not found: {source_category_names}')
        else:
            root_ids = []
        sql_roots = """
            SELECT so.id, so.name
            FROM   sources so
            WHERE parent_id IS NULL
        """
        params = []
        if root_ids:
            sql_roots += f"""
            AND so.id = ANY (
                    SELECT sd.id
                    FROM   UNNEST(%s::int[]) AS r(root_id)
                    CROSS  JOIN LATERAL source_descendants(r.root_id) sd
            )
            """
            params.append(root_ids)
        cur.execute(sql_roots, tuple(params))

        result: dict[str, dict] = {}
        root_id_by_name: dict[int, str] = {}
        for root_id, root_name in cur.fetchall():
            result[root_name] = {}
            root_id_by_name[root_id] = root_name
        if not root_id_by_name:
            return result

        cur.execute(
            """
            SELECT parent_id, name
            FROM   sources
            WHERE  parent_id = ANY(%s)
            """,
            (list(root_id_by_name.keys()),)
        )
        for parent_id, child_name in cur.fetchall():
            root_name = root_id_by_name[parent_id]
            result[root_name].setdefault(child_name, {})
        return result

    @with_pool_cursor
    def get_source_list(self, cur, source_path: str):
        path_parts = source_path.split('/')
        cur.execute(f"SELECT {self.lang}.source_id_from_path(VARIADIC %s)", (path_parts,))
        root_id = cur.fetchone()[0]
        cur.execute("SELECT metadata, lemma_counts FROM sources WHERE id = %s", (root_id,))
        root_meta, lemma_counts = cur.fetchone()
        if lemma_counts and len(lemma_counts) > 10_000:
            lemma_counts = heapq.nlargest(10_000, lemma_counts.items(), key=itemgetter(1))
        cur.execute(
            """
            SELECT name
            FROM   sources
            WHERE  parent_id = %s
            ORDER  BY name
            """, (root_id,))
        children = []
        for name in cur.fetchall():
            children.append(name[0])
        return root_meta, lemma_counts, children

    def get_source_tree_for_id(self, cur, root_id: int) -> dict[int, tuple[int | None, str]]:
        """
        Returns {id: (parent_id, name, is_leaf)} for all nodes under `root_id`
        (including the root itself).
        """
        cur.execute(
            """
            WITH RECURSIVE tree AS (
                SELECT id, parent_id, name, is_leaf
                FROM sources
                WHERE id = %s
                UNION ALL
                SELECT s.id, s.parent_id, s.name, s.is_leaf
                FROM sources s
                JOIN tree t ON s.parent_id = t.id
            )
            SELECT id, parent_id, name, is_leaf
            FROM tree;
            """,
            (root_id,),
        )
        return {row_id: (parent_id, name, is_leaf) for row_id, parent_id, name, is_leaf in cur.fetchall()}

    @with_pool_cursor
    def get_lemma_percentiles(self, cur, source_path, lemmas):
        cur.execute(f"SELECT {self.lang}.source_id_from_path(VARIADIC %s)", (source_path.split('/'),))
        root_id = cur.fetchone()[0]
        cur.execute("SELECT lemma_counts FROM sources WHERE id = %s", (root_id,))
        lemma_counts = cur.fetchone()[0]
        counter = Counter(lemma_counts)
        common = [word for word, count in counter.most_common()]
        return {lemma: (common.index(lemma) / len(counter) if counter[lemma] != 1 else 1.0)
                 for lemma in lemmas if lemma in common}

    @with_conditional_pool_conn
    def add_table_entries(
        self,
        table_name: str,
        entries: list[dict],
        *,
        ignore_duplicates: bool = False,
        return_ids: bool = True,
        conn=None):

        with conn.cursor() as cur:
            if not entries:
                return [] if return_ids else None
            cols = list(entries[0])
            values_tpl = f'({",".join(["%s"] * len(cols))})'
            values_sql = ", ".join(
                cur.mogrify(values_tpl, tuple(e[c] for c in cols)).decode()
                for e in entries)
            query = sql.SQL("""
                INSERT INTO {tbl} ({cols})
                VALUES {vals}
            """).format(
                tbl  = sql.Identifier(table_name),
                cols = sql.SQL(", ").join(map(sql.Identifier, cols)),
                vals = sql.SQL(values_sql))

            if ignore_duplicates:
                query += sql.SQL(" ON CONFLICT DO NOTHING")
            if return_ids:
                query += sql.SQL(" RETURNING id")
            cur.execute(query)
            if return_ids:
                return [row[0] for row in cur.fetchall()]

    def delete_source(self, cur, root_id: int) -> dict[str, list[int] | None]:
        sql = """
            DELETE FROM sources
            WHERE  id = %s
        """
        cur.execute(sql, (root_id,))

    @with_conditional_pool_conn
    def make_schema(self, conn=None):
        schema = self.lang

        commands = [
            f"CREATE SCHEMA IF NOT EXISTS {schema};",
            "CREATE EXTENSION IF NOT EXISTS pgcrypto;",

            f"""
            CREATE TABLE IF NOT EXISTS {schema}.translations (
                hash bytea PRIMARY KEY,
                translation TEXT NOT NULL,
                lang VARCHAR(2) NOT NULL
            );
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.lemmas (
                id SERIAL PRIMARY KEY,
                lemma TEXT NOT NULL UNIQUE
            );
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.words (
                id SERIAL PRIMARY KEY,
                word TEXT NOT NULL,
                pos VARCHAR(20),
                xpos VARCHAR(20),
                lemma_id INTEGER NOT NULL REFERENCES {schema}.lemmas(id),
                UNIQUE(word, pos)
            );
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.sources (
                id SERIAL PRIMARY KEY,
                parent_id INT REFERENCES {schema}.sources(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                metadata jsonb,
                lemma_counts jsonb,
                nesting_level INT NOT NULL,
                is_leaf BOOL NOT NULL,
                UNIQUE (parent_id, name)
            );
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.text_segments (
                id SERIAL PRIMARY KEY,
                "index" INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_s INTEGER,
                end_s INTEGER,
                source_id INTEGER NOT NULL REFERENCES {schema}.sources(id) ON DELETE CASCADE
            );
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {schema}.words_in_text_segments (
                word_id INTEGER NOT NULL REFERENCES {schema}.words(id),
                text_segment_id INTEGER NOT NULL REFERENCES {schema}.text_segments(id) ON DELETE CASCADE
            );
            """,

            # UNIQUE indexes needed for ON CONFLICT
            # (sources has UNIQUE(parent_id, name), lemmas has UNIQUE(lemma), words has UNIQUE(word,pos) already)
            f'CREATE UNIQUE INDEX IF NOT EXISTS uq_text_segments_source_index '
            f'  ON {schema}.text_segments (source_id, "index");',

            f'CREATE UNIQUE INDEX IF NOT EXISTS uq_wits '
            f'  ON {schema}.words_in_text_segments (word_id, text_segment_id);',

            f"""
            CREATE OR REPLACE FUNCTION {schema}.source_descendants(root_id int)
            RETURNS TABLE(id int)
            LANGUAGE sql
            SET search_path = {schema}
            AS $$
                WITH RECURSIVE d(id) AS (
                    SELECT id FROM {schema}.sources WHERE id = $1
                    UNION ALL
                    SELECT s.id FROM {schema}.sources s JOIN d ON s.parent_id = d.id
                )
                SELECT id FROM d;
            $$;
            """,
            f"""
            CREATE OR REPLACE FUNCTION {schema}.source_id_from_path(VARIADIC p_names text[])
            RETURNS int
            LANGUAGE plpgsql
            SET search_path = {schema}
            AS $$
            DECLARE
                part text;
                pid  int := NULL;
            BEGIN
                FOREACH part IN ARRAY p_names LOOP
                    SELECT id INTO pid
                    FROM   {schema}.sources
                    WHERE  parent_id IS NOT DISTINCT FROM pid
                    AND    name = part
                    LIMIT 1;
                    IF pid IS NULL THEN
                        RAISE EXCEPTION 'Path element "%" not found', part;
                    END IF;
                END LOOP;
                RETURN pid;
            END;
            $$;
            """,
            f"""
            CREATE OR REPLACE FUNCTION {schema}.lemmas_with_counts(root_id int)
            RETURNS TABLE(lemma text, cnt int)
            LANGUAGE sql
            SET search_path = {schema}
            AS $$
                SELECT l.lemma,
                    COUNT(*) AS cnt
                FROM   {schema}.source_descendants(root_id) d
                JOIN   {schema}.text_segments ts   ON ts.source_id = d.id
                JOIN   {schema}.words_in_text_segments wits ON wits.text_segment_id = ts.id
                JOIN   {schema}.words w    ON w.id = wits.word_id
                JOIN   {schema}.lemmas l   ON l.id = w.lemma_id
                GROUP  BY l.lemma
                ORDER  BY cnt DESC;
            $$;
            """,
            f"""
            CREATE OR REPLACE VIEW {schema}.source_root_lookup AS
            WITH RECURSIVE link(id, root_id, root_name) AS (
                SELECT id, id AS root_id, name AS root_name
                FROM   {schema}.sources
                WHERE  parent_id IS NULL
                UNION ALL
                SELECT s.id, l.root_id, l.root_name
                FROM   {schema}.sources s
                JOIN   link l ON s.parent_id = l.id
            )
            SELECT * FROM link;
            """,

            f"CREATE INDEX IF NOT EXISTS idx_lemmas_lemma ON {schema}.lemmas (lemma);",
            f"CREATE INDEX IF NOT EXISTS idx_words_lemma_id ON {schema}.words (lemma_id);",
            f"CREATE INDEX IF NOT EXISTS idx_text_segments_source_id ON {schema}.text_segments (source_id);",
        ]

        with conn.cursor() as cur:
            for cmd in commands:
                cur.execute(cmd)
        conn.commit()

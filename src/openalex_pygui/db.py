"""SQLite database layer for the OpenAlex Research Manager."""

import sqlite3
from pathlib import Path

_DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "library.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS works (
    id              TEXT PRIMARY KEY,
    doi             TEXT UNIQUE,
    title           TEXT NOT NULL,
    publication_year INTEGER,
    type            TEXT,
    cited_by_count  INTEGER DEFAULT 0,
    abstract        TEXT,
    bibtex          TEXT,
    notes           TEXT DEFAULT '',
    journal         TEXT,
    date_added      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS authors (
    id       TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    orcid    TEXT
);

CREATE TABLE IF NOT EXISTS work_authors (
    work_id   TEXT NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    author_id TEXT NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    position  INTEGER,
    PRIMARY KEY (work_id, author_id)
);

CREATE TABLE IF NOT EXISTS work_keywords (
    work_id  TEXT NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    keyword  TEXT NOT NULL,
    PRIMARY KEY (work_id, keyword)
);

CREATE TABLE IF NOT EXISTS work_relationships (
    work_id       TEXT NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    related_id    TEXT NOT NULL,
    relationship  TEXT NOT NULL,
    PRIMARY KEY (work_id, related_id, relationship)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

_MIGRATIONS = [
    "ALTER TABLE works ADD COLUMN notes TEXT DEFAULT ''",
    "ALTER TABLE works ADD COLUMN journal TEXT",
]


class Database:
    """Thin wrapper around an SQLite connection for the library."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else _DEFAULT_DB
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(_SCHEMA)
        self._run_migrations()

    def _run_migrations(self):
        for sql in _MIGRATIONS:
            try:
                self.conn.execute(sql)
            except sqlite3.OperationalError:
                pass

    # ── Works ──────────────────────────────────────────────────────────

    def add_work(
        self,
        openalex_id: str,
        title: str,
        *,
        doi: str | None = None,
        publication_year: int | None = None,
        work_type: str | None = None,
        cited_by_count: int = 0,
        abstract: str | None = None,
        journal: str | None = None,
        authors: list[dict] | None = None,
        keywords: list[str] | None = None,
        relationships: list[dict] | None = None,
    ) -> None:
        with self.conn:
            self.conn.execute(
                """INSERT OR IGNORE INTO works
                   (id, doi, title, publication_year, type, cited_by_count, abstract, journal)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (openalex_id, doi, title, publication_year, work_type,
                 cited_by_count, abstract, journal),
            )

            if authors:
                for author in authors:
                    aid = author.get("id")
                    name = author.get("name", "")
                    orcid = author.get("orcid")
                    pos = author.get("position")
                    self.conn.execute(
                        "INSERT OR IGNORE INTO authors (id, name, orcid) VALUES (?, ?, ?)",
                        (aid, name, orcid),
                    )
                    self.conn.execute(
                        "INSERT OR IGNORE INTO work_authors (work_id, author_id, position) VALUES (?, ?, ?)",
                        (openalex_id, aid, pos),
                    )

            if keywords:
                for kw in keywords:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO work_keywords (work_id, keyword) VALUES (?, ?)",
                        (openalex_id, kw),
                    )

            if relationships:
                for rel in relationships:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO work_relationships (work_id, related_id, relationship) VALUES (?, ?, ?)",
                        (openalex_id, rel["id"], rel["type"]),
                    )

    def remove_work(self, openalex_id: str) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM works WHERE id = ?", (openalex_id,))

    def remove_works(self, openalex_ids: list[str]) -> None:
        with self.conn:
            self.conn.executemany(
                "DELETE FROM works WHERE id = ?", [(wid,) for wid in openalex_ids]
            )

    def get_work(self, openalex_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM works WHERE id = ?", (openalex_id,)).fetchone()
        if not row:
            return None
        cols = [d[0] for d in self.conn.execute("SELECT * FROM works LIMIT 0").description]
        return dict(zip(cols, row))

    def list_works(self, *, search: str | None = None, sort_by: str = "date_added") -> list[dict]:
        order_cols = {"title", "publication_year", "cited_by_count", "date_added"}
        if sort_by not in order_cols:
            sort_by = "date_added"

        if search:
            rows = self.conn.execute(
                f"""SELECT * FROM works
                    WHERE title LIKE ? OR abstract LIKE ?
                    ORDER BY {sort_by} DESC""",
                (f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            rows = self.conn.execute(
                f"SELECT * FROM works ORDER BY {sort_by} DESC"
            ).fetchall()

        cols = [d[0] for d in self.conn.execute("SELECT * FROM works LIMIT 0").description]
        return [dict(zip(cols, r)) for r in rows]

    def work_exists(self, openalex_id: str) -> bool:
        return (
            self.conn.execute("SELECT 1 FROM works WHERE id = ?", (openalex_id,)).fetchone()
            is not None
        )

    def set_bibtex(self, openalex_id: str, bibtex: str) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE works SET bibtex = ? WHERE id = ?", (bibtex, openalex_id)
            )

    def set_notes(self, openalex_id: str, notes: str) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE works SET notes = ? WHERE id = ?", (notes, openalex_id)
            )

    def set_abstract(self, openalex_id: str, abstract: str) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE works SET abstract = ? WHERE id = ?", (abstract, openalex_id)
            )

    # ── Authors ────────────────────────────────────────────────────────

    def get_authors_for_work(self, openalex_id: str) -> list[dict]:
        rows = self.conn.execute(
            """SELECT a.id, a.name, a.orcid, wa.position
               FROM authors a JOIN work_authors wa ON a.id = wa.author_id
               WHERE wa.work_id = ?
               ORDER BY wa.position""",
            (openalex_id,),
        ).fetchall()
        cols = ["id", "name", "orcid", "position"]
        return [dict(zip(cols, r)) for r in rows]

    # ── Settings ───────────────────────────────────────────────────────

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
            )

    # ── Export ─────────────────────────────────────────────────────────

    def export_bibtex(self, *, ids: list[str] | None = None) -> str:
        """Return BibTeX string. If *ids* given, export only those; otherwise all."""
        if ids:
            placeholders = ",".join("?" for _ in ids)
            rows = self.conn.execute(
                f"SELECT bibtex FROM works WHERE id IN ({placeholders}) AND bibtex IS NOT NULL",
                ids,
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT bibtex FROM works WHERE bibtex IS NOT NULL ORDER BY date_added DESC"
            ).fetchall()
        return "\n\n".join(r[0] for r in rows)

    # ── Lifecycle ──────────────────────────────────────────────────────

    def close(self) -> None:
        self.conn.close()

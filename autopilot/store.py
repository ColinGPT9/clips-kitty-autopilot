"""Independent application state, admission and publication outbox."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from datetime import time as clock_time
from pathlib import Path
from zoneinfo import ZoneInfo

from cryptography.fernet import Fernet

from . import destinations

ACTIVE = ("queued", "rendering", "review", "sending", "scheduled", "needs_check")
DEFAULTS = {"enabled": False, "per_day": 5, "max_pending": 5, "gap_hours": 1,
            "day_start": "09:00", "timezone": "America/New_York", "twitch_client_id": "",
            "woop_project_id": "", "instagram_id": "", "instagram_username": "", "accounts": [],
            "selected_account_ids": None, "destination_options": {}}


class Store:
    def __init__(self, directory: Path):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db_path = self.directory / "autopilot.sqlite3"
        key = os.environ.get("AUTOPILOT_ENCRYPTION_KEY")
        key_path = self.directory / "encryption.key"
        if not key:
            if not key_path.exists():
                try:
                    with key_path.open("xb") as stream:
                        stream.write(Fernet.generate_key())
                    key_path.chmod(0o600)
                except FileExistsError:
                    pass
            key = key_path.read_bytes()
        self.fernet = Fernet(key)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS secrets(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS watches(
              id INTEGER PRIMARY KEY, login TEXT NOT NULL UNIQUE, min_views INTEGER NOT NULL DEFAULT 10000,
              lookback_days INTEGER NOT NULL DEFAULT 45, backfill INTEGER NOT NULL DEFAULT 0,
              mode TEXT NOT NULL DEFAULT 'ask', enabled INTEGER NOT NULL DEFAULT 1,
              initialized INTEGER NOT NULL DEFAULT 0, last_polled REAL NOT NULL DEFAULT 0,
              error TEXT NOT NULL DEFAULT '', options TEXT NOT NULL DEFAULT '{"captions":true}');
            CREATE TABLE IF NOT EXISTS clips(
              id TEXT PRIMARY KEY, watch_id INTEGER NOT NULL REFERENCES watches(id),
              title TEXT NOT NULL, views INTEGER NOT NULL, creator TEXT NOT NULL,
              source TEXT NOT NULL, state TEXT NOT NULL, reached_at REAL NOT NULL DEFAULT 0,
              backfilled INTEGER NOT NULL DEFAULT 0, options TEXT NOT NULL,
              output TEXT NOT NULL DEFAULT '', error TEXT NOT NULL DEFAULT '',
              duration REAL NOT NULL DEFAULT 0, created_at REAL NOT NULL,
              account_id TEXT NOT NULL DEFAULT '', account_username TEXT NOT NULL DEFAULT '',
              project_id TEXT NOT NULL DEFAULT '');
            CREATE TABLE IF NOT EXISTS slots(clip_id TEXT PRIMARY KEY, scheduled_for TEXT NOT NULL UNIQUE);
            CREATE TABLE IF NOT EXISTS posts(
              clip_id TEXT PRIMARY KEY REFERENCES clips(id), request_id TEXT NOT NULL DEFAULT '',
              media_id TEXT NOT NULL DEFAULT '', scheduled_for TEXT NOT NULL,
              post_url TEXT NOT NULL DEFAULT '', updated_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS events(
              id INTEGER PRIMARY KEY, at REAL NOT NULL, message TEXT NOT NULL, clip_id TEXT NOT NULL DEFAULT '');
            """)
            for table, column in [("clips", "destinations"), ("posts", "deliveries")]:
                if column not in {r["name"] for r in db.execute(f"PRAGMA table_info({table})")}:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT NOT NULL DEFAULT '[]'")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def settings(self, patch=None):
        with self.connect() as db:
            if patch:
                for key, value in patch.items():
                    if key not in DEFAULTS:
                        raise ValueError("Unknown setting")
                    db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, json.dumps(value)))
            result = {**DEFAULTS, **{r["key"]: json.loads(r["value"]) for r in db.execute("SELECT * FROM settings")}}
        return result

    def secret(self, key, value=None):
        with self.connect() as db:
            if value is not None:
                db.execute("INSERT OR REPLACE INTO secrets VALUES (?,?)",
                           (key, self.fernet.encrypt(str(value).encode()).decode()))
            row = db.execute("SELECT value FROM secrets WHERE key=?", (key,)).fetchone()
            return self.fernet.decrypt(row["value"].encode()).decode() if row else ""

    def event(self, message, clip_id=""):
        with self.connect() as db:
            db.execute("INSERT INTO events(at,message,clip_id) VALUES (?,?,?)", (time.time(), message, clip_id))

    def events(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 40")]

    def add_watch(self, login, **values):
        login = login.strip().lower().lstrip("@")
        if not re.fullmatch(r"[a-z0-9_]{1,25}", login):
            raise ValueError("Use a Twitch channel login, such as zackrawrr.")
        allowed = {"min_views", "lookback_days", "backfill", "mode", "enabled", "options"}
        if values.keys() - allowed:
            raise ValueError("Unknown watch field")
        if "options" in values:
            values["options"] = json.dumps(values["options"])
        with self.connect() as db:
            keys = ["login", *values]
            db.execute(f"INSERT INTO watches({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                       [login, *values.values()])
            row = db.execute("SELECT * FROM watches WHERE login=?", (login,)).fetchone()
            return dict(row)

    def watches(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM watches ORDER BY id DESC")]

    def watch(self, watch_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM watches WHERE id=?", (watch_id,)).fetchone()
            if row is None:
                raise ValueError("Watch not found")
            return dict(row)

    def update_watch(self, watch_id, **values):
        allowed = {"min_views", "lookback_days", "backfill", "mode", "enabled", "last_polled", "error", "options"}
        if not values or values.keys() - allowed:
            raise ValueError("Unknown or empty watch update")
        if isinstance(values.get("options"), dict):
            values["options"] = json.dumps(values["options"])
        with self.connect() as db:
            db.execute(f"UPDATE watches SET {','.join(k+'=?' for k in values)} WHERE id=?",
                       [*values.values(), watch_id])
        return self.watch(watch_id)

    def clips(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM clips ORDER BY created_at DESC,id LIMIT 500")]

    def clip(self, clip_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM clips WHERE id=?", (clip_id,)).fetchone()
            if row is None:
                raise ValueError("Clip not found")
            return dict(row)

    def update_clip(self, clip_id, **values):
        allowed = {"state", "error", "output", "duration", "views", "account_id", "account_username", "project_id"}
        if not values or values.keys() - allowed:
            raise ValueError("Unknown clip update")
        with self.connect() as db:
            db.execute(f"UPDATE clips SET {','.join(k+'=?' for k in values)} WHERE id=?",
                       [*values.values(), clip_id])

    @staticmethod
    def _pending(db):
        return db.execute(f"SELECT count(*) FROM clips WHERE state IN ({','.join('?' for _ in ACTIVE)})", ACTIVE).fetchone()[0]

    @staticmethod
    def _overlaps(db, watch_id, row):
        vod, offset = row.get("video_id"), row.get("vod_offset")
        duration = row.get("duration", 0)
        if not vod or offset is None or duration <= 0:
            return False
        states = (*ACTIVE, "published")
        for found in db.execute(f"SELECT source FROM clips WHERE watch_id=? AND state IN ({','.join('?' for _ in states)})", [watch_id, *states]):
            old = json.loads(found["source"])
            if old.get("video_id") != vod or old.get("vod_offset") is None:
                continue
            length = old.get("duration", 0)
            intersection = min(offset + duration, old["vod_offset"] + length) - max(offset, old["vod_offset"])
            if min(duration, length) > 0 and intersection / min(duration, length) >= .8:
                return True
        return False

    def observe(self, watch_id, rows):
        admitted = []
        maximum = self.settings()["max_pending"]
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            watch = dict(db.execute("SELECT * FROM watches WHERE id=?", (watch_id,)).fetchone())
            pending = self._pending(db)
            for row in sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True):
                if row["view_count"] < watch["min_views"]:
                    continue
                slug = row["id"]
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", slug):
                    raise ValueError("Twitch returned an invalid clip ID")
                if db.execute("SELECT 1 FROM clips WHERE id=?", (slug,)).fetchone():
                    db.execute("UPDATE clips SET views=? WHERE id=?", (row["view_count"], slug))
                    continue
                backfilled = not watch["initialized"]
                if backfilled and not watch["backfill"]:
                    state = "baseline"
                elif self._overlaps(db, watch_id, row):
                    state = "overlap"
                else:
                    state = "queued" if pending < maximum else "waiting"
                now = time.time()
                db.execute("""INSERT INTO clips(id,watch_id,title,views,creator,source,state,reached_at,
                           backfilled,options,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                           (slug, watch_id, row.get("title", "Viewer clip"), row["view_count"],
                            row.get("creator_name", "viewer"), json.dumps(row), state,
                            0 if backfilled else now, int(backfilled), watch["options"], now))
                if state == "queued":
                    pending += 1
                    admitted.append(slug)
                    message = "already has" if backfilled else "reached"
                    db.execute("INSERT INTO events(at,message,clip_id) VALUES (?,?,?)", (now,
                               f'{row.get("title", "Viewer clip")} {message} {row["view_count"]:,} views (target {watch["min_views"]:,})', slug))
            db.execute("UPDATE watches SET initialized=1,last_polled=?,error='' WHERE id=?", (time.time(), watch_id))
        return admitted

    def admit_waiting(self):
        maximum = self.settings()["max_pending"]
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            count = self._pending(db)
            for row in db.execute("SELECT clips.* FROM clips JOIN watches ON watches.id=clips.watch_id WHERE clips.state='waiting' AND watches.enabled=1 ORDER BY clips.created_at,clips.id").fetchall():
                if count >= maximum:
                    break
                if self._overlaps(db, row["watch_id"], json.loads(row["source"])):
                    db.execute("UPDATE clips SET state='overlap' WHERE id=?", (row["id"],))
                else:
                    db.execute("UPDATE clips SET state='queued' WHERE id=?", (row["id"],))
                    count += 1

    def queue_clip(self, clip_id):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE clips SET state='waiting',error='' WHERE id=? AND state IN ('baseline','denied','error')", (clip_id,))
        self.admit_waiting()
        return self.clip(clip_id)

    def deny(self, clip_id):
        with self.connect() as db:
            db.execute("UPDATE clips SET state='denied' WHERE id=? AND state IN ('baseline','waiting','queued','review','error')", (clip_id,))

    def claim_render(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT clips.* FROM clips JOIN watches ON watches.id=clips.watch_id WHERE clips.state='queued' AND watches.enabled=1 ORDER BY clips.created_at,clips.id LIMIT 1").fetchone()
            if row is None:
                return None
            db.execute("UPDATE clips SET state='rendering' WHERE id=?", (row["id"],))
            return dict(row)

    def destinations(self):
        return destinations.selected(self.settings())

    def destination_revision(self):
        return destinations.revision(self.destinations())

    def approve(self, clip_id, *, expected_account_id=None, expected_account_ids=None, expected_revision=None):
        settings = self.settings()
        accounts = destinations.selected(settings)
        if not accounts or not settings["woop_project_id"]:
            raise ValueError("Select the publishing profiles in Settings first.")
        ids = [a["id"] for a in accounts]
        expected = expected_account_ids if expected_account_ids is not None else ([expected_account_id] if expected_account_id is not None else None)
        if expected is not None and (len(expected) != len(ids) or set(expected) != set(ids)):
            raise ValueError("The destinations changed. Refresh and review the displayed profiles before scheduling.")
        if expected_revision is not None and expected_revision != destinations.revision(accounts):
            raise ValueError("Destination options changed. Refresh and review before scheduling.")
        destinations.post_body(accounts, media_id="check", text="check", title="check", when="2026-01-01T00:00:00Z")
        with self.connect() as db:
            db.execute("UPDATE clips SET state='sending',account_id=?,account_username=?,project_id=?,destinations=? WHERE id=? AND state='review'",
                       (accounts[0]["id"], accounts[0]["username"], settings["woop_project_id"], json.dumps(accounts), clip_id))
        return self.clip(clip_id)

    def reserve_slot(self, clip_id, *, now=None):
        settings = self.settings()
        zone = ZoneInfo(settings["timezone"])
        earliest = (now or datetime.now(UTC)).astimezone(UTC) + timedelta(minutes=17)
        hour, minute = map(int, settings["day_start"].split(":"))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT scheduled_for FROM slots WHERE clip_id=?", (clip_id,)).fetchone()
            if existing:
                return existing[0]
            reserved = [datetime.fromisoformat(r[0].replace("Z", "+00:00")) for r in db.execute("SELECT scheduled_for FROM slots")]
            day = earliest.astimezone(zone).date()
            for _ in range(366):
                anchor = datetime.combine(day, clock_time(hour, minute), zone)
                today = [t for t in reserved if t.astimezone(zone).date() == day]
                if len(today) < settings["per_day"]:
                    candidate = anchor.astimezone(UTC)
                    while candidate.astimezone(zone).date() == day:
                        if candidate >= earliest and all(abs((candidate - t).total_seconds()) >= settings["gap_hours"] * 3600 for t in reserved):
                            when = candidate.isoformat().replace("+00:00", "Z")
                            db.execute("INSERT INTO slots VALUES (?,?)", (clip_id, when))
                            return when
                        candidate += timedelta(hours=settings["gap_hours"])
                day += timedelta(days=1)
        raise ValueError("No free schedule slot within a year")

    def recover(self):
        with self.connect() as db:
            db.execute("UPDATE clips SET state='queued' WHERE state='rendering'")
            db.execute("UPDATE clips SET state='needs_check',error='Publishing was interrupted. Check WoopSocial before retrying.' WHERE state='sending'")

    def posts(self):
        with self.connect() as db:
            result = [dict(r) for r in db.execute("SELECT posts.*,clips.title,clips.state,clips.account_username,clips.destinations FROM posts JOIN clips ON clips.id=posts.clip_id ORDER BY scheduled_for")]
        for row in result:
            row["destinations"] = json.loads(row["destinations"])
            row["deliveries"] = json.loads(row["deliveries"])
        return result

    def post(self, clip_id, **values):
        allowed = {"request_id", "media_id", "scheduled_for", "post_url", "deliveries"}
        if values.keys() - allowed:
            raise ValueError("Unknown post field")
        if "deliveries" in values:
            values["deliveries"] = json.dumps(values["deliveries"])
        with self.connect() as db:
            existing = db.execute("SELECT * FROM posts WHERE clip_id=?", (clip_id,)).fetchone()
            if existing:
                if values:
                    db.execute(f"UPDATE posts SET {','.join(k+'=?' for k in values)},updated_at=? WHERE clip_id=?", [*values.values(), time.time(), clip_id])
                else:
                    db.execute("UPDATE posts SET updated_at=? WHERE clip_id=?", (time.time(), clip_id))
            else:
                db.execute("INSERT INTO posts(clip_id,scheduled_for,updated_at) VALUES (?,?,?)", (clip_id, values.get("scheduled_for", ""), time.time()))
                for key in ("request_id", "media_id", "post_url", "deliveries"):
                    if key in values:
                        db.execute(f"UPDATE posts SET {key}=? WHERE clip_id=?", (values[key], clip_id))
            row = db.execute("SELECT * FROM posts WHERE clip_id=?", (clip_id,)).fetchone()
            return dict(row)

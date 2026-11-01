"""Owner dashboard and explicit, Instagram-only publication controls."""
from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import __version__
from .engine.account import AccountError
from .engine.errors import PublishError
from .service import Service
from .store import ACTIVE, Store

STATIC = Path(__file__).parent / "static"
basic = HTTPBasic()


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SettingsInput(Input):
    twitch_client_id: str | None = Field(default=None, max_length=100, pattern=r"^[A-Za-z0-9]*$")
    woop_key: str | None = Field(default=None, max_length=8192)
    per_day: int | None = Field(default=None, ge=1, le=5)
    max_pending: int | None = Field(default=None, ge=1, le=5)
    gap_hours: int | None = Field(default=None, ge=1, le=12)
    day_start: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    timezone: str | None = Field(default=None, max_length=100)

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value):
        if value is not None:
            try:
                ZoneInfo(value)
            except (ValueError, ZoneInfoNotFoundError):
                raise ValueError("Use an IANA timezone such as America/New_York") from None
        return value


class RenderOptions(Input):
    captions: bool = True
    detect_camera: bool = True


class WatchInput(Input):
    login: str = Field(pattern=r"^@?[A-Za-z0-9_]{1,25}$")
    min_views: int = Field(default=10000, ge=0, le=10000000)
    lookback_days: int = Field(default=45, ge=1, le=90)
    backfill: bool = False
    mode: Literal["ask", "auto"] = "ask"
    enabled: bool = True
    options: RenderOptions = Field(default_factory=RenderOptions)


class WatchPatch(Input):
    min_views: int | None = Field(default=None, ge=0, le=10000000)
    lookback_days: int | None = Field(default=None, ge=1, le=90)
    backfill: bool | None = None
    mode: Literal["ask", "auto"] | None = None
    enabled: bool | None = None
    options: RenderOptions | None = None


class EnabledInput(Input):
    enabled: bool


class ProjectInput(Input):
    project_id: str = Field(default="", max_length=100, pattern=r"^\d*$")


class InstagramInput(Input):
    account_id: str = Field(max_length=100, pattern=r"^\d+$")


class FlowInput(Input):
    flow_id: str = Field(pattern=r"^[a-f0-9]{32}$")


class ClipActionInput(Input):
    account_id: str | None = Field(default=None, max_length=100, pattern=r"^\d+$")


def create_app(data_dir=None, *, password=None, start_worker=True):
    store = Store(Path(data_dir or os.environ.get("DATA_DIR", "data")))
    password = password or os.environ.get("AUTOPILOT_PASSWORD")
    if not password:
        password_path = store.directory / "owner-password.txt"
        if not password_path.exists():
            try:
                with password_path.open("x", encoding="utf-8") as stream:
                    stream.write(secrets.token_urlsafe(24))
                password_path.chmod(0o600)
            except FileExistsError:
                pass
        password = password_path.read_text(encoding="utf-8").strip()
    if len(password) < 12:
        raise ValueError("AUTOPILOT_PASSWORD must contain at least 12 characters.")
    service = Service(store)

    @asynccontextmanager
    async def lifespan(app):
        if start_worker:
            service.start()
        yield
        service.close()

    def owner(credentials: HTTPBasicCredentials = Depends(basic)):
        valid = secrets.compare_digest(credentials.username.encode(), b"owner")
        valid &= secrets.compare_digest(credentials.password.encode(), password.encode())
        if not valid:
            raise HTTPException(401, "Sign in as owner.", headers={"WWW-Authenticate": "Basic"})

    app = FastAPI(title="Clips Kitty Autopilot", version=__version__, lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store, app.state.service = store, service

    @app.middleware("http")
    async def browser_guards(request: Request, call_next):
        if request.method in {"POST", "PATCH", "PUT", "DELETE"} and request.headers.get("X-Autopilot-Action") != "1":
            return JSONResponse({"detail": "Use the dashboard to perform this action."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "media-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # Pydantic's default includes submitted inputs, which may contain keys.
        return JSONResponse({"detail": [{"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
                                        for e in error.errors()]}, status_code=422)

    @app.exception_handler(ValueError)
    async def value_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=400)

    @app.exception_handler(AccountError)
    async def account_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=400)

    @app.exception_handler(PublishError)
    async def publish_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=400)

    @app.exception_handler(sqlite3.IntegrityError)
    async def duplicate(request, error):
        return JSONResponse({"detail": "That channel or action is already saved."}, status_code=409)

    def require_connections():
        settings = store.settings()
        if not settings["twitch_client_id"] or not store.secret("twitch_token"):
            raise ValueError("Connect your Twitch viewer account in Settings first.")
        if not store.secret("woop_key") or not settings["instagram_id"]:
            raise ValueError("Connect WoopSocial and select your Instagram destination first.")

    @app.get("/health")
    def health():
        return {"app": "Clips Kitty Autopilot", "version": __version__, "ok": True}

    @app.get("/", dependencies=[Depends(owner)])
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/static/{name}", dependencies=[Depends(owner)])
    def asset(name: Literal["app.js", "app.css"]):
        return FileResponse(STATIC / name)

    @app.get("/api/status", dependencies=[Depends(owner)])
    def status():
        watches = store.watches()
        for watch in watches:
            watch["options"] = json.loads(watch["options"])
        clips = []
        for saved in store.clips():
            clip = {key: value for key, value in saved.items() if key not in {"source", "output", "options"}}
            clip["options"] = json.loads(saved["options"])
            clip["media_url"] = "/media/" + clip["id"] if saved["output"] else ""
            clip["source_url"] = "https://clips.twitch.tv/" + clip["id"]
            clips.append(clip)
        token = json.loads(store.secret("twitch_token") or "{}")
        return {"settings": store.settings(), "watches": watches, "clips": clips, "posts": store.posts(),
                "events": store.events(), "connections": {"twitch": bool(token),
                "twitch_login": token.get("identity", {}).get("login", ""), "woopsocial": bool(store.secret("woop_key"))},
                "counts": {"pending": sum(c["state"] in ACTIVE for c in clips),
                           "review": sum(c["state"] == "review" for c in clips),
                           "scheduled": sum(c["state"] == "scheduled" for c in clips),
                           "published": sum(c["state"] == "published" for c in clips)}}

    @app.post("/api/settings", dependencies=[Depends(owner)])
    def settings(data: SettingsInput):
        patch = data.model_dump(exclude_none=True)
        key = patch.pop("woop_key", None)
        if key:
            store.secret("woop_key", key.strip())
            store.settings({"accounts": [], "instagram_id": "", "instagram_username": "", "woop_project_id": ""})
        if "twitch_client_id" in patch and patch["twitch_client_id"] != store.settings()["twitch_client_id"]:
            store.secret("twitch_token", "")
            store.settings({"enabled": False})
        store.settings(patch)
        return {"saved": True}

    @app.post("/api/twitch/start", dependencies=[Depends(owner)])
    def twitch_start():
        return service.begin_twitch()

    @app.post("/api/twitch/poll", dependencies=[Depends(owner)])
    def twitch_poll(data: FlowInput):
        return service.poll_twitch(data.flow_id)

    @app.post("/api/connections", dependencies=[Depends(owner)])
    def connections(data: ProjectInput):
        return service.connections(data.project_id)

    @app.post("/api/instagram", dependencies=[Depends(owner)])
    def instagram(data: InstagramInput):
        service.select_instagram(data.account_id)
        return {"saved": True}

    @app.post("/api/automation", dependencies=[Depends(owner)])
    def automation(data: EnabledInput):
        if data.enabled:
            require_connections()
        store.settings({"enabled": data.enabled})
        service.wake.set()
        return {"enabled": data.enabled}

    @app.post("/api/watches", dependencies=[Depends(owner)])
    def add_watch(data: WatchInput):
        if data.mode == "auto":
            require_connections()
        values = data.model_dump()
        login = values.pop("login")
        result = store.add_watch(login, **values)
        service.wake.set()
        return result

    @app.patch("/api/watches/{watch_id}", dependencies=[Depends(owner)])
    def patch_watch(watch_id: int, data: WatchPatch):
        values = data.model_dump(exclude_none=True)
        if data.mode == "auto":
            require_connections()
        result = store.update_watch(watch_id, **values)
        service.wake.set()
        return result

    @app.post("/api/watches/{watch_id}/check", dependencies=[Depends(owner)])
    def check(watch_id: int):
        return service.poll_watch(watch_id)

    @app.post("/api/clips/{clip_id}/{action}", dependencies=[Depends(owner)])
    def clip_action(clip_id: str, action: Literal["queue", "approve", "deny"], data: ClipActionInput):
        store.clip(clip_id)
        if action == "queue":
            store.queue_clip(clip_id)
        elif action == "approve":
            if not data.account_id:
                raise ValueError("Review and include the selected Instagram account before scheduling.")
            store.approve(clip_id, expected_account_id=data.account_id)
        else:
            store.deny(clip_id)
        service.wake.set()
        return {"state": store.clip(clip_id)["state"]}

    @app.get("/media/{clip_id}", dependencies=[Depends(owner)])
    def video(clip_id: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", clip_id):
            raise HTTPException(404)
        output = Path(store.clip(clip_id)["output"]).resolve()
        if not output.is_relative_to(store.directory / "renders") or output.suffix != ".mp4" or not output.is_file():
            raise HTTPException(404)
        return FileResponse(output, media_type="video/mp4")

    return app

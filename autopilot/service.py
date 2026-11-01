"""Standalone orchestration; no desktop service or database is required."""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path

from . import destinations, media
from .engine.account import AccountError
from .engine.twitch import TwitchProvider
from .engine.woopsocial import PLATFORMS, WoopSocialClient
from .feed import collect_clips


class Service:
    def __init__(self, store):
        self.store = store
        self.provider = None
        self._flows = {}
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.thread = None
        self.failures = 0

    def twitch(self):
        identifier = self.store.settings()["twitch_client_id"]
        if self.provider is None or self.provider.client_id != identifier:
            if self.provider is not None:
                self.provider.close()
            self.provider = TwitchProvider(identifier)
        return self.provider

    def begin_twitch(self):
        import uuid
        result = self.twitch().begin([])
        flow_id = uuid.uuid4().hex
        self._flows = {flow_id: {**result, "expires_at": time.time() + result["expires_in"], "next": time.time()}}
        return {"flow_id": flow_id, "user_code": result["user_code"], "interval": result["interval"],
                "verification_uri": result.get("verification_uri_complete") or result["verification_uri"]}

    def poll_twitch(self, flow_id):
        flow = self._flows.get(flow_id)
        if flow is None or flow["expires_at"] < time.time():
            raise ValueError("The Twitch connection request expired. Start again.")
        if time.time() < flow["next"]:
            return {"pending": True}
        flow["next"] = time.time() + flow["interval"]
        try:
            token = self.twitch().poll(flow["device_code"])
        except AccountError as error:
            if error.code in ("authorization_pending", "slow_down"):
                if error.code == "slow_down":
                    flow["interval"] += 5
                return {"pending": True}
            raise
        identity = self.twitch().identity(token["access_token"])
        validated = self.twitch().validate(token["access_token"])
        token["expires_at"] = time.time() + min(token["expires_in"], validated["expires_in"])
        token["validated_at"] = time.time()
        token["identity"] = identity
        self.store.secret("twitch_token", json.dumps(token))
        self._flows.clear()
        self.store.event("Connected Twitch viewer @" + identity["login"])
        return {"connected": True, "login": identity["login"]}

    def perform(self, **params):
        raw = self.store.secret("twitch_token")
        if not raw:
            raise ValueError("Connect your Twitch viewer account in Settings.")
        token = json.loads(raw)
        provider = self.twitch()
        if token["expires_at"] < time.time() + 60:
            renewed = provider.refresh(token.get("refresh_token", ""))
            token.update(renewed)
            token["expires_at"] = time.time() + renewed["expires_in"]
        if token.get("validated_at", 0) < time.time() - 3600:
            provider.validate(token["access_token"])
            token["validated_at"] = time.time()
        self.store.secret("twitch_token", json.dumps(token))
        account = {"user_id": token["identity"]["id"], "scopes": token.get("scope", [])}
        return provider.perform(token["access_token"], account, "clips", **params)

    def woop(self):
        key = self.store.secret("woop_key")
        if not key:
            raise ValueError("Add your WoopSocial key in Settings.")
        return WoopSocialClient(key)

    def connections(self, project_id=""):
        client = self.woop()
        settings = self.store.settings()
        project_id = project_id or settings["woop_project_id"]
        projects = client.projects()
        if not project_id:
            if len(projects) != 1:
                return {"projects": [{"id": p["id"], "name": p.get("name", "Project")} for p in projects], "accounts": []}
            project_id = str(projects[0]["id"])
        if project_id not in {str(p["id"]) for p in projects}:
            raise ValueError("Choose a project returned by your WoopSocial account.")
        accounts = [{"id": str(a["id"]), "platform": str(a.get("platform", "")).lower(),
                     "username": str(a.get("username") or "")[:100]}
                    for a in client.social_accounts(project_id) if a.get("id") and str(a.get("status", "CONNECTED")).upper() == "CONNECTED"]
        patch = {"accounts": accounts, "woop_project_id": project_id}
        current = settings["instagram_id"]
        if not any(a["id"] == current and a["platform"] == "instagram" for a in accounts):
            patch.update(instagram_id="", instagram_username="")
        if settings["selected_account_ids"] is not None:
            available = {a["id"] for a in accounts if a["platform"] in PLATFORMS}
            patch["selected_account_ids"] = [identifier for identifier in settings["selected_account_ids"] if identifier in available]
        self.store.settings(patch)
        return {"projects": [{"id": str(p["id"]), "name": p.get("name", "Project")} for p in projects], "accounts": accounts}

    def select_instagram(self, account_id):
        settings = self.store.settings()
        account = next((a for a in settings["accounts"] if a["id"] == account_id and a["platform"] == "instagram"), None)
        if account is None:
            raise ValueError("Refresh connections and choose a connected Instagram account.")
        self.select_destinations([account_id])

    def select_destinations(self, account_ids, options=None):
        settings = self.store.settings()
        if len(account_ids) != len(set(account_ids)):
            raise ValueError("Select each profile only once.")
        roster = {a["id"]: a for a in settings["accounts"] if a["platform"] in PLATFORMS}
        if any(identifier not in roster for identifier in account_ids):
            raise ValueError("Refresh connections and select only connected publishing profiles.")
        options = options or {}
        if set(options) - set(account_ids):
            raise ValueError("Options must belong to selected profiles.")
        proposed = {**settings, "selected_account_ids": account_ids, "destination_options": options}
        if account_ids:
            destinations.post_body(destinations.selected(proposed), media_id="check", text="check", title="check", when="2026-01-01T00:00:00Z")
        instagram = next((roster[i] for i in account_ids if roster[i]["platform"] == "instagram"), {})
        self.store.settings({"selected_account_ids": account_ids, "destination_options": options,
                             "instagram_id": instagram.get("id", ""), "instagram_username": instagram.get("username", "")})

    def poll_watch(self, watch_id):
        watch = self.store.watch(watch_id)
        try:
            rows = collect_clips(self.perform, watch["login"], watch["min_views"], watch["lookback_days"])
            admitted = self.store.observe(watch_id, rows)
            self.store.event(f"Checked twitch.tv/{watch['login']}; admitted {len(admitted)} new clip(s).")
            self.wake.set()
            return {"listed": len(rows), "admitted": len(admitted)}
        except Exception as error:
            message = str(error) if isinstance(error, (ValueError, AccountError)) else "Clip listing failed. Try again shortly."
            self.store.update_watch(watch_id, last_polled=time.time(), error=message)
            raise ValueError(message) from None

    def process_one(self):
        clip = self.store.claim_render()
        if clip is None:
            return
        try:
            self.store.event("Rendering the whole viewer clip: " + clip["title"], clip["id"])
            source = media.download(clip["id"], self.store.directory / "downloads" / clip["id"])
            target = self.store.directory / "renders" / (clip["id"] + ".mp4")
            result = media.render_whole(source, target, json.loads(clip["options"]))
            self.store.update_clip(clip["id"], state="review", output=str(target), duration=result["duration"], error="")
            self.failures = 0
            self.store.event("Whole vertical clip is ready for review: " + clip["title"], clip["id"])
            watch = self.store.watch(clip["watch_id"])
            if watch["mode"] == "auto" and watch["enabled"] and self.store.settings()["enabled"]:
                try:
                    self.store.approve(clip["id"])
                except ValueError as error:
                    self.store.update_clip(clip["id"], error=str(error))
        except Exception:
            self.failures += 1
            self.store.update_clip(clip["id"], state="error", error="Processing failed. Check FFmpeg, caption model access and source availability.")
            self.store.event("Clip processing needs attention: " + clip["title"], clip["id"])
            if self.failures >= 3:
                self.store.settings({"enabled": False})
                self.store.event("Watching paused after three processing failures. Check setup before resuming.")

    def send_one(self):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM clips WHERE state='sending' ORDER BY created_at LIMIT 1").fetchone()
            if row is None:
                return
            clip = dict(row)
            # A durable hold before networking: restart or ambiguous transport never blindly resends.
            db.execute("UPDATE clips SET state='needs_check',error='Delivery is being verified.' WHERE id=?", (clip["id"],))
        try:
            client = self.woop()
            roster = {str(a["id"]): a for a in client.social_accounts(clip["project_id"]) if str(a.get("status", "CONNECTED")).upper() == "CONNECTED"}
            accounts = destinations.frozen(clip)
            if not accounts or any(a["id"] not in roster or str(roster[a["id"]].get("platform", "")).upper() != PLATFORMS[a["platform"]] for a in accounts):
                raise ValueError("An approved profile is no longer connected. Refresh Settings; destinations were not changed.")
            when = self.store.reserve_slot(clip["id"])
            post = self.store.post(clip["id"], scheduled_for=when)
            if post["request_id"]:
                raise ValueError("A provider post already exists. Check its status before retrying.")
            if post["media_id"]:
                raise ValueError("A prior send needs inspection in WoopSocial before another post can be created.")
            media_id = client.upload_media(Path(clip["output"]), clip["project_id"])
            self.store.post(clip["id"], media_id=media_id)
            watch = self.store.watch(clip["watch_id"])
            credit = f"Clipped by {clip['creator']} on twitch.tv/{watch['login']}"
            body = destinations.post_body(accounts, media_id=media_id, text=clip["title"] + "\n\n" + credit,
                                          title=clip["title"], when=when)
            validation = client.validate_post(body)
            if validation.get("isValid") is not True:
                errors = "; ".join(str(e.get("message", "Invalid destination settings")) for e in validation.get("errors", []) if isinstance(e, dict))
                raise ValueError("WoopSocial validation failed before creating a post. " + errors[:500])
            response = client.create_post(body)
            request_id = str(response.get("id") or response.get("postId") or "")
            if request_id:
                self.store.post(clip["id"], request_id=request_id)
            results = destinations.deliveries(response, accounts)
            self.store.post(clip["id"], deliveries=results)
            if not request_id or any(r["state"] in ("failed", "skipped") for r in results):
                raise ValueError("WoopSocial did not confirm this schedule. Inspect its dashboard before retrying.")
            self.store.update_clip(clip["id"], state="scheduled", error="")
            self.store.event(f"Scheduled {clip['title']} to {destinations.label(accounts)} at {when}", clip["id"])
        except Exception as error:
            message = str(error) if isinstance(error, ValueError) else "Publishing needs inspection in WoopSocial. The send was not retried."
            self.store.update_clip(clip["id"], state="needs_check", error=message)
            self.store.event(message, clip["id"])

    def refresh_posts(self):
        for post in self.store.posts():
            if post["state"] not in ("scheduled", "needs_check") or not post["request_id"]:
                continue
            if post["state"] == "needs_check" and post["deliveries"] and all(r["state"] in ("published", "failed", "skipped") for r in post["deliveries"]):
                continue
            due = datetime.fromisoformat(post["scheduled_for"].replace("Z", "+00:00")).timestamp()
            if time.time() < max(due, post["updated_at"] + 60):
                continue
            try:
                raw = self.woop().get_post(post["request_id"])
                clip = self.store.clip(post["clip_id"])
                accounts = destinations.frozen(clip)
                results = destinations.deliveries(raw, accounts)
                self.store.post(clip["id"], deliveries=results)
                if all(r["state"] == "published" for r in results):
                    self.store.update_clip(clip["id"], state="published", error="")
                    self.store.post(clip["id"], post_url=next((r["post_url"] for r in results if r["post_url"]), ""))
                    self.store.event("Published to " + destinations.label(accounts), clip["id"])
                elif any(r["state"] in ("failed", "skipped") for r in results):
                    self.store.update_clip(clip["id"], state="needs_check", error="WoopSocial reports a delivery failure on a selected profile; inspect before retrying.")
                else:
                    self.store.post(clip["id"])
            except Exception:
                self.store.post(post["clip_id"])
                self.store.event("Could not refresh a WoopSocial post; its saved schedule is retained.", post["clip_id"])

    def tick(self):
        if self.store.settings()["enabled"]:
            for watch in self.store.watches():
                if watch["enabled"] and watch["last_polled"] < time.time() - 900:
                    try:
                        self.poll_watch(watch["id"])
                    except ValueError:
                        pass
            self.store.admit_waiting()
            self.process_one()
        self.send_one()
        self.refresh_posts()

    def start(self):
        self.store.recover()
        def loop():
            while not self.stop.is_set():
                try:
                    self.tick()
                except Exception:
                    self.store.event("The worker encountered an error; saved work is retained.")
                self.wake.wait(10)
                self.wake.clear()
        self.thread = threading.Thread(target=loop, name="clips-kitty-autopilot", daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=2)

import json
import time

import pytest

from autopilot.service import Service
from autopilot.store import Store


@pytest.fixture
def service(tmp_path):
    store = Store(tmp_path)
    w = store.add_watch("fixturechannel", min_views=1, backfill=True)
    store.observe(w["id"], [{"id": "fixture", "title": "Viewer moment", "view_count": 1, "creator_name": "fixtureviewer"}])
    store.update_clip("fixture", state="review", output=str(tmp_path / "fixture.mp4"))
    (tmp_path / "fixture.mp4").write_bytes(b"fixture")
    store.settings({"instagram_id": "12", "instagram_username": "fixturebrand", "woop_project_id": "34"})
    return Service(store)


class Provider:
    def __init__(self):
        self.bodies = []
        self.uploads = 0
        self.ambiguous = False

    def social_accounts(self, project_id):
        return [{"id": "12", "platform": "INSTAGRAM", "username": "fixturebrand"},
                {"id": "56", "platform": "TIKTOK", "username": "otherfixture"}]

    def upload_media(self, path, project_id):
        self.uploads += 1
        return "78"

    def create_post(self, body):
        self.bodies.append(body)
        if self.ambiguous:
            raise TimeoutError("fixture lost response")
        return {"id": "90", "socialAccountPosts": [{"socialAccountId": "12", "platform": "INSTAGRAM", "deliveryStatus": "NOT_STARTED"}]}

    def validate_post(self, body):
        return {"isValid": True, "errors": [], "warnings": []}


def test_explicit_approval_schedules_once_to_frozen_instagram(service, monkeypatch):
    provider = Provider()
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("fixture")
    service.store.settings({"instagram_id": "56", "instagram_username": "changedfixture"})
    service.send_one()
    service.store.approve("fixture")
    service.send_one()
    assert provider.uploads == len(provider.bodies) == 1
    body = provider.bodies[0]
    assert body["socialAccounts"] == [{"platform": "INSTAGRAM", "socialAccountId": "12", "postType": "REEL"}]
    assert body["schedule"]["type"] == "SCHEDULE_FOR_LATER"
    assert "Clipped by fixtureviewer on twitch.tv/fixturechannel" in body["content"][0]["text"]
    assert service.store.clip("fixture")["state"] == "scheduled"


def test_ambiguous_remote_send_is_never_retried(service, monkeypatch):
    provider = Provider()
    provider.ambiguous = True
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("fixture")
    service.send_one()
    service.store.recover()
    service.store.queue_clip("fixture")
    service.store.approve("fixture")
    service.send_one()
    assert len(provider.bodies) == 1
    assert service.store.clip("fixture")["state"] == "needs_check"
    assert service.store.posts()[0]["media_id"] == "78"


def test_disconnected_approved_destination_never_switches_accounts(service, monkeypatch):
    provider = Provider()
    monkeypatch.setattr(provider, "social_accounts", lambda project: [{"id": "99", "platform": "INSTAGRAM"}])
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("fixture")
    service.send_one()
    assert provider.bodies == [] and provider.uploads == 0
    assert service.store.clip("fixture")["state"] == "needs_check"


def test_viewer_identity_is_adapted_to_sdk_account_contract(service, monkeypatch):
    class Twitch:
        def perform(self, token, account, operation, **params):
            assert account == {"user_id": "123", "scopes": []}
            assert operation == "clips" and params["broadcaster_login"] == "fixturechannel"
            return {"clips": []}
    service.store.secret("twitch_token", json.dumps({"access_token": "fixture", "identity": {"id": "123"},
                                                   "expires_at": time.time() + 3600, "validated_at": time.time()}))
    monkeypatch.setattr(service, "twitch", lambda: Twitch())
    assert service.perform(broadcaster_login="fixturechannel") == {"clips": []}


def test_pausing_during_render_prevents_automatic_scheduling(service, monkeypatch):
    store = service.store
    w = store.watches()[0]
    store.update_watch(w["id"], mode="auto")
    store.update_clip("fixture", state="queued")
    store.settings({"enabled": True})
    monkeypatch.setattr("autopilot.media.download", lambda *args: "fixture")
    def render(*args):
        store.settings({"enabled": False})
        return {"duration": 30}
    monkeypatch.setattr("autopilot.media.render_whole", render)
    service.process_one()
    assert store.clip("fixture")["state"] == "review"

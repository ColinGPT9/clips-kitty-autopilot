import json
import time

import pytest

from autopilot.service import Service
from autopilot.store import Store


def ready(tmp_path):
    store = Store(tmp_path)
    watch = store.add_watch("fixture", min_views=1, backfill=True)
    store.observe(watch["id"], [{"id": "moment", "view_count": 1, "title": "Moment", "creator_name": "viewer"}])
    path = tmp_path / "moment.mp4"
    path.write_bytes(b"fixture")
    store.update_clip("moment", state="review", output=str(path))
    store.settings({"woop_project_id": "project", "instagram_id": "ig", "instagram_username": "kitty",
                    "accounts": [{"id": "ig", "platform": "instagram", "username": "kitty"},
                                 {"id": "tt", "platform": "tiktok", "username": "kitty"}]})
    return Service(store)


class Provider:
    def __init__(self, accounts):
        self.accounts = [{**a, "platform": a["platform"].upper()} for a in accounts]
        self.bodies = []
        self.uploads = 0
        self.statuses = {}

    def social_accounts(self, project):
        return self.accounts

    def upload_media(self, path, project):
        self.uploads += 1
        return "media"

    def create_post(self, body):
        self.bodies.append(body)
        return self.get_post("request")

    def validate_post(self, body):
        assert "projectId" not in body, "The documented validate/create schema derives the project from the selected profiles"
        return {"isValid": True, "errors": [], "warnings": []}

    def get_post(self, identifier):
        return {"id": "request", "socialAccountPosts": [
            {"socialAccountId": a["socialAccountId"], "platform": a["platform"],
             "deliveryStatus": self.statuses.get(a["socialAccountId"], "NOT_STARTED"),
             "externalPostUrl": "https://example.com/" + a["socialAccountId"]}
            for a in self.bodies[0]["socialAccounts"]]}


def test_existing_instagram_selection_does_not_enable_connected_tiktok(tmp_path):
    service = ready(tmp_path)
    assert [a["id"] for a in service.store.destinations()] == ["ig"]


def test_one_upload_schedules_only_frozen_selected_profiles(tmp_path, monkeypatch):
    service = ready(tmp_path)
    service.select_destinations(["ig", "tt"])
    provider = Provider(service.store.settings()["accounts"])
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("moment", expected_account_ids=["ig", "tt"])
    service.select_destinations(["ig"])
    service.send_one()
    assert provider.uploads == len(provider.bodies) == 1
    assert {a["socialAccountId"] for a in provider.bodies[0]["socialAccounts"]} == {"ig", "tt"}
    assert service.store.clip("moment")["state"] == "scheduled"
    service.send_one()
    assert len(provider.bodies) == 1


def test_stale_profile_selection_and_legacy_client_cannot_approve_extra_profiles(tmp_path):
    service = ready(tmp_path)
    service.select_destinations(["ig", "tt"])
    with pytest.raises(ValueError, match="changed"):
        service.store.approve("moment", expected_account_ids=["ig"])
    with pytest.raises(ValueError, match="changed"):
        service.store.approve("moment", expected_account_id="ig")
    assert service.store.clip("moment")["state"] == "review"


def test_pinterest_board_is_required_and_frozen_per_account(tmp_path, monkeypatch):
    service = ready(tmp_path)
    accounts = [{"id": "pin1", "platform": "pinterest", "username": "one"},
                {"id": "pin2", "platform": "pinterest", "username": "two"}]
    service.store.settings({"accounts": accounts})
    with pytest.raises(ValueError, match="board"):
        service.select_destinations(["pin1"])
    service.select_destinations(["pin1", "pin2"], {"pin1": {"pinterestBoardId": "board1"}, "pin2": {"pinterestBoardId": "board2"}})
    provider = Provider(accounts)
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("moment")
    service.send_one()
    assert [a["pinterestBoardId"] for a in provider.bodies[0]["socialAccounts"]] == ["board1", "board2"]


def test_all_documented_platforms_can_be_explicitly_selected(tmp_path, monkeypatch):
    service = ready(tmp_path)
    platforms = ["instagram", "tiktok", "youtube", "facebook", "x", "threads", "linkedin", "linkedin_pages", "pinterest", "bluesky", "wooptest"]
    accounts = [{"id": str(i), "platform": p, "username": p} for i, p in enumerate(platforms)]
    service.store.settings({"accounts": accounts})
    service.select_destinations([a["id"] for a in accounts], {"8": {"pinterestBoardId": "board"}})
    provider = Provider(accounts)
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("moment")
    service.send_one()
    assert service.store.clip("moment")["state"] == "scheduled"
    assert len(provider.bodies[0]["socialAccounts"]) == len(platforms)


def test_partial_failure_keeps_individual_results_and_never_resends(tmp_path, monkeypatch):
    service = ready(tmp_path)
    service.select_destinations(["ig", "tt"])
    provider = Provider(service.store.settings()["accounts"])
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("moment")
    service.send_one()
    service.store.post("moment", scheduled_for="2026-01-01T00:00:00Z")
    with service.store.connect() as db:
        db.execute("UPDATE posts SET updated_at=?", (time.time()-120,))
    provider.statuses = {"ig": "PUBLISHED", "tt": "FAILED"}
    service.refresh_posts()
    post = service.store.posts()[0]
    assert {a["account_id"]: a["state"] for a in post["deliveries"]} == {"ig": "published", "tt": "failed"}
    assert service.store.clip("moment")["state"] == "needs_check"
    service.store.recover()
    service.send_one()
    assert len(provider.bodies) == 1


def test_disconnected_one_of_multiple_approved_profiles_blocks_upload(tmp_path, monkeypatch):
    service = ready(tmp_path)
    service.select_destinations(["ig", "tt"])
    service.store.approve("moment")
    provider = Provider([service.store.settings()["accounts"][0]])
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.send_one()
    assert provider.uploads == 0
    assert service.store.clip("moment")["state"] == "needs_check"


def test_destination_options_change_invalidates_visible_approval(tmp_path):
    service = ready(tmp_path)
    service.select_destinations(["tt"])
    revision = service.store.destination_revision()
    service.select_destinations(["tt"], {"tt": {"privacyLevel": "SELF_ONLY"}})
    with pytest.raises(ValueError, match="changed"):
        service.store.approve("moment", expected_account_ids=["tt"], expected_revision=revision)


def test_destination_snapshot_is_durable_across_store_restart(tmp_path):
    service = ready(tmp_path)
    service.select_destinations(["ig", "tt"])
    service.store.approve("moment")
    store = Store(tmp_path)
    assert {a["id"] for a in json.loads(store.clip("moment")["destinations"])} == {"ig", "tt"}


def test_api_requires_review_of_exact_selected_profiles_and_options(tmp_path):
    from fastapi.testclient import TestClient

    from autopilot.app import create_app

    app = create_app(tmp_path, password="fixture-password", start_worker=False)
    with TestClient(app) as client:
        client.auth = ("owner", "fixture-password")
        client.headers["X-Autopilot-Action"] = "1"
        store = app.state.store
        store.settings({"woop_project_id": "project", "accounts": [
            {"id": "ig", "platform": "instagram", "username": "kitty"},
            {"id": "tt", "platform": "tiktok", "username": "kitty"}]})
        assert client.post("/api/destinations", json={"account_ids": ["ig", "tt"]}).status_code == 200
        state = client.get("/api/status").json()
        assert len(state["settings"]["selected_destinations"]) == 2
        w = store.add_watch("fixture", min_views=1, backfill=True)
        store.observe(w["id"], [{"id": "moment", "view_count": 1}])
        store.update_clip("moment", state="review")
        assert client.post("/api/clips/moment/approve", json={"account_ids": ["ig", "tt"]}).status_code == 400
        body = {"account_ids": ["ig", "tt"], "destination_revision": state["settings"]["destination_revision"]}
        assert client.post("/api/clips/moment/approve", json=body).status_code == 200
        assert len(json.loads(store.clip("moment")["destinations"])) == 2
        assert client.post("/api/destinations", json={"account_ids": ["not-connected"]}).status_code == 400
        assert client.post("/api/destinations", json={"account_ids": ["ig"], "options": {"ig": {"unknown": True}}}).status_code == 422


def test_provider_validation_error_never_creates_or_retries_a_post(tmp_path, monkeypatch):
    service = ready(tmp_path)
    provider = Provider(service.store.settings()["accounts"])
    monkeypatch.setattr(service, "woop", lambda: provider)
    monkeypatch.setattr(provider, "validate_post", lambda body: {"isValid": False, "errors": [{"message": "Video duration exceeds this profile's limit"}]})
    service.store.approve("moment")
    service.send_one()
    service.send_one()
    assert provider.bodies == []
    assert "Video duration" in service.store.clip("moment")["error"]
    assert service.store.clip("moment")["state"] == "needs_check"


def test_provider_disconnected_status_blocks_an_approved_profile(tmp_path, monkeypatch):
    service = ready(tmp_path)
    provider = Provider(service.store.settings()["accounts"])
    provider.accounts[0]["status"] = "DISCONNECTED"
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("moment")
    service.send_one()
    assert provider.uploads == 0


def test_refreshing_connections_never_selects_other_connected_profiles(tmp_path, monkeypatch):
    service = ready(tmp_path)
    provider = Provider(service.store.settings()["accounts"] + [{"id": "yt", "platform": "youtube", "username": "kitty"}])
    provider.projects = lambda: [{"id": "project", "name": "Fixture"}]
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.connections()
    assert [a["id"] for a in service.store.destinations()] == ["ig"]


def test_two_profiles_on_same_platform_keep_separate_delivery_links(tmp_path, monkeypatch):
    service = ready(tmp_path)
    accounts = [{"id": "one", "platform": "instagram", "username": "first"},
                {"id": "two", "platform": "instagram", "username": "second"}]
    service.store.settings({"accounts": accounts})
    service.select_destinations(["one", "two"])
    provider = Provider(accounts)
    monkeypatch.setattr(service, "woop", lambda: provider)
    service.store.approve("moment")
    service.send_one()
    service.store.post("moment", scheduled_for="2026-01-01T00:00:00Z")
    with service.store.connect() as db:
        db.execute("UPDATE posts SET updated_at=?", (time.time()-120,))
    provider.statuses = {"one": "PUBLISHED", "two": "PUBLISHED"}
    service.refresh_posts()
    assert service.store.clip("moment")["state"] == "published"
    assert {a["account_id"]: a["post_url"] for a in service.store.posts()[0]["deliveries"]} == {
        "one": "https://example.com/one", "two": "https://example.com/two"}


def test_missing_provider_child_is_held_with_request_id_and_never_resent(tmp_path, monkeypatch):
    service = ready(tmp_path)
    service.select_destinations(["ig", "tt"])
    provider = Provider(service.store.settings()["accounts"])
    monkeypatch.setattr(service, "woop", lambda: provider)
    get_post = provider.get_post
    monkeypatch.setattr(provider, "get_post", lambda identifier: {**get_post(identifier), "socialAccountPosts": get_post(identifier)["socialAccountPosts"][:1]})
    service.store.approve("moment")
    service.send_one()
    assert service.store.clip("moment")["state"] == "needs_check"
    assert service.store.posts()[0]["request_id"] == "request"
    service.store.recover()
    service.send_one()
    assert len(provider.bodies) == 1

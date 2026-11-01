import json

import pytest
from fastapi.testclient import TestClient

from autopilot.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, password="fixture-password", start_worker=False)
    with TestClient(app) as client:
        client.auth = ("owner", "fixture-password")
        client.headers["X-Autopilot-Action"] = "1"
        yield client


def test_owner_auth_and_csrf(client):
    assert client.get("/health", auth=("", "")).status_code == 200
    assert client.get("/api/status", auth=("", "")).status_code == 401
    assert client.post("/api/automation", json={"enabled": True}, headers={"X-Autopilot-Action": ""}).status_code == 403
    assert client.get("/").status_code == 200
    assert "Clips Kitty Autopilot" in client.get("/").text


def test_defaults_and_secret_validation(client):
    response = client.post("/api/settings", json={"woop_key": "fixture-private-key", "per_day": 5})
    assert response.status_code == 200
    state = client.get("/api/status").json()
    assert state["settings"]["per_day"] == state["settings"]["max_pending"] == 5
    assert state["settings"]["enabled"] is False
    assert state["connections"]["woopsocial"] is True
    assert "fixture-private-key" not in json.dumps(state)
    bad = client.post("/api/settings", json={"woop_key": "super-private", "per_day": 6})
    assert bad.status_code == 422
    assert "super-private" not in bad.text


def test_watch_validation_and_edits(client):
    assert client.post("/api/watches", json={"login": "https://evil.test"}).status_code == 422
    response = client.post("/api/watches", json={"login": "fixturechannel", "min_views": 25})
    assert response.status_code == 200
    identifier = response.json()["id"]
    assert client.patch(f"/api/watches/{identifier}", json={"min_views": 40}).status_code == 200
    state = client.get("/api/status").json()
    assert state["watches"][0]["min_views"] == 40
    assert state["watches"][0]["options"]["captions"] is True
    assert client.post("/api/watches", json={"login": "fixturechannel"}).status_code == 409


def test_media_is_not_arbitrary_file_access(client):
    assert client.get("/media/not-a-clip").status_code == 400
    store = client.app.state.store
    watch = store.add_watch("fixturechannel", min_views=1, backfill=True)
    store.observe(watch["id"], [{"id": "fixture", "title": "test", "view_count": 1}])
    store.update_clip("fixture", output=str(store.directory / "encryption.key"))
    assert client.get("/media/fixture").status_code == 404


def test_missing_integrations_block_automatic_mode(client):
    assert client.post("/api/watches", json={"login": "fixturechannel", "mode": "auto"}).status_code == 400
    assert client.post("/api/automation", json={"enabled": True}).status_code == 400


def test_stale_destination_is_refused_before_publication(client):
    store = client.app.state.store
    w = store.add_watch("fixturechannel", min_views=1, backfill=True)
    store.observe(w["id"], [{"id": "fixture", "view_count": 1}])
    store.update_clip("fixture", state="review")
    store.settings({"instagram_id": "34", "instagram_username": "changedfixture", "woop_project_id": "56"})
    response = client.post("/api/clips/fixture/approve", json={"account_id": "12"})
    assert response.status_code == 400
    assert store.clip("fixture")["state"] == "review"


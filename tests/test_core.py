from datetime import UTC, datetime

import pytest

from autopilot.feed import collect_clips
from autopilot.store import Store


def clip(slug="fixture", views=10, offset=20):
    return {"id": slug, "title": "Viewer's moment", "view_count": views,
            "created_at": "2026-10-30T12:00:00Z", "duration": 30.0,
            "creator_name": "fixtureviewer", "video_id": "fixturevod", "vod_offset": offset}


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


def test_baseline_and_crossing_survive_reopen(store):
    watch = store.add_watch("fixturechannel", min_views=10)
    assert store.observe(watch["id"], [clip(views=9)]) == []
    assert store.clips() == []
    assert store.observe(watch["id"], [clip(views=10)]) == ["fixture"]
    assert store.observe(watch["id"], [clip(views=11)]) == []
    reopened = Store(store.directory)
    assert reopened.observe(watch["id"], [clip(views=12)]) == []
    assert len(reopened.clips()) == 1
    assert reopened.clip("fixture")["reached_at"] > 0
    assert reopened.claim_render()["id"] == "fixture"
    assert reopened.claim_render() is None


def test_first_look_is_earlier_unless_backfill_chosen(store):
    w = store.add_watch("baselinechannel", min_views=10)
    store.observe(w["id"], [clip()])
    assert store.clip("fixture")["state"] == "baseline"
    assert store.clip("fixture")["reached_at"] == 0
    assert store.claim_render() is None
    store.queue_clip("fixture")
    store.queue_clip("fixture")
    assert store.claim_render()["id"] == "fixture"
    assert store.claim_render() is None


def test_busy_channel_keeps_five_pending_and_backfill_provenance(store):
    w = store.add_watch("busyfixture", min_views=10, backfill=True)
    store.observe(w["id"], [clip(str(i), offset=i * 100) for i in range(9)])
    assert sum(c["state"] == "queued" for c in store.clips()) == 5
    assert sum(c["state"] == "waiting" for c in store.clips()) == 4
    assert all(c["reached_at"] == 0 for c in store.clips())
    store.deny("0")
    store.admit_waiting()
    assert sum(c["state"] == "queued" for c in store.clips()) == 5
    assert all(c["reached_at"] == 0 for c in store.clips())


def test_overlapping_vod_moment_is_skipped(store):
    w = store.add_watch("fixturechannel", min_views=10, backfill=True)
    store.observe(w["id"], [clip("first"), clip("second", offset=21)])
    assert sorted(c["state"] for c in store.clips()) == ["overlap", "queued"]


def test_edited_target_applies_on_next_poll(store):
    w = store.add_watch("fixturechannel", min_views=50)
    store.observe(w["id"], [clip(views=20)])
    store.update_watch(w["id"], min_views=10)
    assert store.observe(w["id"], [clip(views=20)]) == ["fixture"]


def test_daily_slots_are_shared_and_dst_aware(store):
    store.settings({"day_start": "09:00", "timezone": "America/New_York"})
    now = datetime(2026, 11, 1, 4, 30, tzinfo=UTC)
    slots = [store.reserve_slot(str(i), now=now) for i in range(6)]
    assert slots[0] == "2026-11-01T14:00:00Z"
    assert slots[4] == "2026-11-01T18:00:00Z"
    assert slots[5] == "2026-11-02T14:00:00Z"
    assert store.reserve_slot("0", now=now) == slots[0]


def test_post_ambiguity_is_held_across_restart(store):
    w = store.add_watch("fixturechannel", min_views=10, backfill=True)
    store.observe(w["id"], [clip()])
    store.update_clip("fixture", state="sending")
    store.recover()
    assert store.clip("fixture")["state"] == "needs_check"
    assert store.claim_render() is None


def test_tokens_are_encrypted_and_not_in_public_state(store):
    secret = "fixture-secret-" + "a" * 30
    store.secret("woop_key", secret)
    assert store.secret("woop_key") == secret
    assert secret.encode() not in store.db_path.read_bytes()
    assert secret not in str(store.settings())


def test_clip_pagination_stops_below_target_and_splits_saturation():
    calls = []
    def perform(**params):
        calls.append(params)
        return {"clips": [clip(views=9)], "cursor": "not-needed"}
    assert collect_clips(perform, "fixturechannel", 10, 1, now=1793400000) == []
    assert len(calls) == 1


def test_saturated_window_is_bisected_instead_of_truncated():
    calls = []
    def perform(**params):
        calls.append(params)
        if params["started_at"] == "2026-10-30T00:00:00Z" and params["ended_at"] == "2026-10-31T00:00:00Z":
            return {"clips": [clip(str(i)) for i in range(100)], "cursor": str(len(calls))}
        return {"clips": [clip("unique")], "cursor": ""}
    rows = collect_clips(perform, "fixturechannel", 10, 1, now=1793404800)
    assert len(rows) == 1
    assert len(calls) == 12

"""Window splitting adapted from Clips Kitty's in-period viewer-clip feed."""
import time
from datetime import UTC, datetime


def collect_clips(perform, channel, min_views, lookback_days, *, now=None):
    end = int(time.time() if now is None else now)
    beginning = end - max(1, min(90, lookback_days)) * 86400
    windows = [(max(beginning, stop - 86400), stop) for stop in range(end, beginning, -86400)]
    found = {}
    while windows:
        start, stop = windows.pop(0)
        cursor, cursors, count, rows = "", set(), 0, []
        while True:
            params = {"broadcaster_login": channel, "first": 100,
                      "started_at": datetime.fromtimestamp(start, UTC).isoformat().replace("+00:00", "Z"),
                      "ended_at": datetime.fromtimestamp(stop, UTC).isoformat().replace("+00:00", "Z")}
            if cursor:
                params["after"] = cursor
            result = perform(**params)
            page = result.get("clips")
            if not isinstance(page, list):
                raise ValueError("Twitch did not return a clip listing")
            count += len(page)
            under = False
            for row in page:
                if row["view_count"] < min_views:
                    under = True
                    break
                rows.append(row)
            cursor = result.get("cursor", "")
            if under or not cursor or count >= 1000:
                break
            if cursor in cursors:
                raise ValueError("Twitch repeated a clip page")
            cursors.add(cursor)
        if count >= 1000:
            if stop - start <= 1:
                raise ValueError("Too many clips in one second; raise the view target")
            middle = (start + stop) // 2
            windows[:0] = [(middle, stop), (start, middle)]
            continue
        for row in rows:
            found[row["id"]] = row
    return sorted(found.values(), key=lambda r: r.get("created_at", ""), reverse=True)

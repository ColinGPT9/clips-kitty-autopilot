"""Explicit account selection and frozen, account-specific publishing options."""
import hashlib
import json

from .engine.woopsocial import PLATFORMS, build_post, parse_post

NAMES = {"instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube", "facebook": "Facebook",
         "x": "X", "threads": "Threads", "linkedin": "LinkedIn", "linkedin_pages": "LinkedIn Page",
         "pinterest": "Pinterest", "bluesky": "Bluesky", "wooptest": "WoopSocial Test"}
OPTION_KEYS = {"pinterestBoardId", "privacy", "privacyLevel", "allowComment", "allowDuet", "allowStitch",
               "isYourBrand", "isBrandedContent", "autoAddMusic", "madeForKids"}
PLATFORM_OPTIONS = {"youtube": {"privacy", "madeForKids"}, "pinterest": {"pinterestBoardId"},
                    "tiktok": {"privacyLevel", "allowComment", "allowDuet", "allowStitch", "isYourBrand", "isBrandedContent", "autoAddMusic"}}


def label(accounts):
    return ", ".join(f"{NAMES.get(a['platform'], a['platform'])} @{a.get('username') or a['id']}" for a in accounts)


def selected(settings):
    ids = settings.get("selected_account_ids")
    if ids is None:
        return ([{"id": settings["instagram_id"], "platform": "instagram", "username": settings["instagram_username"], "options": {}}]
                if settings.get("instagram_id") else [])
    roster = {str(a["id"]): a for a in settings["accounts"]}
    result = []
    for identifier in ids:
        account = roster.get(identifier)
        if account is None or account["platform"] not in PLATFORMS:
            raise ValueError("A selected profile is no longer connected. Refresh connections and review your destinations.")
        result.append({"id": identifier, "platform": account["platform"], "username": account.get("username", ""),
                       "options": settings.get("destination_options", {}).get(identifier, {})})
    return result


def revision(accounts):
    return hashlib.sha256(json.dumps(accounts, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def frozen(clip):
    accounts = json.loads(clip.get("destinations") or "[]")
    if accounts:
        return accounts
    return ([{"id": clip["account_id"], "platform": "instagram", "username": clip["account_username"], "options": {}}]
            if clip.get("account_id") else [])


def post_body(accounts, *, media_id, text, title, when):
    children = []
    for account in accounts:
        platform = account["platform"]
        if platform not in PLATFORMS:
            raise ValueError("A selected platform is not supported by this WoopSocial adapter.")
        options = account.get("options", {})
        if set(options) - OPTION_KEYS:
            raise ValueError("Unknown destination option")
        if set(options) - PLATFORM_OPTIONS.get(platform, set()):
            raise ValueError("These destination options do not apply to the selected platform.")
        raw = {**account, "platform": PLATFORMS[platform]}
        body = build_post(media_id=media_id, text=text, accounts=[raw], title=title, scheduled_for=when,
                          overrides={platform: options})
        if len(body["socialAccounts"]) != 1:
            raise ValueError("Choose a Pinterest board for every selected Pinterest profile.")
        children.extend(body["socialAccounts"])
    if not children:
        raise ValueError("Select at least one publishing profile in Settings.")
    body["socialAccounts"] = children
    return body


def deliveries(raw, accounts):
    if not accounts:
        raise ValueError("The approved destination snapshot is missing. Inspect WoopSocial before retrying.")
    children = raw.get("socialAccountPosts", [])
    wanted = {a["id"]: a for a in accounts}
    if len(children) != len(wanted) or {str(a.get("socialAccountId")) for a in children} != set(wanted):
        raise ValueError("WoopSocial did not confirm every approved destination. Inspect its dashboard.")
    result = []
    for child in children:
        identifier = str(child["socialAccountId"])
        account = wanted[identifier]
        if str(child.get("platform", "")).upper() != PLATFORMS[account["platform"]]:
            raise ValueError("Provider destination did not match the approved profile")
        parsed = parse_post({"socialAccountPosts": [child]})
        if len(parsed.outcomes) != 1:
            raise ValueError("WoopSocial returned an unknown delivery result")
        outcome = parsed.outcomes[0]
        result.append({"account_id": identifier, "platform": account["platform"], "username": account["username"],
                       "state": outcome.state, "post_url": outcome.post_url, "error": outcome.error})
    return result

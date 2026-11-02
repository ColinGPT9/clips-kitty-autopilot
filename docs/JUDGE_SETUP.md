# Judge setup: Clips Kitty Autopilot

Code: https://github.com/ColinGPT9/clips-kitty-autopilot

Demo: https://youtu.be/_9trPSK_6gE

This is a self-hosted, BYOK browser application. No source checkout of the earlier Clips Kitty application is required. The public repository contains the independent app and its disclosed reusable libraries. There is no shared paid account, bundled provider key or public demo login. See [provenance](../PROVENANCE.md) and [BYOK details](BYOK.md).

## Inspect the app without provider credentials

Follow the [local README setup](../README.md#run-locally) or Docker instructions. Set your own app password, start the app and open `http://127.0.0.1:8877`. Username is `owner`; use your configured or installation-generated password. A fresh installation has no connected accounts, selected profiles or scheduled work, and automation is paused. Browsing the dashboard does not publish a post.

## Offline checks

With Python 3.11+ and a virtual environment activated, install development dependencies and run the platform subset:

```bash
python -m pip install -e '.[dev]'
python -m pytest -m 'not media'
```

This validates feed/state/provider logic with synthetic fixtures and offline provider fakes, without Twitch or WoopSocial credentials and without public posts. It is test evidence, not a simulated live demonstration. The current subset passes 213 tests. For the complete 217-test suite, install FFmpeg/FFprobe on PATH and run `python -m pytest`; four cases perform real media rendering/decoding. Model inference checks additionally run in CI's 3 GiB CPU container; see [validation](VALIDATION.md).

## Live Twitch and whole-clip preview

1. Install media dependencies with `python -m pip install -e '.[dev,media]'`, or use the documented Docker image. Local model inference runs on CPU; a 4 GB RAM server was used for cloud checks. First use downloads models and processing can take several minutes.
2. In Settings, enter your own public Twitch application Client ID, choose Connect Twitch and complete device authorization using your own viewer account.
3. Save your own WoopSocial key, refresh connections, choose your project and explicitly select the social profiles you want. Only selected profiles receive posts.
4. Add a channel whose media you are authorized to process. Choose a view target and lookback, and retain **Ask First** with backfill off for an unposted preview test.
5. Choose Check now. Clips already over the target on first observation appear under Earlier clips. Choose Clip this for an earlier clip, then Start watching to allow rendering. An earlier clip or edited target is not a natural view-count crossing.
6. Preview the completed whole vertical clip. Pause watching after the test. In Ask First mode, leave Schedule untouched to keep the output unposted.

## Publication behavior

Schedule is a real approval to create a provider post for the displayed selected profiles. Automatic mode is a separate explicit opt-in: eligible completed clips are approved and scheduled without per-clip review. WoopSocial handles delivery to connected social accounts, using the installer's allowances. The default budget is five clips per day and five upcoming, shared across channels. Changed settings do not redirect already-approved work, and ambiguous/partial delivery is held for inspection instead of automatically resent.

Damage Control only opens a preview dialog. It performs no deletion, takedown or attorney contact. The demonstration's extra lawyer-notice wording is a local video caption edit; the feature's behavior is unchanged.

## Demonstration and provenance notes

The new app's live tests covered real Twitch reads on two channels, target edits, deduplication and whole Gaming renders. Those cloud clips remained unposted. A new natural crossing and live publication from the standalone deployment are not claimed. The Clips Kitty Instagram recording in the video is a labeled previously published example. The reused foundation, adapted files, source revision and licenses are documented in PROVENANCE.md.

For HTTPS hosting on your own account, use the [AWS walkthrough](AWS_SETUP.md). Do not publish provider keys, server passwords or runtime data in a submission or issue.

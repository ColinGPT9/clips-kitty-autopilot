# Standalone cloud test evidence

Observed November 1, 2026. Times below use UTC to avoid ambiguity during the US daylight-saving change.

## Deployment and connections

- Owner deployed this repository on an AWS Lightsail Ubuntu instance in Ohio (`us-east-2a`): 4 GB RAM, 2 vCPU, 80 GB disk.
- HTTPS was checked on a private demonstration deployment. Its address and credentials are omitted from these public instructions. Installers use their own server and provider accounts; see [BYOK setup](BYOK.md).
- Verified HTTPS certificate, HTTP-to-HTTPS redirect, successful health response, and unauthenticated rejection of the private status endpoint.
- The independent app connected a Twitch viewer account through device authorization and selected the project's test Instagram profile through WoopSocial. No YouTube or TikTok destination was selected or sent a post.
- Instagram-only was the owner's live-test choice. Version 0.1.3 adds explicit multi-profile selection across WoopSocial's documented networks; additional profiles remain unselected unless the owner chooses them. This support is covered by offline tests, with no claim of new live delivery on those networks.
- Shared limits are five daily posts and five upcoming clips. The test watch uses **Ask first**.

## Twitch read and whole Gaming render

1. A read of `zackrawrr` viewer clips, one-day lookback and a two-view test target returned 15 real clips. All were already above the target on first observation. They were recorded as Earlier clips, with no new crossing claimed.
2. The owner-authorized test queued the existing clip **“What you doing?”**, Twitch ID `TameAbstrusePeppermintKippa-h1F6KV6x2gCYHTTN`. This is an earlier-clip render test, not evidence of a natural target crossing.
3. Cloud processing began at approximately **07:59:46 UTC** and completed at **08:10:08 UTC**, about 10 minutes 22 seconds. Models and media ran on the Lightsail CPU deployment.
4. Downloaded output measured **60.100 seconds, 1080×1920**, with audio. Full-file FFmpeg decoding passed. Visual inspection confirmed separate streamer camera and gameplay regions, plus generated captions.
5. Inspection also found generated bottom captions overlapping subtitles already burned into the source. Source correction `810d23e` moves generated captions above the gameplay divider in split layouts. The owner installed the update and confirmed its import check. The corrected cloud rerender ran from **08:48:20 UTC to 08:58:18 UTC**, about 9 minutes 57 seconds.
6. The corrected output again measured **60.100 seconds, 1080×1920, with audio**, and passed full-file decoding. Visual checks at 3, 12, 25 and 48 seconds confirmed that generated captions clear the gameplay divider while existing source subtitles stay intact. Output SHA-256: `cd98364bb25fbc8c5ed126f78a943efe10518a7005b402eabae35e1be473e5dd`.

Watching was paused again after the corrected render. The last verified state had one clip ready for review, zero scheduled posts and zero published posts. No public scheduling request was sent from this new app. Actual authenticated browser footage captured the correct Instagram destination, five/five limits, Earlier clips, completed preview playback and the request-free satire popup; no synthetic API responses or UI counts were used.

## Second-channel private test: LIRIK

At 09:07 UTC the standalone cloud app read real `lirik` clips with a one-day lookback and target of 50 views. The 285-view clip became Earlier; clips with 46 and 19 views were not recorded. The target was then edited to 20. The unchanged 46-view clip qualified and entered the queue once. Two further checks each admitted zero clips, and the 19-view clip remained absent. This was admission after a target change, **not natural view-count growth**.

The admitted clip (`FineSplendidShrimpKevinTurtle-GEPiRvC999bpNCVl`) rendered from approximately 09:07:21 to 09:09:35 UTC, about 2 minutes 14 seconds. Output measured **15.900 seconds, 1080×1920, with audio**, and full-file decoding passed. Visual checks at 3, 8 and 13 seconds confirmed the no-camera whole-source layout and generated captions. No game character was promoted to a webcam. Output SHA-256: `13ca94b4f934be40a86c8e2c1000dbc67a9acd924b50c5a732e6d00faf4af50f`.

No public post was created. Watching was paused, the temporary LIRIK watch was disabled, and the original watch's enabled setting was restored. The private output remains available for review.

## Webcam-aware crop correction: version 0.1.1

The owner then identified that the standalone webcam split's game panel included a duplicate small source webcam. The standalone media adapter had forced a full-frame game box, overriding the foundation's webcam-exclusion geometry. Version 0.1.1 lets the original geometry choose the game region when a webcam exists; the no-camera path still fits the full source.

A failing-first real FFmpeg regression reproduced the duplicate webcam. It now verifies that the rendered game panel excludes a distinctive source webcam while preserving duration. A local 60.100-second framing comparison, using the source app's existing detected camera box with fresh head refinement and captions, passed full decoding and visual checks against the original app's same-clip output. That initial comparison reused the existing camera decision.

The owner then deployed the correction, independently verified by the live health response reporting **0.1.1**. A fresh cloud model/render pass ran from **09:31:55 UTC to 09:43:42 UTC**, about 11 minutes 47 seconds. The downloaded output measured **60.100 seconds, 1080×1920, with audio** and passed full-file decoding. Visual checks at 3, 12, 25 and 48 seconds confirmed a larger game region, no duplicated source webcam, and generated captions above the gameplay divider. Output SHA-256: `0a87bf9ac761903692773bc08f1d7557f0424e5d130ada6ea1773fb77c00b622`. This is actual standalone cloud inference and rendering, independently of the earlier local comparison.

Actual authenticated cloud preview footage was captured again with the corrected output. The demo was rebuilt from that footage and the corrected cloud video; its displayed test results reference source `2ed3bca` and passing [CI run 41292553292](https://github.com/ColinGPT9/clips-kitty-autopilot/actions/runs/41292553292).

## Posting decision and remaining evidence

- The owner chose to keep the cloud clip unposted. Public provider scheduling/delivery was not tested in this new deployment.
- Observe a genuine later view-count crossing if one becomes available. A read-only check at 08:51 UTC found the channel offline and no clips from the previous 30 minutes. Counts were not changed or fabricated.
- The latest review demo, `Clips-Kitty-Contest-Demo-WoW-Forever.mp4`, is **167.954 seconds**. It uses WoW footage and the owner's full Instagram recording as a previously published example, actual deployed UI, a wedding hook and anonymous Damage Control payoff, and an all-socials closing. Preferred female narration, full-file decoding and normalized audio passed (mean -18.3 dB, peak -1.5 dB). The owner uploads this version publicly to YouTube and supplies its actual URL.

## Clip actions and owner-supplied published example

Version **0.1.2** was independently verified live. Authenticated captures show Schedule, Damage Control and Deny on ready clips, and the existing popup opening directly from the Asmongold clip card. No scheduling or deletion was triggered by those captures.

The project supplied a 14.328-second phone recording created at 00:53:10 UTC on November 1 (October 31 evening in Eastern time). It visibly shows the existing Asmongold Reel on the project's Instagram profile. The recording is included alongside the new cloud preview in the demo. Labels identify it as a **previously published example**, rather than a new cloud-app delivery. The cloud test clips remain unposted.

The latest cut uses the matching WoW: Forever edit beside that recording and labels both as previously published examples. Its narration omits the older application's platform label and the three public figures' names. Source provenance here remains unchanged: this recording is historical publication evidence, not a new cloud post.

For the threshold segment, actual paused-cloud controls were recorded saving **100** and **10,000** as example targets, then restoring the original **2**. Ask First and the global pause were retained; no polling or scheduling was triggered, and no view counts were altered. The footage demonstrates editing configuration, not natural view growth.

The previously published desktop-app Reel and its target-crossing evidence belong to the starter foundation. They are not claimed as standalone cloud results.

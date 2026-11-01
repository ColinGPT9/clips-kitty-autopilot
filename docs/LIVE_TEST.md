# Standalone cloud test evidence

Observed November 1, 2026. Times below use UTC to avoid ambiguity during the US daylight-saving change.

## Deployment and connections

- Owner deployed this repository on an AWS Lightsail Ubuntu instance in Ohio (`us-east-2a`): 4 GB RAM, 2 vCPU, 80 GB disk.
- HTTPS deployment: https://13-184-154-246.sslip.io. The owner dashboard requires authentication; credentials are not published for judging.
- Verified HTTPS certificate, HTTP-to-HTTPS redirect, successful health response, and unauthenticated rejection of the private status endpoint.
- The independent app connected a Twitch viewer account through device authorization and selected Instagram **@clipskitty2** through WoopSocial. No YouTube or TikTok destination was selected or sent a post.
- Shared limits are five daily posts and five upcoming clips. The test watch uses **Ask first**.

## Twitch read and whole Gaming render

1. A read of `zackrawrr` viewer clips, one-day lookback and a two-view test target returned 15 real clips. All were already above the target on first observation. They were recorded as Earlier clips, with no new crossing claimed.
2. The owner-authorized test queued the existing clip **“What you doing?”**, Twitch ID `TameAbstrusePeppermintKippa-h1F6KV6x2gCYHTTN`. This is an earlier-clip render test, not evidence of a natural target crossing.
3. Cloud processing began at approximately **07:59:46 UTC** and completed at **08:10:08 UTC**, about 10 minutes 22 seconds. Models and media ran on the Lightsail CPU deployment.
4. Downloaded output measured **60.100 seconds, 1080×1920**, with audio. Full-file FFmpeg decoding passed. Visual inspection confirmed separate streamer camera and gameplay regions, plus generated captions.
5. Inspection also found generated bottom captions overlapping subtitles already burned into the source. Source correction `810d23e` moves generated captions above the gameplay divider in split layouts. The owner installed the update and confirmed its import check. The corrected cloud rerender ran from **08:48:20 UTC to 08:58:18 UTC**, about 9 minutes 57 seconds.
6. The corrected output again measured **60.100 seconds, 1080×1920, with audio**, and passed full-file decoding. Visual checks at 3, 12, 25 and 48 seconds confirmed that generated captions clear the gameplay divider while existing source subtitles stay intact. Output SHA-256: `cd98364bb25fbc8c5ed126f78a943efe10518a7005b402eabae35e1be473e5dd`.

Watching was paused again after the corrected render. The last verified state had one clip ready for review, zero scheduled posts and zero published posts. No public scheduling request was sent from this new app. Actual authenticated browser footage captured the correct Instagram destination, five/five limits, Earlier clips, completed preview playback and the request-free satire popup; no synthetic API responses or UI counts were used.

## Remaining live evidence

- Obtain approval for the exact Instagram test before sending a real schedule; record the provider result and delivery separately.
- Observe a genuine later view-count crossing if one becomes available. A read-only check at 08:51 UTC found the channel offline and no clips from the previous 30 minutes. Counts were not changed or fabricated.
- The new standalone review demo is complete: 125.581 seconds, actual cloud UI/preview footage, corrected Gaming output, local female narration and the satire popup. Full-file decoding and audible normalized narration were verified. The owner must upload it publicly to YouTube and supply the actual URL.

The previously published desktop-app Reel and its target-crossing evidence belong to the starter foundation. They are not claimed as standalone cloud results.

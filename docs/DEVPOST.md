# Devpost field answers: Clips Kitty Autopilot

Prepared for the Codex x TwitchCon Hackathon. Copy the answers below into the matching fields. Hackathon-specific additional questions may use different labels.

## Project name

Clips Kitty Autopilot

## Elevator pitch / tagline

Your community clips. You keep playing. Clips Kitty turns viewer-made Twitch clips into captioned vertical videos and schedules them to your socials.

## Video demo URL

https://youtu.be/_9trPSK_6gE

The supplied landscape demo file is 167.954 seconds (2:48). Confirm the uploaded video is Public and is the intended version; the YouTube page could not be independently fetched during this preparation.

## Code repository URL

https://github.com/ColinGPT9/clips-kitty-autopilot

## Try it out / project website links

- Project and installation: https://github.com/ColinGPT9/clips-kitty-autopilot#readme
- AWS walkthrough: https://github.com/ColinGPT9/clips-kitty-autopilot/blob/main/docs/AWS_SETUP.md
- Judge setup: https://github.com/ColinGPT9/clips-kitty-autopilot/blob/main/docs/JUDGE_SETUP.md

This is a self-hosted BYOK project. The links do not grant access to a shared paid account or private demonstration server.

## Codex session ID

01a18b17-1906-7f23-b4c4-9a99fd010bd9

Confirmed against the active build thread's `CODEX_THREAD_ID` during submission preparation.

## Built With

OpenAI Codex, Python, FastAPI, JavaScript, HTML, CSS, SQLite, Twitch API, WoopSocial, Whisper, YOLOv8, TalkNet, OpenCV, FFmpeg, PyTorch, NumPy, Docker, Caddy, AWS Lightsail, GitHub Actions

## Project story — paste this section into the story field

### Inspiration

Viewers already choose great stream moments when they make and share Twitch clips. Turning those moments into social posts still takes the streamer away from playing: downloading, reframing, captioning and scheduling. With a holiday gaming season ahead, I wanted a workflow where the community picks the moments and the streamer keeps playing.

### What it does

Clips Kitty Autopilot is an independent, self-hosted browser app for Twitch communities. Add a Twitch channel, set a clip-view threshold and choose a publishing mode. The app reads viewer-made clips through the Twitch API and checks clips again on later polls. Smaller channels can start with a lower target; busy channels can raise it to filter the flood.

The viewer already selected the moment, so Clips Kitty preserves the whole clip. It creates a vertical Gaming video, adds optional local speech captions and credits the viewer who clipped it. YOLOv8n locates people, TalkNet matches speech and lip movement to help identify the speaking streamer, OpenCV refines the facecam borders, and Whisper generates captions.

In Automatic mode, qualifying clips are rendered and scheduled to explicitly selected social profiles. In Ask First, each clip waits for a preview and a Schedule or Deny decision. WoopSocial is the publishing service that sends scheduled videos to the connected social accounts; Instagram is the example shown in the demo, rather than the only supported destination.

The default limits are five clips per day and five upcoming clips, shared across channels. Persistent storage retains work across restarts. Duplicate and overlapping moments are filtered, and ambiguous or partially failed sends are held for inspection rather than blindly resent. Existing clips already above the target on the first check remain under Earlier clips until explicitly selected, unless backfill was enabled.

Ready clips also include a Damage Control preview. It opens a dialog; it does not delete VODs or clips, send takedowns or contact a lawyer.

### How I built it with Codex

I used Codex as the implementation and debugging partner for the standalone FastAPI application, SQLite queue and publication outbox, browser dashboard, Twitch feed integration, multi-profile publishing controls, tests, packaging and deployment documentation. Codex also helped investigate real rendering defects, including duplicate webcam imagery and captions overlapping gameplay, and validate fixes with decoded video frames.

The project runs locally or in Docker on a persistent server. The demonstrated deployment used Ubuntu on AWS Lightsail, with Caddy HTTPS and sequential CPU model processes. Whisper captions and Gaming inference run locally on the installation; no OpenAI API key is needed to run that pipeline.

### Existing foundation and work during the submission period

This project uses the pre-existing open-source Clips Kitty application as a disclosed starter foundation. Provider adapters, Gaming geometry and detection libraries, TalkNet source and portions of the regression suite were reused under their licenses. Twitch Autopilot work was developed October 30–31, 2026, and the independent browser application was assembled November 1, with its own dashboard, database, worker, packaging and deployment. The repository's PROVENANCE.md lists the exact source revision and file origins. I am not claiming that the reused engine or the earlier application was written from scratch during this hackathon.

### Challenges

The main challenges were fitting detection, speech transcription and encoding into a small CPU server; selecting a real streamer camera rather than a game character; keeping generated captions clear of gameplay; and avoiding duplicate public sends after interruption. Another challenge was keeping approvals tied to exactly the selected profiles even if Settings changed later.

### Accomplishments

The standalone app ran on AWS with authenticated HTTPS, real Twitch reads on two channels and whole-clip Gaming rendering. The project passes 217 local automated checks, including real FFmpeg render/decode cases. Windows, Linux and a memory-limited CPU container also passed CI checks, including real model inference. The demo includes actual interface footage and a clearly labeled, previously published Clips Kitty Instagram example.

### What I learned

Reliable automation depends on state transitions and recoverable failures as much as on model output. Streamer detection needs several signals, small CPU deployments benefit from releasing model memory between stages, and a clear approval screen is essential when one clip can reach several social accounts.

### What's next

I want to improve setup onboarding, make destination-specific validation easier to act on, add media-retention controls and gather more end-to-end feedback across games and social networks. The project stays open source and BYOK: each installation uses its own keys, accounts, social profiles and hosting, with no shared creator-funded usage.

## Additional question: How did you use Codex?

Codex implemented the independent web dashboard, FastAPI routes, SQLite state machine and outbox, Twitch clip polling, explicit multi-profile approvals, provider integration, regression tests, container configuration and setup documentation. I directed the product and reviewed the behavior. Codex also helped diagnose and fix real Gaming crop and caption-placement defects, run Windows/Linux/container checks, and prepare the demonstration. Reused Clips Kitty components are disclosed separately in PROVENANCE.md. Build session: 01a18b17-1906-7f23-b4c4-9a99fd010bd9.

## Additional question: How does it connect to Twitch?

It uses Twitch public-client device authorization with the installer's own Twitch application Client ID and viewer account. Authenticated Twitch Clips API reads retrieve viewer-made clips for selected channels. The worker polls their view counts, applies the editable target and queues eligible clips while retaining the clipper's name for post credit. It is an API-connected browser application, not a Twitch Extension.

## Additional question: What is new / what was reused?

The independent browser dashboard, SQLite application state and worker, approval/destination snapshots, publication outbox, container/cloud setup and related integration tests were assembled during the submission period. It builds on the existing Clips Kitty provider and Gaming libraries, including Twitch Autopilot work developed October 30–31. The foundation predates the event and is not claimed as new; exact origins are documented at https://github.com/ColinGPT9/clips-kitty-autopilot/blob/main/PROVENANCE.md.

## Additional question: Platforms / installation / testing

Self-hosted web application accessed in a browser. Validated on Windows and Linux; the demonstrated server is Ubuntu on AWS Lightsail with Docker, persistent volumes and Caddy HTTPS. Run locally with Python 3.11+, FFmpeg and the documented dependencies, or use Docker. Each installer brings their own Twitch and WoopSocial connections. Instructions and an offline test path are in docs/JUDGE_SETUP.md; no private credentials or shared quotas are included.

## Additional question: Validation / demonstration notes

Real standalone-cloud checks cover Twitch reads, edited-target admission, deduplication and whole-clip rendering. Automated tests cover later crossings and multi-profile provider behavior. The standalone test clips were intentionally kept unposted, and a new natural live crossing is not claimed. The Instagram publication recording is a labeled historical example. The Damage Control popup caption was amended locally for the demo; it does not represent a server action or a real takedown/deletion feature.

## Fields that require the entrant's own answers

- Team members and submission type: use the actual contributors and your Devpost profile.
- Country of residence, age and other personal eligibility answers: enter your real information privately on the form.
- Rules/rights declarations: review and answer truthfully; this document does not accept terms or claim organizer approval of project eligibility.
- Any extra form questions not listed here: use the actual question wording before answering.

## Final submission steps

Deadline verified November 1: **November 2, 2026, 2 p.m. Pacific / 5 p.m. Eastern**. Judging is scheduled through November 15. Sources: [hackathon rules](https://twitchcon-codex.devpost.com/rules), [Devpost submission steps](https://help.devpost.com/article/126-know-your-submission-steps).

1. Enter the name and pitch, paste the story, add Built With tags, repository links, demo URL and Codex session ID.
2. Upload the prepared 3:2 project thumbnail and optional gallery images from the local submission package.
3. Check the YouTube video is Public and plays with sound while signed out.
4. Review the reuse disclosure and personal/rights declarations. Keep credentials and the private server address out of public fields.
5. Preview the project, then complete Devpost's final Submit project step. A saved draft is not a submitted entry. Look for Devpost's Submitted confirmation; this preparation has not submitted the project.

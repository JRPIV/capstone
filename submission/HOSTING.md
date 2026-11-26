# Hosting handoff

Prepared 2026-11-26. The public address is not created. Nothing in this file is a secret.

## Recommendation

GitHub Pages cannot run this demonstration. The page is only the front of a Python process. That process writes a SQLite file and calls Gemini with `GEMINI_API_KEY`, which has to stay on the server.

The smallest compatible host is one Fly.io app in Ashburn (`iad`): a shared 512 MB Machine, the Dockerfile in this repository, and a 1 GB Fly Volume mounted at `/data`. `fly.toml` already names that shape. Render can do the same job, but its free web service sleeps after 15 minutes and drops the SQLite file, and a persistent disk there requires a paid instance (published disk price $0.25 per GB per month, plus a paid compute plan that starts at $7 per month). Fly is the smaller bill for a short grading window.

## Cost and account setup

Prices below are Fly.io’s published rates for Ashburn as read on 2026-11-26 from [Fly.io resource pricing](https://docs.fly.io/about/pricing). They can change.

| Piece | Published price | This demo |
|---|---|---|
| Personal organization, no card | $1 of credit | Not enough for a month of the Machine below |
| Personal organization after a card is added | $5 of usage per month | The intended ceiling |
| `shared-cpu-1x`, 512 MB, running the whole month | $3.69 | Lower if the Machine auto-stops while idle |
| Volume, 1 GB | $0.15 per GB per month, including while the Machine is stopped | $0.15 |
| Volume snapshots | $0.08 per GB per month after the first 10 GB | Likely inside the free 10 GB for this file |

A card is required to keep the $5 monthly credit. I have not created a Fly account, app, volume, or secret, and I have not attached a card. Creating them is the step that can start charges.

Render’s free instance is not a substitute: it has an ephemeral disk, so a restart or a 15-minute idle period deletes the cases. Source: [Render free instances](https://render.com/docs/free) and [Render persistent disks](https://render.com/docs/disks), read 2026-11-26.

## What a visitor can and cannot do

`DEMO_ACCESS_TOKEN` is optional. Unset, this computer behaves as it does now: loopback only, no token, no model cap. Set on the host, the page asks for the token and every `POST /events` requires the header `X-Demo-Token`. A wrong or missing token returns 401 and writes nothing. The token is not in the page, the repository, the health response, or the logs. Give it to the professor in a separate message only after the host exists.

Model starts are capped by `DEMO_MODEL_CALLS_PER_HOUR`, default 8, counted in the running process. Intake, replies that do not call a model, and a repeated completed event do not count. Over the limit the server returns 429 and does not call Gemini. Restarting the Machine clears that hour’s counter. It does not clear the SQLite file.

There is one shared case file. A person who has the token can append events to the same demonstration the professor is watching. They cannot wipe it from the page. Reset stays the operator command `.venv/bin/python -m onboarding.reset_demo` on the host, or deleting the volume file. There is no public reset address. The people and the office stay fictional.

## Local verification

Docker is not installed on this computer, so the image was not built. The process the image runs was started on `127.0.0.1:8010` with a temporary SQLite file, `DEMO_ACCESS_TOKEN` set to a throwaway value, and `GEMINI_API_KEY` set to a stand-in so the real key was not used.

| Check | Result |
|---|---|
| `GET /health` | 200, `status: ok`, `demo_lock: true` |
| Page and `src/main.js` | 200. The page calls the same host. It does not call `127.0.0.1`. |
| `POST /events` without the token | 401, `demo_lock`, no case written |
| Intake with the token | 202 |
| Health, page, script, and both responses | Did not contain the token or the stand-in key |
| `.venv/bin/python -m unittest discover -s onboarding/tests -q` | 58 tests, 0.882s, OK. No Gemini call |

The Dockerfile copies `requirements.txt`, `onboarding/`, and `workspace/` only. `.dockerignore` excludes `.env`, `.venv`, and `onboarding/data`. `docker-compose.yml` and `fly.toml` pass `GEMINI_API_KEY` and `DEMO_ACCESS_TOKEN` through the environment. Neither file contains a value.

## Recording fallback

If the host stays off, record the local page for about four minutes with the script in `ASSIGNMENT.md`. Capture the held intake, the plan staying inactive until Alex Rivera approves it, and the Gemini answer with citation P2. QuickTime’s screen recording is enough. The recording does not need the API key, and it does not spend a visitor’s quota.

## Commands, after you say yes

These are not run yet.

```
fly auth login
fly apps create capstone-onboarding
fly volumes create onboarding_data --region iad --size 1
fly secrets set GEMINI_API_KEY=... DEMO_ACCESS_TOKEN=...
fly deploy
```

Use a new demo token for the secret. Do not reuse a value from `.env`, and do not paste either value into the repository. The app name in `fly.toml` can be changed if `capstone-onboarding` is already taken. After deploy, the working address is the `https://` host Fly prints. Send the token to the professor separately.

## Sources

- `onboarding/server.py`, `onboarding/demo_guard.py`, `onboarding/router.py`, `workspace/src/main.js`, `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `fly.toml`, `.env.example`.
- Fly.io resource pricing, https://docs.fly.io/about/pricing, read 2026-11-26.
- Render free web services, https://render.com/docs/free, and persistent disks, https://render.com/docs/disks, read 2026-11-26.
- Local process check on `127.0.0.1:8010` and the 58-test run, both on 2026-11-26. Docker was not installed.

## Assumptions

- One grader, a short window, and fictional cases. A single Machine and a 1 GB volume are enough.
- The $5 Fly credit still requires a card. The $1 no-card credit does not cover the Machine for a month.
- Auto-stop is acceptable. The first request after a stop waits for the Machine to start.
- Gemini billing is separate from Fly and remains on the existing key. The hourly cap is the control on that spend.

## Open Questions

- Whether to create the Fly app and attach a card. Not done.
- The demo URL. There is none until that deploy finishes.
- How the professor receives `DEMO_ACCESS_TOKEN`. It must stay out of the repository and out of the recording.

## Audit

- **Persona:** devops.eng, recorded in this session because a separate persona process was not run.
- **Action:** prepare deployment configuration and the hosting handoff. No app, volume, secret, or deploy was created.
- **Timestamp:** 2026-11-26T22:45:00Z
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** omitted. This handoff names controls and prices. It does not include a model prompt or a secret.
- **Doc sync:** no updates to README or the build artifacts. The default local server is still `127.0.0.1:8000` when `ONBOARDING_HOST` and `PORT` are unset. `submission/ASSIGNMENT.md` now points here and records the 58-test run.

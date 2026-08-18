# AI Live Studio

A full-stack, production-ready SaaS platform for AI-enhanced live streaming
— built with Django, PostgreSQL, and a Bootstrap 5 dark UI in a mature
**teal + copper** color theme. Deploys to [Render.com](https://render.com)
without modification.

The platform handles everything around a live stream — accounts, credits,
subscriptions, billing, analytics, notifications, real browser-to-browser
live viewing via WebRTC, an OBS Browser Source integration, and a full AI
Studio UI with camera preview — while leaving the actual AI video/voice
transformation as clean, modular placeholders in the `api/` app.
**Drop your own AI streaming API into those functions and you're live.**

> **Note on API integration:** The AI engine is configured once, by you,
> directly in the backend code (`api/stream.py`, `api/camera.py`,
> `api/avatar.py`, `api/credits.py`, `api/analytics.py`). End users of the
> platform never see, generate, or manage an API key — the AI capability is
> a property of the platform itself, not something each user connects.
> See **"Where to plug in your own AI API"** below for exact file/function
> locations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript, Bootstrap 5 |
| Backend | Python, Django 5 |
| Database | PostgreSQL (SQLite fallback for local dev) |
| Static files | WhiteNoise |
| WSGI server | Gunicorn |
| DB driver | psycopg2-binary |
| Charts | Chart.js |
| Deployment | Render.com |

---

## Project Structure

```
ai_live_studio/
├── config/              # Django project settings, root urls, wsgi/asgi
├── core/                # Landing page, shared ActivityLog, context processors
├── accounts/            # Custom User model, auth (register/login/reset/profile)
├── dashboard/           # Dashboard home, settings, tutorial, feed, AI jobs
├── studio/               # AI Studio (Stream model + UI)
├── analytics/            # Analytics dashboard + Chart.js data
├── payments/              # Credits, billing/subscriptions, transactions
├── notifications/          # In-app notifications
├── api/                    # ⭐ Modular AI placeholders + JSON endpoints
│   ├── stream.py            #   start_ai_stream / stop_ai_stream / transform_video
│   ├── camera.py             #   camera & mic device switching, mirror, mute
│   ├── avatar.py               #   AI character & background switching
│   ├── credits.py               #   credit cost calculation / charge / refund
│   ├── analytics.py              #   event hooks for external analytics
│   ├── views.py                   #   /start-stream/, /stop-stream/, etc.
│   └── urls.py
├── broadcast/                       # Admin-only bulk email (SendGrid) — see admin.py
│   └── services.py                    #   send_bulk_email() — the real sending logic
├── templates/                       # All HTML templates (dark glass UI)
├── static/                           # CSS + vanilla JS (incl. studio.js camera logic)
├── requirements.txt
├── runtime.txt
├── build.sh                            # Render build script
├── Procfile                             # Render start command
├── render.yaml                           # Render Blueprint (web service + Postgres)
└── .env.example
```

---

## Where to Plug In Your Own AI API

This is the most important part. The platform never implements real AI
video/voice processing — it calls into these functions instead. **These
five files are the only places you need to touch to bring your AI engine
online:**

| File | Function | Called when |
|---|---|---|
| `api/stream.py` | `start_ai_stream(stream, **kwargs)` | The moment a user clicks "Go Live" |
| `api/stream.py` | `stop_ai_stream(stream, **kwargs)` | The moment a user clicks "Stop Stream" |
| `api/stream.py` | `create_realtime_client_token(user, **kwargs)` | **This is the real one** — called once per broadcast session to exchange your DECART_API_KEY for a short-lived browser token. See the dedicated section below. |
| `api/camera.py` | `change_camera` / `change_microphone` | Device switching (already functional; extend if your AI needs device-level hooks) |
| `api/avatar.py` | `change_avatar(stream, look)` | User picks an uploaded "look" — in Studio, works pre-live and live |
| `api/avatar.py` | `change_background(stream, background_id)` | User picks a background |
| `api/credits.py` | `calculate_stream_cost(quality, minutes)` | Pricing model — tune to match your AI provider's real cost |
| `api/analytics.py` | `record_stream_event` / `push_external_metrics` | Optional hooks to forward events to your own analytics/monitoring |

Example — this is literally what's in the file today:

```python
# api/stream.py
def start_ai_stream(stream, **kwargs):
    # INSERT MY API HERE
    pass
```

Replace `pass` with a call to your AI service (e.g. kick off a processing
job, open a connection to your inference server, etc). `stream` is the
Django model instance for this session, so you have `stream.user`,
`stream.look`, `stream.background`, `stream.quality`,
`stream.resolution`, `stream.stream_id`, and so on available immediately.

These functions are already wired into the `/api/start-stream/`,
`/api/stop-stream/`, `/api/change-avatar/`, `/api/change-camera/`,
`/api/change-quality/`, and `/api/change-background/` endpoints, which are
in turn called by the AI Studio UI (`static/js/studio.js`) — including the
"Choose your look" thumbnails, which work **before** going live during
camera preview, not just mid-stream. So once you fill in the function
bodies, the whole flow works end to end without touching routing, auth,
credits, or any template.

Once your AI engine is live, flip this platform-wide flag (in `.env` or
your Render environment variables) so the UI reflects it:

```
AI_ENGINE_CONNECTED=True
```

This does **not** require end users to do anything — it's a single flag
you (the site owner) set once.

---

## Real-Time Face Swap (Decart)

This platform's real-time face swap is built specifically around **Decart**
(platform.decart.ai). Users upload a photo of the face they want from
**AI Studio → Choose your look → Add Look** — that's a real feature, not a
placeholder. Once a look is selected and you go live, Decart swaps your
face for the uploaded one in real time.

**Why this isn't a simple "send image, get image back" REST call:** that
approach is too slow for live video (round-trip latency alone kills it).
Decart instead connects your browser **directly** to their realtime
servers over WebRTC — video frames never touch your Django backend at
all. Here's the actual connection flow:

```
1. Browser asks Django: "give me a token" (POST /api/ai/realtime-token/)
2. Django exchanges your permanent DECART_API_KEY for a short-lived
   client token (10 min TTL) via Decart's own token endpoint
   → api/stream.py: create_realtime_client_token()  ← YOUR API KEY IS USED HERE
3. Browser fetches your selected look's photo (already authenticated,
   same-origin request — never a public URL)
4. Browser loads the Decart SDK (static/js/decart_realtime.js) and opens
   a WebRTC connection DIRECTLY to Decart, using the short-lived token
   + your uploaded photo as the reference face
5. Decart streams the transformed video straight back to the browser
6. That transformed stream — not your raw camera — is what gets sent to
   viewers/OBS via this platform's existing WebRTC broadcast system
```

**Where your API key goes:**

```
DECART_API_KEY=dct_your_real_key_here
```

Set this in your `.env` (local) or Render environment variables
(production) — never in any JS file, never committed to git. The moment
it's set, `AI_ENGINE_CONNECTED` auto-activates.

**Note — there's no separate "API URL" to configure.** Unlike a generic
REST provider, Decart's endpoint (`api.decart.ai`) is fixed and built into
their SDK — your key is the only thing you need.

**If you use a different Decart model:** the default is `lucy-2.5`
(their realtime character-transform model as of this build). Override with:
```
DECART_MODEL=your-model-name
```

**Built-in safety behavior:**
- No look selected ("My Camera") → raw passthrough, Decart never gets called.
- Key not configured yet → raw passthrough, everything else still works.
- Token exchange or WebRTC connection fails → falls back to raw camera
  rather than breaking the stream. A status badge in the camera preview
  shows **AI: Connecting…**, **AI: Active**, or **AI: Fallback** so you
  can tell what's happening at a glance.
- Switching your look while already live triggers a clean reconnect
  (stop + restart the outbound stream with the new reference face) — a
  brief ~1-2s hiccup for viewers, since Decart's realtime session doesn't
  support swapping the reference image mid-connection.

**A practical note on responsible use:** since this feature lets someone
swap a live stream into any face they upload, you're responsible for how
it's used on your platform — most face-swap API providers' terms of
service (including Decart's) require the uploader to have the right to
use that likeness (their own face, or someone who's consented), and using
someone's face without consent can raise real legal issues (impersonation,
right-of-publicity, fraud) depending on jurisdiction. Worth adding a
consent checkbox or terms acknowledgment to the upload form if this is
going to production.

---

## How Live Viewing Works (the `/watch/` link)

When a user clicks "Go Live" in AI Studio, they get a shareable link like
`https://yoursite.com/watch/<uuid>/`. Anyone who opens that link — no
account required — connects directly to the broadcaster's browser via
**WebRTC**, using simple HTTP-poll signaling (`api/webrtc.py` +
the `/api/webrtc/...` endpoints). No websocket server, TURN service, or
media server is required to get this working out of the box.

This is a direct browser-to-browser (mesh) connection — great for demos,
local networks, and small audiences. For large-scale public broadcasting
you'd eventually front this with a proper SFU/media server; the signaling
contract is written so that swap is a backend-only change (the frontend
API — join/offer/answer/ice — stays the same).

## AI & OBS (feed your stream into Zoom, WhatsApp, TikTok, etc.)

The **AI & OBS** page (sidebar) gives each user a private, regenerable
Browser Source URL (`/obs/<token>/`) they can paste directly into OBS
Studio as a Browser Source. It shows their camera preview immediately and
automatically switches to the live AI output when they go live in AI
Studio. From there, OBS's built-in **Virtual Camera** feature lets them use
that AI-processed feed as their webcam in literally any app — Zoom,
WhatsApp Desktop, Discord, TikTok LIVE Studio, Twitch, etc. That hand-off
to other apps is OBS's own feature; this platform just needs to get a
clean video feed into OBS, which the Browser Source URL does.

---

## Local Setup

### 1. Clone and create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` as needed. By default `DATABASE_URL` is empty, so the app uses
local SQLite automatically — no PostgreSQL setup required for local dev.

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (for the Django admin)

```bash
python manage.py createsuperuser
```

### 6. Collect static files (optional locally; required in production)

```bash
python manage.py collectstatic --no-input
```

### 7. Run the dev server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

---

## Using PostgreSQL Locally (optional)

```bash
createdb ai_live_studio
```

In `.env`:

```
DATABASE_URL=postgres://YOUR_USER:YOUR_PASSWORD@localhost:5432/ai_live_studio
```

Then re-run `python manage.py migrate`.

---

## Deploying to Render.com

### Option A — One-click Blueprint

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint** and point it at your repo.
   `render.yaml` already defines a web service and a free PostgreSQL
   database, and wires `DATABASE_URL` and a generated `SECRET_KEY`
   automatically.
3. Click **Apply**. Render will run `build.sh` (installs dependencies,
   collects static files, runs migrations) and then start Gunicorn via the
   `Procfile`.

### Option B — Manual Web Service

1. **New → Web Service**, connect your repo.
2. **Build Command:** `./build.sh`
3. **Start Command:** `gunicorn config.wsgi:application`
4. **Environment variables:**
   - `SECRET_KEY` — generate a long random string
   - `DEBUG` — `False`
   - `DATABASE_URL` — from a Render PostgreSQL instance (or your own)
   - `AI_ENGINE_CONNECTED` — `True` once your AI API is wired in
5. Add a **PostgreSQL** instance from the Render dashboard and copy its
   internal connection string into `DATABASE_URL`.

### After first deploy

Create an admin user directly on Render via the **Shell** tab:

```bash
python manage.py createsuperuser
```

---

## Email Broadcasts (SendGrid) — Django Admin only

Bulk email is controlled **exclusively from Django admin** — there is no
separate dashboard page, and only superusers (`is_superuser=True`) can see
or use it, not just any staff user. Regular staff with other admin access
cannot view this section at all, and a direct URL attempt is blocked with
a 403.

**How to send one:**
1. Log into `/admin/` as a superuser
2. Find **Broadcast → Email Broadcasts** in the admin index
3. Click **Add Email Broadcast**, fill in Subject + Message (the form
   shows exactly how many active users will receive it)
4. Click **Save** — that's the trigger. There's no separate "send" step;
   creating the row *is* what starts the send (see
   `broadcast/admin.py`'s `save_model()`), which kicks off a background
   thread so your browser doesn't hang waiting.
5. Watch progress by refreshing the changelist or the broadcast's detail
   page — `sent_count` / `failed_count` update live as batches complete.

Once created, a broadcast is **permanently read-only** — subject, message,
and all stats can be viewed but never edited or resent, so there's no way
to accidentally alter or re-trigger something already in flight or sent.

**Why SendGrid's own library instead of django-anymail:** django-anymail
is a popular Django/ESP integration library, but its own docs currently
flag SendGrid support as no longer officially tested/supported. So this
uses **`sendgrid-python`** instead — the library maintained directly by
Twilio/SendGrid, called from `broadcast/services.py`, independent of
Django's own transactional email system (which still handles account
verification/password-reset emails as before).

**Where your SendGrid API key goes:**
```
SENDGRID_API_KEY=SG.your_real_key_here
BROADCAST_FROM_EMAIL=you@yourdomain.com
```
Set these in `.env` locally or Render environment variables in
production. `BROADCAST_FROM_EMAIL` must be a **verified sender or domain**
in your SendGrid account, or sends will fail — verify one at
[app.sendgrid.com/settings/sender_auth](https://app.sendgrid.com/settings/sender_auth).
Get your key from
[app.sendgrid.com/settings/api_keys](https://app.sendgrid.com/settings/api_keys)
(needs **Mail Send** permission).

**How it works under the hood:**
- `broadcast/admin.py` — the entire access-control + trigger logic. Only
  superusers get `has_module_permission` / `has_add_permission`; everyone
  else doesn't even see "Broadcast" in the admin index.
- `broadcast/services.py` → `send_bulk_email()` — the actual sending
  logic; this is the file to edit if you need to change how emails are
  built or sent.
- Recipients are batched (`BROADCAST_BATCH_SIZE`, default 500) into
  separate SendGrid API calls, each using **personalizations** so no
  recipient ever sees anyone else's email address.
- Progress (`sent_count`, `failed_count`) is saved to the database after
  every batch, so even a crash mid-send doesn't lose progress.

**A note on scale:** background threads are enough for a straightforward
"email everyone" admin tool at moderate user counts. If you grow into the
tens of thousands of users, or need retry-on-failure/redelivery
guarantees, the natural upgrade path is swapping the threading call in
`broadcast/admin.py`'s `save_model()` for a real task queue (Celery +
Redis) — `send_bulk_email()` itself wouldn't need to change, just how
it's invoked.

### Testing locally without emailing anyone for real

`BROADCAST_SANDBOX_MODE` defaults to **on** automatically whenever
`DEBUG=True`, so local testing is safe by default — SendGrid validates
your request (catching bad API keys, malformed data, etc.) and returns
success, but **never actually delivers the email**. Any broadcast sent
this way shows `sandbox_mode: True` in its admin record.

To test locally:
1. Set `SENDGRID_API_KEY` in your `.env` (a real key — sandbox mode still
   needs a valid key to authenticate the request, it just skips delivery)
2. Run `python manage.py runserver`, log in to `/admin/` as your
   superuser
3. Add an Email Broadcast — it'll show as sandboxed, `sent_count` will
   increment as if delivered, but nothing lands in any inbox
4. To send for real once you're ready, set
   `BROADCAST_SANDBOX_MODE=False` explicitly (or just deploy with
   `DEBUG=False`, which turns sandbox off automatically)

---

## Admin Dashboard, Payments & Access Control

Your admin panel is at **`/admin_dashboard/`** (light "fintech" theme,
separate from Django's own `/admin/`). Only staff users can access it.
From here you can:

- **Users** — search, create, suspend/reactivate, delete, and manually
  add/adjust credits (plus a plan label and note) for any account
- **Credit Plans** — create/edit/delete plans (name, price, credits,
  minutes label, description) — these are what show on the landing page
  pricing section and the payment page, live, with no redeploy needed
- **Payment Methods** — add/remove bank accounts and crypto wallets users
  pay into
- **Payment Approvals** — view uploaded receipts and approve/reject each
  submission; approving grants the user's plan credits and unlocks their
  account
- **Decart API Key** — override your production Decart key any time,
  without touching `.env` or redeploying

### The payment gate (first login only)

Right after registering, a user's **first** login redirects them to a
plan-selection + payment page (`/billing/gate/`) — they pick a plan, pay
via bank transfer or crypto, upload a receipt, and wait for admin
approval. Every other page is blocked until then (enforced by
`core/middleware.py`'s `PaymentGateMiddleware`). Once approved, that
user is **never gated again** — even if their credits later hit zero,
they keep full dashboard access.

### Credit lock (ongoing)

Once credits run out, the user's dashboard, analytics, billing, etc. all
stay reachable — but going live and switching looks in AI Studio are
blocked with a clear "buy more credits" prompt (`api/views.py`'s
`start_stream` / `change_avatar`), until they submit another payment via
the same admin-approval flow.

---



## Environment Variables Reference

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Django cryptographic signing key | insecure dev key (change in prod) |
| `DEBUG` | Debug mode toggle | `True` locally, set `False` in prod |
| `ALLOWED_HOSTS` | Extra comma-separated allowed hosts | Render host auto-added |
| `CSRF_TRUSTED_ORIGINS` | Extra comma-separated trusted origins | Render host auto-added |
| `DATABASE_URL` | PostgreSQL connection string | empty → falls back to SQLite |
| `DECART_API_KEY` | Your Decart account key — see "Real-Time Face Swap" above | empty (raw camera passthrough) |
| `DECART_MODEL` | Which Decart realtime model to use | `lucy-2.5` |
| `AI_ENGINE_CONNECTED` | Platform-wide flag shown in the UI once your AI API is live | auto-detected from `DECART_API_KEY` |
| `SENDGRID_API_KEY` | Your SendGrid key — see "Email Broadcasts" above | empty (broadcasts fail with a clear error) |
| `BROADCAST_FROM_EMAIL` | Verified sender address broadcasts are sent from | falls back to `DEFAULT_FROM_EMAIL` |
| `BROADCAST_BATCH_SIZE` | Recipients per SendGrid API call | `500` |
| `BROADCAST_SANDBOX_MODE` | Dry-run mode — validates but never delivers | `True` when `DEBUG=True`, else `False` |
| `EMAIL_BACKEND` / `EMAIL_HOST*` | SMTP config for verification & reset emails | console backend (prints to logs) |

---

## Database Migrations

Whenever you change a model:

```bash
python manage.py makemigrations
python manage.py migrate
```

On Render, migrations run automatically as part of `build.sh` on every
deploy.

---

## Static Files

Static files are served by **WhiteNoise** directly from Gunicorn — no
separate static file host or CDN is required. Run before deploying (or let
`build.sh` do it automatically):

```bash
python manage.py collectstatic --no-input
```

---

## Default App Structure Recap

- **accounts** — custom `User` model (credits, subscription plan, country,
  avatar, bio), registration, login, logout, forgot/reset password, change
  password, email verification, profile editing.
- **dashboard** — home with stat cards (credits, plan, status, streams,
  bandwidth/storage estimates, AI engine status), settings, tutorial, feed,
  AI jobs list.
- **studio** — the AI Studio: live camera/mic preview, device switching,
  mirror/mute, AI character & background selectors, quality/resolution
  selectors, start/stop stream, live URL + copy, audience counter, duration
  timer, status badge.
- **analytics** — Chart.js-powered daily stream chart, quality breakdown
  doughnut chart, watch time / credit usage / active sessions stats, stream
  history table.
- **payments** — credit packages (purchase flow, simulated — swap in a real
  gateway), plan/subscription switching, transaction history.
- **notifications** — in-app notification center with mark-read / mark-all
  / delete.
- **api** — the pluggable AI placeholder modules plus the JSON endpoints the
  Studio UI calls.
- **core** — landing page (hero, features, pricing, FAQ, testimonials,
  footer), shared `ActivityLog` audit trail, error pages.

---

## Troubleshooting

**`django.db.utils.OperationalError` locally** — you set `DATABASE_URL` but
don't have PostgreSQL running. Either start Postgres or unset the variable
to fall back to SQLite.

**Static files missing in production (404s on CSS/JS)** — make sure
`collectstatic` ran (it's part of `build.sh`) and that `DEBUG=False` isn't
blocking WhiteNoise from serving `staticfiles/`.

**Emails not arriving** — the default `EMAIL_BACKEND` is the console
backend, which prints emails to your server logs instead of sending them.
Set real SMTP credentials in your environment variables to send actual
email.

**Camera preview doesn't request permissions** — browsers only allow
camera/mic access over `https://` or `http://localhost`. This is a browser
security restriction, not a bug in the app.

**"CSRF verification failed" calling `/api/...` endpoints from custom
JS** — make sure requests include the `X-CSRFToken` header (see
`static/js/main.js`'s `csrfFetch` helper) and that cookies are sent with
the request.

---

## License

This codebase is provided as a starting point for your own product. Adapt
freely.

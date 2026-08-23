# Roadmap

Deferred work — ideas and suggestions only, nothing here is being built yet.
Update this file as items get picked up or dropped.

## Decided

**Pyodide stays scoped to the browser demo only.** It is not something a
downstream user should embed in their own production frontend — the ~6-10MB
WASM payload and 2-3s boot are fine for a one-time demo visit, not for a form
validator that fires on every keystroke. The API (below) is the real answer
for "use urlgenie from a frontend."

**The demo stays Pyodide-based; the API is additive, not a replacement.** A
static Pyodide page can only ever be *slow to start* — GitHub Pages doesn't go
down. A demo backed by a free-tier API can be *unreachable*, and in the worst
way: a recruiter clicks it after the instance has gone idle, a free-tier cold
start takes 20-30s, and they close the tab before anything renders. That's
strictly worse than what Pyodide was chosen to avoid in the first place. Once
the API exists, link to it (or embed its Swagger UI) as a secondary "try the
live API" option rather than rewiring the demo to depend on it.

## 1. FastAPI wrapper

A thin REST layer over the existing functions. Suggested shape:

```
api/
  main.py          # FastAPI app, routers
  schemas.py       # Pydantic request/response models
  routers/
    generalize.py
    validate.py
    extract.py
  Dockerfile
  requirements.txt (or reuse pyproject.toml's [project.optional-dependencies])
```

**Endpoints:**

| Method | Path | Wraps | Notes |
|---|---|---|---|
| POST | `/generalize` | `generalize()` | body: `{url, ...flags}` |
| POST | `/generalize/many` | `generalize_many()` | body: `{urls, separator, drop_invalid, ...flags}` → list of `{original, result}` |
| POST | `/generalize/social` | `generalize_social()` | |
| GET | `/social/handle` | `extract_social_handle()` | query: `?url=` → `{platform, handle, original_handle, rule}` or 404 |
| GET | `/social/platform` | `detect_platform()` | query: `?url=` → `{platform}` or 404 |
| POST | `/extract/contacts` | `extract_contacts()` + optional `validate_contacts()` | body: `{text, include, exclude, validate_url}` |
| GET | `/validate/url` | `validate_url()` | query: `?url=&require_suffix=&allowed_schemes=` |
| GET | `/validate/email` | `validate_email()` | query: `?email=&url=` |
| GET | `/validate/phone` | `validate_phone()` / `normalize_phone()` | returns `{valid, normalized}` |
| GET | `/validate/social` | `validate_social()` | |
| GET | `/parse` | `parse_url()` | debugging/education endpoint — returns every `ParsedUrl` field |
| GET | `/health` | — | for uptime checks / host health probes |
| GET | `/version` | `urlgenie.__version__` | |

**Why this is worth building beyond the demo:** it lets someone reuse the
*real* urlgenie logic from a stack that isn't Python at all — a Node/PHP/Ruby
frontend can call `GET /validate/email` for live form validation without ever
installing the package. That cross-language reuse is the actual value prop of
having an API at all, separate from the demo.

**Suggestions:**
- Pydantic models for every response — free OpenAPI docs at `/docs`, which
  doubles as its own interactive demo (worth linking to from the README).
- CORS: needs to be open (`allow_origins=["*"]` or scoped) since the whole
  point is arbitrary frontends calling it cross-origin.
- Rate limiting (`slowapi` or similar) — it'll be public and unauthenticated,
  worth guarding against abuse from day one rather than after an incident.
- No auth for v1. Revisit only if abuse becomes a real problem.
- Batch endpoints return partial results with per-item status rather than
  failing the whole request on one bad input — same principle as the
  `generalize_many()` fix (2.0.1): never let one bad row silently break or
  hide the rest.

## 2. Hosting the API

Free tier options, ranked by how well they avoid the cold-start problem:

| Option | Cold start | Notes |
|---|---|---|
| **Google Cloud Run** | ~1-2s | Scales to zero, generous free tier, requires a card on file even for free usage. Probably the best balance of "actually production-grade" and "cheap." |
| **Fly.io** | ~1-3s | Free allowance, machines can still sleep depending on config. |
| **Render (free web service)** | ~20-30s | The failure mode this roadmap explicitly warns about. Avoidable with a scheduled keep-alive ping (GitHub Actions cron hitting `/health` every ~10 min) but that's a hack, not a fix. |
| **Railway** | varies | Usage-based free credits, may require a card. |

Recommendation: Cloud Run if willing to add a card, Fly.io otherwise. Skip
Render's free tier for anything meant to be recruiter-facing.

## 3. Demo enhancements not yet built

- Loading state text is in place ("Booting Python runtime…" /
  "Installing urlgenie from PyPI…"); worth watching whether that's enough
  once tested in a real browser, or whether a progress bar is warranted.
- "View this rule on GitHub" link next to the rule-matched chip in the
  Generalize panel, deep-linking to the exact line in `config.py`.
- Favicon + Open Graph tags for when the demo link gets shared.
- Once the API exists: a small "Also try the live API ↗" link or embedded
  Swagger iframe, per the decision above.

## 4. Open questions

- Should the API version independently from the PyPI package, or stay in
  lockstep? Leaning towards lockstep (simpler to reason about) unless the API
  layer needs a fix that doesn't touch the core package.
- Should `api/` live in this repo or a separate one? Leaning towards this
  repo for now — tightly coupled, easier to keep in sync — revisit if it
  grows large enough to want its own release cadence.

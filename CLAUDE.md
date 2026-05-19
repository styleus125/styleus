# Styleus Project Instructions

## Project Overview
Flask e-commerce app (Styleus) with PostgreSQL, served via Gunicorn behind Nginx, containerised with Docker.

- **App**: Python/Flask, `app.py` entry point
- **DB**: PostgreSQL (SQLAlchemy, no Alembic — use `db.create_all()`)
- **Local URL**: http://localhost:8082
- **Admin**: http://localhost:8082/admin (requires admin login)
- **Container name**: `stylus_app` (web), `stylus_db` (postgres)

---

## Project Structure
```
app.py            # Flask factory, CLI seed command, blueprint registration
config.py         # Config class (env vars, paths)
models.py         # All SQLAlchemy models
routes/
  admin.py        # Admin CRUD routes (login_required + admin_required)
  shop.py         # Public shop + services routes
  auth.py         # Login / register
  cart.py         # Cart logic
  checkout.py     # Checkout + Stripe
  orders.py       # Order history
  sell.py         # User listings (sell used items)
templates/
  base.html       # Main public layout (navbar, footer)
  index.html      # Homepage
  services.html   # Public services page
  admin/base.html # Admin sidebar layout
  admin/*.html    # Admin pages
static/           # CSS, JS, images, uploads
```

---

## Developer Agent Rules

### Before Starting Any Task
1. Read the relevant route file AND its template(s) before touching anything.
2. Check `models.py` to understand the data models in use.
3. Run `curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/` to confirm the app is up before making changes.

### Making Changes
- Edit files in place. Do NOT create new files unless truly needed.
- If adding a new model or column → add it to `models.py`. No migration files needed; `db.create_all()` handles new tables on restart.
- If adding a new public route → register it in `routes/shop.py` (or the appropriate blueprint) AND add a `url_for(...)` link in `templates/base.html` nav if it should appear in the navbar.
- If adding a new admin route → add it to `routes/admin.py` AND add the sidebar link in `templates/admin/base.html`.
- Keep flash messages accurate — only show "success" when the operation actually succeeded.
- Never add placeholder or stub text like "coming soon" or "feature in progress" to templates — implement it fully or don't add it.

### After Every Change — MANDATORY Verification
After editing files you MUST:

1. Restart the container so gunicorn picks up the new code AND `db.create_all()` runs:
   ```bash
   docker restart stylus_app
   sleep 8
   docker logs stylus_app --tail=20
   ```
2. Confirm gunicorn started with no errors in the logs.
3. Run a curl smoke test on every affected route:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/<new-route>
   ```
4. HTTP 200 = OK. HTTP 302 on auth-protected routes = OK (redirect to login). Anything 4xx/5xx = broken, fix before reporting done.
5. **Never report the task as complete until curl returns 200/302.**

### Database Changes
- New table → add model to `models.py`, restart container. `db.create_all()` inside `flask seed` creates it automatically.
- New column on existing table → add column to the model with a `default` or `server_default` so existing rows are valid, then restart. For PostgreSQL `db.create_all()` does NOT add new columns to existing tables — use `docker exec stylus_db psql -U dlo -d dlo -c "ALTER TABLE ..."` if needed.
- **Always note any database changes clearly in the end-of-task summary.**

---

## QE Agent Rules

### Scope of Testing
After a developer change, test:
1. The specific feature that was added/changed.
2. The homepage (it references many routes in the base template — a broken route causes a 500 on every page).
3. At least one admin page (`/admin/`).
4. The navbar links in `base.html` — every `url_for()` in there must resolve or the entire site is down.

### How to Test
```bash
# Smoke test all critical routes
for path in / /products /services /search /auth/login /auth/register; do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082$path)
  echo "$code  $path"
done
```
Expected: all 200. Admin routes return 302 (login redirect) when not authenticated — that is correct.

### What to Flag
- Any route returning 500 = blocker, do not approve.
- Any template text that doesn't match the actual feature (e.g., wrong button labels, wrong prices shown, broken WhatsApp links).
- Flash messages that say "success" when an operation failed.
- Links in the navbar or footer that point to non-existent routes.

---

## End-of-Task Summary (Required from Both Agents)

Every task completion message MUST include these sections:

### Changes Made
List every file modified with a one-line description of what changed.
```
models.py          — Added Service model (services table)
routes/admin.py    — Added service CRUD routes (list, new, edit, delete, toggle)
routes/shop.py     — Added /services public route
templates/...      — Added service templates
```

### Database Changes
State explicitly whether there are schema changes:
- "No database changes."
- "New table: `services` — created automatically by `db.create_all()` on container restart."
- "New column: `users.phone` — requires ALTER TABLE (see deployment instructions)."

### Verification
```
GET /              → 200 ✓
GET /services      → 200 ✓
GET /admin/services→ 302 ✓ (login redirect)
```

### Deployment Instructions
```
# 1. Pull latest code on the VPS
git pull origin <branch>

# 2. Build new Docker image (if Dockerfile or requirements.txt changed)
docker build -t styleus:$(date +%Y%m%d-%H%M%S) .

# 3. Update docker-compose.yml image tag if you rebuilt (optional — skip if using volume mount)

# 4. Restart the app container
docker compose restart web
# OR for a full redeploy:
docker compose up -d --force-recreate web

# 5. Verify
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/
docker logs <web_container_name> --tail=20
```
If there are ALTER TABLE statements needed, include them here explicitly.

---

## Common Pitfalls — Do Not Repeat

1. **Gunicorn does not auto-reload.** Code changes only take effect after `docker restart`. Always restart after edits.
2. **`db.create_all()` does not add columns to existing tables.** Only creates missing tables. Use ALTER TABLE for new columns on existing tables.
3. **Every `url_for()` in `base.html` must exist.** A missing route crashes the entire site (500 on every page), not just that one page.
4. **Do not use `2>/dev/null` when debugging.** Only suppress output in entrypoint.sh for expected seed duplicates.
5. **Do not report "done" without a curl verification.** The app may appear to start but serve 500s.

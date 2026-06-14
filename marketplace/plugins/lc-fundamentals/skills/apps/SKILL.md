---
name: apps
description: Author and deploy LimaCharlie "apps" — self-contained AI-generated HTML mini-apps that render in a sandboxed iframe in the LimaCharlie web UI and call LimaCharlie APIs through a brokered, permission-scoped runtime (window.lc). Use when a user wants to create, edit, or understand a custom app/dashboard/tool embedded in the LimaCharlie console (the `app` hive).
allowed-tools:
  - Bash
  - Read
  - Write
---

# LimaCharlie Apps

An **app** is a single self-contained HTML document (HTML + inline CSS + inline
JS) stored in the `app` hive. The LimaCharlie web UI renders it inside a
**sandboxed iframe** and injects a trusted runtime, `window.lc`, that brokers
LimaCharlie API calls using a JWT scoped to a subset of the viewing user's
permissions. You write **only the app body** — the runtime, base styles, and
security wrapper are injected by the host.

Full contract: `web-app-frontend/docs/ai-guides/apps-runtime-contract.md`.

## The golden rules (apps are validated against these)

1. Output is a **single self-contained `<body>` fragment**. Do NOT emit
   `<html>`, `<head>`, `<base>`, or `<meta http-equiv>` — the host owns those.
2. **No external resources**: no `<script src>`, external stylesheets, CDNs, or
   web fonts. Inline everything. (The CSP blocks external loads.)
3. **All LimaCharlie data goes through `lc.api(...)`.** Never embed a token/API
   key, never prompt the user for credentials.
4. **External network only to declared `allowed_origins`** via your own `fetch`.
   Everything else is blocked.
5. **Style with the design system**: compose `.lc-*` classes and reference
   `--lc-*` variables. Never hardcode colors or fonts (so dark mode works).
6. **Least privilege**: request the fewest `required_permissions`. Prefer
   read-only (`*.get`, `*.list`). You can only declare permissions you yourself
   hold. Sensitive perms (`billing.ctrl`, `user.ctrl`, `apikey.ctrl`) trigger a
   severe warning to every viewer; write perms (`*.set`, `*.del`, `*.task`,
   `*.ctrl`) trigger a lesser one.

## The `window.lc` runtime

```js
await lc.ready                              // wait for the secure handshake
lc.version                                  // '1'
lc.ctx.user                                 // { id, email, displayName }
lc.ctx.orgs                                 // [{ oid, name }]
lc.ctx.context                              // embed identifiers, e.g. { sid }
lc.ctx.theme                                // { mode, vars } (presentation only)
await lc.api(method, path, body?, opts?)    // brokered LC API call -> JSON
lc.onThemeChange(theme => { /* ... */ })    // live dark-mode updates
```

- `path` is a site-relative LC path under `/v1`, e.g. `'/v1/who'` or
  `'/v1/orgs/<oid>/...'`. Absolute URLs / other hosts / writes to
  `/v1/hive/app/...` are rejected.
- **Other LC services.** Some LimaCharlie APIs live off the main API on their own
  hosts. Reach one by passing `opts.service` AND listing it in `required_services`
  (a service you didn't declare is rejected with `denied`). The parent host-pins
  the call and brokers it with the same scoped JWT — it does NOT rewrite your
  path, so use the EXACT path/method the service expects (verify against
  `/openapi`). Valid services:
  - `search` — the historical-events query API (LCQL), the same backend as the
    query console. Two steps: POST `/v1/search/` with a JSON body
    (`{ oid, query, startTime, endTime, ... }`) to get a `queryId`, then poll
    GET `/v1/search/<queryId>/`. This is the `search` service — NOT `replay`.
  - `cases` — case management, e.g. GET `/orgs/<oid>/cases`.
  - `ai` — AI sessions / agents.
  - `replay` — sensor *telemetry* replay (rarely needed; NOT the query API).
  ```js
  const init = await lc.api('POST', '/v1/search/',
    { oid, query, startTime, endTime }, { service: 'search' })
  const page = await lc.api('GET', '/v1/search/' + init.queryId + '/',
    null, { service: 'search' })
  ```
- On failure, `lc.api` rejects with `Error & { code, status }`; `code` is one of
  `denied | rate_limited | unauthorized | http | timeout | aborted | malformed`.
- Limits: ~10 req/s (burst 20), 8 concurrent, 256 KB body.

## Design system

Tokens: `--lc-bg --lc-surface --lc-line --lc-ink --lc-muted --lc-accent
--lc-positive --lc-warning --lc-danger --lc-input-bg --lc-input-line
--lc-font-sans --lc-font-mono --lc-radius --lc-space`.

Classes: `.lc-card .lc-btn (--primary/--danger) .lc-input .lc-select
.lc-textarea .lc-label .lc-badge (--positive/--warning/--danger) .lc-table
.lc-kpi (.lc-kpi__value/.lc-kpi__label) .lc-row .lc-col .lc-stack .lc-muted
.lc-spinner`.

## Golden reference app

A complete, conforming app body. Use it as the template.

```html
<div class="lc-stack">
  <div class="lc-card">
    <div class="lc-row" style="justify-content:space-between">
      <h2>Sensor status</h2>
      <button class="lc-btn lc-btn--primary" id="refresh">Refresh</button>
    </div>
    <div id="status" class="lc-muted">Loading…</div>
  </div>

  <div class="lc-card">
    <div class="lc-kpi">
      <span class="lc-kpi__value" id="count">—</span>
      <span class="lc-kpi__label">Sensors online</span>
    </div>
  </div>
</div>

<script>
  const $ = (id) => document.getElementById(id)

  async function load() {
    $('status').textContent = 'Loading…'
    try {
      await lc.ready
      const oid = lc.ctx.orgs[0].oid
      const res = await lc.api('GET', '/v1/sensors/' + oid)
      const sensors = res.sensors || []
      $('count').textContent = sensors.filter((s) => s.is_online).length
      $('status').innerHTML =
        '<span class="lc-badge lc-badge--positive">' + sensors.length + ' sensors</span>'
    } catch (e) {
      $('status').innerHTML =
        '<span class="lc-badge lc-badge--danger">Error: ' + e.code + '</span>'
    }
  }

  $('refresh').addEventListener('click', load)
  load()
</script>
```

This app would declare `required_permissions: ["sensor.list"]` and no
`allowed_origins`.

## Creating the app record

Apps live in the `app` hive (org-scoped). Authoring is done via the CLI; the web
UI is for running and managing apps, not editing HTML.

1. **Validate the HTML against the golden rules above** before writing it.
2. Write the record JSON to a file (the `data` payload mirrors the backend
   `AppRecord`):

   ```bash
   cat > /tmp/app.json << 'EOF'
   {
     "display_name": "Sensor status",
     "description": "Live count of online sensors",
     "icon": "🛰️",
     "html": "<...the app body from above...>",
     "required_permissions": ["sensor.list"],
     "allowed_origins": [],
     "required_services": [],
     "locations": ["standalone"],
     "expected_context": []
   }
   EOF
   ```

   - `locations`: any of `standalone`, `within_a_sensor`, `within_a_detection`,
     `within_a_case`, `within_a_dr_rule`. For embeds, list the identifiers you
     read from `lc.ctx.context` in `expected_context` (e.g. `["sid"]`).
   - `allowed_origins`: only `https://host` origins (no path), and only if the
     app must reach an external (third-party) API directly. Empty = LC only (safest).
   - `required_services`: first-party LC services the app calls via
     `lc.api(..., { service })` — any of `search`, `replay`, `cases`, `ai`. Empty
     = main API only. Declaring a service is required before the app can call it.

3. **Set** the record (the `--key` is the app's stable id/slug):

   ```bash
   limacharlie hive set --hive-name app --key sensor-status --input-file /tmp/app.json --oid <oid>
   ```

4. **Enable it** — hive records are NOT auto-enabled on set:

   ```bash
   limacharlie hive enable --hive-name app --key sensor-status --oid <oid>
   ```

5. Manage from the UI: **Apps** in the org sidebar (`/orgs/<oid>/apps`), or the
   matching object-context page for embeds.

## Common pitfalls

- **Author lacks a declared permission** → the `set` is rejected. You can only
  require perms you hold.
- **App "works for me" but not for an admin** is impossible by design: at view
  time the JWT is `required ∩ viewer's perms`, so it can only ever shrink.
- **Forgot to enable** → the app won't appear/run. Run `hive enable`.
- **External fetch fails silently** → the origin isn't in `allowed_origins`
  (CSP blocked it). Add it, or route via `lc.api` if it's LC data.
- **`lc.api(..., { service })` rejected with `denied`** → the service isn't in
  `required_services` (or the org can't resolve it). Add it to the record.
- **Unstyled / wrong colors** → you hardcoded styles or loaded an external
  sheet. Use `.lc-*` / `--lc-*`.

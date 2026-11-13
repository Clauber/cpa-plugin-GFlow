# Management console

The host serves `static/manage.html` at `/v0/resource/plugins/gflow/manage`. It shows account stats, the account list, configuration, models, and the login-helper download, and calls `/v0/management/plugins/gflow/api/*` with the management key.

## Sub-features

- Connection: automatic (reads the management center's remembered login from `localStorage` key `cli-proxy-auth`) or manual (`#connection-setup`).
- Status cards: total accounts, recently verified logins, cached credits, Python runtime.
- Tabs: accounts, configuration, models and endpoints.
- Login-helper download and extension config copy.

## How to get to it (user POV)

In the CLIProxyAPI management center the operator opens the GFlow menu entry, or browses to the console URL directly on the host machine.

## Driving it with launch_host.py and the browser preview

1. `launch_host.py start`, then open `console` from `session.json` with `preview_open`.
2. Click the `#connection-setup` summary, type the management key into `#connection-key`, click `#connection-setup button`.
3. Wait about 4 seconds, then read `#connection-status` and the header with `preview_evaluate`; save a screenshot.
4. Click each tab in the navigation landmark and save a screenshot of each.
5. For a language check, count CJK characters in `document.body.innerText`; the English build should report 0.

## Gotchas

- Automatic connection fails on hosts whose management center stores `enc::v2::` logins; use manual connect.
- The accounts tab is empty on a clean install; account rows need a real Google login via the login helper.

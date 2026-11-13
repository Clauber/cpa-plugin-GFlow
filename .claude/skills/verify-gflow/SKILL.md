---
name: verify-gflow
description: Verify the GFlow CLIProxyAPI plugin the way an operator uses it. Loads a built gflow.dll into a real, isolated CLIProxyAPI host on Windows, checks registration, models, project control and host streaming over HTTP, and drives the GFlow management console in a browser. Use after any change to the plugin, its console, its registration metadata, or the host contract.
---

# Verify GFlow

GFlow is a native CLIProxyAPI plugin (`gflow.dll` with an embedded Python worker). Users touch three surfaces: the OpenAI-compatible API on the host (`/v1/models`, `/v1/chat/completions`), the host's management API (`/v0/management/plugins`), and the GFlow management console the host serves at `/v0/resource/plugins/gflow/manage`. The browser extension is a fourth surface, covered only by unit tests.

Every recipe here runs from the repository root in Git Bash on Windows. `PY` is a Python 3.12 with `psutil` (the repo's `.build/venv` works: `PY=.build/venv/Scripts/python.exe`).

## Inputs

- A CLIProxyAPI Windows build. Download a release zip from `https://github.com/router-for-me/CLIProxyAPI/releases`, check its sha256 against the release `checksums.txt`, and unzip it under `.build/hosts/cpa-<version>/`.
- A GFlow plugin archive that contains only `gflow.dll`: a release `gflow_<version>_windows_amd64.zip` or the `dist-windows-amd64` artifact from the Build workflow. The DLL cannot be built from this checkout without the Rust MSVC toolchain and the frozen worker; CI builds it.

## Launch

Two launch modes. Both stage everything under a new directory in `.build/` and never touch an installed CLIProxyAPI, EasyCLIProxyAPI, or its data.

Scripted smoke (no management key, exits when done):

```bash
$PY -B .github/scripts/host_project_smoke.py --host .build/hosts/cpa-<v>/cli-proxy-api.exe \
  --archive <gflow zip> --stage .build/stage-$(date +%s) --report .build/evidence/host-smoke-<label>.json
```

Interactive host for the console (management enabled with a random key):

```bash
$PY -B .claude/skills/verify-gflow/launch_host.py start --host .build/hosts/cpa-<v>/cli-proxy-api.exe \
  --archive <gflow zip> --stage .build/verify-<label>
```

Ready means the command printed `{"ready": true, "console": ...}`: the host answered `/v1/models` with `gflow-project-control`, so the plugin loaded and registered. The stage holds `session.json` with the port, pid, API key and management key, and `host.log`.

## Doctor

```bash
$PY -B .claude/skills/verify-gflow/launch_host.py doctor --stage .build/verify-<label>
```

Read-only. Worth driving when `models_status` is 200, `plugin_registered` is true, `plugin_version` is the version you built, and `gflow_models` lists 8 ids including `gflow-project-control`. `menus` and `config_fields` show the registration text the host shows operators.

## Drive

- API and host contract: run the scripted smoke above. It proves the host loads the plugin, requires an API key, runs `capabilities` and `projects.list` through `gflow-project-control`, keeps structured control errors, streams through the native host-stream callbacks with one `[DONE]`, and leaves the Google account database empty.
- Registration contract on the DLL itself: `$PY -B .github/scripts/smoke_plugin.py --library <dir>/gflow.dll --expected-version <v>` loads the DLL through ctypes on a clean install and asserts the negotiated `schema_version` (6 with no host version, the host's version up to 10), English registration and console text, management routes, and project control.
- Console: open `console` from `session.json` in the browser preview. Expand the details element `#connection-setup` (summary text is the manual-connect label), type the management key into `#connection-key`, and click `#connection-setup button`. Connected state: the header shows `v<version>`, `#connection-status` reports the Python worker answered, the total-accounts card reads `0`, and the Python runtime card shows a Python version. Then click each tab in the `navigation` landmark (accounts, configuration, models) and capture each.

## Evidence

Write every artifact to `.build/evidence/` with a label for the build under test (for example `baseline-0.1.20` or the commit sha): smoke reports (`host-smoke-*.json`), doctor output (`doctor-*.json`), DLL probe logs, and console screenshots saved with `preview_snapshot` `save: true` then copied there. A proof captures the connected console, not the disconnected landing state, and records the host version and DLL sha256 (the smoke report includes both). No Google account is involved: media generation and cloud project creation stay "not called"; say so in the report instead of implying generation works.

## Cleanup

```bash
$PY -B .claude/skills/verify-gflow/launch_host.py stop --stage .build/verify-<label>
```

`stop` terminates only the pid recorded in `session.json`, and only if its executable lives inside that stage. The scripted smoke stops its own host. Remove `.build/verify-*` and `.build/stage-*` directories when done; `.build/evidence/` stays.

## Features

See [features/README.md](features/README.md).

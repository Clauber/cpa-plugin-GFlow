# Project control through the API

`gflow-project-control` is a chat model that takes a JSON control message (`{"version":1,"op":...,"workspaceId":...}`) and returns a JSON receipt without generating media.

## Sub-features

- `capabilities` lists the 7 media models and the instance id.
- `projects.list` returns the fixed projects bound to the workspace (empty on a clean install).
- Unsupported protocol versions return a structured `unsupported_protocol` error.
- Streaming requests go through the host's native stream callbacks.

## How to get to it (user POV)

A client (CutFlow, or any OpenAI-compatible client) sends `POST /v1/chat/completions` with `model: gflow-project-control` and the host API key.

## Driving it with host_project_smoke.py

Run the scripted smoke. All 7 checks in the report must be `passed`, `hostStopped` and `existingServicesUnchanged` true, and `passed` true.

## Gotchas

- The smoke uses a synthetic auth file only so the host picks the plugin executor; it holds no Google session.
- `projects.create` is never called; it would create a real Google Flow project.

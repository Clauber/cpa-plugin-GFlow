# Host registration and model catalog

The host loads `gflow.dll`, calls `plugin.register`, and publishes GFlow's models and its management menu.

## Sub-features

- RPC schema negotiation: GFlow answers with the host's `schema_version` clamped to 6..10, and 6 when the host sends none.
- Registration metadata: name, version, description, and the `data_dir` config field the host shows in its plugin list.
- Model catalog: 7 media models plus `gflow-project-control`.

## How to get to it (user POV)

An operator drops the plugin archive into the host's `plugins/windows/amd64` directory and restarts the host. The plugin then appears in the host's plugin list, and its models appear in `/v1/models`.

## Driving it with launch_host.py and the smokes

1. `launch_host.py start` with the build under test; wait for `ready`.
2. `launch_host.py doctor`: expect `plugin_registered: true`, the built version, 8 `gflow-*` models, and English `menus[].description` and `config_fields[].description`.
3. `smoke_plugin.py --library <gflow.dll>`: asserts `schema_version` 6 for an empty request, 10 and 8 when the request carries them, and English metadata.

## Gotchas

- The host never reports the plugin's declared schema; host acceptance plus the DLL probe are the evidence.
- A host older than the declared schema refuses the plugin with `plugin schema version N is not supported` in `host.log`.

"""Start an isolated CLIProxyAPI host with the GFlow plugin and management enabled.

Usage:
  python launch_host.py start --host <cli-proxy-api.exe> --archive <gflow_*_windows_amd64.zip> --stage <new dir under .build>
  python launch_host.py doctor --stage <dir>
  python launch_host.py stop --stage <dir>

start writes <stage>/session.json (port, pid, management key, URLs) and returns once
the host lists gflow-project-control. The key never leaves the stage directory.
"""
import argparse
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def get(url, key, timeout=3):
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def start(host, archive, stage):
    stage = stage.resolve()
    if not stage.is_relative_to(ROOT / ".build") or stage.exists():
        sys.exit("--stage must be a new directory under .build/")
    plugins = stage / "plugins/windows/amd64"
    plugins.mkdir(parents=True)
    shutil.copy2(host, stage / "cli-proxy-api.exe")
    with zipfile.ZipFile(archive) as bundle:
        if bundle.namelist() != ["gflow.dll"]:
            sys.exit("the plugin archive must contain only gflow.dll")
        (plugins / "gflow.dll").write_bytes(bundle.read("gflow.dll"))
    (stage / "auths").mkdir()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    api_key, management_key = "verify-" + secrets.token_urlsafe(24), "mgmt-" + secrets.token_urlsafe(24)
    (stage / "config.yaml").write_text(f"""server:
  host: "127.0.0.1"
  port: {port}
  discovery:
    enabled: false
management:
  allow-remote: false
  secret-key: {json.dumps(management_key)}
  disable-control-panel: true
  disable-auto-update-panel: true
access:
  api-keys:
    - {json.dumps(api_key)}
oauth:
  auth-dir: {json.dumps(str(stage / "auths"))}
plugins:
  enabled: true
  dir: {json.dumps(str(stage / "plugins"))}
  configs:
    gflow:
      enabled: true
      data_dir: {json.dumps(str(stage / "gflow-data"))}
""", encoding="utf-8")
    for name in ("tmp", "profile/Roaming", "profile/Local"):
        (stage / name).mkdir(parents=True)
    environment = os.environ.copy()
    environment.update(TMP=str(stage / "tmp"), TEMP=str(stage / "tmp"), TMPDIR=str(stage / "tmp"),
                       APPDATA=str(stage / "profile/Roaming"), LOCALAPPDATA=str(stage / "profile/Local"),
                       PYTHONDONTWRITEBYTECODE="1")
    for name in ("GFLOW_WORKER_BINARY", "GFLOW_DATA_DIR", "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        environment.pop(name, None)
    log = (stage / "host.log").open("wb")
    process = subprocess.Popen([str(stage / "cli-proxy-api.exe"), "-config", str(stage / "config.yaml"), "-local-model"],
                               cwd=stage, env=environment, stdout=log, stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    base = f"http://127.0.0.1:{port}"
    session = {"pid": process.pid, "port": port, "base": base, "api_key": api_key, "management_key": management_key,
               "console": base + "/v0/resource/plugins/gflow/manage"}
    (stage / "session.json").write_text(json.dumps(session, indent=2), encoding="utf-8")
    deadline = time.monotonic() + 100
    while time.monotonic() < deadline:
        if process.poll() is not None:
            sys.exit(f"host exited early; see {stage / 'host.log'}")
        try:
            status, body = get(base + "/v1/models", api_key)
            if status == 200 and b"gflow-project-control" in body:
                print(json.dumps({"ready": True, "console": session["console"], "session": str(stage / "session.json")}))
                return
        except OSError:
            pass
        time.sleep(0.3)
    sys.exit("host never listed gflow-project-control")


def doctor(stage):
    session = json.loads((stage / "session.json").read_text(encoding="utf-8"))
    models = get(session["base"] + "/v1/models", session["api_key"])
    plugins = get(session["base"] + "/v0/management/plugins", session["management_key"])
    entry = next((item for item in json.loads(plugins[1]).get("plugins", []) if item.get("id") == "gflow"), {})
    print(json.dumps({"models_status": models[0], "gflow_models": [m["id"] for m in json.loads(models[1])["data"] if m["id"].startswith("gflow-")],
                      "plugin_registered": entry.get("registered"), "plugin_version": (entry.get("metadata") or {}).get("version"),
                      "menus": entry.get("menus"), "config_fields": entry.get("config_fields")}, ensure_ascii=False, indent=2))


def stop(stage):
    import psutil
    session = json.loads((stage / "session.json").read_text(encoding="utf-8"))
    try:
        process = psutil.Process(session["pid"])
    except psutil.NoSuchProcess:
        print("already stopped")
        return
    if not Path(process.exe()).resolve().is_relative_to(stage.resolve()):
        sys.exit("pid no longer belongs to this stage; not touching it")
    for child in process.children(recursive=True) + [process]:
        child.terminate()
    psutil.wait_procs([process], timeout=10)
    print("stopped")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "doctor", "stop"])
    parser.add_argument("--host", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--stage", type=Path, required=True)
    options = parser.parse_args()
    if options.command == "start":
        start(options.host.resolve(), options.archive.resolve(), options.stage)
    elif options.command == "doctor":
        doctor(options.stage.resolve())
    else:
        stop(options.stage.resolve())


if __name__ == "__main__":
    main()

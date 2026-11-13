"""Verify a non-editable wheel outside the checkout, with a Node-free native server."""

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, cwd, log=None, **kwargs):
    result = subprocess.run(
        [str(a) for a in args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf8",
        errors="replace",
        timeout=360,
        **kwargs,
    )
    if log:
        log.write_text(result.stdout + result.stderr, encoding="utf8")
    if result.returncode:
        raise RuntimeError("Release command failed; inspect the owned verification log")
    return result.stdout


def stop(process):
    if process.poll() is None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=10
            )
        else:
            process.terminate()
    process.wait(timeout=10)


def launch(python, work, env, args):
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    process = subprocess.Popen(
        [str(python), *args, "--port", str(port)],
        cwd=work,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process, f"http://127.0.0.1:{port}"


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def ready(process, base):
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError("Owned server exited before becoming ready")
        try:
            return get(base + "/health")
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Owned server did not start")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    wheel = args.wheel.resolve()
    work = Path(tempfile.mkdtemp(prefix="traceweaver-release-")).resolve()
    assert not work.is_relative_to(root)
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    node = shutil.which("node")
    source = None
    source_browser = None
    if args.source_check:
        source = work / "source"
        names = run(["git", "ls-files", "-z"], root).split("\0")
        for name in filter(None, names):
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, target)
        assert not (source / ".venv").exists()
        assert not (source / "web/node_modules").exists()
        assert not (source / "src/traceweaver/web_static").exists()
        run([sys.executable, "-m", "venv", source / ".venv"], work)
        source_python = source / (
            ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
        )
        run(
            [source_python, "-m", "pip", "install", "-r", "requirements-dev.lock", "-e", ".[dev]"],
            source,
            out / "source-pip.txt",
        )
        run([npm, "--prefix", "web", "ci"], source, out / "source-npm.txt")
        run([npm, "--prefix", "web", "run", "build"], source, out / "source-build.txt")
        run(
            [
                source_python,
                "-m",
                "traceweaver.judge",
                "--bundle",
                "examples/judge-demo",
                "--check",
            ],
            source,
            out / "source-check.txt",
        )
        source_env = os.environ.copy()
        source_env.pop("PYTHONPATH", None)
        server, origin = launch(
            source_python,
            source,
            source_env,
            ["-m", "traceweaver.judge", "--bundle", "examples/judge-demo"],
        )
        try:
            status, body = ready(server, origin)
            assert status == 200 and json.loads(body)["node_count"] == 51
            source_browser = json.loads(
                run(
                    [node, root / "scripts/release_browser.mjs", origin, out / "source-browser"],
                    source,
                    out / "source-browser-command.txt",
                )
            )
        finally:
            stop(server)
    run([sys.executable, "-m", "venv", work / "env"], work)
    python = work / ("env/Scripts/python.exe" if os.name == "nt" else "env/bin/python")
    run(
        [python, "-m", "pip", "install", "-c", root / "requirements-dev.lock", wheel],
        work,
        out / "wheel-pip.txt",
    )
    run([python, "-m", "pip", "check"], work, out / "wheel-pip-check.txt")
    location = run([python, "-c", "import traceweaver;print(traceweaver.__file__)"], work).strip()
    assert str(work).lower() in location.lower() and str(root).lower() not in location.lower()
    bundle = work / "bundle"
    shutil.copytree(root / "examples/judge-demo", bundle)
    before = {p.name: digest(p) for p in bundle.iterdir() if p.is_file()}
    check = json.loads(
        run([python, "-m", "traceweaver.judge", "--bundle", bundle, "--check"], work)
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PATH"] = (
        str(python.parent)
        + os.pathsep
        + str(Path(os.environ.get("SystemRoot", "/usr")) / "System32")
    )
    assert shutil.which("node", path=env["PATH"]) is None
    process, base = launch(python, work, env, ["-m", "traceweaver.judge", "--bundle", str(bundle)])
    try:
        status, body = ready(process, base)
        health = json.loads(body)
        assert status == 200 and health["node_count"] == 51 and health["relationship_count"] == 67
        _, html = get(base)
        with zipfile.ZipFile(wheel) as archive:
            for asset in re.findall(r'(?:src|href)="(/assets/[^\"]+)"', html.decode()):
                status, content = get(base + asset)
                assert status == 200 and content == archive.read("traceweaver/web_static" + asset)
        browser = json.loads(
            run(
                [
                    node,
                    root / "scripts/release_browser.mjs",
                    base,
                    out / "browser",
                ],
                work,
                out / "browser-command.txt",
            )
        )
    finally:
        stop(process)
    assert before == {p.name: digest(p) for p in bundle.iterdir() if p.is_file()}
    # Test actual HTTP storage errors against independent copies, never a user-store writer.
    failures = {}
    helper = work / "failure_server.py"
    helper.write_text(
        "import sys,uvicorn\nfrom traceweaver.api import create_app\n"
        "from traceweaver.config import Settings\n"
        "uvicorn.run(create_app(Settings(database=sys.argv[1])),host='127.0.0.1',port=int(sys.argv[3]))\n",
        encoding="utf8",
    )
    for kind in ("missing", "corrupt", "locked"):
        copy = work / (kind + ".rl")
        holder = None
        if kind == "corrupt":
            copy.write_bytes(b"not a Relate store")
        if kind == "locked":
            shutil.copyfile(bundle / "traceweaver-demo.rl", copy)
            holder = subprocess.Popen(
                [
                    str(python),
                    "-u",
                    "-c",
                    "import sys;from traceweaver.storage import GraphStore;"
                    "s=GraphStore(sys.argv[1],read_only=False);s.__enter__();print('READY',flush=True);"
                    "sys.stdin.readline();s.__exit__(None,None,None)",
                    str(copy),
                ],
                cwd=work,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            assert holder.stdout.readline().strip() == "READY"
        process, base = launch(python, work, env, [str(helper), str(copy)])
        try:
            status, body = ready(process, base)
            assert status == 503 and json.loads(body) == {"detail": "Graph database unavailable"}
            status, body = get(base + "/incidents/INC-001/dashboard")
            assert status == 503 and json.loads(body) == {"detail": "Graph database unavailable"}
            failures[kind] = {"status": status, "generic": True, "fallback": False}
        finally:
            stop(process)
            if holder:
                holder.communicate("close\n", timeout=10)
                assert holder.returncode == 0
    result = {
        "status": "PASS",
        "outside_checkout": True,
        "non_editable": True,
        "node_on_server_path": False,
        "fresh_source_setup": bool(source),
        "source_browser": source_browser,
        "wheel_sha256": digest(wheel),
        "check": check,
        "browser": browser,
        "failure_copies": failures,
        "bundle_bytes_unchanged": True,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    (out / "scratch.json").write_text(json.dumps({"work": str(work)}), encoding="utf8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()

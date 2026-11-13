"""Verify the independently installed public image with real browser proof and bounded resources."""

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def command(args, cwd, *, env=None, timeout=360, log=None):
    result = subprocess.run(
        [str(arg) for arg in args], cwd=cwd, env=env, capture_output=True, timeout=timeout
    )
    if log:
        log.write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("Owned public verification command failed")
    return result.stdout.decode("utf8", errors="replace")


def get(base, path, method="GET"):
    try:
        with urllib.request.urlopen(
            urllib.request.Request(base + path, method=method), timeout=15
        ) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with socket.socket() as available:
        available.bind(("127.0.0.1", 0))
        port = available.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    container = command(
        [
            "docker",
            "run",
            "--detach",
            "--read-only",
            "--memory=512m",
            "--cpus=0.1",
            "--pids-limit=64",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--publish",
            f"127.0.0.1:{port}:10000",
            "--env",
            f"TRACEWEAVER_PUBLIC_HOSTS=127.0.0.1:{port}",
            "--env",
            "TRACEWEAVER_PUBLIC_ALLOW_HTTP=1",
            args.image,
        ],
        root,
    ).strip()
    if not re.fullmatch(r"[a-f0-9]{64}", container):
        raise RuntimeError("Owned container identity unavailable")
    try:
        for _ in range(150):
            try:
                status, body, _ = get(base, "/health")
                if status == 200:
                    break
            except OSError:
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("Owned public container did not start")
        assert json.loads(body)["database_engine"] == "relate"
        configuration = json.loads(command(["docker", "inspect", container], root))[0]
        assert configuration["HostConfig"]["Memory"] == 512 * 1024 * 1024
        assert configuration["HostConfig"]["ReadonlyRootfs"] is True
        assert configuration["HostConfig"]["NanoCpus"] == 100_000_000
        assert configuration["Config"]["User"] == "10001:10001"
        status, body, headers = get(base, "/incidents/INC-001/dashboard")
        assert status == 200 and len(json.loads(body)["investigation"]["candidates"]) == 2
        assert "connect-src 'self'" in headers["content-security-policy"]
        status, body, _ = get(base, "/incidents/CASE-INC/dashboard")
        classes = [p["classification"] for p in json.loads(body)["investigation"]["contradictions"]]
        assert status == 200 and classes.count("CONFLICTING_OBSERVATIONS") == 1
        assert classes.count("UNDETERMINED") == 2
        assert get(base, "/console/models/capabilities", "POST")[0] == 404
        node = shutil.which("node")
        if not node:
            raise RuntimeError("Browser test client requires Node outside the server image")
        env = {**os.environ, "TRACEWEAVER_PUBLIC_BASE_URL": base}
        browser = command(
            [node, root / "scripts/test_public_browser.mjs"],
            root,
            env=env,
            log=output / "browser-command.txt",
        )
        (output / "browser.txt").write_text(browser, encoding="utf8")
        match = re.search(r"Owned public browser evidence: (.+)", browser)
        assert match
        evidence = Path(match.group(1).strip())
        report = json.loads((evidence / "playwright.json").read_text(encoding="utf8"))
        assert report["stats"]["unexpected"] == 0 and report["stats"]["skipped"] == 0
        assert report["stats"]["expected"] >= 11
        measured = json.loads(
            command(
                [
                    "docker",
                    "exec",
                    container,
                    "python",
                    "-c",
                    "import pathlib,json,hashlib,sys,os,traceweaver,importlib.util;"
                    "p=pathlib.Path('/sys/fs/cgroup/memory.peak');"
                    "print(json.dumps({'python':sys.version.split()[0],'uid':os.geteuid(),"
                    "'module':traceweaver.__file__,'node_in_image':bool(__import__('shutil').which('node')),"
                    "'memory_peak_bytes':int(p.read_text()) if p.is_file() else None,"
                    "'database_sha256':hashlib.sha256(pathlib.Path('/app/judge-demo/traceweaver-demo.rl').read_bytes()).hexdigest(),"
                    "'manifest_sha256':hashlib.sha256(pathlib.Path('/app/judge-demo/MANIFEST.json').read_bytes()).hexdigest()}))",
                ],
                root,
            )
        )
        assert measured["python"].startswith("3.11.") and measured["uid"] == 10001
        assert "site-packages" in measured["module"] and measured["node_in_image"] is False
        assert (
            measured["database_sha256"]
            == "29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239"
        )
        assert (
            measured["manifest_sha256"]
            == "50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab"
        )
        result = {
            "status": "PASS",
            "image": args.image,
            "runtime": measured,
            "browser_passed": report["stats"]["expected"],
            "browser_skipped": 0,
            "memory_limit_bytes": 512 * 1024 * 1024,
            "cpu_limit": 0.1,
            "read_only_filesystem": True,
            "host_port_numeric_loopback_only": True,
            "scope": "Local measured synthetic container workload, not a Render memory guarantee",
        }
        (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf8")
        print(json.dumps(result))
    finally:
        logs = subprocess.run(["docker", "logs", container], capture_output=True, timeout=15)
        (output / "container.txt").write_bytes(logs.stdout + logs.stderr)
        subprocess.run(
            ["docker", "stop", "--time", "10", container], capture_output=True, timeout=20
        )


if __name__ == "__main__":
    main()

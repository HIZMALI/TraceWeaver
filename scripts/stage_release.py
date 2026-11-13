"""Export only allowlisted judge artifacts to a new directory, with offline runtime wheels."""

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from verify_release import digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    wheels = output / "wheels"
    wheels.mkdir()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--only-binary=:all:",
            "-c",
            str(root / "requirements-dev.lock"),
            "--dest",
            str(wheels),
            str(args.wheel.resolve()),
        ],
        check=True,
        timeout=180,
    )
    shutil.copytree(root / "examples/judge-demo", output / "judge-demo")
    for source, name in [
        ("docs/JUDGE_QUICK_START.md", "QUICK_START.md"),
        ("docs/SPRINT07_PUBLIC_READINESS.md", "PUBLIC_READINESS.md"),
        ("docs/DEPENDENCY_LICENSES.md", "DEPENDENCY_LICENSES.md"),
        ("web/public/assets/third-party-licenses.txt", "third-party-licenses.txt"),
        ("requirements-dev.lock", "requirements-dev.lock"),
        ("scripts/run_release.ps1", "RUN_JUDGE.ps1"),
    ]:
        shutil.copyfile(root / source, output / name)
    files = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file()
    }
    assert [n for n in files if n.endswith(".rl")] == ["judge-demo/traceweaver-demo.rl"]
    assert not any(n.endswith((".exe", ".mp4", ".webm")) for n in files)
    manifest = {
        "format": "traceweaver-local-release-1",
        "platform": platform.system(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "license_decision": "OWNER_PENDING",
        "publication": "NOT_PERFORMED",
        "files": files,
    }
    (output / "SHA256.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    print(
        json.dumps(
            {
                "files": len(files),
                "manifest_sha256": digest(output / "SHA256.json"),
                "bytes": sum(p.stat().st_size for p in output.rglob("*") if p.is_file()),
            }
        )
    )


if __name__ == "__main__":
    main()

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
        ("docs/PACKAGING.md", "PUBLIC_READINESS.md"),
        ("docs/DEPENDENCY_LICENSES.md", "DEPENDENCY_LICENSES.md"),
        ("LICENSE", "LICENSE"),
        ("NOTICE", "NOTICE"),
        ("web/public/assets/third-party-licenses.txt", "third-party-licenses.txt"),
        ("requirements-dev.lock", "requirements-dev.lock"),
        ("scripts/run_release.ps1", "RUN_JUDGE.ps1"),
    ]:
        shutil.copyfile(root / source, output / name)
    # Retarget source-document links for the standalone export without changing source guides.
    links = {
        "../README.md#quick-start": "https://github.com/HIZMALI/TraceWeaver#quick-start",
        "../examples/judge-demo/MANIFEST.json": "judge-demo/MANIFEST.json",
        "../examples/judge-demo/README.md": "judge-demo/README.md",
        "ARCHITECTURE.md": "https://github.com/HIZMALI/TraceWeaver/blob/main/docs/ARCHITECTURE.md",
        "AGENT_TOOL_CONTRACT.md": (
            "https://github.com/HIZMALI/TraceWeaver/blob/main/docs/AGENT_TOOL_CONTRACT.md"
        ),
        "PACKAGING.md": "PUBLIC_READINESS.md",
        "../LICENSE": "LICENSE",
        "../NOTICE": "NOTICE",
        "../web/public/assets/third-party-licenses.txt": "third-party-licenses.txt",
    }
    for name in ("QUICK_START.md", "DEPENDENCY_LICENSES.md"):
        path = output / name
        text = path.read_text(encoding="utf8")
        for target, replacement in links.items():
            text = text.replace("](" + target + ")", "](" + replacement + ")")
        path.write_text(text, encoding="utf8", newline="\n")
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
        "license_decision": "Apache-2.0",
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

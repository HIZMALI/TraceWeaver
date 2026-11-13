"""Build from a fresh owned source copy so setuptools cannot retain old hashed web assets."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", required=True, type=Path, help="Directory without an existing TraceWeaver wheel"
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if list(output.glob("traceweaver-*.whl")):
        parser.error("Choose a new output directory; existing wheels are preserved")
    root = Path(__file__).resolve().parents[1]
    if not (root / "src/traceweaver/web_static/index.html").is_file():
        parser.error("Build the frontend first: npm --prefix web run build")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="traceweaver-wheel-source-") as temporary:
        source = Path(temporary)
        shutil.copytree(
            root / "src",
            source / "src",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
        )
        for name in ("pyproject.toml", "README.md"):
            shutil.copyfile(root / name, source / name)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                str(source),
                "--no-deps",
                "--wheel-dir",
                str(output),
            ],
            check=True,
            timeout=180,
        )
    (wheel,) = output.glob("traceweaver-*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert (
            sum(n.startswith("traceweaver/web_static/assets/") and n.endswith(".js") for n in names)
            == 1
        )
        assert (
            sum(
                n.startswith("traceweaver/web_static/assets/") and n.endswith(".css") for n in names
            )
            == 1
        )
        assert "traceweaver/web_static/assets/third-party-licenses.txt" in names
        assert not any(n.endswith(".rl") for n in names)
    print(
        json.dumps(
            {
                "wheel": wheel.name,
                "bytes": wheel.stat().st_size,
                "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                "fresh_source_build": True,
                "single_asset_generation": True,
            }
        )
    )


if __name__ == "__main__":
    main()

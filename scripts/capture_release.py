"""Capture the installed offline judge application; optionally encode with an existing FFmpeg."""

import argparse
import json
import os
import shutil
from pathlib import Path

from verify_release import digest, launch, ready, run, stop


def subtitle_time(seconds):
    centiseconds = round(seconds * 100)
    return (
        f"{centiseconds // 360000}:{centiseconds // 6000 % 60:02}:"
        f"{centiseconds // 100 % 60:02}.{centiseconds % 100:02}"
    )


def captions(events):
    """Use measured successful action times; captions never precede their corresponding proof."""
    if len(events) != 10 or any(
        a["seconds"] >= b["seconds"] for a, b in zip(events, events[1:], strict=False)
    ):
        raise ValueError("Ten strictly ordered real scene cues required")
    header = (
        """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
[V4+ Styles]
"""
        + (
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,29,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,"
            "0,0,0,0,100,100,0,0,1,0,0,2,55,55,14,1\n"
            "Style: Label,Arial,18,&H00B9D9C5,&H00FFFFFF,&H00000000,&H00000000,"
            "0,0,0,0,100,100,0,0,1,0,0,8,20,20,968,1\n"
        )
        + """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        + (
            "Dialogue: 0,0:00:00.00,0:01:55.00,Label,,0,0,0,,EXPLANATORY CAPTIONS | "
            "SYNTHETIC / READ ONLY / OFFLINE / NOT AI-GENERATED\n"
        )
    )
    for n, event in enumerate(events):
        end = events[n + 1]["seconds"] if n + 1 < len(events) else 115
        text = event["caption"]
        if any(c in text for c in "{}\\\n\r") or not 0 <= event["seconds"] < end <= 115:
            raise ValueError("Unsafe or out-of-range caption")
        header += (
            f"Dialogue: 1,{subtitle_time(event['seconds'])},{subtitle_time(end)},"
            f"Default,,0,0,0,,{text}\n"
        )
    return header


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python", type=Path, required=True, help="Independent installed-wheel Python"
    )
    parser.add_argument("--bundle", type=Path, required=True, help="Intact synthetic bundle COPY")
    parser.add_argument("--output", type=Path, required=True, help="New ignored output directory")
    parser.add_argument(
        "--ffmpeg", type=Path, help="Existing encoder, never installed or redistributed"
    )
    parser.add_argument(
        "--check-actions", action="store_true", help="Validate actions without video holds"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output, bundle, python = args.output.resolve(), args.bundle.resolve(), args.python.resolve()
    if output.exists():
        parser.error("Choose a new output; existing recordings are preserved")
    output.parent.mkdir(parents=True, exist_ok=True)
    check = json.loads(
        run([python, "-m", "traceweaver.judge", "--bundle", bundle, "--check"], bundle)
    )
    assert check["status"] == "PASS" and check["graph_counts"] == {
        "node_count": 51,
        "relationship_count": 67,
    }
    before = {p.name: digest(p) for p in bundle.iterdir() if p.is_file()}
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PATH"] = (
        str(python.parent)
        + os.pathsep
        + str(Path(os.environ.get("SystemRoot", "/usr")) / "System32")
    )
    process, base = launch(
        python, bundle, env, ["-m", "traceweaver.judge", "--bundle", str(bundle)]
    )
    try:
        status, _ = ready(process, base)
        assert status == 200
        run(
            [
                shutil.which("node"),
                root / "scripts/record_judge_demo.mjs",
                base,
                output,
                "check-actions" if args.check_actions else "record",
            ],
            root,
        )
    finally:
        stop(process)
    assert before == {p.name: digest(p) for p in bundle.iterdir() if p.is_file()}
    capture = json.loads((output / "capture.json").read_text(encoding="utf8"))
    (output / "captions.ass").write_text(captions(capture["events"]), encoding="utf8")
    if args.ffmpeg and not args.check_actions:
        run(
            [
                args.ffmpeg.resolve(),
                "-hide_banner",
                "-nostdin",
                "-n",
                "-i",
                "native-judge-demo.webm",
                "-t",
                "115",
                "-an",
                "-c:v",
                "copy",
                "traceweaver-judge-115s.webm",
            ],
            output,
            output / "webm-trim.txt",
        )
        run(
            [
                args.ffmpeg.resolve(),
                "-hide_banner",
                "-nostdin",
                "-n",
                "-i",
                "native-judge-demo.webm",
                "-vf",
                "pad=1920:1080:0:0:black,ass=captions.ass",
                "-t",
                "115",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "traceweaver-judge-115s-1080p.mp4",
            ],
            output,
            output / "encode.txt",
        )
    hashes = {p.name: digest(p) for p in output.iterdir() if p.is_file()}
    (output / "sha256.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf8")
    print(
        json.dumps(
            {
                "status": "CAPTURED_NOT_YET_VISUALLY_REVIEWED",
                "bundle_unchanged": True,
                "model_calls": 0,
                "sha256": hashes,
            }
        )
    )


if __name__ == "__main__":
    main()

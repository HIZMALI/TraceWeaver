"""Bounded regular-file access for offline tools. URLs and remote paths are not inputs."""

import ctypes
import json
import os
import re
import stat
from pathlib import Path

from traceweaver.tool_errors import ToolError

MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_JSON_DEPTH = 8


def local_path(value: str | Path, *, must_exist: bool = False) -> Path:
    text = os.fspath(value)
    if (
        text.startswith(("\\\\", "//"))
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", text)
        or (re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", text) and not re.match(r"^[A-Za-z]:[\\/]", text))
        or "\x00" in text
    ):
        raise ToolError("UNSAFE_LOCAL_PATH", "Only local filesystem paths are accepted.", 8)
    # abspath is lexical: it does not resolve a remote/symlink target.
    path = Path(os.path.abspath(text))
    if os.name == "nt":
        if ":" in str(path)[2:] or ctypes.windll.kernel32.GetDriveTypeW(path.anchor) != 3:
            raise ToolError("UNSAFE_LOCAL_PATH", "A local fixed drive is required.", 8)
        reserved = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{n}" for n in range(1, 10)),
            *(f"LPT{n}" for n in range(1, 10)),
        }
        if any(part.split(".")[0].upper() in reserved for part in path.parts):
            raise ToolError("UNSAFE_LOCAL_PATH", "Device paths are not supported.", 8)
    elif os.name == "posix" and Path("/proc/self/mountinfo").is_file():
        mounts = []
        for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
            fields, tail = line.split(" - ", 1)
            mount = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), fields.split()[4])
            if path.is_relative_to(Path(mount)):
                mounts.append((len(mount), tail.split()[0]))
        local_types = {
            "ext2",
            "ext3",
            "ext4",
            "xfs",
            "btrfs",
            "overlay",
            "tmpfs",
            "zfs",
            "rootfs",
            "ramfs",
        }
        if not mounts or max(mounts)[1] not in local_types:
            raise ToolError(
                "UNSAFE_LOCAL_PATH", "Only recognized local filesystems are supported.", 8
            )
    else:
        raise ToolError("UNSAFE_LOCAL_PATH", "Local filesystem classification is unavailable.", 8)
    for component in [*reversed(path.parents), path]:
        try:
            info = component.lstat()
        except FileNotFoundError:
            if must_exist:
                raise ToolError(
                    "INPUT_NOT_FOUND", "The selected local input does not exist.", 9
                ) from None
            break
        except OSError:
            raise ToolError(
                "LOCAL_ACCESS_ERROR", "Cannot inspect the selected local path.", 1
            ) from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ToolError(
                "UNSAFE_LOCAL_PATH", "Symlink and reparse-point traversal is not allowed.", 8
            )
    return path


def read_local_bytes(value: str | Path, limit: int = MAX_INPUT_BYTES) -> bytes:
    path = local_path(value, must_exist=True)
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ToolError("NOT_REGULAR_FILE", "Input must be a regular local file.", 8)
        if info.st_size > limit:
            raise ToolError("INPUT_TOO_LARGE", "Input exceeds the admitted byte limit.")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        with os.fdopen(os.open(path, flags), "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ToolError("NOT_REGULAR_FILE", "Input must be a regular local file.", 8)
            data = source.read(limit + 1)
            after = os.fstat(source.fileno())
        if len(data) > limit:
            raise ToolError("INPUT_TOO_LARGE", "Input exceeds the admitted byte limit.")
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ino,
        ) or len(data) != after.st_size:
            raise ToolError("INPUT_CHANGED", "Input changed while it was being read.")
        return data
    except OSError:
        raise ToolError(
            "LOCAL_ACCESS_ERROR", "Cannot read the selected regular local file.", 1
        ) from None


def parse_json_document(data: bytes, *, max_depth: int = MAX_JSON_DEPTH) -> dict:
    try:
        text = data.decode("utf-8")
    except UnicodeError:
        raise ToolError("INVALID_JSON", "JSON input must be UTF-8.") from None
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > max_depth:
                raise ToolError("JSON_DEPTH_LIMIT", "JSON exceeds its admitted container depth.")
        elif char in "]}":
            depth -= 1

    def unique_object(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ToolError("DUPLICATE_JSON_KEY", "Duplicate JSON object keys are not allowed.")
            result[key] = item
        return result

    def invalid_constant(value):
        raise ToolError("INVALID_JSON", "Non-finite JSON constants are not allowed.")

    try:
        result = json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    except (ValueError, RecursionError):
        raise ToolError("INVALID_JSON", "Input is not a valid JSON document.") from None
    if not isinstance(result, dict):
        raise ToolError("INVALID_JSON", "The document must be a JSON object.")
    return result


def canonical_json(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"

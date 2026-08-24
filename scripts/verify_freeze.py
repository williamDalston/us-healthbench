"""Verify the v1.0 benchmark against the frozen SHA-256 in VERSION.json.

Line-ending note: v1.0 was frozen on a Windows workstation, so the recorded
content hash is over CRLF-terminated bytes. Git may check the file out with
LF endings depending on platform and core.autocrlf, which changes the bytes
without changing the content. This script hashes the raw file first and, on
mismatch, retries against a CRLF-normalized form so a clone on any platform
can confirm the freeze is intact.

Exit code 0 if the freeze verifies, 1 otherwise.

Usage:  python -m scripts.verify_freeze
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

BENCH_DIR = Path("data/benchmark_v1")
VERSION = BENCH_DIR / "VERSION.json"


def main() -> int:
    version = json.loads(VERSION.read_text(encoding="utf-8"))
    expected = version["content_hash_sha256"]
    items = BENCH_DIR / version["files"]["items"]
    raw = items.read_bytes()

    as_is = hashlib.sha256(raw).hexdigest()
    lf = raw.replace(b"\r\n", b"\n")
    as_crlf = hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest()

    n_items = len([ln for ln in raw.decode("utf-8").splitlines() if ln.strip()])
    print(f"file:     {items}")
    print(f"items:    {n_items} (expected {version['total_items']})")
    print(f"expected: {expected}")

    if as_is == expected:
        print(f"actual:   {as_is}  [raw bytes]")
        ok = True
    elif as_crlf == expected:
        print(f"actual:   {as_crlf}  [CRLF-normalized]")
        print("note:     working copy has LF endings; freeze verifies after normalization")
        ok = True
    else:
        print(f"actual:   {as_is}  [raw bytes]")
        print(f"          {as_crlf}  [CRLF-normalized]")
        ok = False

    if n_items != version["total_items"]:
        print("FAIL: item count does not match VERSION.json")
        return 1
    print("PASS: benchmark freeze verified" if ok else "FAIL: content hash mismatch")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Write the 21 November 2026 front-page image to the output directory.

The image is bundled in this repository as entry.png (JPEG bytes under a
.png name, which make.fun allows: the file type is told apart by its first
bytes). This program copies it byte for byte to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output) and verifies the copy:
dimensions 1024x1024, size at most 1 MiB, and identical sha256.

Standard library only; no network; deterministic: every run writes the
same bytes.
"""

import hashlib
import os
import sys
from pathlib import Path

EXPECTED_SHA256 = "a3ac6bf957993d9fd6af272192bf91d34af917a21e6bb7c2c05507a83a09230d"
EXPECTED_SIZE = 284674
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_BYTES = 1048576


def image_dimensions(data):
    """Return (width, height) of a PNG or JPEG byte string, stdlib only."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        return width, height
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError("not a PNG or JPEG file")
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            raise ValueError("bad JPEG marker at offset %d" % pos)
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        length = int.from_bytes(data[pos + 2:pos + 4], "big")
        if length < 2 or pos + 2 + length > len(data):
            raise ValueError("truncated JPEG segment")
        if marker in (0xC0, 0xC1, 0xC2):
            height = int.from_bytes(data[pos + 5:pos + 7], "big")
            width = int.from_bytes(data[pos + 7:pos + 9], "big")
            return width, height
        pos += 2 + length
    raise ValueError("no JPEG start-of-frame marker found")


def fail(message):
    print("error: %s" % message, file=sys.stderr)
    return 1


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    here = Path(__file__).resolve().parent
    src = here / "entry.png"
    if not src.is_file():
        return fail("bundled image not found: %s" % src)
    data = src.read_bytes()
    if len(data) != EXPECTED_SIZE:
        return fail("bundled image is %d bytes, expected %d"
                    % (len(data), EXPECTED_SIZE))
    if len(data) > MAX_BYTES:
        return fail("bundled image exceeds 1 MiB")
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        return fail("bundled image sha256 mismatch")
    width, height = image_dimensions(data)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        return fail("bundled image is %dx%d, expected %dx%d"
                    % (width, height, EXPECTED_WIDTH, EXPECTED_HEIGHT))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dst = out / "entry.png"
    dst.write_bytes(data)

    back = dst.read_bytes()
    if len(back) != EXPECTED_SIZE:
        return fail("written copy is %d bytes, expected %d"
                    % (len(back), EXPECTED_SIZE))
    if hashlib.sha256(back).hexdigest() != EXPECTED_SHA256:
        return fail("written copy sha256 mismatch")
    back_width, back_height = image_dimensions(back)
    if (back_width, back_height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        return fail("written copy is %dx%d, expected %dx%d"
                    % (back_width, back_height,
                       EXPECTED_WIDTH, EXPECTED_HEIGHT))
    print("wrote %s (%dx%d, %d bytes, sha256 %s)"
          % (dst, back_width, back_height, len(back), EXPECTED_SHA256))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

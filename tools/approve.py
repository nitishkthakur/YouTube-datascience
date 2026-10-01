"""Approve a shot list — binding the approval to its content.

    uv run python tools/approve.py <tier_dir>              # Nitish, after reading shotlist.md
    uv run python tools/approve.py <tier_dir> --revoke

Rewrites the `Status:` line as `Status: approved <hash>` where <hash> is the sha256 (8 hex) of
the file with the Status line removed. status.py recomputes it: any later edit shows as
"approved but edited since" and the tier is not approved until re-run. A bare
`Status: approved` without a hash is treated as not approved.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

STATUS_RE = re.compile(r"^Status:\s*(.*)$", re.M)


def body_hash(text: str) -> str:
    body = STATUS_RE.sub("", text, count=1)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]


def approval_state(text: str) -> tuple[str, str]:
    """('approved'|'edited'|'draft'|'unbound'|'none', detail)."""
    m = STATUS_RE.search(text)
    if not m:
        return "none", "no Status line"
    value = m.group(1).strip()
    parts = value.split()
    if not parts or parts[0].lower() != "approved":
        return "draft", value
    if len(parts) < 2:
        return "unbound", "approved without hash — run tools/approve.py"
    return ("approved", parts[1]) if parts[1] == body_hash(text) else ("edited", f"approved as {parts[1]}, now {body_hash(text)}")


def set_status(text: str, value: str) -> str:
    if STATUS_RE.search(text):
        return STATUS_RE.sub(f"Status: {value}", text, count=1)
    return text.rstrip("\n") + f"\n\nStatus: {value}\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("tier", type=Path)
    ap.add_argument("--revoke", action="store_true")
    args = ap.parse_args(argv)
    path = args.tier / "shotlist.md"
    text = path.read_text()
    if args.revoke:
        path.write_text(set_status(text, "draft"))
        print(f"{path}: Status: draft")
        return 0
    # hash the body as it will be after the Status line is rewritten
    new = set_status(text, "approved PENDING")
    h = body_hash(new)
    path.write_text(set_status(text, f"approved {h}"))
    print(f"{path}: Status: approved {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

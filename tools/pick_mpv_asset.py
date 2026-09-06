#!/usr/bin/env python3
"""Pick the ONE libmpv archive to ship from a zhongfly/mpv-winbuild release.

The release lists several ``mpv-dev`` archives per architecture, and the
names differ only by a suffix: ``mpv-dev-x86_64-<date>-git-<hash>.7z`` is
the baseline build, ``mpv-dev-x86_64-v3-...`` is compiled for x86-64-v3
(AVX2 - "a CPU not older than Intel Haswell or AMD Excavator"), and there
are LGPL variants. A substring test like ``'mpv-dev-x86_64' in name``
matches the v3 archive too, and which one ``next()`` returned depended on
the order the API happened to list them in. The CI runner has AVX2, so a
v3 build passes the self-check there and then refuses to load on an older
PC - silently, as the embedded player merely falls back to external mpv.

Match the whole name instead, and insist on exactly one hit.

    curl .../releases/latest | python tools/pick_mpv_asset.py x86_64
"""
from __future__ import annotations

import json
import re
import sys


def pick(names: list[str], arch: str) -> str:
    """The baseline ``mpv-dev`` archive for *arch* (``x86_64``/``aarch64``)
    among *names*. Raises ``LookupError`` unless exactly one matches."""
    pat = re.compile(
        rf"^mpv-dev-{re.escape(arch)}-\d{{8}}-git-[0-9a-f]+\.7z$")
    hits = [n for n in names if pat.match(n)]
    if len(hits) != 1:
        raise LookupError(
            f"expected exactly one baseline mpv-dev archive for {arch}, "
            f"found {hits or 'none'} among {sorted(names)}")
    return hits[0]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: pick_mpv_asset.py <x86_64|aarch64>  < release.json",
              file=sys.stderr)
        return 2
    release = json.load(sys.stdin)
    assets = release.get("assets") or []
    if not assets:
        print("::error::no assets in the release JSON (rate-limited? body: "
              f"{json.dumps(release)[:300]})", file=sys.stderr)
        return 1
    by_name = {a["name"]: a["browser_download_url"] for a in assets}
    try:
        print(by_name[pick(list(by_name), argv[0])])
    except LookupError as e:
        print(f"::error::{e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

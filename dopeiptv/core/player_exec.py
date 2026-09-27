"""Locate external player binaries (mpv / VLC) on the host.

A small OS-integration helper. It lives in ``core`` because both the
recording manager (``core``) and the external-player launchers
(``media``) need it, and neither layer should reach up into the other.
"""

from __future__ import annotations

import os
import shutil
import sys

#: Popen creationflags for a console program (ffmpeg, ffprobe) started from
#: the app. A windowed Windows build has no console of its own, so Windows
#: gave each one a console window: one flashing up per thumbnail and probe,
#: and one sitting open for the whole of a recording - close it and the
#: recording died. CREATE_NO_WINDOW; 0 everywhere else, where Popen accepts
#: nothing but 0.
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def find_player_executable(player: str) -> str | None:
    """Locate the mpv or vlc binary, or None if it isn't installed."""
    if player == "mpv":
        candidates = ["mpv"]
    else:
        candidates = ["vlc", "cvlc"]
    if sys.platform == "darwin":
        from .platform_macos import extra_player_candidates
        candidates += extra_player_candidates(player)
    for c in candidates:
        if os.path.isabs(c):
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c
        else:
            found = shutil.which(c)
            if found:
                return found
    return None

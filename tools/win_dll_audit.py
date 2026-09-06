#!/usr/bin/env python3
"""Audit a Windows DLL's import table against what a clean Windows provides.

The libmpv we ship on Windows (zhongfly/mpv-winbuild's ``libmpv-2.dll``)
hard-links ``vulkan-1.dll`` - the Vulkan loader, which is NOT part of
Windows: GPU vendor drivers install it. On a PC whose graphics driver
predates Vulkan, on a VM, or on the Microsoft Basic Display Adapter, Windows
refuses to load ``mpv-2.dll`` ("The specified module could not be found"),
python-mpv reports "ctypes.CDLL could not load it", and the app quietly
falls back to an external player - issue #19, "Windows no embedded player".
The release self-check never noticed because the CI runner happens to have
the loader.

So: for every DLL named on the command line, list what it imports and fail
loudly on anything that is neither shipped next to it nor part of Windows.
Runs anywhere (pure Python, no Windows needed) - it reads the PE import
directory itself.

    python tools/win_dll_audit.py dist/dopeiptv/_internal/mpv-2.dll

Exit status 1 if any import is unresolved. An inbox DLL missing from
``INBOX`` below shows up as unresolved too: add it here once you have
checked it really ships with Windows 10.
"""
from __future__ import annotations

import os
import struct
import sys

# DLLs every Windows 10 installation has in System32. Deliberately a
# literal list: a name not on it is a question to answer, not a pattern to
# widen. API-set forwarders (api-ms-win-*, ext-ms-win-*) are matched by
# prefix below, since the set is open-ended and all of them are inbox.
INBOX = {
    "advapi32.dll", "avicap32.dll", "avrt.dll", "bcrypt.dll",
    "bcryptprimitives.dll", "cfgmgr32.dll", "comctl32.dll", "comdlg32.dll",
    "crypt32.dll", "d2d1.dll", "d3d11.dll", "d3d12.dll", "d3d9.dll",
    "d3dcompiler_47.dll", "dbghelp.dll", "dnsapi.dll", "dwmapi.dll",
    "dwrite.dll", "dxgi.dll", "gdi32.dll", "gdiplus.dll", "hid.dll",
    "imm32.dll", "iphlpapi.dll", "kernel32.dll", "mf.dll", "mfplat.dll",
    "mfreadwrite.dll", "mmdevapi.dll", "mpr.dll", "msimg32.dll",
    "msvcrt.dll", "ncrypt.dll", "netapi32.dll", "normaliz.dll", "ntdll.dll",
    "ole32.dll", "oleaut32.dll", "opengl32.dll", "powrprof.dll",
    "propsys.dll", "psapi.dll", "rpcrt4.dll", "secur32.dll", "setupapi.dll",
    "shcore.dll", "shell32.dll", "shlwapi.dll", "user32.dll", "userenv.dll",
    "uxtheme.dll", "version.dll", "winhttp.dll", "wininet.dll", "winmm.dll",
    "winspool.drv", "wintrust.dll", "wldap32.dll", "ws2_32.dll",
    "wtsapi32.dll",
}
_INBOX_PREFIXES = ("api-ms-win-", "ext-ms-win-", "ext-ms-onecore-")


def imports_of(path: str) -> list[str]:
    """The DLL names in *path*'s import directory (PE32 or PE32+), in
    table order. Delay-load imports are not included: a delay-loaded DLL
    is only needed when its first function is called, which is exactly the
    case that does not stop the library from loading."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:2] != b"MZ":
        raise ValueError(f"{path}: not a PE file (no MZ header)")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError(f"{path}: not a PE file (no PE signature)")
    n_sections, opt_size = struct.unpack_from("<H", data, pe + 6)[0], \
        struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    if magic == 0x20B:          # PE32+
        data_dirs = opt + 112
    elif magic == 0x10B:        # PE32
        data_dirs = opt + 96
    else:
        raise ValueError(f"{path}: unknown optional header magic {magic:#x}")
    import_rva, import_size = struct.unpack_from("<II", data, data_dirs + 8)
    if not import_rva or not import_size:
        return []

    sections = []
    sec = opt + opt_size
    for i in range(n_sections):
        _, vsize, vaddr, rawsize, rawptr = struct.unpack_from(
            "<8sIIII", data, sec + i * 40)
        sections.append((vaddr, max(vsize, rawsize), rawptr))

    def offset(rva: int) -> int:
        for vaddr, size, rawptr in sections:
            if vaddr <= rva < vaddr + size:
                return rva - vaddr + rawptr
        raise ValueError(f"{path}: RVA {rva:#x} is in no section")

    names = []
    pos = offset(import_rva)
    while True:
        _, _, _, name_rva, _ = struct.unpack_from("<IIIII", data, pos)
        if name_rva == 0:
            break
        start = offset(name_rva)
        end = data.index(b"\0", start)
        names.append(data[start:end].decode("ascii", "replace"))
        pos += 20
    return names


def unresolved(path: str, search: list[str] | None = None) -> list[str]:
    """Imports of *path* that neither Windows nor a file beside it (or in
    one of the extra *search* dirs) provides."""
    dirs = [os.path.dirname(os.path.abspath(path))] + list(search or [])
    present = set()
    for d in dirs:
        try:
            present.update(n.lower() for n in os.listdir(d))
        except OSError:
            pass
    missing = []
    for name in imports_of(path):
        low = name.lower()
        if low in INBOX or low.startswith(_INBOX_PREFIXES):
            continue
        if low in present:
            continue
        missing.append(name)
    return missing


def main(argv: list[str]) -> int:
    extra: list[str] = []
    files: list[str] = []
    it = iter(argv)
    for arg in it:
        if arg == "--search":
            extra.append(next(it))
        else:
            files.append(arg)
    if not files:
        print(__doc__)
        return 2
    rc = 0
    for path in files:
        names = imports_of(path)
        bad = unresolved(path, extra)
        print(f"{path}: {len(names)} imported DLLs")
        for name in names:
            mark = "MISSING" if name in bad else "ok"
            print(f"  {mark:8s} {name}")
        if bad:
            rc = 1
            print(f"::error::{os.path.basename(path)} needs {', '.join(bad)}, "
                  "which is neither part of Windows nor shipped in the bundle "
                  "- the DLL will not load on a clean PC")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

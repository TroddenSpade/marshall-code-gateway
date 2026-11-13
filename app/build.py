#!/usr/bin/env python3
# ============================================================
#  Marshall CODE · Gateway Web — one-file build script
#  ------------------------------------------------------------
#  Produces a single double-click executable with PyInstaller.
#
#  Usage:
#      python3 build.py                 # build for this OS
#      python3 build.py --name Foo      # custom binary name
#      python3 build.py --console       # keep a console (debug)
#      python3 build.py --no-icon       # build without an application icon
#
#  Requires:  pip install pyinstaller
#
#  The web app files (index.html, styles.css, data.js, app.js)
#  are embedded into the binary, so the result is fully portable:
#  copy the single file anywhere and double-click it.
# ============================================================

import os
import sys
import shutil
import subprocess
import tempfile

# Redirected stdout/stderr on Windows can default to cp1252, which cannot
# encode the arrow in the "Done ->" banner.  Force UTF-8 so the build never
# crashes at the final print (and the exit code stays 0).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))      # gateway/
GATEWAY = os.path.dirname(HERE)                        # repo gateway/
DIST = os.path.join(GATEWAY, "dist")
BUILD = os.path.join(GATEWAY, "build", "pyinstaller")

APPS = ["index.html", "styles.css", "data.js", "app.js"]

# The icons are generated with the standard library (app/make_icon.py) so the
# build stays dependency-free; regenerate them if they are missing.
ICONS = ("icon.png", "icon.ico")


def ensure_icons():
    """Create the icon files on demand. Returns True when they exist."""
    if all(os.path.isfile(os.path.join(GATEWAY, f)) for f in ICONS):
        return True
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import make_icon
        make_icon.main()
    except Exception as e:
        print("Could not generate icons: %s" % e)
    return all(os.path.isfile(os.path.join(GATEWAY, f)) for f in ICONS)


def pick_icon():
    """Return the icon file appropriate for this OS, or None."""
    if os.name == "nt":
        ico = os.path.join(GATEWAY, "icon.ico")           # Windows needs .ico
    elif sys.platform == "darwin":
        ico = os.path.join(GATEWAY, "icon.icns")          # macOS needs .icns
    else:
        ico = os.path.join(GATEWAY, "icon.png")           # Linux takes .png
    return ico if os.path.isfile(ico) else None


def main():
    args = sys.argv[1:]
    name = "Code Gateway"
    if "--name" in args:
        name = args[args.index("--name") + 1]
    console = "--console" in args
    want_icon = "--no-icon" not in args

    try:
        import PyInstaller.__main__ as pyi
    except ImportError:
        print("PyInstaller is not installed.  Run:  python3 -m pip install pyinstaller")
        return 1

    # Verify the app assets exist before packaging.
    missing = [f for f in APPS if not os.path.isfile(os.path.join(GATEWAY, f))]
    if missing:
        print("Missing app files: %s" % ", ".join(missing))
        return 1

    sep = ";" if os.name == "nt" else ":"
    add_data = [os.path.join(GATEWAY, f) + sep + "." for f in APPS]

    cmd = [
        os.path.join(HERE, "desktop.py"),
        "--name", name,
        "--onefile",
        "--clean", "--noconfirm",
        "--distpath", DIST,
        "--workpath", BUILD,
        "--specpath", BUILD,
        # The launcher imports proxy.server; point the analysis at the source tree.
        "--paths", GATEWAY,
        "--collect-submodules", "proxy",
    ]
    for d in add_data:
        cmd += ["--add-data", d]
    if not console:
        cmd += ["--windowed"]
    if want_icon and ensure_icons():
        icon = pick_icon()
        if icon:
            cmd += ["--icon", icon]
        elif sys.platform == "darwin":
            print("No icon.icns present; building without an icon.")

    print("Building %s ..." % name)
    pyi.run(cmd)

    exe = os.path.join(DIST, name + (".exe" if os.name == "nt" else ""))
    if os.path.isfile(exe):
        size = os.path.getsize(exe) / (1024 * 1024)
        print("\nDone → %s  (%.1f MB)" % (exe, size))
        print("Double-click it to launch; no terminal or Python needed.")
        return 0
    print("\nBuild finished but no executable was found at %s" % exe)
    return 2


if __name__ == "__main__":
    sys.exit(main())

#turns the  FileRenamer.py file into a exe adding version logs
"""
build.py  –  PyInstaller build script for FileRenamer
------------------------------------------------------
Run with:   python build.py

What it does each time:
  1. Reads the current version from version.txt (creates 1.0.0 on first run)
  2. Auto-increments the PATCH number  (1.0.2 → 1.0.3)
  3. Writes a Windows version-info file so the exe shows version metadata
     in File Properties → Details
  4. Cleans the dist/ and build/ folders from the previous build
  5. Calls PyInstaller with all the right flags
  6. Renames the output exe to include the version  e.g. FileRenamer_v1.0.3.exe
  7. Saves the new version back to version.txt
"""

import os
import re
import shutil
import subprocess
import sys

# ── Configuration ─────────────────────────────────────────────────────────────

SCRIPT      = "FileRenamer.py"          # source file to compile
APP_NAME    = "FileRenamer"             # base name for the output exe
VERSION_FILE = "version.txt"           # persists the version between builds
ICON_FILE   = "icon.ico"               # .ico path – skipped if file not found
VERSION_INFO_FILE = "version_info.txt" # temp file passed to PyInstaller

# ── Version helpers ───────────────────────────────────────────────────────────

def read_version():
    """Return (major, minor, patch) from version.txt, defaulting to 1.0.0."""
    if not os.path.exists(VERSION_FILE):
        return (1, 0, 0)
    text = open(VERSION_FILE).read().strip()
    m = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', text)
    if not m:
        print(f"  ⚠  Could not parse '{text}' in {VERSION_FILE}, resetting to 1.0.0")
        return (1, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def increment_patch(version):
    """Bump the patch number: (1, 0, 2) → (1, 0, 3)."""
    major, minor, patch = version
    return (major, minor, patch + 1)


def version_str(version):
    return "{}.{}.{}".format(*version)


def save_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(version_str(version))

# ── Windows version-info file ─────────────────────────────────────────────────

def write_version_info(version):
    """
    Write a PyInstaller-compatible version info file.
    This is what populates File Properties → Details in Windows Explorer.
    The four-tuple format Windows expects is  (major, minor, patch, build).
    """
    major, minor, patch = version
    build = 0
    ver4  = f"({major}, {minor}, {patch}, {build})"
    vs    = version_str(version)

    content = f"""\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={ver4},
    prodvers={ver4},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName',      u''),
         StringStruct(u'FileDescription',  u'{APP_NAME}'),
         StringStruct(u'FileVersion',      u'{vs}'),
         StringStruct(u'InternalName',     u'{APP_NAME}'),
         StringStruct(u'LegalCopyright',   u''),
         StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
         StringStruct(u'ProductName',      u'{APP_NAME}'),
         StringStruct(u'ProductVersion',   u'{vs}')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open(VERSION_INFO_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# ── Cleanup ───────────────────────────────────────────────────────────────────

def clean():
    """Remove dist/, build/, and any leftover .spec files before building."""
    for path in ["dist", "build"]:
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"  Removed  {path}/")
    for spec in [f"{APP_NAME}.spec"]:
        if os.path.exists(spec):
            os.remove(spec)
            print(f"  Removed  {spec}")

# ── Build ─────────────────────────────────────────────────────────────────────

def build(version):
    vs = version_str(version)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                         # single portable exe
        "--windowed",                        # no console window
        "--name", APP_NAME,                  # internal exe name
        "--version-file", VERSION_INFO_FILE, # Windows metadata
    ]

    # Attach icon only when the file actually exists
    if os.path.isfile(ICON_FILE):
        cmd += ["--icon", ICON_FILE]
        print(f"  Icon     {ICON_FILE}")
    else:
        print(f"  Icon     skipped ({ICON_FILE} not found – place it here to enable)")

    cmd.append(SCRIPT)

    print(f"  Running  {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("\n✖  PyInstaller failed – version not saved.")
        sys.exit(result.returncode)

# ── Rename output exe ─────────────────────────────────────────────────────────

def rename_exe(version):
    """
    PyInstaller always writes  dist/<APP_NAME>.exe
    We rename it to            dist/<APP_NAME>_v<version>.exe
    so every build produces a uniquely-named file you can archive.
    """
    vs       = version_str(version)
    src      = os.path.join("dist", f"{APP_NAME}.exe")
    dst      = os.path.join("dist", f"{APP_NAME}_v{vs}.exe")

    if not os.path.exists(src):
        print(f"  ⚠  Expected output not found: {src}")
        return

    if os.path.exists(dst):
        os.remove(dst)           # overwrite any previous build of the same version

    os.rename(src, dst)
    print(f"  Output   {dst}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Make sure we run from the directory that contains this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    old_version = read_version()
    new_version = increment_patch(old_version)

    print("=" * 52)
    print(f"  {APP_NAME} build script")
    print(f"  {version_str(old_version)}  →  {version_str(new_version)}")
    print("=" * 52)

    print("\n[1/4] Writing version info …")
    write_version_info(new_version)

    print("\n[2/4] Cleaning previous build artefacts …")
    clean()

    print("\n[3/4] Building exe …\n")
    build(new_version)

    print("\n[4/4] Renaming output …")
    rename_exe(new_version)

    # Only save the new version if everything succeeded
    save_version(new_version)

    # Clean up the temporary version-info file
    if os.path.exists(VERSION_INFO_FILE):
        os.remove(VERSION_INFO_FILE)

    print(f"\n✔  Build complete  –  version {version_str(new_version)}")
    print("=" * 52)


if __name__ == "__main__":
    main()
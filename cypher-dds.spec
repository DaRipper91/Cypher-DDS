# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the desktop cypher-dds executable (Windows .exe, and
usable the same way for a Linux/macOS standalone binary).

PyInstaller must run on the target OS to produce a native executable for
it — there's no meaningful way to cross-build a Windows .exe from this
repo's Linux dev environment. .github/workflows/build-windows.yml runs
this spec on a windows-latest GitHub Actions runner; that CI run is the
real build *and* verification step for this artifact.

Build locally (on the target OS, from the repo root):
    pip install -e ".[build]"
    pyinstaller cypher-dds.spec
"""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
for pkg in ("textual", "serial"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ["src/cypher_dds/tui/app.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="cypher-dds",
    console=True,  # it's a terminal UI — keep the console window
    onefile=True,
)

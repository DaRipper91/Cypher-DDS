# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the desktop cypher-dds GUI executable.

Build locally (on the target OS, from the repo root):
    pip install -e ".[build]"
    pyinstaller cypher-dds-gui.spec
"""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
for pkg in ("serial",):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ["src/cypher_dds/gui/app.py"],
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
    name="cypher-dds-gui",
    console=False,
    onefile=True,
)

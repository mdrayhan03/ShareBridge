# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the Linux one-folder build of ShareBridge.
#
# PyInstaller is NOT a cross-compiler — build this ON Linux:
#
#     pip install pyinstaller
#     pyinstaller sharebridge_linux.spec
#
# Result: dist/ShareBridge/  (a one-folder build)
#   - Run it with:  ./dist/ShareBridge/ShareBridge
#   - Ship it as a tarball, or package it into a single-file AppImage
#     (see documents/COMPILE_LINUX.md).

import os

import kivymd
from kivy.tools.packaging.pyinstaller_hooks import hookspath, runtime_hooks

from version import __version__  # noqa: F401 (kept for parity / future use)

# KivyMD ships a PyInstaller hook that bundles its fonts/images/kv files.
kivymd_hooks_path = os.path.join(
    os.path.dirname(kivymd.__file__), "tools", "packaging", "pyinstaller"
)

a = Analysis(
    ['MainApplication.py'],
    pathex=[],
    binaries=[],
    # Bundle our source folders so the .kv files and assets ship inside the app.
    datas=[('src', 'src'), ('assets', 'assets'), ('services', 'services')],
    hiddenimports=['kivymd', 'aiohttp', 'websockets', 'pydantic', 'plyer'],
    hookspath=[kivymd_hooks_path, *hookspath()],
    hooksconfig={},
    runtime_hooks=runtime_hooks(),
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # one-folder build
    name='ShareBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # windowed GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ShareBridge',
)

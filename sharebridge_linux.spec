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
import sys

# Make the project root importable (parity with the macOS spec).
try:
    _root = SPECPATH  # injected by PyInstaller: the spec's directory
except NameError:
    _root = os.path.abspath(os.getcwd())
sys.path.insert(0, _root)

import kivymd
from kivy.tools.packaging.pyinstaller_hooks import get_deps_all, hookspath, runtime_hooks
from PyInstaller.utils.hooks import collect_submodules

from version import __version__  # noqa: F401 (kept for parity / future use)

# KivyMD ships a PyInstaller hook that bundles its fonts/images/kv files.
kivymd_hooks_path = os.path.join(
    os.path.dirname(kivymd.__file__), "tools", "packaging", "pyinstaller"
)

# Collect all kivymd submodules (e.g. kivymd.icon_definitions) and every Kivy
# provider + native library, or the frozen app can't load icons/images.
kivymd_submodules = collect_submodules('kivymd')
kivy_deps = get_deps_all()

a = Analysis(
    ['MainApplication.py'],
    pathex=[_root],
    binaries=kivy_deps['binaries'],
    # Bundle our source folders so the .kv files and assets ship inside the app.
    datas=[('src', 'src'), ('assets', 'assets'), ('services', 'services')],
    hiddenimports=['kivymd', 'aiohttp', 'websockets', 'plyer'] + kivymd_submodules + kivy_deps['hiddenimports'],
    hookspath=[kivymd_hooks_path, *hookspath()],
    hooksconfig={},
    runtime_hooks=runtime_hooks(),
    excludes=kivy_deps['excludes'],
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

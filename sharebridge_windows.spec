# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the Windows one-folder build of ShareBridge.
# Build on Windows:  pip install pyinstaller && pyinstaller sharebridge_windows.spec
# Result: dist\ShareBridge\  (with ShareBridge.exe inside)
#   - Package it into an installer with sharebridge_installer.iss (Inno Setup).

import os
import sys

# Make the project root importable (parity with the macOS/Linux specs).
try:
    _root = SPECPATH  # injected by PyInstaller: the spec's directory
except NameError:
    _root = os.path.abspath(os.getcwd())
sys.path.insert(0, _root)

import kivymd
from kivy.tools.packaging.pyinstaller_hooks import get_deps_all, hookspath, runtime_hooks
from PyInstaller.utils.hooks import collect_submodules

# Collect all kivymd submodules (e.g. kivymd.icon_definitions) and every Kivy
# provider + native library, or the frozen app can't load icons/images.
kivymd_hooks_path = os.path.join(
    os.path.dirname(kivymd.__file__), "tools", "packaging", "pyinstaller"
)
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

# One-folder build: EXE holds only the launcher; COLLECT gathers the rest into
# dist/ShareBridge/. This launches faster than one-file and pairs with the installer.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ShareBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # hide the console window for the GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
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

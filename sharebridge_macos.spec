# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for building the macOS .app bundle of ShareBridge.
#
# PyInstaller is NOT a cross-compiler — build this ON a Mac:
#
#     pip install pyinstaller
#     pyinstaller sharebridge_macos.spec
#
# Result: dist/ShareBridge.app
#   - Drag it into /Applications, or package it into a .dmg for distribution.
#   - It is unsigned, so on first launch users must right-click the app > Open
#     (Gatekeeper blocks a double-click on unsigned apps). Sign + notarize with
#     an Apple Developer account to remove that step.
#
# The build targets the architecture of the machine it runs on (arm64 on Apple
# Silicon, x86_64 on Intel). Build on each to cover both, or set target_arch
# to 'universal2' if you have a universal Python.

import os

import kivymd
from kivy.tools.packaging.pyinstaller_hooks import hookspath, runtime_hooks

from version import __version__

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
    exclude_binaries=True,
    name='ShareBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,               # UPX can corrupt macOS dylibs/frameworks — keep off
    console=False,           # windowed GUI app, no terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,        # None = the building machine's arch
    codesign_identity=None,  # unsigned build
    entitlements_file=None,
    # icon='assets/icon.icns',  # add an .icns to assets and uncomment
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ShareBridge',
)

app = BUNDLE(
    coll,
    name='ShareBridge.app',
    icon=None,  # set to 'assets/icon.icns' once you have an app icon
    bundle_identifier='com.mdrayhan.sharebridge',
    info_plist={
        'CFBundleName': 'ShareBridge',
        'CFBundleDisplayName': 'ShareBridge',
        'CFBundleShortVersionString': __version__,
        'CFBundleVersion': __version__,
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        # macOS 15+ requires this so the OS shows a proper Local Network
        # permission prompt. ShareBridge's device discovery sends UDP
        # broadcasts on the LAN, which is gated behind that permission.
        'NSLocalNetworkUsageDescription':
            'ShareBridge finds other devices on your Wi-Fi so you can chat and share files with them.',
        # Declared for the planned Bonjour/mDNS discovery; harmless today.
        'NSBonjourServices': ['_sharebridge._tcp'],
    },
)

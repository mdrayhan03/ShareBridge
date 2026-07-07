[app]

# (str) Title of your application
title = ShareBridge

# (str) Package name
package.name = sharebridge

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py lives (typically the root)
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,md

# (list) Directories to exclude from the APK (dev/build/tooling folders)
source.exclude_dirs = tests, bin, venv, .git, .github, .buildozer, build, dist, docs, documents

# (str) Application versioning
version = 1.0.0

# (str) Application icon
icon.filename = %(source.dir)s/assets/icon.png

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
# KivyMD 2.0 is unreleased, so pin it to the same commit as requirements.txt
# (a bare 'kivymd' installs the old 1.2.0 from PyPI, which lacks MDListItem etc.)
# and list its runtime deps so python-for-android builds them too.
requirements = python3,kivy,pillow,aiohttp,websockets,plyer,asyncgui,asynckivy,materialyoucolor,materialshapes,https://github.com/kivymd/KivyMD/archive/365aa9b96eee63e0e29c04de297dd222f478fce5.zip

# (list) Permissions - Critical for massive file transfers!
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, FOREGROUND_SERVICE, WAKE_LOCK

# (int) Target Android API, should be as high as possible.
android.api = 33

# (bool) Automatically accept the Android SDK licenses (required for headless builds)
android.accept_sdk_license = True

# (str) Pin python-for-android to a stable release. The default (master) targets
# Python 3.14, where pyjnius 1.7.0 fails to build ("No matching distribution").
# This 2024 release targets Python 3.11, where all recipes build.
p4a.branch = v2024.01.21

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (str) Supported orientation (portrait prevents crashes on rotate during transfer)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) List of service to declare
# This is commented out for now, but you will use it later for your foreground service!
services = ShareBridgeService:service.py:foreground

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0

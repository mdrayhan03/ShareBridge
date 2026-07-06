# Automated Release Builds (GitHub Actions CI)

This pipeline builds **all three platforms** and publishes them to a GitHub Release
automatically whenever you push a version tag — so shipping a new version is just:

```bash
git tag v2.0.0
git push origin v2.0.0
```

A few minutes later, `ShareBridge.app` (macOS), `ShareBridge.exe` (Windows), and
the `.apk` (Android) appear on the repo's **Releases** page, ready to download.

---

## Why CI instead of Docker?

Docker only runs Linux, so it can build **Android** (Buildozer is a Linux tool) but
**not** Windows or macOS — a native `.exe` must be built on Windows, and a `.app`
must be built on a Mac (Apple's license forbids macOS in containers). GitHub Actions
gives you real `windows-latest` and `macos-latest` machines, so it can build all
three. That is why the pipeline below uses three separate runners.

| Job | Runner | Tool | Output |
|-----|--------|------|--------|
| Android | `ubuntu-latest` | Buildozer | `.apk` |
| Windows | `windows-latest` | PyInstaller (one-folder) + Inno Setup | `ShareBridgeSetup.exe` installer |
| macOS | `macos-latest` | PyInstaller | `.app` bundle (zipped) |
| Linux | `ubuntu-latest` | PyInstaller (one-folder) | `.tar.gz` |
| Release | `ubuntu-latest` | gh-release | attaches all artifacts |

**A note on "one-folder" per platform:** the *one-folder* choice only applies to
Windows (the PyInstaller spec now uses a one-folder build, which the installer
packages). macOS is already a one-folder `.app` bundle by design, and Android
ships a single `.apk` — neither has a one-file/one-folder switch to change.

---

## Setup

1. Create the file **`.github/workflows/release.yml`** in the repo root.
2. Paste the workflow below.
3. Commit and push it. From then on, pushing a `v*` tag triggers a full release build.

## Building on demand (no local machine needed)

You don't need to cut a release just to get an APK. After the workflow is on
GitHub, go to **Actions → Release Build → Run workflow**. It builds all
platforms on GitHub's runners (x86_64 — no emulation, so the Android build works
cleanly) and, because it wasn't triggered by a tag, **skips the release step and
leaves the apps as downloadable artifacts** on the run. Open the finished run and
download `android-apk` (or any platform) from the **Artifacts** section.

This is the recommended way to build the Android APK if your local machine is
low on disk or is Apple Silicon (where local Docker needs slow x86_64 emulation).

No secrets or tokens are needed — the built-in `GITHUB_TOKEN` (granted by
`permissions: contents: write`) is enough to create the Release.

---

## `.github/workflows/release.yml`

```yaml
name: Release Build

# Runs on a version tag to publish a release, or manually ("Run workflow") to
# just build the apps and download them as artifacts (no release).
on:
  push:
    tags:
      - "v*"
  workflow_dispatch:

permissions:
  contents: write   # needed to create the GitHub Release

jobs:
  # ---------------- Android ----------------
  build-android:
    runs-on: ubuntu-latest
    # Android packaging can fail (see the pydantic note below); don't let it
    # block the desktop releases.
    continue-on-error: true
    steps:
      - uses: actions/checkout@v4

      - name: Build APK with Buildozer
        uses: ArtemSBulgakov/buildozer-action@v1
        with:
          command: buildozer android debug
          buildozer_version: stable

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: android-apk
          path: bin/*.apk

  # ---------------- Windows ----------------
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build the app (one-folder)
        run: pyinstaller sharebridge_windows.spec

      - name: Install Inno Setup
        run: choco install innosetup -y

      - name: Build the installer
        run: '& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion=${{ github.ref_name }} sharebridge_installer.iss'

      - name: Upload Windows installer
        uses: actions/upload-artifact@v4
        with:
          name: windows-installer
          path: Output/ShareBridgeSetup.exe

  # ---------------- macOS ----------------
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build .app
        run: pyinstaller sharebridge_macos.spec

      - name: Zip the .app (ditto preserves the bundle structure)
        run: ditto -c -k --keepParent dist/ShareBridge.app ShareBridge-macos.zip

      - name: Upload macOS artifact
        uses: actions/upload-artifact@v4
        with:
          name: macos-build
          path: ShareBridge-macos.zip

  # ---------------- Linux ----------------
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install system libraries
        run: |
          sudo apt-get update
          sudo apt-get install -y libgl1 libmtdev1

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build the app (one-folder)
        run: pyinstaller sharebridge_linux.spec

      - name: Package tarball
        run: tar -czf ShareBridge-linux.tar.gz -C dist ShareBridge

      - name: Upload Linux artifact
        uses: actions/upload-artifact@v4
        with:
          name: linux-build
          path: ShareBridge-linux.tar.gz

  # ---------------- Publish Release ----------------
  release:
    needs: [build-android, build-windows, build-macos, build-linux]
    if: startsWith(github.ref, 'refs/tags/')   # only publish on a tag; manual runs just upload artifacts
    runs-on: ubuntu-latest
    steps:
      - name: Download all build artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts

      - name: Create GitHub Release and attach files
        uses: softprops/action-gh-release@v2
        with:
          # The tag that triggered the run becomes the release name.
          files: |
            artifacts/android-apk/*.apk
            artifacts/windows-installer/*.exe
            artifacts/macos-build/*.zip
            artifacts/linux-build/*.tar.gz
          generate_release_notes: true   # auto-lists merged PRs / commits
```

---

## Notes & gotchas

- **Trigger:** the pipeline only runs on tags matching `v*`. Normal pushes to
  `main` are ignored, so you don't build on every commit — only when you decide
  to release.
- **Release notes:** `generate_release_notes: true` auto-writes a changelog from
  the commits/PRs since the last tag. Remove it if you prefer to write notes by hand.
- **Python version:** pinned to `3.11` on the runners for the widest Kivy/KivyMD
  wheel availability. Bump it if you rely on 3.12-only features (your dev machine
  uses 3.12, and Kivy 2.3.x ships 3.12 wheels, so `"3.12"` also works).
- **Unsigned builds:** these artifacts are **unsigned**, so users still get the
  Gatekeeper (macOS) and SmartScreen (Windows) warnings on first launch. See
  `COMPILE_MAC.md` / `COMPILE_WINDOWS.md` for the "open anyway" steps. Signing
  would be added as extra CI steps with certificates stored in repo secrets.
- **Android release vs debug:** the workflow builds `buildozer android debug`
  (installable, but a debug APK). For a signed release APK you'd switch to
  `buildozer android release` and add keystore signing via secrets — keep the
  **same keystore** for every version or Android refuses the update.
- **Android build status.** The old blocker — pydantic v2's Rust core, which
  python-for-android can't build — has been removed: the protocol layer is now
  a dependency-free pure-Python schema, and `buildozer.spec` requirements were
  fixed (added `plyer`, dropped the unused `zeroconf`, bumped the version). The
  Android APK should now build. It is still marked `continue-on-error` as a
  safety net because the APK build hasn't been verified end-to-end yet (KivyMD
  2.0 from a zip archive under p4a can need extra care); once it's confirmed on
  a real build, you can remove `continue-on-error` so a broken APK fails loudly.
- **First Android build is slow:** the Buildozer action downloads the Android
  SDK/NDK on the first run (several minutes). Subsequent runs reuse the cache.
- **Cost:** free for public repositories. Private repos consume Actions minutes
  (macOS runners cost more minutes than Linux/Windows).

---

## Local Docker build for Android (alternative to CI)

If you just want the Android APK locally without installing the whole toolchain,
Docker is the clean way (Linux tool, Linux container):

```bash
# From the project root
docker run --rm -v "$PWD":/home/user/hostcwd kivy/buildozer android debug
```

The APK is written to `bin/`. This does **not** work for Windows or macOS — those
require their native OS (hence the CI pipeline above).

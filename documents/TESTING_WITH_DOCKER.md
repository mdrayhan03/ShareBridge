# Building & Testing with Docker (Linux + Android)

Docker containers run **Linux**, so from a single host you can build and test the
**Linux** and **Android** versions of ShareBridge — no local toolchain to install.

**This works on macOS, Windows, and Linux hosts alike** (Docker Desktop on Mac/
Windows runs a Linux VM under the hood). The only thing Docker *cannot* do is
macOS: there is no macOS container image, so the `.app` must be built and tested
on a real Mac (or a macOS CI runner), never in Docker.

| Target | Build in Docker? | Run/test in Docker? |
|--------|:---------------:|:-------------------:|
| Linux   | ✅ yes | ✅ yes (headless via Xvfb) |
| Android | ✅ yes (APK) | ❌ no — use a real phone |
| macOS   | ❌ impossible | ❌ impossible |

## Prerequisites

- Install **Docker Desktop** (macOS / Windows) or Docker Engine (Linux).
- Run all commands from the project root.

> **Path syntax by host** — replace `"$PWD"` with your shell's "current folder":
> - macOS / Linux: `"$PWD"`
> - Windows PowerShell: `${PWD}`
> - Windows CMD: `%cd%`

---

## 1. Linux — build the app in Docker

Compile the one-folder Linux build inside a clean container:

```bash
docker run --rm -v "$PWD":/app -w /app python:3.11 bash -c "
  apt-get update &&
  apt-get install -y libgl1 libmtdev1 &&
  pip install -r requirements.txt pyinstaller &&
  pyinstaller sharebridge_linux.spec
"
```

Result: `dist/ShareBridge/` appears in your project (the container writes to the
mounted folder). This proves the Linux build works. See
[COMPILE_LINUX.md](COMPILE_LINUX.md) for packaging it into a tarball or AppImage.

---

## 2. Linux — run / test the app in Docker (headless)

Kivy needs a display. Inside a container there's no monitor, so give it a
**virtual** one with **Xvfb** (X virtual framebuffer). The app then launches with
no screen, which is enough for an automated smoke test — and Kivy's
`Window.screenshot()` still works, so you can capture what rendered.

**Quick "does it launch?" check:**

```bash
docker run --rm -v "$PWD":/app -w /app python:3.11 bash -c "
  apt-get update &&
  apt-get install -y libgl1 libmtdev1 xvfb &&
  pip install -r requirements.txt &&
  timeout 20 xvfb-run -a python MainApplication.py
"
```

If it starts without a traceback (you'll see the Kivy/log output), the Linux
build runs. `timeout` stops it after 20s since it would otherwise wait for input.

**Functional smoke test with a screenshot:** point the container at a small
driver script that drives the app and calls `Window.screenshot()` (the same
technique used to verify the app on macOS). For example, a script that waits for
the join/opening screen and saves a PNG:

```bash
docker run --rm -v "$PWD":/app -w /app python:3.11 bash -c "
  apt-get update && apt-get install -y libgl1 libmtdev1 xvfb &&
  pip install -r requirements.txt &&
  xvfb-run -a python your_smoke_test.py     # drives the app, saves screenshot.png
"
```

Open the resulting PNG on your host (it's written into the mounted folder) to
*see* what the Linux app rendered — a real visual check without a Linux desktop.

> Interactive GUI (a real clickable window) needs X11 forwarding or a VNC setup,
> which is awkward from a Mac/Windows host. For verification, Xvfb + screenshots
> is the practical path.

---

## 3. Android — build the APK in Docker

This is the standard way to build Android from macOS/Windows. The `kivy/buildozer`
image already has the Android SDK/NDK, Java, and buildozer:

```bash
docker run --rm -v "$PWD":/home/user/hostcwd kivy/buildozer android debug
```

Result: the APK lands in `bin/` (e.g. `bin/sharebridge-1.0.0-*-debug.apk`).

- **First run is slow** (~20–30 min): it downloads the Android SDK/NDK. Later
  builds are cached and quick.
- Building on macOS/Windows works because the container is Linux — buildozer
  never has to run on the host OS.

See [CI_RELEASE.md](CI_RELEASE.md) for building the same APK automatically in CI.

---

## 4. Android — run / test on a real phone

Docker can build the APK but **cannot run it** — an Android emulator needs
hardware virtualization (KVM) that isn't available inside Docker on macOS/Windows.
The best way to test is a **real Android phone**, which also lets you test the
core LAN feature against your computer.

**One-time phone setup:**
1. Settings → About phone → tap **Build number** 7 times to unlock Developer
   options.
2. Settings → Developer options → enable **USB debugging**.

**Install and run (from your host — `adb` runs on macOS/Windows/Linux):**

```bash
# Connect the phone by USB, then:
adb devices                       # should list your phone
adb install -r bin/*.apk          # install (or reinstall) the APK
adb logcat | grep -i python       # watch the app's logs / crashes live
```

Open ShareBridge on the phone from the app drawer. On first launch Android will
ask to allow "install unknown apps" for the source — allow it.

**The most valuable test — cross-device over Wi-Fi:**
Put the phone and your computer on the **same Wi-Fi**, run ShareBridge on both
(the desktop app from source or a build, the APK on the phone), and confirm:
discovery finds the host → chat works both ways → a file shared from one device
downloads on the other. This exercises ShareBridge's whole reason for existing,
and `adb logcat` shows exactly what the phone side is doing.

---

## Summary

- **Linux:** fully build- and run-testable in Docker (Xvfb + screenshots).
- **Android:** build the APK in Docker; run/test it on a real phone via `adb`.
- **macOS:** not a Docker target — test on a real Mac.
- Works from **any host** (macOS, Windows, Linux) because the containers are Linux.

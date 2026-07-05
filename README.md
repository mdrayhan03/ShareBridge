# 🌉 ShareBridge

ShareBridge is a high-performance, locally-networked group chat and massive file-sharing application. Built for desktop and mobile, it lets users on the same Wi-Fi network automatically discover each other, form a chat room, and transfer gigabytes of files — without relying on the internet, accounts, or the cloud.

**⬇️ Download:** [mdrayhan03.github.io/ShareBridge](https://mdrayhan03.github.io/ShareBridge/) · Windows · macOS · Linux · Android

## ✨ Features

- **Automated Network Discovery**: A UDP broadcaster/listener (port 37020) finds the host on the local network automatically — no manual IP entry. Same-machine instances are found via a loopback beacon and a local-server probe, so discovery works even where OS firewalls block LAN broadcast.
- **Secure File Sharing**: Files are shared over a **token registry** — each attached file is exposed only under a random token (`/download/<token>`), never as a raw filesystem path. Nothing outside what the user explicitly shares is reachable, and local paths never leak.
- **Peer-to-Peer Transfers**: Every device runs its own HTTP file server, so **any** participant can share files — not just the host. A dedicated `aiohttp` server streams binary data in chunks, handling 20GB+ files without memory overload.
- **Strict Data Validation**: Every JSON packet is parsed and validated through a lightweight, dependency-free schema layer, so malformed messages are dropped instead of crashing the app (and it packages cleanly on Android — no native dependency).
- **Multi-File Attachments**: A horizontally-scrolling preview bar lets you attach multiple files, grouped into a single chat bubble on the receiver's end.
- **Live Active-Users Sidebar**: A responsive `MDNavigationDrawer` shows a real-time list of connected users, broadcast by the server as a single source of truth.
- **Settings**:
  - **Profile** — set your username and full name (stored in the per-user data directory, so it survives app updates).
  - **Feedback** — export the app log and email a bug report with a trackable subject, all in one place.
  - **About Us** — app info, features, and developer links.
- **In-App Update Checker**: On launch, ShareBridge checks GitHub Releases for a newer version and shows a non-blocking "Update Available" dialog. Fully offline-safe — a failed check never disrupts the app.
- **Clean Logging**: A single rotating log file in the user-data directory captures warnings/errors (no `~/.kivy` log clutter), exportable from the Feedback tab.
- **Beautiful Dark UI**: Built with `KivyMD 2.0`, optimized for both Desktop and Mobile (soft-keyboard panning, physical back-button handling).

## 🛠️ Technology Stack

- **Python 3.12+**
- **Kivy & KivyMD 2.0** — frontend UI
- **WebSockets** — real-time messaging & event state
- **Aiohttp** — high-performance HTTP binary streaming
- **Plyer** — native OS file chooser integration

## ⬇️ Download & Install

The easiest way to get ShareBridge is the **[download page](https://mdrayhan03.github.io/ShareBridge/)**, which always links to the latest build for your platform. You can also grab any version from the [Releases page](https://github.com/mdrayhan03/ShareBridge/releases).

Builds are unsigned, so on first launch:
- **Windows** — the installer's SmartScreen prompt → *More info → Run anyway*.
- **macOS** — right-click the app → *Open* (once).
- **Linux** — extract, then `chmod +x ShareBridge`.
- **Android** — enable "install unknown apps", then open the APK.

## 🚀 Running from Source

### Prerequisites
Python 3.12+ and a virtual environment.

### Installation

```bash
git clone https://github.com/mdrayhan03/ShareBridge.git
cd ShareBridge

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
> ShareBridge uses the unreleased `KivyMD 2.0`, pinned to a specific commit in `requirements.txt` for reproducible builds.

### Running

```bash
python MainApplication.py
```

1. **First launch**: enter a username and full name to build your local profile.
2. **Discovery**: the app scans the Wi-Fi for an existing ShareBridge host.
3. **Host or wait**: if none is found, start your own server; other devices connect automatically.
4. **Chat & share**: open the sidebar to see members, send messages, or attach large files.

### Running the tests

```bash
pip install pytest
pytest tests/
```

## 📦 Building Installers

ShareBridge builds for four platforms from one codebase. Per-platform guides live in [`documents/`](documents/):

| Platform | Guide | Output |
|----------|-------|--------|
| Windows  | [COMPILE_WINDOWS.md](documents/COMPILE_WINDOWS.md) · [installer](documents/COMPILE_WINDOWS_INSTALLER.md) | `ShareBridgeSetup.exe` |
| macOS    | [COMPILE_MAC.md](documents/COMPILE_MAC.md) | `ShareBridge.app` |
| Linux    | [COMPILE_LINUX.md](documents/COMPILE_LINUX.md) | folder / AppImage |
| Android  | [COMPILE_ANDROID.md](documents/COMPILE_ANDROID.md) | `.apk` |

**Automated releases:** pushing a `v*` tag triggers a GitHub Actions pipeline that builds all platforms on their native runners and publishes a Release — see [CI_RELEASE.md](documents/CI_RELEASE.md). The [download page](documents/DOWNLOAD_PAGE.md) then updates itself automatically.

## 📝 Roadmap

- **Automatic Host Migration** — when the host goes offline, elect a new host automatically and reconnect everyone. Design: [HOST_MIGRATION_PLAN.md](documents/HOST_MIGRATION_PLAN.md).
- **Connect by IP** — a manual-connect fallback for networks where discovery is blocked.
- **Direct 1-to-1 Messaging** — private channels alongside the group lobby.
- **Background Android Service** — keep transfers running when the screen is locked.

## 📄 License

Open-source under the [MIT License](LICENSE).

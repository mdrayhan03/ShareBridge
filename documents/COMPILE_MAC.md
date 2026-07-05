# Compiling ShareBridge for macOS (.app)

Building a native macOS `.app` bundle is done with **PyInstaller**. Because PyInstaller is not a cross-compiler, **you must build on a Mac** — you cannot produce a Mac app from Windows or Linux.

## 1. Prerequisites

Make sure you are inside your virtual environment (`venv`) where all project dependencies (Kivy, KivyMD, Websockets, etc.) are installed. Then install PyInstaller.

```bash
# Activate your virtual environment if not already activated
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller
```

## 2. Compiling the Application

The project already contains a customized `sharebridge_macos.spec` file. This file tells PyInstaller to:
1. Bundle all the `.kv` files, images, and services.
2. Use the Kivy and KivyMD hooks so the graphics libraries and fonts are packaged correctly.
3. Build a proper `.app` bundle (not a loose binary).
4. Add the `NSLocalNetworkUsageDescription` key to the app's `Info.plist`, so macOS shows the correct **Local Network permission prompt** — without it, device discovery (UDP broadcast) is silently blocked on macOS 15+.

Run the following command from the root directory of your project:

```bash
pyinstaller sharebridge_macos.spec
```

## 3. Locating Your App

The compilation process will print many logs. When it finishes successfully:
1. A new `dist/` directory will appear in your project folder.
2. Inside `dist/`, you will find **`ShareBridge.app`** — the standalone macOS application.

Drag `ShareBridge.app` into your `/Applications` folder to install it, or package it into a `.dmg` (see below) to share it.

## 4. First Launch — Gatekeeper Warning

The app is **unsigned**, so the first time a user opens it, macOS Gatekeeper will block a normal double-click with a message like *"ShareBridge can't be opened because Apple cannot check it for malicious software."*

This is expected for unsigned apps. To open it:
1. **Right-click** (or Control-click) `ShareBridge.app` and choose **Open**.
2. Click **Open** again in the dialog.

macOS remembers this choice, so it only needs to be done once. To remove the warning entirely, sign and notarize the app with an **Apple Developer account** ($99/year).

## 5. Local Network Permission

On first launch, macOS will ask for **Local Network** access (thanks to the `Info.plist` key in the spec). The user must **Allow** this — it is what lets ShareBridge discover and connect to other devices on the Wi-Fi. If it was denied, it can be re-enabled at:

**System Settings → Privacy & Security → Local Network → ShareBridge**

## 6. Architecture Note (Apple Silicon vs Intel)

PyInstaller builds for the architecture of the machine it runs on:
- Building on **Apple Silicon** (M1/M2/M3) produces an **arm64** app.
- Building on an **Intel** Mac produces an **x86_64** app.

An arm64 app will not run on old Intel Macs (and vice-versa). To cover both, either build on each type of machine, or build with a `universal2` Python and set `target_arch='universal2'` in the spec.

## 7. Packaging into a .dmg (optional, for distribution)

A `.dmg` is the standard way to hand a Mac app to users. The simplest tool is `create-dmg`:

```bash
# Install the tool (one time)
brew install create-dmg

# Create the disk image from the built app
create-dmg ShareBridge.dmg dist/ShareBridge.app
```

Upload the resulting `ShareBridge.dmg` to your download page (e.g. GitHub Releases). Users open the `.dmg`, drag `ShareBridge.app` into Applications, and launch it (using the right-click → Open step above the first time).

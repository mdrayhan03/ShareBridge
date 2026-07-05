# Compiling ShareBridge for Linux

Linux builds use **PyInstaller**, the same tool as Windows and macOS. Because
PyInstaller is not a cross-compiler, **build this on a Linux machine** (or a
Linux VM / WSL). The project includes `sharebridge_linux.spec`.

## 1. Prerequisites

On a Linux machine, inside your virtual environment:

```bash
# A few system libraries Kivy needs at build/run time
sudo apt-get update
sudo apt-get install -y libgl1 libmtdev1

# Install PyInstaller
source venv/bin/activate
pip install pyinstaller
```

## 2. Compiling the Application

Run from the project root:

```bash
pyinstaller sharebridge_linux.spec
```

This produces a one-folder build at `dist/ShareBridge/`, with the launcher
`dist/ShareBridge/ShareBridge` inside.

## 3. Running It

```bash
./dist/ShareBridge/ShareBridge
```

Linux has no Gatekeeper/SmartScreen equivalent, so there is no "unknown
developer" warning. If the binary isn't executable after download, the user
runs `chmod +x ShareBridge` once.

## 4. Distribution — Option A: Tarball (simple)

The easiest way to share the app is to compress the one-folder build:

```bash
tar -czf ShareBridge-linux.tar.gz -C dist ShareBridge
```

Upload `ShareBridge-linux.tar.gz` to your GitHub Releases page. Users extract it
and run `ShareBridge/ShareBridge`. This is the Linux equivalent of the Windows
"portable" folder.

## 5. Distribution — Option B: AppImage (professional, single file)

An **AppImage** is the Linux equivalent of a polished, self-contained installer:
one executable file that runs on most distributions with no installation. Build
it from the PyInstaller output:

```bash
# 1. Assemble an AppDir from the PyInstaller build
mkdir -p AppDir/usr/bin
cp -r dist/ShareBridge/* AppDir/usr/bin/

# 2. Add a .desktop entry
cat > AppDir/ShareBridge.desktop <<'EOF'
[Desktop Entry]
Name=ShareBridge
Exec=ShareBridge
Icon=sharebridge
Type=Application
Categories=Network;
EOF

# 3. Add an icon (256x256 PNG named sharebridge.png at the AppDir root)
cp assets/icon.png AppDir/sharebridge.png    # add an icon.png to assets first

# 4. AppRun entry point -> the launcher
ln -sf usr/bin/ShareBridge AppDir/AppRun

# 5. Build the AppImage
wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage AppDir ShareBridge-x86_64.AppImage
```

The result, `ShareBridge-x86_64.AppImage`, is a single file users download,
`chmod +x`, and run. Upload it to your Releases page.

## 6. User Data Survives Updates

Like the other platforms, ShareBridge stores the user's profile, settings, and
logs in the per-user data directory — on Linux that is
**`~/.config/sharebridge`** (via Kivy's `user_data_dir`, following the XDG
convention). Replacing the app folder or the AppImage on update never touches
it, so profiles and history are preserved.

## 7. Automating in CI

The Linux job in the GitHub Actions release pipeline (see `CI_RELEASE.md`)
builds this on `ubuntu-latest` and publishes the tarball automatically. To ship
an AppImage instead, replace the tarball step with the AppImage steps from
section 5.

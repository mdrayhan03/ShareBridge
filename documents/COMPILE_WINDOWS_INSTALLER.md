# Building a Windows Installer (ShareBridgeSetup.exe)

By default, the PyInstaller build (`sharebridge_windows.spec`) produces a bare
`ShareBridge.exe` — a "portable" app with no Start Menu shortcut, no desktop
icon, and no entry in **Apps & features**. To make ShareBridge feel like a
professional Windows program, wrap that build in an installer using **Inno
Setup**. The project already includes a ready-to-use script:
`sharebridge_installer.iss`.

> Unlike macOS (drag-to-Applications from a `.dmg`) and Android (the `.apk`
> triggers the system installer), Windows has no built-in install convention —
> so this extra step is what gives you a proper installer experience.

## 1. Prerequisites

Do these on a **Windows** machine:

1. **Build the app** first so the installer has something to package:
   ```bash
   pyinstaller sharebridge_windows.spec
   ```
   This creates the one-folder build `dist\ShareBridge\` (with `ShareBridge.exe`
   inside), which the installer packages whole.

2. **Install Inno Setup** (free): https://jrsoftware.org/isdl.php

## 2. Building the Installer

Two ways:

**Option A — GUI:** open `sharebridge_installer.iss` in the **Inno Setup
Compiler**, then click **Build → Compile**.

**Option B — Command line:** run the Inno Setup compiler `ISCC.exe` (installed
with Inno Setup) from the project root:
```bash
ISCC.exe sharebridge_installer.iss
```

The output appears at:
```
Output\ShareBridgeSetup.exe
```

This single `.exe` is the file you distribute — upload it to your GitHub
Releases page.

## 3. What the Installer Does

When a user runs `ShareBridgeSetup.exe`, they get the standard install wizard
(Welcome → install location → install → Finish). Behind the scenes it:

- Copies the app into `C:\Program Files\ShareBridge\`
- Creates a **Start Menu** entry and (optionally) a **desktop shortcut**
- Registers an **uninstaller**, so ShareBridge appears in Windows
  **Settings → Apps → Installed apps** with a proper "Uninstall" button
- Offers to launch the app when finished

## 4. User Data Is Safe Across Updates

The installer only manages **program files** in `Program Files`. ShareBridge
stores the user's profile, settings, and logs in **`%APPDATA%\sharebridge`**
(via Kivy's `user_data_dir`), which the installer never touches. This means:

- **Updating** (running a newer `ShareBridgeSetup.exe`) replaces the program
  files but keeps the user's profile and history.
- **Uninstalling** removes the program files but leaves `%APPDATA%\sharebridge`
  intact by default.

## 5. Version Number

The installer version defaults to `1.0.0`. Keep it in sync with `version.py`.
You can override it at build time without editing the script — handy for CI:

```bash
ISCC.exe /DMyAppVersion=2.0.0 sharebridge_installer.iss
```

> **Important:** never change the `AppId` GUID in the `.iss` file. Windows uses
> it to recognize that a new installer is an *update* of the same app rather
> than a second copy.

## 6. The SmartScreen Warning (Unsigned Builds)

Because the installer is not code-signed, the first time a user runs it Windows
SmartScreen shows: *"Windows protected your PC."* This is expected for unsigned
software. The user clicks **More info → Run anyway**.

To remove this warning entirely you need a **code-signing certificate**
(~$100–300/year), after which you would sign both `ShareBridge.exe` and
`ShareBridgeSetup.exe`. Until then, add a short "click More info → Run anyway"
note on your download page.

## 7. Automating in CI (optional)

Inno Setup can run inside the Windows job of your GitHub Actions release
pipeline (see `CI_RELEASE.md`). After the `pyinstaller` step, install Inno Setup
on the runner (e.g. via Chocolatey: `choco install innosetup`) and run:

```bash
ISCC.exe /DMyAppVersion=${{ github.ref_name }} sharebridge_installer.iss
```

Then upload `Output\ShareBridgeSetup.exe` as the Windows release asset instead
of the zipped folder.

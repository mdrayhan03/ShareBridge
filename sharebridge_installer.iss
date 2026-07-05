; Inno Setup script — builds a professional Windows installer for ShareBridge.
;
; Prerequisites:
;   1. Build the app first:   pyinstaller sharebridge_windows.spec
;      (the spec produces a one-folder build: dist\ShareBridge\ with ShareBridge.exe inside)
;   2. Install Inno Setup:    https://jrsoftware.org/isdl.php
;
; Build the installer:
;   - Open this file in the Inno Setup Compiler and click "Build", OR
;   - From a terminal:   ISCC.exe sharebridge_installer.iss
;   - In CI you can override the version:  ISCC.exe /DMyAppVersion=2.0.0 sharebridge_installer.iss
;
; Output:  Output\ShareBridgeSetup.exe   <- this is the file you distribute.

; Keep MyAppVersion in sync with version.py (CI can override it via /D).
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppName "ShareBridge"
#define MyAppPublisher "MD Rayhan Hossain"
#define MyAppURL "https://github.com/mdrayhan03/ShareBridge"
#define MyAppExeName "ShareBridge.exe"

[Setup]
; AppId uniquely identifies the app so updates replace the same install.
; Never change this GUID once released.
AppId={{B8E7B7A2-3C4D-4E5F-9A1B-2C3D4E5F6A7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
; Install into Program Files; user data lives in %APPDATA%\sharebridge instead,
; so the install folder can be safely replaced on update or removed on uninstall.
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=Output
OutputBaseFilename=ShareBridgeSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
; Ask for admin so we can write to Program Files; users may also pick a
; per-user location without admin via the install-scope dialog.
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; One-folder PyInstaller build: package the whole dist\ShareBridge\ folder
; (matches the current sharebridge_windows.spec).
Source: "dist\ShareBridge\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

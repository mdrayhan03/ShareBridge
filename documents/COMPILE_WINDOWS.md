# Compiling ShareBridge for Windows (.exe)

Building a standalone `.exe` for Windows is straightforward and can be done entirely within your existing Python Virtual Environment on Windows.

## 1. Prerequisites

Ensure you are inside your virtual environment (`venv`) where all project dependencies (Kivy, KivyMD, Websockets, etc.) are installed. You will need `pyinstaller` installed.

```bash
# Activate your virtual environment if not already activated
venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller
```

## 2. Compiling the Application

The project already contains a customized `sharebridge_windows.spec` file. This file tells PyInstaller to:
1. Bundle all the `.kv` files, images, and services.
2. Hide the black command prompt terminal when the app is launched.
3. Include critical hidden imports like `websockets`.

Run the following command from the root directory of your project:

```bash
pyinstaller sharebridge_windows.spec
```

## 3. Locating Your Executable

The compilation process will generate dozens of logs and output text. When it finishes successfully:
1. A new `dist/` directory will appear in your project folder.
2. Inside `dist/ShareBridge/`, you will find your standalone `ShareBridge.exe` application.

**Note on Distribution:** If you want to send this app to a friend, you must zip and send the **entire `ShareBridge` folder** located inside `dist/`. The `.exe` relies on the accompanying DLLs and asset folders generated next to it.

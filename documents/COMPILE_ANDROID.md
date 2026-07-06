# Compiling ShareBridge for Android (.apk)

Kivy applications for Android are compiled using **Buildozer**. Because Buildozer relies heavily on Android NDK and SDK build chains, **it does not run natively on Windows**. You must compile the application using Linux. 

Since you are on Windows, the easiest way to do this is using **WSL** (Windows Subsystem for Linux).

## 1. Setting up WSL (Ubuntu)

If you haven't already, open PowerShell as Administrator and run:
```bash
wsl --install
```
*Restart your PC if prompted, and complete the Ubuntu setup.*

## 2. Installing Android Build Dependencies

Open your WSL Terminal (search "Ubuntu" in your Windows start menu) and run the following commands to install the required Linux packages:

```bash
# Update package lists
sudo apt update

# Install Java, Git, Unzip, and C-Compilers
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```

## 3. Installing Buildozer

Next, install Buildozer globally in your WSL environment:

```bash
pip3 install --user --upgrade buildozer cython virtualenv
```
*(Note: Ensure your `~/.local/bin` is in your `$PATH` if it warns you about paths).*

## 4. Navigating to the Code

From inside WSL, you need to navigate to where your project is stored on your Windows hard drive. Windows drives are mounted under `/mnt/` in WSL. 

For example, if your project is on the `F:` drive:
```bash
cd /mnt/f/Python/"Testing Projects"/WebwsocketTest/ShareBridge
```

## 5. Compiling the APK

The project already contains a pre-configured `buildozer.spec` file that grants all necessary Android Storage permissions and configures the Background Foreground Service.

To start the compilation process, run:
```bash
buildozer android debug
```

**Important Notes:**
- **The First Build:** The very first time you run this command, Buildozer will automatically download the entire Android SDK, NDK, and Platform Tools from Google. This will take roughly **15-30 minutes** depending on your internet speed.
- **Subsequent Builds:** After the first build is cached, future builds will only take a few seconds.

## 6. Locating Your APK

When compilation is successful, a new folder named `bin/` will be generated in your project root. Inside this folder, you will find your compiled Android package:
`sharebridge-0.1-armeabi-v7a-debug.apk`

You can simply drag and drop this file from Windows Explorer straight onto your connected Android device to install it!

---

# Alternative: Build in Google Colab (free, no local install)

If you don't want to set up WSL/Linux locally — or your machine is low on disk,
or it's an Apple Silicon Mac (where local Docker needs slow x86_64 emulation) —
you can build the APK for free in **Google Colab**, a cloud Linux (x86_64)
notebook. Nothing is installed on your machine, and because Colab is native
x86_64 the Android build tools run directly (no emulation, no `aidl` issues).

## Step 0 — Push your code first

Colab clones your GitHub repo, so push your latest code:

```bash
git push origin main
```

## Build cells (copy-paste each into its own Colab cell)

Open <https://colab.research.google.com> → **New notebook**, then run these in
order.

**Cell 1 — system dependencies**

```python
!sudo apt-get update -qq
!sudo apt-get install -y -qq git zip unzip openjdk-17-jdk autoconf libtool \
    pkg-config zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev \
    build-essential libltdl-dev
```

**Cell 2 — install buildozer**

```python
!pip install --upgrade buildozer cython
```

**Cell 3 — get the code**

```python
!git clone https://github.com/mdrayhan03/ShareBridge.git
%cd ShareBridge
```

**Cell 4 — build the APK** (first run ~20–40 min: downloads the SDK/NDK and
compiles; runs unattended thanks to `accept_sdk_license` + `warn_on_root = 0`)

```python
!buildozer android debug
```

**Cell 5 — send the APK to your phone via Google Drive** (easiest; no computer
needed)

```python
from google.colab import drive
drive.mount('/content/drive')
!cp bin/*.apk /content/drive/MyDrive/
print("APK copied to your Google Drive.")
```

*(Or download it straight to your computer instead:)*

```python
from google.colab import files
import glob
files.download(sorted(glob.glob('bin/*.apk'))[-1])
```

**Optional — sanity-check the APK is well-formed** (confirms package,
permissions and that the foreground service is declared; not a functional test)

```python
!~/.buildozer/android/platform/android-sdk/build-tools/*/aapt dump badging bin/*.apk \
    | grep -E "package:|application-label:|uses-permission:|service"
```

## Testing on your phone (Colab can't run the app)

Colab has no screen or Android device, so you test the built APK on a **real
phone**:

1. **Install:** on the phone open the **Google Drive** app, tap the `.apk`, allow
   "install unknown apps" for the source, then **Install → Open**.
2. **Test cross-device (the real test):** run ShareBridge on the **phone** and on
   your **Mac** (`python MainApplication.py` or the built `.app`), both on the
   **same Wi-Fi**, and confirm:
   - one device hosts, the other discovers it automatically;
   - chat works both ways;
   - a file shared from one **downloads on the other**.
3. **Watch logs** (if you have `adb` + a USB cable):

   ```bash
   adb logcat | grep -i python
   ```

> **Keep the app in the foreground during file-transfer tests.** The file server
> currently runs in the app process, so transfers from a *backgrounded /
> screen-off* phone won't work yet — that needs the foreground-service change
> (roadmap). Chat signaling survives backgrounding; file downloads don't.

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

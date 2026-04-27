# 🌉 ShareBridge

ShareBridge is a high-performance, locally-networked group chat and massive file-sharing application. Built for desktop and mobile, it allows users on the same Wi-Fi network to automatically discover each other, form a chat room, and seamlessly transfer gigabytes of files without relying on external internet servers.

## ✨ Features

- **Automated Network Discovery**: Employs a UDP background broadcaster/listener (Port 37020) to automatically find the host server on the local network, avoiding tedious manual IP entry.
- **Hybrid Network Architecture**:
  - **WebSockets**: Handles all rapid signaling, real-time messaging, and active user state broadcasts.
  - **Aiohttp**: Spins up a local HTTP server dedicated entirely to streaming binary files to prevent WebSocket memory overloads, easily transferring 20GB+ files concurrently.
- **Dynamic Multi-File Attachments**: Includes an interactive horizontally-scrolling file preview bar with KivyMD cards before sending. Seamlessly groups multiple attached files into a single, cohesive chat bubble on the receiver's end.
- **Strict Data Validation**: Utilizes `Pydantic` models to strictly serialize and validate every JSON network packet to prevent silent protocol crashes.
- **Live Active Users Sidebar**: Features a responsive `MDNavigationDrawer` displaying a real-time list of connected users managed by a Single-Source-Of-Truth (SSOT) array broadcast by the server.
- **Beautiful Dark UI**: Built with the modern `KivyMD 2.0` framework, boasting a sleek, dark-themed, and responsive interface optimized for both Desktop and Mobile interactions (including soft-keyboard panning and physical back-button handling).

## 🛠️ Technology Stack

- **Python 3.12+**
- **Kivy & KivyMD 2.0** (Frontend UI)
- **WebSockets (`websockets`)** (Real-time Messaging & Event State)
- **Aiohttp** (High-Performance HTTP Binary Streaming)
- **Pydantic** (Data Validation & Serialization)
- **Plyer** (Native OS File Chooser Integration)

## 🚀 Getting Started

### Prerequisites
Make sure you have Python installed. It is highly recommended to use a Virtual Environment to avoid dependency conflicts.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ShareBridge.git
   cd ShareBridge
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   > **Note:** ShareBridge uses the unreleased `KivyMD 2.0` framework, which is pulled directly from the KivyMD master branch via the `requirements.txt`.

### Running the App

Start the application by running the main entry point:
```bash
python MainApplication.py
```

1. **First Launch**: The app will ask for a Username and Full Name to build your local profile.
2. **Network Discovery**: The app will automatically scan for an existing ShareBridge server on your network.
3. **Host or Wait**: If no server is found, a dialog will appear allowing you to instantly start the server natively. Once started, other devices on the network will automatically connect to you.
4. **Chat & Share**: Open the sidebar to view active members, send text messages, or attach large files to share instantly!

## 📱 Mobile Build Instructions

ShareBridge is designed to be cross-platform compatible. You can build an APK for Android using `buildozer`:

1. Ensure you have `buildozer` installed on a Linux environment (or WSL).
2. Use the provided `buildozer.spec` file.
3. Run the following command:
   ```bash
   buildozer android debug deploy run
   ```

## 📝 Roadmap
- **Direct 1-to-1 Messaging**: Transitioning from a group-lobby style network to private, direct user-to-user channels.
- **Background Android Service**: Integrate Kivy's `Foreground Service` to ensure network servers and heavy file transfers continue seamlessly when the phone screen is locked or the app is minimized.

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).

# ShareBridge Project Plan

## 🟢 Completed Milestones

1. **Core KivyMD User Interface**
   - Built a beautiful, dark-themed UI using KivyMD 2.0.
   - Created the `JoinPage` for account registration, `OpeningPage` for network loading, and `InboxPage` for chat.

2. **Automated Local Network Discovery (UDP)**
   - Replaced manual IP entry with a background UDP broadcaster and listener.
   - The app now automatically scans the Wi-Fi network (Port 37020) to find an existing Host Server without freezing the UI.

3. **Multi-Client WebSocket Server**
   - Built an asynchronous Python `websockets` server that runs in a background thread.
   - Refactored the server from a simple echo server into a true "Chat Room" that manages a set of connected clients and broadcasts messages to everyone.

4. **Robust Connection Lifecycle & Error Handling**
   - Created the `ServerActionDialog` to elegantly handle scenarios where no server is found, giving the user the option to WAIT or START SERVER.
   - Fixed complex Kivy/Asyncio garbage collection bugs to ensure smooth UI transitions and background task stability.

5. **Data Validation (Pydantic)**
   - Integrated Pydantic `BaseModel` schemas to strictly define, parse, and validate all incoming and outgoing JSON network packets (e.g., `ChatMessagePacket`). This ensures maximum stability and crash-prevention.

6. **Massive Media File Transfer Architecture**
   - Upgraded raw text strings to a strict JSON protocol to pass metadata.
   - Designed a hybrid approach mimicking modern LAN sharing apps: WebSockets are used purely for signaling/chat, while an auxiliary `aiohttp` HTTP server is spun up locally to stream binary data.
   - This HTTP streaming prevents memory overloads, allowing the transfer of 20GB+ files simultaneously across the network without crashing the host.

7. **Multi-File Selection & UI Previews**
   - Integrated `plyer.filechooser` to allow selection of multiple files from the OS.
   - Built a dynamic horizontal-scrolling `MDScrollView` in the chat input bar showing interactive preview chips for selected files, complete with remove/cancel buttons.
   - Seamlessly bundles all files and the message text into a single cohesive chat bubble containing multiple `MediaWidget` cards.

8. **Mobile Optimization & UI Refinements**
   - **Centralized Downloading**: Refined the chat UI to display all attached files cleanly within a single message card, triggering a unified "Download All" action instead of redundant individual download buttons. Only received messages display the download button.
   - **Keyboard Handling**: Enabled `Window.softinput_mode = "below_target"` to automatically pan the chat interface when the mobile virtual keyboard appears.
   - **Hardware Navigation**: Bound Kivy's keyboard listener to intercept Android physical/gesture "Back" buttons, preventing unexpected app crashes and allowing graceful exits.

9. **Sidebar & Active Users Management**
   - Implemented a strictly typed KivyMD 2.0 `MDNavigationDrawer` to act as a right-aligned sliding sidebar on the `InboxPage`.
   - Upgraded the server with a "Single Source of Truth" state management system that tracks all connected clients in real-time.
   - The server instantly broadcasts connection/disconnection arrays to all users, causing the local apps to seamlessly rewrite and update their sidebar user lists without glitches or ghost users.

## 🛠️ Architecture & Best Practices
- **Virtual Environment (`venv`)**: Migrate the project to a localized `venv` to strictly manage Kivy, KivyMD, and Websockets versions and prevent system-wide package conflicts.
- **Production Builds**: Maintained distinct build specifications for Windows (`PyInstaller` with hidden console) and Android (`Buildozer` with `READ/WRITE_EXTERNAL_STORAGE` and `INTERNET` permissions).

---

## 🚀 Upcoming Features & Roadmap

### Phase 1: Protocol Upgrade & 1-to-1 Messaging
- **Private Inboxes:** Transition the app from the current "Group Chat" lobby into a **1-to-1 Direct Messaging** system. Users will click on an active account in the right sidebar to open a private, direct line of communication with them.
- **Background Android Service**: In Android, network servers get suspended when the screen locks. Implement Kivy's `Foreground Service` so transfers can continue even when the app is minimized.

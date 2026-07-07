"""Entry point for python-for-android / Android.

python-for-android requires the app's entry file to be named `main.py`. Desktop
builds launch `MainApplication.py` directly; this just starts the same app so
both share one implementation.
"""
import asyncio

from MainApplication import ShareBridgeApp

if __name__ == "__main__":
    app = ShareBridgeApp()
    try:
        asyncio.run(app.async_run(async_lib="asyncio"))
    except KeyboardInterrupt:
        pass

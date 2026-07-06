import asyncio
import logging
import os
import time
import uuid

from aiohttp import web

log = logging.getLogger(__name__)

# Shared file links expire this long after they are registered, so a file you
# shared earlier can't be downloaded forever.
TOKEN_TTL = 3600           # 1 hour, in seconds
PURGE_INTERVAL = 300       # sweep expired links every 5 minutes


class FileTransferServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        # token -> {"path": absolute path, "expires_at": monotonic deadline}.
        # Only files the user explicitly attached are downloadable, and only
        # until their link expires.
        self.shared_files = {}
        self.runner = None
        self._purge_task = None
        self.app = web.Application()
        self.app.router.add_get('/download/{token}', self.download_handler)

    def register_file(self, file_path: str) -> str:
        """Register an attached file for sharing. Returns its URL token."""
        token = uuid.uuid4().hex
        self.shared_files[token] = {
            "path": os.path.abspath(file_path),
            "expires_at": time.monotonic() + TOKEN_TTL,
        }
        return token

    def _purge_expired(self):
        now = time.monotonic()
        expired = [t for t, e in self.shared_files.items() if e["expires_at"] <= now]
        for t in expired:
            del self.shared_files[t]
        if expired:
            log.info(f"HTTP: expired {len(expired)} shared file link(s)")

    async def download_handler(self, request):
        token = request.match_info['token']

        entry = self.shared_files.get(token)
        # Drop it if the link has expired.
        if entry and entry["expires_at"] <= time.monotonic():
            del self.shared_files[token]
            entry = None
        if not entry or not os.path.isfile(entry["path"]):
            raise web.HTTPNotFound(text="File not found")

        file_path = entry["path"]
        file_size = os.path.getsize(file_path)

        # Bypass aiohttp's FileResponse to avoid Windows [WinError 87] with 2GB+ files
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        response.headers['Content-Length'] = str(file_size)

        await response.prepare(request)

        loop = asyncio.get_running_loop()

        try:
            with open(file_path, 'rb') as f:
                chunk_size = 1024 * 1024 * 2  # 2MB chunks
                while True:
                    chunk = await loop.run_in_executor(None, f.read, chunk_size)
                    if not chunk:
                        break
                    await response.write(chunk)
        except ConnectionResetError:
            pass  # Client disconnected early

        return response

    async def _purge_loop(self):
        while True:
            await asyncio.sleep(PURGE_INTERVAL)
            self._purge_expired()

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        try:
            await site.start()
        except OSError as e:
            # Port already taken (e.g. two instances on one machine while testing)
            log.error(f"Could not start file server on port {self.port}: {e}")
            return
        self._purge_task = asyncio.create_task(self._purge_loop())
        log.info(f"File server started at http://{self.host}:{self.port}")

    def clear_links(self):
        """Immediately make every download link dead (used on app close)."""
        self.shared_files.clear()

    async def stop(self):
        """Graceful shutdown: stop purging, drop all links, free the port."""
        if self._purge_task:
            self._purge_task.cancel()
            self._purge_task = None
        self.shared_files.clear()
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
        log.info("File server stopped and all links cleared")

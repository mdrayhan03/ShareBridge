import asyncio
import logging
import os
import uuid

from aiohttp import web

log = logging.getLogger(__name__)


class FileTransferServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        # token -> absolute file path. Only files the user explicitly
        # attached are downloadable; raw paths never come from the network.
        self.shared_files = {}
        self.app = web.Application()
        self.app.router.add_get('/download/{token}', self.download_handler)

    def register_file(self, file_path: str) -> str:
        """Register an attached file for sharing. Returns its URL token."""
        token = uuid.uuid4().hex
        self.shared_files[token] = os.path.abspath(file_path)
        return token

    async def download_handler(self, request):
        token = request.match_info['token']

        file_path = self.shared_files.get(token)
        if not file_path or not os.path.isfile(file_path):
            raise web.HTTPNotFound(text="File not found")

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

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        try:
            await site.start()
        except OSError as e:
            # Port already taken (e.g. two instances on one machine while testing)
            log.error(f"Could not start file server on port {self.port}: {e}")
            return
        log.info(f"File server started at http://{self.host}:{self.port}")

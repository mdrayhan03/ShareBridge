from aiohttp import web
import os

class FileTransferServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_get('/download/{file_path:.*}', self.download_handler)

    async def download_handler(self, request):
        file_path = request.match_info['file_path']
        
        # Security: In production, ensure this doesn't traverse outside allowed directories!
        # This is a basic implementation to test LAN sharing.
        if not os.path.exists(file_path):
            raise web.HTTPNotFound(text="File not found")

        # aiohttp handles chunked streaming automatically using FileResponse
        return web.FileResponse(file_path)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"HTTP Server started at http://{self.host}:{self.port}")

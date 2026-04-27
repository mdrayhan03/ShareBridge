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

        file_size = os.path.getsize(file_path)
        
        # Bypass aiohttp's FileResponse to avoid Windows [WinError 87] with 2GB+ files
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        response.headers['Content-Length'] = str(file_size)
        
        await response.prepare(request)
        
        import asyncio
        loop = asyncio.get_running_loop()
        
        try:
            with open(file_path, 'rb') as f:
                chunk_size = 1024 * 1024 * 2 # 2MB chunks
                while True:
                    chunk = await loop.run_in_executor(None, f.read, chunk_size)
                    if not chunk:
                        break
                    await response.write(chunk)
        except ConnectionResetError:
            pass # Client disconnected early
            
        return response

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"HTTP Server started at http://{self.host}:{self.port}")

import asyncio
import os
import time

from aiohttp.test_utils import TestClient, TestServer

from services.http_server import FileTransferServer


def test_register_returns_unique_tokens(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    srv = FileTransferServer()
    t1 = srv.register_file(str(f))
    t2 = srv.register_file(str(f))
    assert t1 != t2
    assert srv.shared_files[t1]["path"] == os.path.abspath(str(f))


def test_expired_link_is_rejected_and_purged(tmp_path):
    async def scenario():
        f = tmp_path / "old.txt"
        f.write_bytes(b"stale")
        srv = FileTransferServer()
        token = srv.register_file(str(f))
        # Force the link to have expired.
        srv.shared_files[token]["expires_at"] = time.monotonic() - 1

        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get(f"/download/{token}")
            assert resp.status == 404          # expired -> not downloadable
        assert token not in srv.shared_files   # and dropped from the registry

    asyncio.run(scenario())


def test_clear_links_kills_all_downloads(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    srv = FileTransferServer()
    srv.register_file(str(f))
    srv.register_file(str(f))
    assert len(srv.shared_files) == 2
    srv.clear_links()
    assert srv.shared_files == {}


def test_download_registered_file(tmp_path):
    async def scenario():
        f = tmp_path / "hello.txt"
        f.write_bytes(b"hello world")

        srv = FileTransferServer()
        token = srv.register_file(str(f))

        async with TestClient(TestServer(srv.app)) as client:
            resp = await client.get(f"/download/{token}")
            assert resp.status == 200
            assert await resp.read() == b"hello world"

    asyncio.run(scenario())


def test_unregistered_paths_are_rejected(tmp_path):
    async def scenario():
        secret = tmp_path / "secret.txt"
        secret.write_text("top secret")

        srv = FileTransferServer()

        async with TestClient(TestServer(srv.app)) as client:
            # Raw filesystem paths must never work (the old path-traversal hole)
            resp = await client.get(f"/download/{secret}")
            assert resp.status == 404

            # Made-up tokens must 404 too
            resp = await client.get("/download/deadbeef")
            assert resp.status == 404

    asyncio.run(scenario())

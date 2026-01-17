import asyncio
import json
import weakref
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import web, WSMsgType

if TYPE_CHECKING:
    from src.config import Config


class WebHost:
    def __init__(self, config: "Config", project_root: Path | None = None):
        self._config = config
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._websockets: weakref.WeakSet[web.WebSocketResponse] = weakref.WeakSet()
        self._running = False

        self._static_dir = Path(__file__).parent / "static"
        self._templates_dir = Path(__file__).parent / "templates"
        self._project_root = project_root or Path(__file__).parent.parent.parent

    def _setup_routes(self, app: web.Application) -> None:
        app.router.add_get("/", self._handle_index)
        app.router.add_get("/ws", self._handle_websocket)
        app.router.add_post("/test-donation", self._handle_test_donation)
        app.router.add_static("/static", self._static_dir, name="static")

        # Media path relative to project root
        media_path = Path(self._config.get_media_path())
        if not media_path.is_absolute():
            media_path = self._project_root / media_path
        media_path = media_path.resolve()

        print(f"[WebHost] Media path: {media_path}")
        if media_path.exists():
            app.router.add_static("/media", media_path, name="media")
        else:
            print(f"[WebHost] Warning: Media path does not exist: {media_path}")

    async def _handle_index(self, request: web.Request) -> web.Response:
        template_path = self._templates_dir / "overlay.html"
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            return web.Response(text=content, content_type="text/html")
        return web.Response(text="Overlay template not found", status=404)

    async def _handle_test_donation(self, request: web.Request) -> web.Response:
        """Handle test donation button click."""
        print("[WebHost] Test donation requested")

        # Send test media to all connected clients
        await self.show_media(
            image_path="video/bebra.gif",
            audio_path="audio/donat_gitara.mp3",
            duration_ms=5000
        )

        return web.json_response({"status": "ok", "message": "Test donation sent"})

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self._websockets.add(ws)
        print(f"[WebHost] WebSocket connected. Total: {len(self._websockets)}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    pass
                elif msg.type == WSMsgType.ERROR:
                    print(f"[WebHost] WebSocket error: {ws.exception()}")
        finally:
            self._websockets.discard(ws)
            print(f"[WebHost] WebSocket disconnected. Total: {len(self._websockets)}")

        return ws

    async def _broadcast(self, message: dict) -> None:
        if not self._websockets:
            return

        data = json.dumps(message)
        tasks = []

        for ws in list(self._websockets):
            if not ws.closed:
                tasks.append(ws.send_str(data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def start_async(self) -> None:
        if self._running:
            return

        self._app = web.Application()
        self._setup_routes(self._app)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        host = self._config.get_host()
        port = self._config.get_port()

        self._site = web.TCPSite(self._runner, host, port)
        await self._site.start()

        self._running = True
        print(f"[WebHost] Server started at http://{host}:{port}")

    async def stop_async(self) -> None:
        if not self._running:
            return

        for ws in list(self._websockets):
            await ws.close()

        if self._runner:
            await self._runner.cleanup()

        self._running = False
        self._app = None
        self._runner = None
        self._site = None
        print("[WebHost] Server stopped")

    def start(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start_async())

    def stop(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.stop_async())

    def is_running(self) -> bool:
        return self._running

    def get_url(self) -> str:
        return f"http://{self._config.get_host()}:{self._config.get_port()}"

    async def show_image(self, image_path: str, duration_ms: int | None = None) -> None:
        duration = duration_ms or self._config.get_default_duration()
        await self._broadcast({
            "type": "show_image",
            "image": f"/media/{image_path}",
            "duration": duration,
        })

    async def show_gif(self, gif_path: str, duration_ms: int | None = None) -> None:
        await self.show_image(gif_path, duration_ms)

    async def show_media(
        self,
        image_path: str,
        audio_path: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        duration = duration_ms or self._config.get_default_duration()
        message = {
            "type": "show_media",
            "image": f"/media/{image_path}",
            "duration": duration,
        }
        if audio_path:
            message["audio"] = f"/media/{audio_path}"

        await self._broadcast(message)

    async def clear(self) -> None:
        await self._broadcast({"type": "clear"})

# api_eazy.py
import asyncio
from aiohttp import web
import sys

class Route:
    _routes = {}  # all routes
    _default = None  # optional default route

    def __init__(self, path=None):
        # If path is None → default route
        self.path = path if path and path.startswith("/") else path

    def __call__(self, func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Route function must be async")
        if self.path:
            Route._routes[self.path] = func
        else:
            Route._default = func
        return func


class Api:
    """Minimal async API server"""
    def __init__(self, name):
        self.name = name
        self.app = web.Application()

        # Global exception handler for asyncio (Windows-safe)
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self._handle_loop_exception)

    def _handle_loop_exception(self, loop, context):
        # Ignore ConnectionResetError (client disconnected)
        exc = context.get("exception")
        if exc and isinstance(exc, ConnectionResetError):
            return
        loop.default_exception_handler(context)

    def _create_handler(self, func):
        async def handler(request):
            try:
                result = await func()
                if isinstance(result, dict):
                    return web.json_response(result)
                return web.Response(text=str(result))
            except ConnectionResetError:
                # Ignore client disconnects
                return web.Response(status=499)  # client closed request
            except Exception as e:
                return web.Response(text=f"500 Internal Server Error: {e}", status=500)
        return handler

    def run(self, host="127.0.0.1", port=8000):
        # Register all specific routes
        for path, func in Route._routes.items():
            self.app.router.add_get(path, self._create_handler(func))
            print(f"Route active: {path}")

        # Register default route at "/" if exists
        if Route._default:
            async def default_handler(request):
                return await Route._default()
            self.app.router.add_get("/", default_handler)
            print("Default route active at /")

        print(f"API server running on http://{host}:{port}")
        web.run_app(self.app, host=host, port=port)


def keep_alive(route):
    """Synchronous keep-alive server"""
    if not route:
        raise ValueError("You must provide a route for keep_alive")
    if not route.startswith("/"):
        route = "/" + route

    async def handler(request):
        return web.json_response({"status": "alive"})

    async def _start():
        app = web.Application()
        app.router.add_get(route, handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8000)
        await site.start()
        print(f"Keep-alive endpoint running at {route}")
        await asyncio.Event().wait()  # keep running

    asyncio.run(_start())

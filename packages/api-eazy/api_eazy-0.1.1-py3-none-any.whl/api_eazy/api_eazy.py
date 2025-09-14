import asyncio
from aiohttp import web

class Route:
    """Decorator to register async routes"""
    _routes = {}  # class-level storage

    def __init__(self, path):
        if not path:
            raise ValueError("Route path must be set")
        self.path = path if path.startswith("/") else "/" + path

    def __call__(self, func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Route function must be async")
        Route._routes[self.path] = func
        return func

class Api:
    """Minimal async API server"""
    def __init__(self, name):
        self.name = name
        self.app = web.Application()

    def _create_handler(self, func):
        async def handler(request):
            try:
                result = await func()
                if isinstance(result, dict):
                    return web.json_response(result)
                return web.Response(text=str(result))
            except Exception as e:
                return web.Response(text=f"500 Internal Server Error: {e}", status=500)
        return handler

    def run(self, host="0.0.0.0", port=8000):
        for path, func in Route._routes.items():
            self.app.router.add_get(path, self._create_handler(func))
        print(f"API server running on http://{host}:{port}")
        web.run_app(self.app, host=host, port=port)


def keep_alive(route):
    """Start a minimal keep-alive server at the specified route (synchronous function)"""
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
        # Keep the server running forever
        await asyncio.Event().wait()

    # Run the async server in the event loop
    asyncio.run(_start())

import asyncio
from aiohttp import web

# Internal route storage
_routes = {}

class Route:
    """Decorator to register a route"""
    def __init__(self, path):
        if not path:
            raise ValueError("Route path must be set")
        self.path = path

    def __call__(self, func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Route function must be async")
        _routes[self.path] = func
        return func

class Api:
    """Minimal async API server"""
    def __init__(self, name):
        self.name = name
        self.app = web.Application()

    async def _handle_request(self, request):
        func = _routes.get(request.path)
        if not func:
            return web.Response(text="404 Not Found", status=404)
        try:
            result = await func()
            if isinstance(result, dict):
                return web.json_response(result)
            return web.Response(text=str(result))
        except Exception as e:
            return web.Response(text=f"500 Internal Server Error: {e}", status=500)

    def run(self, host="0.0.0.0", port=8000):
        for path in _routes:
            self.app.router.add_get(path, self._handle_request)
        print(f"API server running on http://{host}:{port}")
        web.run_app(self.app, host=host, port=port)

async def keep_alive(route):
    """Start a minimal keep-alive server at the specified route"""
    if not route:
        raise ValueError("You must provide a route for keep_alive")

    async def handler(request):
        return web.json_response({"status": "alive"})

    app = web.Application()
    app.router.add_get(route, handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    print(f"Keep-alive endpoint running at {route}")

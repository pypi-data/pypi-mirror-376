# api_eazy.py
import asyncio
from aiohttp import web

class Route:
    _routes = {}  # class-level storage
    _default = None  # fallback handler

    def __init__(self, path=None):
        # If path is None, this will be the default route
        self.path = path if path and path.startswith("/") else path

    def __call__(self, func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Route function must be async")
        if self.path:
            Route._routes[self.path] = func
        else:
            Route._default = func  # store as default handler
        return func

class Api:
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

    def run(self, host="127.0.0.1", port=8000):
        # Register all routes
        for path, func in Route._routes.items():
            self.app.router.add_get(path, self._create_handler(func))
            print(f"Route active: {path}")

        # Register default route if it exists
        if Route._default:
            async def default_handler(request):
                return await Route._default()
            self.app.router.add_get("/", default_handler)
            print("Default route active at /")

        print(f"API server running on http://{host}:{port}")
        web.run_app(self.app, host=host, port=port)


def keep_alive(route):
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
        await asyncio.Event().wait()

    asyncio.run(_start())

import asyncio
from aiohttp import web, ClientSession
import json

class Route:
    _routes = {}
    _default = None
    _metadata = {}  # optional metadata like query params

    def __init__(self, path=None, query_params=None):
        self.path = path if path and path.startswith("/") else path
        self.query_params = query_params or []

    def __call__(self, func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Route function must be async")
        if self.path:
            Route._routes[self.path] = func
            Route._metadata[self.path] = self.query_params
        else:
            Route._default = func
        return func

class Api:
    def __init__(self, name):
        self.name = name
        self.app = web.Application()
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self._handle_loop_exception)

    def _handle_loop_exception(self, loop, context):
        exc = context.get("exception")
        if exc and isinstance(exc, ConnectionResetError):
            return
        loop.default_exception_handler(context)

    def _create_handler(self, func):
        async def handler(request):
            try:
                result = await func(request)
                if isinstance(result, dict):
                    return web.json_response(result)
                return web.Response(text=str(result))
            except ConnectionResetError:
                return web.Response(status=499)
            except Exception as e:
                return web.Response(text=f"500 Internal Server Error: {e}", status=500)
        return handler

    def add_routes(self):
        # Register all normal routes
        for path, func in Route._routes.items():
            self.app.router.add_get(path, self._create_handler(func))
            print(f"Route active: {path}")

        # Default route at /
        if Route._default:
            async def default_handler(request):
                return await Route._default(request)
            self.app.router.add_get("/", default_handler)
            print("Default route active at /")

        # Route to send metadata to another endpoint
        async def send_metadata(request):
            target_url = request.query.get("target")
            if not target_url:
                return web.json_response({"error": "Please provide ?target= URL"}, status=400)
            
            data = [
                {"path": p, "query_params": Route._metadata.get(p, [])}
                for p in Route._routes
            ]
            async with ClientSession() as session:
                try:
                    async with session.post(target_url, json=data) as resp:
                        resp_text = await resp.text()
                        return web.json_response({
                            "status": resp.status,
                            "response": resp_text
                        })
                except Exception as e:
                    return web.json_response({"error": str(e)}, status=500)

        self.app.router.add_get("/send_metadata", send_metadata)
        print("Route active: /send_metadata (use ?target=your_endpoint)")

    def run(self, host="127.0.0.1", port=8000):
        self.add_routes()
        print(f"API server running on http://{host}:{port}")
        web.run_app(self.app, host=host, port=port)

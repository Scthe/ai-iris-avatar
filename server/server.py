import weakref
from aiohttp import web, WSMsgType, WSCloseCode
from typing import Callable
from termcolor import colored


# store websockets
# https://docs.aiohttp.org/en/stable/web_advanced.html#websocket-shutdown
websockets = web.AppKey("websockets", weakref.WeakSet)

socket_msg_handler = web.AppKey("socket_msg_handler", Callable)  # type: ignore


async def status(_request):
    return web.Response(text="OK")


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print(colored("Websocket connected", "yellow"))

    request.app[websockets].add(ws)

    handler = request.app[socket_msg_handler](ws)

    try:
        async for msg in ws:
            # print("RAW MSG:", msg)
            if msg.type == WSMsgType.TEXT:
                if handler:
                    msg = msg.json()
                    await handler(msg)
            elif msg.type == WSMsgType.ERROR:
                print("ws connection closed with exception %s" % ws.exception())
    finally:
        request.app[websockets].discard(ws)
    print(colored("Websocket connection closed", "yellow"))

    return ws


async def index_handler(_request):
    raise web.HTTPFound(location="/index.html")


async def on_shutdown(app):
    for ws in set(app[websockets]):
        await ws.close(code=WSCloseCode.GOING_AWAY, message="Server shutdown")


def create_server(static_dir):
    app = web.Application()

    app[websockets] = weakref.WeakSet()
    app.on_shutdown.append(on_shutdown)

    app.add_routes([web.get("/status", status)])
    app.add_routes([web.get("/", websocket_handler)])
    app.add_routes([web.get("/ui", index_handler)])

    # bleh, bleh, development only (aiohttp docs mumbling continues..)
    app.add_routes([web.static("/", static_dir)])

    return app


def set_socket_msg_handler(app, handler):
    app[socket_msg_handler] = handler


def start_server(app, host="localhost", port=8080):
    web.run_app(app, host=host, port=port)

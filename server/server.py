import weakref
from aiohttp import web, WSMsgType, WSCloseCode
from typing import Callable
from server.app_logic import AppLogic
from termcolor import colored
import json


# store websockets
# https://docs.aiohttp.org/en/stable/web_advanced.html#websocket-shutdown
websockets = web.AppKey("websockets", weakref.WeakSet)
socket_msg_handler_ctx = web.AppKey("socket_msg_handler_ctx", Callable)  # type: ignore
app_logic_ctx = web.AppKey("app_logic", AppLogic)  # type: ignore


async def status(_request):
    return web.Response(text="OK")


def is_unity_websocket(request):
    for k, _ in request.raw_headers:
        if k == b"Cache-Control":
            return False
    return True


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app[websockets].add(ws)

    is_unity = is_unity_websocket(request)
    handler = request.app[socket_msg_handler_ctx](ws, is_unity)
    is_unity_str = "unity" if is_unity else "web_browser"
    print(colored(f"Websocket connected ({is_unity_str})", "yellow"))

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
        handler.on_disconnect()
    print(colored(f"Websocket connection closed ({is_unity_str})", "yellow"))

    return ws


async def index_handler(_request):
    raise web.HTTPFound(location="/index.html")


async def prompt_handler(request):
    is_post = request.method == "POST"

    if is_post:
        data = await request.json()
        for k, v in data.items():
            print(f"'{k}'='{v}'")
        print(f"total={len(data)}")
        prompt = data.get("value", "")
    else:
        prompt = request.query.get("value", "")

    if not prompt:
        field_type = "field" if is_post else "query param"
        reason = f"The {request.method} request is missing 'value' {field_type}."
        res = json.dumps({"status": "error", "reason": reason})
        return web.HTTPBadRequest(text=res, reason=reason)
    # print(f'prompt="{prompt}"')

    app_logic = request.app[app_logic_ctx]
    llm_text = await app_logic.ask_query(prompt)
    res = {"status": "ok", "received_prompt": prompt, "resp": llm_text}
    return web.json_response(res)


async def on_shutdown(app):
    for ws in set(app[websockets]):
        await ws.close(code=WSCloseCode.GOING_AWAY, message="Server shutdown")


def create_server(static_dir, ws_handler, app_logic):
    app = web.Application()
    app[socket_msg_handler_ctx] = ws_handler
    app[app_logic_ctx] = app_logic

    app[websockets] = weakref.WeakSet()
    app.on_shutdown.append(on_shutdown)

    app.add_routes([web.get("/status", status)])
    app.add_routes(
        [web.get("/", websocket_handler)]
    )  # unity might have problem otherwise?
    app.add_routes([web.get("/ui", index_handler)])
    app.add_routes(
        [web.get("/prompt", prompt_handler), web.post("/prompt", prompt_handler)]
    )

    # bleh, bleh, development only (aiohttp docs mumbling continues..)
    app.add_routes([web.static("/", static_dir)])

    return app


def start_server(app, host="localhost", port=8080):
    web.run_app(app, host=host, port=port)

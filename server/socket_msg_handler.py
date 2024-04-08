import traceback
from aiohttp import web

from termcolor import colored
from typing import Any

from server.message_handler import MessageHandler
from server.tts_utils import generate_id


class SocketMsgHandler:
    def __init__(
        self,
        ws: web.WebSocketResponse,
        handler: MessageHandler,
        is_unity: bool,
    ):
        self.ws = ws
        self.handler = handler
        self.is_unity = is_unity

        if self.is_unity:
            # handler.on_text_response.append(self.on_text_response)
            handler.on_tts_response.append(self.on_tts_response)
            handler.on_play_vfx.append(self.on_play_vfx)
        else:
            # web browser
            handler.on_query.append(self.on_query)
            handler.on_text_response.append(self.on_text_response)
            handler.on_tts_timings.append(self.on_tts_timinigs)

    def on_disconnect(self):
        self.handler.on_query.safe_remove(self.on_query)
        self.handler.on_text_response.safe_remove(self.on_text_response)
        self.handler.on_tts_response.safe_remove(self.on_tts_response)
        self.handler.on_tts_timings.safe_remove(self.on_tts_timinigs)
        self.handler.on_play_vfx.safe_remove(self.on_play_vfx)

    async def __call__(self, msg):
        # print(msg)
        type = msg.get("type", "")

        try:
            if type == "query":
                msg_id = msg.get("msgId", generate_id())
                text = msg.get("text", "")
                await self.handler.ask_query(text, msg_id)
            elif type == "play-vfx":
                vfx = msg.get("vfx", "")
                await self.handler.play_vfx(vfx)
            else:
                print(
                    colored(f'[Socket error] Unrecognised message: "{type}"', "red"),
                    msg,
                )

        except Exception as e:
            traceback.print_exception(e)
            data = {
                "type": "error",
                "msgId": msg_id,
                "error": str(e),
            }
            await self.ws_send_json(data)

    async def on_query(self, msg: str, msg_id: str):
        data = {
            "type": "query",
            "msgId": msg_id,
            "text": msg,
        }
        await self.ws_send_json(data)

    async def on_text_response(self, msg: str, msg_id: str, elapsed_llm: float):
        data = {
            "type": "done",
            "msgId": msg_id,
            "text": msg,
            "elapsed_llm": elapsed_llm,
        }
        print(data)
        await self.ws_send_json(data)

    async def on_tts_response(self, bytes):
        # print("on_tts_response()")
        await self.ws_send_bytes(bytes)

    async def on_tts_timinigs(self, msg_id: str, elapsed_tts: float):
        data = {
            "type": "tts-elapsed",
            "msgId": msg_id,
            "elapsed_tts": elapsed_tts,
        }
        await self.ws_send_json(data)

    async def on_play_vfx(self, vfx: str):
        data = {
            "type": "play-vfx",
            "vfx": vfx,
        }
        await self.ws_send_json(data)

    async def ws_send_json(self, data: Any):
        await self.ws.send_json((data))

    async def ws_send_bytes(self, data: Any):
        await self.ws.send_bytes(data)

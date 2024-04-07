import traceback
from aiohttp import web

from termcolor import colored
from typing import Any

from server.message_handler import MessageHandler


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
            handler.on_text_response.append(self.on_text_response)
            handler.on_tts_response.append(self.on_tts_response)
        else:
            # web browser
            # TODO add on_query here too. Can happen if unity asked the question.
            # Web browser should show queries from both itself and unity
            handler.on_text_response.append(self.on_text_response)

    def on_disconnect(self):
        # self.handler.on_query.safe_remove(self.on_query)
        self.handler.on_text_response.safe_remove(self.on_text_response)
        self.handler.on_tts_response.safe_remove(self.on_tts_response)

    async def __call__(self, msg):
        type = msg.get("type", "")

        try:
            if type == "query":
                msg_id = msg.get("msgId", "")
                text = msg.get("text", "")
                await self.handler.ask_query(text, msg_id=msg_id)
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

    async def on_text_response(self, msg, **kwargs):
        # TODO add LLM timings
        data = {
            "type": "done",
            "msgId": kwargs.get("msgId", ""),
            "text": msg,
        }
        print(data)
        await self.ws_send_json(data)

    async def on_tts_response(self, bytes):
        print("on_tts_response()")
        await self.ws_send_bytes(bytes)

    async def ws_send_json(self, data: Any):
        await self.ws.send_json((data))

    async def ws_send_bytes(self, data: Any):
        await self.ws.send_bytes(data)

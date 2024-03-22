import traceback
from aiohttp import web

# from TTS.api import TTS
from termcolor import colored
from typing import Any

from server.config import AppConfig
from server.tts_utils import exec_tts, wav2bytes


class SocketMsgHandler:
    """
    https://github.com/Scthe/rag-chat-with-context/blob/master/src/socket_msg_handler.py
    """

    def __init__(
        self,
        cfg: AppConfig,
        tts: None,  # TTS,
        ws: web.WebSocketResponse,
    ):
        self.cfg = cfg
        self.ws = ws
        self.tts = tts

    async def __call__(self, msg):
        msg_id = msg.get("msgId", "")
        type = msg.get("type", "")

        try:
            if type == "query":
                await self.ask_question(msg_id, msg)
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

    async def ask_question(self, msg_id, msg):
        q = msg.get("text", "")
        print(colored(f"Q:", "blue"), q)

        self.tts_and_send_to_client(msg_id, "Hello, this is a sample response")

        """
        data = {
            "type": "done",
            "msgId": msg_id,
            "text": q,
        }
        # print(data)
        await self.ws_send_json(data)
        """

    def tts_and_send_to_client(self, msg_id, text):
        import asyncio

        # TODO https://docs.coqui.ai/en/latest/models/xtts.html#streaming-manually
        if len(text) <= 0:
            return
        # print(colored("voicing:", "green"), tokens)

        async def tts_internal():
            wav = exec_tts(self.cfg, self.tts, text)
            bytes = wav2bytes(self.tts, wav)

            # Remember: websockets are on TCP. Always in correct order.
            await self.ws_send_bytes(bytes)

        loop = asyncio.get_running_loop()
        # asyncio.run(tts_internal())
        loop.create_task(tts_internal())

    async def ws_send_json(self, data: Any):
        await self.ws.send_json((data))

    async def ws_send_bytes(self, data: Any):
        await self.ws.send_bytes(data)

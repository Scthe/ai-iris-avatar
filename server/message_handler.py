from TTS.api import TTS
from termcolor import colored

from server.config import AppConfig
from server.tts_utils import exec_tts_async
from server.signal import Signal


class MessageHandler:
    """
    Based on:
    https://github.com/Scthe/rag-chat-with-context/blob/master/src/socket_msg_handler.py
    """

    def __init__(
        self,
        cfg: AppConfig,
        tts: TTS,
    ):
        self.cfg = cfg
        self._tts = tts
        self.on_query = Signal()
        # self.on_text_response_token = Signal(self)  # TODO
        self.on_text_response = Signal()
        self.on_tts_response = Signal()

    async def ask_query(self, query, **kwargs):
        print(colored("Query:", "blue"), f"'{query}'", kwargs)
        await self.on_query.send(query, **kwargs)

        resp_text = "Hello, this is a sample response"
        await self.on_text_response.send(resp_text, query=query, **kwargs)

        if not self.on_tts_response:
            # TODO send TTS timings: 0
            return
        await self.tts(resp_text)
        # TODO send TTS timings

    async def tts(self, text: str):
        await exec_tts_async(
            self.cfg,
            self._tts,
            text,
            lambda bytes: self.tts_send(bytes),
        )

    async def tts_send(self, bytes):
        # TODO should we time this and send separate 'ai-tts-elapsed' message?
        await self.on_tts_response.send(bytes)

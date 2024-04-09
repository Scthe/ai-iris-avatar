from TTS.api import TTS
from termcolor import colored

from server.config import AppConfig
from server.tts_utils import exec_tts_async
from server.signal import Signal
from server.utils import Timer


class AppLogic:
    """
    1. Execute all actions. Ask LLM, do the TTS etc.
    2. Event dispatcher between websockets. A pub/sub.

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
        self.on_tts_timings = Signal()
        self.on_play_vfx = Signal()

    async def ask_query(self, query: str, msg_id: str):
        print(colored("Query:", "blue"), f"'{query}' (msg_id={msg_id})")
        await self.on_query.send(query, msg_id)

        with Timer() as llm_timer:
            resp_text = "Hello, this is a sample response"
        await self.on_text_response.send(resp_text, msg_id, llm_timer.delta)

        with Timer() as tts_timer:
            await self.tts(resp_text)
        await self.on_tts_timings.send(msg_id, tts_timer.delta)

    async def play_vfx(self, vfx: str):
        print(colored("VFX (particle system):", "blue"), f"'{vfx}'")
        await self.on_play_vfx.send(vfx)

    async def tts(self, text: str):
        # skip if no event listeners
        if not self.on_tts_response:
            return

        # split into sentences to lower time to first chunk
        sentences = self._tts.split_into_sentences(text)
        for sentence in sentences:
            await exec_tts_async(
                self.cfg,
                self._tts,
                sentence,
                lambda bytes: self.tts_send(bytes),
            )

    async def tts_send(self, bytes):
        await self.on_tts_response.send(bytes)

from TTS.api import TTS
from termcolor import colored
from ollama import AsyncClient as OllamaAsyncClient
import asyncio

from server.config import AppConfig
from server.tts_utils import exec_tts, wav2bytes
from server.signal import Signal
from server.utils import Timer


def wrap_prompt_gemma2b(text, **kwargs):
    GEMMA_TEMPLATE = """<start_of_turn>user
    Answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise.
    
    Question: {text}<end_of_turn>
    <start_of_turn>model"""

    return GEMMA_TEMPLATE.format(text=text, **kwargs)


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
        llm: OllamaAsyncClient,
        tts: TTS,
    ):
        self.cfg = cfg
        self.llm = llm
        self._tts = tts

        self.on_query = Signal()
        self.on_text_response = Signal()
        self.on_tts_response = Signal()
        self.on_tts_timings = Signal()
        self.on_play_vfx = Signal()

    async def ask_query(self, query: str, msg_id: str):
        print(colored("Query:", "blue"), f"'{query}' (msg_id={msg_id})")
        await self.on_query.send(query, msg_id)

        with Timer() as llm_timer:
            resp_text = await self._exec_llm(query)
        await self.on_text_response.send(resp_text, msg_id, llm_timer.delta)

        await self._exec_tts(resp_text, msg_id)  # internally can use different thread

    async def play_vfx(self, vfx: str):
        print(colored("VFX (particle system):", "blue"), f"'{vfx}'")
        await self.on_play_vfx.send(vfx)

    async def _exec_llm(self, query: str):
        """If this fn returns nothing, just restart ollama"""

        cfg = self.cfg.llm
        if isinstance(cfg.mocked_response, str):
            print(
                colored("Mocked LLM response based on config:", "blue"),
                f"'{cfg.mocked_response}'",
            )
            return query if cfg.mocked_response == "" else cfg.mocked_response

        # TODO self.llm.chat
        prompt = wrap_prompt_gemma2b(query)
        # https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion
        resp = await self.llm.generate(
            model=cfg.model,
            prompt=prompt,
            # https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
            options={
                "temperature": self.cfg.llm.temperature,
                "top_k": self.cfg.llm.top_k,
                "top_p": self.cfg.llm.top_p,
            },
        )
        return resp.get("response")

    async def _exec_tts(self, text: str, msg_id: str):
        # skip if no event listeners
        if not self.on_tts_response:
            await self.on_tts_timings.send(msg_id, 0)
            return

        # TODO https://docs.coqui.ai/en/latest/models/xtts.html#streaming-manually

        # split into sentences to lower time to first chunk
        sentences = self._tts.synthesizer.split_into_sentences(text)

        async def tts_internal():
            is_first_sentence = True
            with Timer() as tts_timer:
                for sentence in sentences:
                    await self._tts_sentence(sentence, is_first_sentence)
                    is_first_sentence = False

            # tts done, send timings
            await self.on_tts_timings.send(msg_id, tts_timer.delta)

        loop = asyncio.get_running_loop()
        loop.create_task(tts_internal())

    async def _tts_sentence(self, sentence: str, is_first_sentence: bool):
        wav = exec_tts(self.cfg, self._tts, sentence)
        bytes = wav2bytes(self._tts, wav)
        await self._tts_send(bytes)

        if is_first_sentence:
            print(colored("Finished first TTS sentence (see above)", "blue"))

    async def _tts_send(self, bytes):
        await self.on_tts_response.send(bytes)

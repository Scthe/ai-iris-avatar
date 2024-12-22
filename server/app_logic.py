from TTS.api import TTS
from termcolor import colored
from ollama import AsyncClient as OllamaAsyncClient
from typing import Optional
import types
import asyncio

from server.config import AppConfig
from server.tts_utils import exec_tts, wav2bytes, wav2bytes_streamed
from server.signal import Signal
from server.utils import Timer, generate_id


class GemmaChatContext:
    """https://ai.google.dev/gemma/docs/pytorch_gemma"""

    USER_CHAT_TEMPLATE = "<start_of_turn>user\n{prompt}<end_of_turn>\n"
    MODEL_CHAT_TEMPLATE = "<start_of_turn>model\n{prompt}<end_of_turn>\n"

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.history = []

    def add_user_query(self, query):
        self.history.append(GemmaChatContext.USER_CHAT_TEMPLATE.format(prompt=query))

    def add_model_response(self, resp):
        self.history.append(GemmaChatContext.MODEL_CHAT_TEMPLATE.format(prompt=resp))

    def reset(self):
        self.history = []

    def generate_prompt(self):
        ctx_len = self.cfg.llm.context_length
        if ctx_len > 0:
            self.history = self.history[-ctx_len * 2 :]
        else:
            self.history = self.history[-1:]
        context = "".join(self.history)

        system_message = self.cfg.llm.system_message
        system_message = system_message if isinstance(system_message, str) else ""
        system_message = system_message.strip()
        sys_prompt = ""
        if len(system_message) > 0:
            sys_prompt = GemmaChatContext.USER_CHAT_TEMPLATE.format(
                prompt=system_message
            )

        return sys_prompt + context + "<start_of_turn>model\n"


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
        self.chat_context = GemmaChatContext(cfg)

        self.on_query = Signal()
        self.on_text_response = Signal()
        self.on_tts_response = Signal()
        self.on_tts_timings = Signal()
        self.on_tts_first_chunk = Signal()
        self.on_play_vfx = Signal()

    async def ask_query(self, query: str, msg_id: Optional[str] = ""):
        if not msg_id:
            msg_id = generate_id()
        print(colored("Query:", "blue"), f"'{query}' (msg_id={msg_id})")
        await self.on_query.send(query, msg_id)
        self.chat_context.add_user_query(query)

        time_to_first_tts = Timer(start=True)

        with Timer() as llm_timer:
            resp_text = await self._exec_llm(query)
            self.chat_context.add_model_response(resp_text)
        await self.on_text_response.send(resp_text, msg_id, llm_timer.delta)

        # internally can use different thread
        await self._exec_tts(resp_text, msg_id, time_to_first_tts)

        return resp_text

    async def play_vfx(self, vfx: str):
        print(colored("VFX (particle system):", "blue"), f"'{vfx}'")
        await self.on_play_vfx.send(vfx)

    def reset_context(self):
        self.chat_context.reset()

    async def _exec_llm(self, query: str) -> str:
        """If this fn returns nothing, just restart ollama"""

        cfg = self.cfg.llm
        if isinstance(cfg.mocked_response, str):
            print(
                colored("Mocked LLM response based on config:", "blue"),
                f"'{cfg.mocked_response}'",
            )
            return query if cfg.mocked_response == "" else cfg.mocked_response

        prompt = self.chat_context.generate_prompt()
        # print(colored(prompt, "yellow"))

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

    async def _exec_tts(self, text: str, msg_id: str, time_to_first_tts: Timer):
        # skip if no event listeners
        if not self.on_tts_response:
            await self.on_tts_timings.send(msg_id, 0)
            await self.on_tts_first_chunk.send(msg_id, 0)
            return

        # split into sentences to lower time to first chunk
        sentences = self._tts.synthesizer.split_into_sentences(text)

        async def tts_internal():
            with Timer() as tts_timer:
                for sentence in sentences:
                    await self._tts_sentence(sentence)
                    await self._time_first_audio_chunk(msg_id, time_to_first_tts)

            # tts done, send timings
            await self.on_tts_timings.send(msg_id, tts_timer.delta)

        loop = asyncio.get_running_loop()
        loop.create_task(tts_internal())

    async def _tts_sentence(self, sentence: str):
        output = exec_tts(self.cfg, self._tts, sentence)  # either object or generator

        if not isinstance(output, types.GeneratorType):
            # when not streaming
            bytes = wav2bytes(self._tts, output)
            await self.on_tts_response.send(bytes)  # send to client
        else:
            # when streaming
            for i, chunk in enumerate(output):
                bytes = wav2bytes_streamed(self._tts, chunk)
                # print(colored(f"raw_chunk_{i}", "yellow"), "sending")
                await self.on_tts_response.send(bytes)  # send to client
                # print(colored(f"raw_chunk_{i}", "yellow"), "send success")

    async def _time_first_audio_chunk(self, msg_id: str, time_to_first_tts: Timer):
        if not time_to_first_tts.is_running():
            return

        delta = time_to_first_tts.stop()
        await self.on_tts_first_chunk.send(msg_id, delta)
        print(
            colored("First TTS chunk:", "blue"),
            f"{time_to_first_tts.delta:.2f}s",
        )

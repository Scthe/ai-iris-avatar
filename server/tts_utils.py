from TTS.api import TTS
from server.config import AppConfig
from termcolor import colored


def get_torch_device(tts: TTS):
    model = tts.synthesizer.tts_model
    return next(model.parameters()).device


def list_speakers(tts: TTS):
    sm = tts.synthesizer.tts_model.speaker_manager
    if sm == None:
        return []
    return list(tts.synthesizer.tts_model.speaker_manager.name_to_id)


def get_tts_options(cfg: AppConfig, tts: TTS):
    kw = {}
    is_cloning = False

    if tts.is_multi_speaker:
        kw["speaker"] = cfg.tts.speaker
    if tts.is_multi_lingual:
        kw["language"] = cfg.tts.language
    # emotion: str = None,
    # speed: float = None,
    # split_sentences: bool = True,

    sample_of_cloned_voice_wav = cfg.tts.sample_of_cloned_voice_wav
    if sample_of_cloned_voice_wav:
        is_cloning = True
        kw["speaker_wav"] = sample_of_cloned_voice_wav

    return is_cloning, kw


def exec_tts(cfg: AppConfig, tts: TTS, text: str):
    is_cloning, tts_kwargs = get_tts_options(cfg, tts)

    if is_cloning:
        wav = tts.tts_with_vc(text=text, **tts_kwargs)
    else:
        wav = tts.tts(text=text, **tts_kwargs)

    return wav


async def exec_tts_async(cfg: AppConfig, tts: TTS, text: str, callback):
    import asyncio

    # TODO https://docs.coqui.ai/en/latest/models/xtts.html#streaming-manually
    if len(text) <= 0:
        return
    # print(colored("voicing:", "green"), tokens)

    async def tts_internal():
        wav = exec_tts(cfg, tts, text)
        bytes = wav2bytes(tts, wav)

        # Remember: websockets are on TCP. Always in correct order.
        await callback(bytes)

    loop = asyncio.get_running_loop()
    # asyncio.run(tts_internal())
    loop.create_task(tts_internal())


def exec_tts_to_file(
    cfg: AppConfig, tts: TTS, text: str, out_file_path: str, verbose=False
):
    is_cloning, tts_kwargs = get_tts_options(cfg, tts)

    if is_cloning:
        if verbose:
            speaker = tts_kwargs.get("speaker_wav", "")
            print(colored("Cloning voice based on:", "blue"), f"'{speaker}'")
        wav = tts.tts_with_vc_to_file(text=text, file_path=out_file_path, **tts_kwargs)
    else:
        if verbose:
            print(colored("Voice cloning:", "blue"), "OFF")
        wav = tts.tts_to_file(text=text, file_path=out_file_path, **tts_kwargs)

    return wav


def wav2bytes(tts: TTS, wav):
    import io

    out = io.BytesIO()
    tts.synthesizer.save_wav(wav, out)
    return out.getbuffer()


def generate_id():
    import random
    import string

    length = 8
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

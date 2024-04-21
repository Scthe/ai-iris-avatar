from TTS.api import TTS
from server.config import AppConfig
from termcolor import colored

from server.tts_deepspeed import xtts_with_deepspeed, can_load_xtts2_with_deepspeed


def get_torch_device(tts: TTS):
    model = tts.synthesizer.tts_model
    return next(model.parameters()).device


def create_tts(cfg: AppConfig):
    from TTS.api import TTS

    model_name = cfg.tts.model_name
    print(colored("TTS model:", "blue"), model_name)
    if can_load_xtts2_with_deepspeed(cfg):
        return xtts_with_deepspeed(cfg)

    tts = TTS(model_name=model_name, gpu=cfg.tts.use_gpu, progress_bar=True)
    print(colored("TTS device:", "blue"), get_torch_device(tts))
    return tts


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

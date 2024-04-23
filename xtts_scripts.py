from typing import Optional
from termcolor import colored
from tqdm import tqdm
import click
import os.path

from server.tts_utils import (
    create_tts,
    exec_tts_to_file,
    get_tts_options,
    list_speakers as list_speakers_util,
)
from server.config import load_app_config

DEFAULT_TEXT = "The current algorithm only upscales the luma, the chroma is preserved as-is. This is a common trick known"


@click.command()
@click.option("--config", "-c", help="Config file")
@click.option(
    "--voice", "-v", type=click.Path(exists=True), help="Cloned voice, overrides config"
)
def create_speaker_samples(config: str, voice: Optional[str]):
    """Generate samples for each speaker in the TTS model. Supports voice cloning."""

    cfg = load_app_config(config)
    cfg.tts.streaming_enabled = False
    print(colored("TTS config:", "blue"), cfg.tts)
    tts = create_tts(cfg)
    if not tts.is_multi_speaker:
        print(colored("Model is not multispeaker", "red"))
        exit(1)

    speakers = list_speakers_util(tts)
    print(colored("TTS speakers:", "blue"), speakers)

    text = DEFAULT_TEXT
    print(colored("Sample sentence:", "blue"), f"'{text}'")

    out_dir = "out_speaker_samples"
    print(colored("Will write to:", "blue"), f"'{out_dir}'")
    os.makedirs(out_dir, exist_ok=True)

    for speaker in tqdm(speakers):
        # print(speaker)
        out_file = os.path.join(out_dir, f"out_{speaker}.wav")

        if os.path.exists(out_file):
            # print(f"SKIP: {speaker}")
            continue

        cfg.tts.speaker = speaker
        is_cloning, tts_kwargs = get_tts_options(cfg, tts)
        tts_kwargs["text"] = text
        tts_kwargs["file_path"] = out_file

        if is_cloning:
            tts.tts_with_vc_to_file(speaker_wav=voice, **tts_kwargs)  # type: ignore
        else:
            tts.tts_to_file(**tts_kwargs)


@click.command()
@click.option("--config", "-c", help="Config file")
@click.option("--input", "-t", help="Text to say")
@click.option(
    "--voice", "-v", type=click.Path(exists=True), help="Cloned voice, overrides config"
)
def speak(config: str, input: str, voice: Optional[str]):
    """Speak the text and write the result into the file. Can also voice-clone."""

    cfg = load_app_config(config)
    cfg.tts.streaming_enabled = False
    if voice != None:
        cfg.tts.sample_of_cloned_voice_wav = voice
    print(colored("Config", "blue"), cfg)

    text = input if input != None else DEFAULT_TEXT
    print(colored("Text to say:", "blue"), f"'{text}'")

    tts = create_tts(cfg)

    out_file_path = "out_speak_result.wav"
    print(colored("Will write result to:", "blue"), out_file_path)

    exec_tts_to_file(cfg, tts, text, out_file_path, verbose=True)

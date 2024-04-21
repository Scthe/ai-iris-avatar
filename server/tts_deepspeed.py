from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from TTS.utils.synthesizer import Synthesizer
from termcolor import colored

from server.config import AppConfig

"""
TODO
- voice cloning with cached latents?
    - make sure it works with xtts_scripts
- https://docs.coqui.ai/en/latest/models/xtts.html#streaming-manually
"""


class FakeTTSWithDeepspeed:
    def __init__(self, tts_config: XttsConfig, model: Xtts):
        self.model = model
        self.is_multi_speaker = True
        self.is_multi_lingual = True
        self.gpt_cond_latent = None
        self.speaker_embedding = None

        self.synthesizer = Synthesizer(use_cuda=True)  # TODO use
        self.synthesizer.tts_config = tts_config
        self.synthesizer.tts_model = model
        self.synthesizer.output_sample_rate = tts_config.audio["output_sample_rate"]

    def _get_speaker_embedding_and_latents(self, speaker_name: str):
        if not self.gpt_cond_latent:
            speaker = self.model.speaker_manager.speakers.get(speaker_name)
            gpt_cond_latent = speaker.get("gpt_cond_latent")
            speaker_embedding = speaker.get("speaker_embedding")
            self.gpt_cond_latent = gpt_cond_latent.to(self.model.device)
            self.speaker_embedding = speaker_embedding.to(self.model.device)
        return self.speaker_embedding, self.gpt_cond_latent

    def tts(self, text: str, **kwargs):
        language = kwargs.get("language", "")
        speaker = kwargs.get("speaker", "")
        wav = self.synthesizer.tts(
            text=text,
            speaker_name=speaker,
            language_name=language,
            # speaker_wav=speaker_wav,
            reference_wav=None,
            style_wav=None,
            style_text=None,
            reference_speaker_name=None,
            # split_sentences=split_sentences,
            # **kwargs,
        )
        return wav

    def tts_to_file(self, text: str, file_path: str, **kwargs):
        wav = self.tts(
            text=text,
            **kwargs,
        )
        self.synthesizer.save_wav(wav=wav, path=file_path, pipe_out=None)
        return file_path

    def tts_v0(self, text: str, **kwargs):
        language = kwargs.get("language")
        speaker = kwargs.get("speaker")

        speaker_embedding, gpt_cond_latent = self._get_speaker_embedding_and_latents(
            speaker
        )

        # speaker_id = self.model.speaker_manager.name_to_id[speaker]
        # gpt_cond_latent, speaker_embedding = self.model.speaker_manager.speakers[
        # speaker_id
        # ].values()
        outputs = self.model.inference(
            text=text,
            language=language,
            gpt_cond_latent=self.gpt_cond_latent,
            speaker_embedding=self.speaker_embedding,
        )
        # TODO .venv\Lib\site-packages\TTS\tts\utils\synthesis.py?
        # print(colored("result", "blue"), outputs.keys())
        waveform = outputs["wav"]
        # waveform = waveform.cpu()
        # exit(0)
        # return out
        return [waveform]

    def tts_to_file_v0(self, text: str, file_path: str, **kwargs):
        import numpy as np
        import torch
        import torchaudio
        from TTS.utils.audio.numpy_transforms import save_wav

        wav = self.tts(text, **kwargs)
        torchaudio.save(file_path, torch.tensor(wav[0]).unsqueeze(0), 24000)

    def tts_with_vc(self, text: str, **kwargs):
        raise Exception("Not available with deepspeed: tts_with_vc()")

    def tts_with_vc_to_file(self, text: str, **kwargs):
        raise Exception("Not available with deepspeed: tts_with_vc_to_file()")


def check_deepspeed():
    deepspeed_available = False
    try:
        import deepspeed

        deepspeed_available = True
    except ImportError:
        pass
    return deepspeed_available


def can_load_xtts2_with_deepspeed(cfg: AppConfig):
    is_ds = check_deepspeed()
    is_xtts2 = "xtts_v2" in cfg.tts.model_name
    is_cfg = cfg.tts.deepspeed_enabled
    result = is_ds and is_xtts2 and is_cfg
    reason = f"has_library={is_ds}, is_xtts2={is_xtts2}, cfg_allows={is_cfg}"
    print(colored("Deepspeed:", "blue"), "ON" if result else "OFF", f"({reason})")
    return result


def xtts_with_deepspeed(cfg: AppConfig):
    tts = TTS(progress_bar=True)
    xtts_model_dir, config_path, model_item = tts.manager.download_model(
        cfg.tts.model_name
    )
    # print(f"model_path={xtts_model_dir}")
    # print(f"config_path={config_path}")
    # print(f"model_item={model_item}")

    config = XttsConfig()
    config.load_json(f"{xtts_model_dir}/config.json")  # "/path/to/xtts/config.json"
    model = Xtts.init_from_config(config)
    model.load_checkpoint(
        config,
        checkpoint_dir=xtts_model_dir,
        use_deepspeed=True,
    )
    # model.to(device)
    model.cuda()

    # print("---")
    # print(colored("dir", "blue"), dir(model.speaker_manager))
    # print(colored("num_speakers", "blue"), model.speaker_manager.num_speakers)
    # print(colored("name_to_id", "blue"), model.speaker_manager.name_to_id)
    # speaker = model.speaker_manager.speakers.get("Rosemary Okafor")
    # print(colored("speakers", "blue"), dir(speaker))
    # print(colored("speakers", "blue"), speaker.keys())
    # exit(0)

    return FakeTTSWithDeepspeed(config, model)

from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from TTS.utils.synthesizer import Synthesizer
from termcolor import colored

from server.config import AppConfig


class FakeTTSWithRawXTTS2:
    def __init__(
        self,
        app_config: AppConfig,
        tts_config: XttsConfig,
        model: Xtts,
        use_streaming=False,
    ):
        print(colored(f"--- Using custom TTS class {type(self).__name__}--", "blue"))
        self.app_config = app_config
        self.streaming_enabled = use_streaming
        self.model = model  # this model already has deepspeed flag
        self.is_multi_speaker = True
        self.is_multi_lingual = True
        self.gpt_cond_latent = None
        self.speaker_embedding = None

        self.synthesizer = Synthesizer(use_cuda=True)
        self.synthesizer.tts_config = tts_config
        self.synthesizer.tts_model = model
        self.synthesizer.output_sample_rate = tts_config.audio["output_sample_rate"]

        cloned_voice_wav = app_config.tts.sample_of_cloned_voice_wav
        if cloned_voice_wav != None:
            if self.streaming_enabled:
                print(
                    colored("Streaming with voice cloning:", "blue"),
                    f"'{cloned_voice_wav}'",
                )
            gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
                audio_path=[cloned_voice_wav]
            )
            self.gpt_cond_latent = gpt_cond_latent.to(self.model.device)
            self.speaker_embedding = speaker_embedding.to(self.model.device)

    def _get_speaker_embedding_and_latents(self, speaker_name: str):
        """Used only for streaming mode"""
        if self.gpt_cond_latent == None:
            speaker = self.model.speaker_manager.speakers.get(speaker_name)
            gpt_cond_latent = speaker.get("gpt_cond_latent")
            speaker_embedding = speaker.get("speaker_embedding")
            self.gpt_cond_latent = gpt_cond_latent.to(self.model.device)
            self.speaker_embedding = speaker_embedding.to(self.model.device)
        return self.speaker_embedding, self.gpt_cond_latent

    def tts(self, text: str, **kwargs):
        if self.streaming_enabled:
            return self.tts_streamed(text, **kwargs)
        else:
            return self._tts_internal(text, **kwargs)

    def tts_to_file(self, text: str, file_path: str, **kwargs):
        wav = self._tts_internal(
            text=text,
            **kwargs,
        )
        self.synthesizer.save_wav(wav=wav, path=file_path, pipe_out=None)
        # torchaudio.save(file_path, torch.tensor(wav[0]).unsqueeze(0), 24000) # alternative
        return file_path

    def _tts_internal(self, text: str, **kwargs):
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

    def tts_streamed(self, text: str, **kwargs):
        language = kwargs.get("language")
        speaker: str = kwargs.get("speaker")  # type: ignore

        speaker_embedding, gpt_cond_latent = self._get_speaker_embedding_and_latents(
            speaker
        )

        outputs = self.model.inference_stream(
            text=text,
            language=language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            enable_text_splitting=False,  # assumed you've already did it
            stream_chunk_size=self.app_config.tts.streaming_chunk_size,
            overlap_wav_len=self.app_config.tts.streaming_overlap_wav_len,
        )
        for i, chunk in enumerate(outputs):
            # print(colored(f"raw_chunk_{i}", "yellow"), chunk)
            yield chunk

    def tts_with_vc(self, text: str, **kwargs):
        # assumes latents are already set in constructor
        return self.tts(text, **kwargs)

    def tts_with_vc_to_file(self, text: str, **kwargs):
        # assumes latents are already set in constructor
        return self.tts_to_file(text, **kwargs)


def check_deepspeed():
    deepspeed_available = False
    try:
        import deepspeed

        deepspeed_available = True
    except ImportError:
        pass
    return deepspeed_available


def create_wrapped_xtts(
    app_config: AppConfig, use_deepspeed=False, use_streaming=False
):
    tts = TTS(progress_bar=True)
    xtts_model_dir, config_path, model_item = tts.manager.download_model(
        app_config.tts.model_name
    )
    # print(f"model_path={xtts_model_dir}")
    # print(f"config_path={config_path}")
    # print(f"model_item={model_item}")

    model_config = XttsConfig()
    model_config.load_json(
        f"{xtts_model_dir}/config.json"
    )  # "/path/to/xtts/config.json"
    model = Xtts.init_from_config(model_config)
    model.load_checkpoint(
        model_config,
        checkpoint_dir=xtts_model_dir,
        use_deepspeed=use_deepspeed,
    )
    # model.to(device)
    model.cuda()  # let's be honest. You will use deepspeed/streaming with CUDA..

    # print("---")
    # print(colored("dir", "blue"), dir(model.speaker_manager))
    # print(colored("num_speakers", "blue"), model.speaker_manager.num_speakers)
    # print(colored("name_to_id", "blue"), model.speaker_manager.name_to_id)
    # speaker = model.speaker_manager.speakers.get("Rosemary Okafor")
    # print(colored("speakers", "blue"), dir(speaker))
    # print(colored("speakers", "blue"), speaker.keys())
    # exit(0)

    return FakeTTSWithRawXTTS2(
        app_config, model_config, model, use_streaming=use_streaming
    )


def raw_xtts_model_required(cfg: AppConfig):
    """Use custom TTS class if needed, instead of the one from library"""
    is_ds = check_deepspeed()
    is_xtts2 = "xtts_v2" in cfg.tts.model_name
    is_cfg_ds = cfg.tts.deepspeed_enabled
    is_cfg_stream = cfg.tts.streaming_enabled

    reason_ds = f"is_xtts2={is_xtts2}, has_library={is_ds}, cfg_allows={is_cfg_ds}"
    reason_stream = f"is_xtts2={is_xtts2}, cfg_allows={is_cfg_stream}"

    requires_raw_xtts = is_ds and is_xtts2 and (is_cfg_ds or is_cfg_stream)
    if requires_raw_xtts:
        flag_str = lambda x: "ON" if x else "OFF"
        print(colored("Deepspeed:", "blue"), flag_str(is_cfg_ds), f"({reason_ds})")
        print(
            colored("Streaming:", "blue"), flag_str(is_cfg_stream), f"({reason_stream})"
        )
        return create_wrapped_xtts(cfg, is_cfg_ds, is_cfg_stream)

    print(colored("Deepspeed:", "blue"), "OFF", f"({reason_ds})")
    print(colored("Streaming:", "blue"), "OFF", f"({reason_stream})")
    return None

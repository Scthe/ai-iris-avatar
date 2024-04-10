from typing import Optional
from yaml import load, Loader
from pydantic import BaseModel, PositiveInt, NonNegativeInt, PositiveFloat, StrictBool
from termcolor import colored


class LlmCfg(BaseModel):
    mocked_response: Optional[str] = None
    model: str = "gemma:2b"
    temperature: PositiveFloat = 0.7
    top_k: PositiveInt = 40
    top_p: PositiveFloat = 0.9
    api: str = "http://localhost:11434"


class TtsCfg(BaseModel):
    # pydantic 'forbidds' using 'model_' prefix. But it's only a warning,
    # if there is no actual collision.
    model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"
    # vocoder_name: str = "vocoder_models/en/ljspeech/hifigan_v2"
    use_gpu: StrictBool = True
    chunk_size: NonNegativeInt = 0
    speaker: Optional[str] = None
    language: Optional[str] = None
    sample_of_cloned_voice_wav: Optional[str] = None


class ServerCfg(BaseModel):
    host: str = "localhost"
    port: PositiveInt = 8080


class AppConfig(BaseModel):
    """https://docs.pydantic.dev/latest/api/types/"""

    # verbose: StrictBool = False
    llm: LlmCfg = LlmCfg()
    tts: TtsCfg = TtsCfg()
    server: ServerCfg = ServerCfg()


def load_app_config(filepath="config.yaml") -> AppConfig:
    """https://github.com/Scthe/rag-chat-with-context/blob/master/src/config.py"""

    print(colored("Loading config file", "blue"), f"'{filepath}'")
    with open(filepath, "r") as f:
        yaml_content = load(f.read(), Loader=Loader)

    cfg = AppConfig(**yaml_content)
    return cfg

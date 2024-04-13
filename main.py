from inject_external_torch_into_path import inject_path
from xtts_scripts import create_speaker_samples, speak

inject_path()

from termcolor import colored
from ollama import AsyncClient
import click

from server.config import load_app_config
from server.tts_utils import create_tts

DEFAULT_TTS_TEXT = "The current algorithm only upscales the luma, the chroma is preserved as-is. This is a common trick known"


@click.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
def serve(config: str):
    """Start the server for TTS service"""
    # https://github.com/Scthe/rag-chat-with-context/blob/master/main.py#L175

    from server.server import create_server, start_server
    from server.socket_msg_handler import SocketMsgHandler
    from server.app_logic import AppLogic

    STATIC_DIR = "./server/static"

    cfg = load_app_config(config)
    print(colored("Config:", "blue"), cfg)

    llm = AsyncClient(cfg.llm.api)
    tts = create_tts(cfg)
    app_logic = AppLogic(cfg, llm, tts)

    # create server and set socket handlers
    create_ws_handler = lambda ws, is_unity: SocketMsgHandler(ws, app_logic, is_unity)
    app = create_server(STATIC_DIR, create_ws_handler, app_logic)

    # START!
    print(colored("Webui:", "green"), f"http://{cfg.server.host}:{cfg.server.port}/ui")
    start_server(app, host=cfg.server.host, port=cfg.server.port)

    print("=== DONE ===")


@click.group()
def main():
    """Available commands below"""


if __name__ == "__main__":
    main.add_command(serve)
    main.add_command(create_speaker_samples)
    main.add_command(speak)
    main()

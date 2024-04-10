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

    from server.server import create_server, set_socket_msg_handler, start_server
    from server.socket_msg_handler import SocketMsgHandler
    from server.app_logic import AppLogic

    STATIC_DIR = "./server/static"
    DEFAULT_CONFIG_FILE = "config.yaml"

    cfg_file = config if config else DEFAULT_CONFIG_FILE
    cfg = load_app_config(cfg_file)
    print(colored("Config:", "blue"), cfg)

    llm = AsyncClient(cfg.llm.api)
    tts = create_tts(cfg)
    msg_handler = AppLogic(cfg, llm, tts)

    # create server and set socket handlers
    app = create_server(STATIC_DIR)
    create_ws_handler = lambda ws, is_unity: SocketMsgHandler(ws, msg_handler, is_unity)
    set_socket_msg_handler(app, create_ws_handler)

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

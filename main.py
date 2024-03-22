from server.inject_external_torch_into_path import inject_path

inject_path()

from termcolor import colored
import argparse
from TTS.api import TTS

from server.server import create_server, set_socket_msg_handler, start_server
from server.socket_msg_handler import SocketMsgHandler
from server.config import load_app_config
from server.tts_utils import get_torch_device

STATIC_DIR = "./server/static"
DEFAULT_CONFIG_FILE = "config.yaml"

if __name__ == "__main__":
    # https://github.com/Scthe/rag-chat-with-context/blob/master/main.py#L175

    parser = argparse.ArgumentParser(
        description=f"LLM chat with voice-over",
    )
    parser.add_argument("--config", "-c", help="Config file")
    args = parser.parse_args()

    cfg_file = args.config if args.config else DEFAULT_CONFIG_FILE
    cfg = load_app_config(cfg_file)
    print(colored("Config:", "blue"), cfg)

    app = create_server(STATIC_DIR)

    tts = TTS(model_name=cfg.tts.model_name, gpu=cfg.tts.use_gpu)
    print(colored("TTS device:", "blue"), get_torch_device(tts))

    handler = lambda ws: SocketMsgHandler(cfg, tts, ws)
    set_socket_msg_handler(app, handler)

    print(colored("Webui:", "green"), f"http://{cfg.server.host}:{cfg.server.port}/ui")
    start_server(app, host=cfg.server.host, port=cfg.server.port)

    print("=== DONE ===")

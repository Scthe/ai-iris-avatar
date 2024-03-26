from inject_external_torch_into_path import inject_path
from server.utils import Timer

inject_path()

from termcolor import colored
import click


# TODO help texts


@click.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
def serve(config: str):
    """Start the server for TTS service"""
    # https://github.com/Scthe/rag-chat-with-context/blob/master/main.py#L175

    from TTS.api import TTS

    from server.server import create_server, set_socket_msg_handler, start_server
    from server.socket_msg_handler import SocketMsgHandler
    from server.config import load_app_config
    from server.tts_utils import get_torch_device

    STATIC_DIR = "./server/static"
    DEFAULT_CONFIG_FILE = "config.yaml"

    cfg_file = config if config else DEFAULT_CONFIG_FILE
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


@click.command()
@click.option("--count", "-c", default=1, type=int, help="How many samples to generate")
@click.option("--gen-64", "-64", is_flag=True, help="Size of sample: 64x64px")
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    help="Directory that contains images to crop. Exatly one of the images should contain '.unity.' in name. This is the original image from unity. Rest of the images are ones from stable-diffusion.",
)
def st_generate_samples(count, gen_64, input):
    """Style transfer: generate samples for cnn training."""
    from style_transfer_cnn.gen_samples import generate_samples
    from os.path import join

    OUTPUT_DIR = join("style_transfer_cnn", "samples_gen")

    sample_size = 64 if gen_64 else 32
    if count <= 0:
        raise Exception(f"Count has to be > 0. Received: {count}")

    generate_samples(input, OUTPUT_DIR, count, sample_size)

    print("--- DONE ---")


@click.command()
@click.option("--epochs", "-e", default=50, type=int, help="How long to train")
@click.option("--new-model", "-n", is_flag=True, help="Start training from scratch")
@click.option("--cpu", is_flag=True, help="Force to use CPU")
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    help="Directory with training samples",
)
@click.option(
    "--test-image",
    "-ti",
    type=click.Path(exists=True),
    help="Infer this image on every checkpoint",
)
def st_train(epochs, new_model, cpu, input, test_image):
    """Style transfer: Train the cnn."""
    from style_transfer_cnn.style_transfer import exec_train
    from os.path import join

    MODELS_DIR = join("style_transfer_cnn", "models")
    BATCH_SIZE = 20
    # LEARNING_RATE = 0.0000001
    LEARNING_RATE = 0.00001
    cp_step = 100
    checkpoint_schedule = [x for x in range(0, epochs, cp_step) if x > 0 and x < epochs]

    with Timer() as timer:
        exec_train(
            models_dir=MODELS_DIR,
            samples_dir=input,
            new_model=new_model,
            use_cpu=cpu,
            epochs=epochs,
            batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            test_image=test_image,
            checkpoint_schedule=checkpoint_schedule,
        )

    print(colored(f"Elapsed {timer.delta :4.2f}s", "green"))
    print("--- DONE ---")


""" TODO model?
@click.option(
    "--model",
    "-m",
    default=None,
    type=click.Path(exists=True),
    help="Model",
)
"""


@click.command()
@click.option("--cpu", is_flag=True, help="Force to use CPU")
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    help="Image to upscale",
)
def st_test(cpu, input):
    """Style transfer: Train the cnn."""
    from style_transfer_cnn.style_transfer import exec_infer
    from os.path import join

    MODELS_DIR = join("style_transfer_cnn", "models")
    OUTPUT_DIR = join("style_transfer_cnn", "images_test_results")

    exec_infer(
        models_dir=MODELS_DIR, use_cpu=cpu, img_path=input, output_dir=OUTPUT_DIR
    )

    print("--- DONE ---")


@click.group()
def main():
    """---"""


if __name__ == "__main__":
    main.add_command(serve)
    main.add_command(st_generate_samples)
    main.add_command(st_train)
    main.add_command(st_test)
    main()

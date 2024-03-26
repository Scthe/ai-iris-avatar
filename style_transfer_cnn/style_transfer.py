from os.path import join, splitext, basename
from typing import List, Optional
from termcolor import colored

from .model_storage import ModelStorage
from .training_reporter import TrainingReporter
from .cnn import pick_device, load_model, train, style_transfer, save_image


def generate_date_for_filename():
    from datetime import datetime

    now = datetime.now()
    return now.strftime("%Y-%m-%d--%H-%M-%S")


def exec_train(
    models_dir: str,
    samples_dir: str,
    new_model: bool,
    use_cpu: bool,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    test_image: Optional[str],
    checkpoint_schedule: List[int],
):
    [device, device_name] = pick_device(use_cpu)
    print(colored("Using device:", "blue"), f"'{device_name}'({device})")

    datestamp = generate_date_for_filename()
    model_storage = ModelStorage(models_dir, datestamp)
    print(colored("Output directory:", "blue"), model_storage.store_dir)
    model_path = model_storage.find_model_file(new_model)
    model = load_model(device, model_path)
    print(colored("Model:", "blue"), model)

    training_reporter = TrainingReporter(
        model, epochs, test_image, checkpoint_schedule, model_storage
    )
    print(colored("Checkpoint schedule:", "blue"), checkpoint_schedule)

    train(
        device, model, samples_dir, epochs, batch_size, learning_rate, training_reporter
    )
    print(colored("Training finshed", "green"))

    # save model params
    training_reporter.store_checkpoint(epochs, is_final=True)


def exec_infer(
    models_dir: str,
    use_cpu: bool,
    img_path: str,
    output_dir: str,
):
    [device, device_name] = pick_device(use_cpu)
    print(colored("Using device:", "blue"), f"'{device_name}'({device})")

    model_storage = ModelStorage(models_dir)
    model_path = model_storage.find_model_file()
    if model_path == None:
        raise Exception(f"No checkpoint model found in: '{models_dir}'")
    model = load_model(device, model_path)
    print(colored("Model:", "blue"), model)

    result = style_transfer(device, model, img_path)
    print(colored("Style transfer finshed", "green"))

    # save result
    base = basename(img_path)
    filename = splitext(base)[0]
    out_date = generate_date_for_filename()
    out_filename = join(output_dir, f"{filename}.{out_date}.png")
    print(colored("Saving result to:", "blue"), f"'{out_filename}'")
    save_image(result, out_filename)

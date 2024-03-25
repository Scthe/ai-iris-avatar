from os import listdir
from os.path import join, isfile, splitext, getmtime, basename

from termcolor import colored

from .cnn import pick_device, load_model, train, save_model, style_transfer, save_image

MODEL_EXT = ".pt"


def find_model_file(models_dir, force_new=False):
    if force_new:
        return None

    def is_model_file(f):
        fullpath = join(models_dir, f)
        # print(fullpath, isfile(fullpath), splitext(f)[1])
        return isfile(fullpath) and splitext(f)[1] == MODEL_EXT

    models = [join(models_dir, f) for f in listdir(models_dir) if is_model_file(f)]
    # print(models)
    if not models:
        print("No previous model found")
        return None

    models.sort(key=lambda x: getmtime(x))
    return models[-1]


def generate_date_for_filename():
    from datetime import datetime

    now = datetime.now()
    return now.strftime("%Y-%m-%d--%H-%M-%S")


def args_require(args, key):
    value = vars(args)[key]
    if value is None:
        raise Exception(f"Missing program arg: '{key}'")
    return value


def exec_train(
    models_dir: str,
    samples_dir: str,
    new_model: bool,
    use_cpu: bool,
    epochs: int,
    batch_size: int,
    learning_rate: float,
):
    [device, device_name] = pick_device(use_cpu)
    print(colored("Using device:", "blue"), f"'{device_name}'({device})")

    model_path = find_model_file(models_dir, new_model)
    model = load_model(model_path)
    model = model.to(device)
    print(colored("Model:", "blue"), model)

    train(device, model, samples_dir, epochs, batch_size, learning_rate)
    print(colored("Training finshed", "green"))

    # save model params
    out_date = generate_date_for_filename()
    out_filename = join(models_dir, f"st_model.{out_date}.pt")
    print(colored("Saving model parameters to:", "blue"), f"'{out_filename}'")
    save_model(model, out_filename)


def exec_infer(
    models_dir: str,
    use_cpu: bool,
    img_path: str,
    output_dir: str,
):
    [device, device_name] = pick_device(use_cpu)
    print(colored("Using device:", "blue"), f"'{device_name}'({device})")

    model_path = find_model_file(models_dir)
    model = load_model(model_path)
    model = model.to(device)
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

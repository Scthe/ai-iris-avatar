from random import choice
import os
from os.path import join, splitext

from termcolor import colored
from torchvision.utils import save_image as torch_save_image
from torchvision.io import read_image

"""
- https://github.com/Scthe/SRCNN-PyTorch/blob/master/gen_samples.py
- https://pytorch.org/vision/stable/transforms.html#v2-api-reference-recommended
"""


def list_input_images(dir_):
    image_paths = [join(dir_, f) for f in os.listdir(dir_)]
    result = []
    allowed_ext = [".jpg", ".jpeg", ".png"]
    for img_path in image_paths:
        ext = splitext(img_path)[1]
        if ext not in allowed_ext:
            if not img_path.endswith(".gitkeep"):
                print(
                    colored(f"Non image file found:", "yellow"),
                    f"'{img_path}'. It will be ignored.",
                )
        else:
            result.append(img_path)
    return result


def prepare_images(image_paths):
    UNITY_PATTERN = ".unity."
    is_org_unity_img = lambda x: UNITY_PATTERN in x
    samples = [x for x in image_paths if not is_org_unity_img(x)]
    org_unity_image = [x for x in image_paths if is_org_unity_img(x)]

    if len(org_unity_image) != 1:
        raise Exception(
            f"Expected 1 image containing '{UNITY_PATTERN}', found {len(org_unity_image)}"
        )
    org_unity_image = org_unity_image[0]
    print(colored("Input unity image:", "blue"), f"'{org_unity_image}'")
    print(
        colored("Will generate samples from the rest of the images", "blue"),
        f"({len(samples)} images).",
    )

    samples = [read_image(x) for x in samples]
    org_unity_image = read_image(org_unity_image)
    return org_unity_image, samples


def random_string(size):
    import random
    import string

    return "".join(random.choices(string.ascii_lowercase + string.digits, k=size))


def random_crop_images(img_unity, img_sd, sample_size):
    import torch
    import random
    from torchvision.transforms import v2
    from torchvision.transforms.functional import crop

    w, h = img_unity.shape[1], img_unity.shape[2]
    x = random.randint(0, w - sample_size)
    y = random.randint(0, h - sample_size)

    # https://pytorch.org/vision/0.9/transforms.html#torchvision.transforms.functional.crop
    def exec_crop(img):
        cropped = crop(img, top=y, left=x, width=sample_size, height=sample_size)
        transforms = v2.Compose([v2.ToDtype(torch.float32, scale=True)])
        return transforms(cropped)

    result_unity = exec_crop(img_unity)
    result_sd = exec_crop(img_sd)
    return result_unity, result_sd


def generate_samples(input_dir: str, output_dir: str, count: int, sample_size: int):
    print(
        colored(f"Will generate {count} samples from images in:", "blue"),
        f"'{input_dir}'",
    )

    image_paths = list_input_images(input_dir)
    if len(image_paths) == 0:
        raise Exception(f"Found no images in '{input_dir}'")
    print(
        colored("Found input images:", "blue"),
        f"{len(image_paths)} images",
    )

    org_unity_image, styled_images = prepare_images(image_paths)

    output_dir = f"{output_dir}_{sample_size}"
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    print(
        colored(f"Will store result in: ", "blue"),
        f"'{output_dir}'",
    )

    for _ in range(count):
        input_img = choice(styled_images)
        img_unity, img_styled = random_crop_images(
            org_unity_image, input_img, sample_size
        )
        file_name = random_string(8)
        out_filename_styled = join(output_dir, f"{file_name}.styled.png")
        out_filename_unity = join(output_dir, f"{file_name}.unity.png")
        torch_save_image(img_styled, out_filename_styled)
        torch_save_image(img_unity, out_filename_unity)

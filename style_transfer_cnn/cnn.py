import os
from typing import List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision.utils import save_image as torch_save_image
from torchvision.io import read_image, ImageReadMode
from termcolor import colored

from .loss_fn import VGGPerceptualLoss

# https://pytorch.org/tutorials/beginner/blitz/neural_networks_tutorial.html
# https://www.kdnuggets.com/building-a-convolutional-neural-network-with-pytorch
# https://pyimagesearch.com/2021/07/19/pytorch-training-your-first-convolutional-neural-network-cnn/


def pick_device(force_cpu=False):
    device = "cpu"
    name = "CPU"
    if torch.cuda.is_available() and not force_cpu:
        print("CUDA devices:")
        for dev_id in range(torch.cuda.device_count()):
            print(f"\t[{dev_id}]", torch.cuda.get_device_name(dev_id))
        dev_id = 0
        torch.cuda.device(dev_id)
        # print(f"Using device [{dev_id}]", torch.cuda.get_device_name())
        device = f"cuda:{dev_id}"
        name = torch.cuda.get_device_name()
    return [device, name]


conv_layer = lambda kernel_size, outputs=0: (kernel_size, outputs)
ConvLayerDef = Tuple[int, int]


class Net(nn.Module):
    def __init__(self, conv_def: List[ConvLayerDef]):
        super(Net, self).__init__()

        conv_kwargs = {
            "stride": 1,
            "padding": "same",
            "padding_mode": "reflect",
            "bias": True,
        }
        # TODO add massive dropout layer
        # TODO weight decay
        # TODO perceptual loss fn?
        prev_layer_outputs = 3

        def create_conv(conv_def: ConvLayerDef):
            nonlocal prev_layer_outputs
            kernel_size, outputs = conv_def
            l = nn.Conv2d(prev_layer_outputs, outputs, kernel_size, **conv_kwargs)
            prev_layer_outputs = outputs
            return l

        self.conv1 = create_conv(conv_def[0])
        self.conv2 = create_conv(conv_def[1])
        self.conv3 = create_conv(conv_def[2])
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = self.conv3(x)

        # lin:
        # x = F.relu(self.conv3(x))
        # x = torch.reshape(x, (-1, 3))  # TODO hardcoded img size 64x64
        # x = self.lin1(x)
        # x = torch.reshape(x, (-1,64,64, 3))  # TODO hardcoded img size 64x64
        return x


def load_model(device, filepath: Optional[str]):
    if filepath is None:
        print(colored("Creating new model", "blue"))
        # model = Net(8, 3, 8, 3, 3)  # Net(64, 9, 32, 1, 5)
        # model = Net(64, 9, 32, 1, 5)  # org. SRCNN
        model = Net(
            [
                conv_layer(kernel_size=9, outputs=64),
                conv_layer(kernel_size=1, outputs=32),
                conv_layer(kernel_size=5, outputs=3),
            ]
        )
    elif os.path.isfile(filepath):
        print(colored("Loading model from:", "blue"), f"'{filepath}'")
        model = torch.load(filepath)
    else:
        raise Exception(f"Model file not found: '{filepath}'")
    model = model.to(device)
    return model


def save_model(model, filepath: Optional[str]):
    torch.save(model, filepath)


def prepare_image(device, img):
    from torchvision.transforms import v2

    if isinstance(img, str):
        img = read_image(img, mode=ImageReadMode.RGB)
    transforms = v2.Compose([v2.ToDtype(torch.float32, scale=True)])
    # print(image_path)
    img = transforms(img)
    img = img.to(device)
    return img


####################################
# TRAINING


class SrcnnDataset(Dataset):
    def __init__(self, device, image_paths: List[str]):
        self.device = device
        self.image_paths = image_paths

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx: int):
        x_path, y_path = self.image_paths[idx]
        x_image = prepare_image(self.device, x_path)
        y_image = prepare_image(self.device, y_path)
        return x_image, y_image


def list_samples(samples_dir: str):
    from os import listdir
    from os.path import isfile, join, splitext
    import re

    def is_valid_sample_file(f):
        ext = splitext(f)[1]
        f = join(samples_dir, f)
        return isfile(f) and ext == ".png"

    sample_files = [f for f in listdir(samples_dir) if is_valid_sample_file(f)]
    # print(sample_files)
    samples = {}
    for sample_file in sample_files:
        # parse name for `id` and `size`
        x = re.search(r"([a-z0-9]+?)\.(unity|styled)\.png", sample_file)
        if x is None:
            raise Exception(f"Invalid sample file name: '{sample_file}'")
        [id, img_type] = x.groups()  # img_type is either 'unity' or 'styled'
        # print(f"'{sample_file}' id='{id}' size='{size}'")

        image_path = join(samples_dir, sample_file)
        item = samples.get(id, [None, None])
        if img_type == "unity":
            item[0] = image_path
        else:
            item[1] = image_path
        samples[id] = item
    allSamples = list(samples.values())
    result = []
    for x, y in allSamples:
        if x is None or y is None:
            print(f"Invalid image pair: ('{x}','{y}')")
        else:
            result.append([x, y])
    return result


def create_data_loader(device, img_paths: List[str], batch_size: int, is_train=False):
    ds = SrcnnDataset(device, img_paths)
    params = {
        "batch_size": batch_size,
        "shuffle": is_train,
        # 'drop_last': is_train,
        # 'num_workers': 0
    }
    return DataLoader(ds, **params)


def lr_mod_from_batch_size(batch_size: int):
    """
    # Explanation:

    * If `batch_size==1`, then you update weights once per image. So if you process 10 images,
        it will trigger 10 changes.
    * If `batch_size==10`, then you update weights once per 10 images. So if you process 10 images,
        it will trigger 1 change. It would learn much slower than `batch_size==1`.

    # Solution

    Increase learning rate based on the `batch_size`. Usually it's linear or sqrt.

    @see https://stackoverflow.com/questions/53033556/how-should-the-learning-rate-change-as-the-batch-size-change
    """
    return batch_size


def train(
    device,
    model: Net,
    samples_dir: str,
    n_epochs: int,
    batch_size: int,
    learning_rate: float,
    training_reporter,
):
    model.train()  # train mode

    if n_epochs <= 0:
        raise Exception(f"Invalid epoch count: {n_epochs}")

    print(colored(f"Reading samples from:", "blue"), f"'{samples_dir}'")
    all_sample_paths = list_samples(samples_dir)
    if len(all_sample_paths) == 0:
        raise Exception(f"No training data found in: '{samples_dir}'")
    print(colored(f"Found {len(all_sample_paths)} samples", "blue"))

    n1 = int(0.9 * len(all_sample_paths))
    train_image_paths = all_sample_paths[:n1]
    train_loader = create_data_loader(
        device, train_image_paths, batch_size, is_train=True
    )
    validation_image_paths = all_sample_paths[n1:]
    validation_loader = create_data_loader(device, validation_image_paths, batch_size)
    print(colored(f"Train images:", "blue"), len(train_image_paths))
    print(colored(f"Validation images:", "blue"), len(validation_image_paths))

    # loss_fn = nn.MSELoss()
    loss_fn = VGGPerceptualLoss(device)
    optimizer = optim.SGD(
        model.parameters(),
        lr=learning_rate * lr_mod_from_batch_size(batch_size),
    )
    print(
        colored(f"Starting training", "blue"),
        f"(epochs: {n_epochs}, batch_size: {batch_size}, learning_rate: {learning_rate})",
    )

    for epoch in range(n_epochs):
        training_reporter.start_epoch()

        # train
        for in_image, expected in train_loader:
            # Forward pass
            output = model(in_image)
            loss = loss_fn(output, expected)

            # Backward pass and optimize
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

        # evaluate
        loss_acc = 0
        with torch.no_grad():
            for in_image, expected in validation_loader:
                output = model(in_image)
                loss = loss_fn(output, expected)
                # print(in_image.shape, output.shape, loss, loss.item())
                loss_acc += loss.item()

        loss_avg = loss_acc / len(validation_image_paths)
        training_reporter.report_epoch(epoch, loss_avg)


####################################
# STYLE TRANSFER INFER


def save_image(image, filepath: str):
    torch_save_image(image, filepath)


def style_transfer(device, model: Net, input_image_path: str):
    print(colored("Style transfer image:", "blue"), f"'{input_image_path}'")
    my_image = prepare_image(device, input_image_path)
    # print(colored("Size:", "blue"), my_image.shape)

    model.eval()  # inference mode
    with torch.no_grad():
        result = model(my_image)
    model.train()  # train mode
    return result

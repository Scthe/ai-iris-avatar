from os import listdir, makedirs
from os.path import join, isfile, isdir, splitext, getmtime
from typing import Optional
from termcolor import colored

from .cnn import save_model

MODEL_EXT = ".pt"


def is_model_file(fullpath: str):
    return isfile(fullpath) and splitext(fullpath)[1] == MODEL_EXT


def list_files(dir: str, filter):
    all_files = [join(dir, f) for f in listdir(dir)]
    return [x for x in all_files if filter(x)]


def list_models_from_dir(dir: str):
    dirs = list_files(dir, isdir)
    dirs.append(dir)

    model_files = [list_files(dir, is_model_file) for dir in dirs]
    model_files = sum(model_files, [])  # flatten
    return model_files


class ModelStorage:
    def __init__(self, models_dir: str, store_subdir: Optional[str] = None):
        self.models_dir = models_dir
        self.store_dir = (
            models_dir if store_subdir == None else join(models_dir, store_subdir)
        )

    def find_model_file(self, force_new=False):
        if force_new:
            return None

        models = list_models_from_dir(self.models_dir)
        # print(models)
        if not models:
            print("No previous model found")
            return None

        models.sort(key=lambda x: getmtime(x))
        return models[-1]

    def create_filepath(self, epoch: int, ext: str, is_final=False):
        final_suffix = ".final" if is_final else ""
        filename = f"st_model.{epoch}{final_suffix}{ext}"
        return join(self.store_dir, filename)

    def save_model(self, model, epoch: int, is_final=False):
        makedirs(self.store_dir, exist_ok=True)
        filepath = self.create_filepath(epoch, MODEL_EXT, is_final)
        print(colored("Saving model parameters to:", "blue"), f"'{filepath}'")
        save_model(model, filepath)

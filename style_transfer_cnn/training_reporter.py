from typing import List, Optional
import timeit
from termcolor import colored

from .model_storage import ModelStorage
from .cnn import style_transfer, save_image, Net


class TrainingReporter:
    def __init__(
        self,
        model: Net,
        n_epochs: int,
        test_image: Optional[str],
        checkpoint_schedule: List[int],
        model_storage: ModelStorage,
    ):
        self.model = model
        self.n_epochs = n_epochs
        self.losses = []
        self.test_image = test_image
        self.checkpoint_schedule = checkpoint_schedule
        self.model_storage = model_storage

    def start_epoch(self):
        self.start_time = timeit.default_timer()

    def report_epoch(self, epoch: int, loss: float):
        duration = timeit.default_timer() - self.start_time
        self.losses += [loss]
        max_loss = max(self.losses)

        iters_left = self.n_epochs - epoch - 1
        eta = "" if iters_left == 0 else f"ETA: {iters_left*duration:4.1f}s"
        progress = (epoch + 1) * 100 // self.n_epochs
        loss_percent = loss * 100 / max_loss
        print(
            colored(f"[{progress:3d}%] Epoch {epoch + 1:5d}:", "magenta"),
            f"Loss: {loss:2.7f} ({loss_percent:5.1f}%). Took {duration:4.2f}s. {eta}",
        )

        if epoch in self.checkpoint_schedule:
            self.store_checkpoint(epoch, is_final=False)

    def store_checkpoint(self, epoch: int, is_final: bool):
        # print(colored(f"Store checkpoint", "yellow"))
        self.model_storage.save_model(self.model, epoch, is_final)
        if self.test_image:
            device = next(self.model.parameters()).device
            result = style_transfer(device, self.model, self.test_image)
            out_filename = self.model_storage.create_filepath(epoch, ".png", is_final)
            save_image(result, out_filename)

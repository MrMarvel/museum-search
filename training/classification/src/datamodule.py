import pytorch_lightning as pl
import torch
import numpy as np
from pytorch_lightning.utilities.types import EVAL_DATALOADERS, TRAIN_DATALOADERS
from torch.utils.data import TensorDataset, DataLoader


class HeadDataModule(pl.LightningDataModule):
    def __init__(self, config) -> None:
        super().__init__()
        self.config = config
        self.num_classes = 15

    def setup(self, stage: str) -> None:
        self.train_ds = TensorDataset(
            torch.from_numpy(np.load(self.config.dataset.train.embeds)),
            torch.from_numpy(np.load(self.config.dataset.train.labels))
        )
        self.val_ds = TensorDataset(
            torch.from_numpy(np.load(self.config.dataset.val.embeds)),
            torch.from_numpy(np.load(self.config.dataset.val.labels))
        )
        self.test_ds = TensorDataset(
            torch.from_numpy(np.load(self.config.dataset.test.embeds)),
            torch.from_numpy(np.load(self.config.dataset.test.labels))
        )
        
    def train_dataloader(self) -> TRAIN_DATALOADERS:
        return DataLoader(
            self.train_ds,
            batch_size=self.config.model.batch_size,
            shuffle=True,
            num_workers=4,
        )
    def val_dataloader(self) -> EVAL_DATALOADERS:
        return DataLoader(
            self.val_ds,
            batch_size=self.config.model.batch_size,
            shuffle=False,
            num_workers=4,
        )
    def test_dataloader(self) -> EVAL_DATALOADERS:
        return DataLoader(
            self.test_ds,
            batch_size=self.config.model.batch_size,
            shuffle=False,
            num_workers=4,
        )
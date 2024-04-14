import pytorch_lightning as pl
import hydra
from utils import get_metric_value
from datamodule import HeadDataModule
from model import LightningMLP
from pytorch_lightning import seed_everything
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger


@hydra.main(version_base=None, config_path='../configs', config_name='config.yaml')
def train_pipeline(cfg):
    # fix seed
    seed_everything(42)
    # init logger
    tb_logger = TensorBoardLogger("tb_logs")
    # init datamodule
    dm = HeadDataModule(config=cfg)
    # init model
    model = LightningMLP(config=cfg, num_classes=dm.num_classes)
    
    checkpoint_callback = ModelCheckpoint(
        save_top_k=1,
        monitor="val_f1",
        mode="max",
        filename="vit_mlp-{epoch:02d}-{val_f1}",
    )
    checkpoint_callback2 = ModelCheckpoint(
        save_top_k=1,
        monitor="train_f1",
        mode="max",
        filename="vit_mlp-{epoch:02d}-{train_f1}",
    )

    # train
    trainer = pl.Trainer(
        callbacks=[
            # EarlyStopping(monitor="val_loss", mode="min"), 
            checkpoint_callback,
            checkpoint_callback2
        ],
        logger=tb_logger,
        accelerator='gpu',
        devices=[0],
        min_epochs=1,
        max_epochs=cfg.max_epochs,
        precision=16
    )
    trainer.fit(model, dm)
    train_metrics = trainer.callback_metrics
    metric_dict = {**train_metrics}

    metric_value = get_metric_value(
        metric_dict=metric_dict, metric_name=cfg.get("optimized_metric")
    )
    return metric_value

if __name__ == '__main__':
    train_pipeline()
import os
import pytorch_lightning as pl
import hydra
from pytorch_lightning.loggers import TensorBoardLogger
from datamodule import HeadDataModule
from model import LightningMLP
from pytorch_lightning import seed_everything


@hydra.main(version_base=None, config_path='../configs', config_name='config.yaml')
def test_vit_mlp_pipeline(cfg):
    # fix seed
    seed_everything(42)
    tb_logger = TensorBoardLogger(save_dir='tb_test')
    # init datamodule
    dm = HeadDataModule(config=cfg)
    # init model
    model = LightningMLP(config=cfg, num_classes=dm.num_classes)
    # train
    trainer = pl.Trainer(
        logger=tb_logger,
        accelerator='gpu',
        devices=[0],
        precision=16
    )
    trainer.test(model, datamodule=dm, ckpt_path='/home/free4ky/projects/museum_search/training/classification/tb_logs/lightning_logs/version_12/checkpoints/vit_mlp-epoch=99-val_f1=0.9042589068412781.ckpt')

if __name__ == '__main__':
    test_vit_mlp_pipeline()

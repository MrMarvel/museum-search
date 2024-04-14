from typing import Any
import torch

import matplotlib.pyplot as plt
import seaborn as sns
from torch import nn
from hydra.utils import instantiate
from torchmetrics import Accuracy, Precision, Recall, F1Score
from collections import defaultdict
from typing import *

class MLP(nn.Module):
    def __init__(self, input_size=1408):
        super().__init__()
        self.input_size=input_size
        self.layers = nn.Sequential(
            nn.Linear(self.input_size, 1024),
            nn.LeakyReLU(),
            nn.Dropout(0.2),
            nn.Linear(1024, 2048),
            nn.LeakyReLU(),
            nn.Dropout(0.2),
            nn.Linear(2048, 1024),
            nn.LeakyReLU(),
            nn.Dropout(0.2),
            nn.Linear(1024, 256),
            nn.LeakyReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.LeakyReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 15),
        )
    
    def forward(self, x):
        return self.layers(x)

class LightningMLP(pl.LightningModule):
    def __init__(self, config=None, num_classes=None):
        super().__init__()
        if config:
             self.config = config
        if num_classes:
            self.num_classes = num_classes
            self.make(config)
        self.model = MLP()

        self.accum = defaultdict(lambda: torch.tensor([]))
    
    def forward(self, x) -> Any:
        return self.model(x)
    
    def on_training_epoch_start(self, ):
        self.accum = defaultdict(lambda: torch.tensor([]))

    def make(self, config):
        self.loss_func = instantiate(config.loss)
        self.f1_scorer = F1Score(task='multiclass', num_classes=self.num_classes, average='macro')
        self.accuracy_scorer = Accuracy(task='multiclass',num_classes=self.num_classes, average='macro')
        self.precision_scorer = Precision(task='multiclass', num_classes=self.num_classes, average='macro')
        self.recall_scorer = Recall(task='multiclass', num_classes=self.num_classes, average='macro')

    def _common_step(self, batch, batch_idx, mode:str):
        x, y = batch # input, label, path
        logits = self.forward(x)
        loss = self.loss_func(logits, y)
        preds = logits.argmax(dim=-1)
        self.log(f"{mode}_loss", loss, prog_bar=True, on_step=False, on_epoch=True, logger=True, sync_dist=True)
        self.accum[f'{mode}_preds'] = torch.cat([self.accum[f'{mode}_preds'], preds.detach().cpu()])
        self.accum[f'{mode}_y'] = torch.cat([self.accum[f'{mode}_y'], y.detach().cpu()])
        return x, y, preds, logits, loss
    
    def _log_step(self, mode, accuracy, precision, recall, f1_score):
        self.log(f"{mode}_accuracy", accuracy, prog_bar=True, on_step=False, on_epoch=True, logger=True, sync_dist=True)
        self.log(f"{mode}_precision", precision, prog_bar=True, on_step=False, on_epoch=True, logger=True, sync_dist=True)
        self.log(f"{mode}_recall", recall, prog_bar=True, on_step=False, on_epoch=True, logger=True, sync_dist=True)
        self.log(f"{mode}_f1", f1_score, prog_bar=True, on_step=False, on_epoch=True, logger=True, sync_dist=True)
    
    def _calc_metric(self, mode):
        y, preds = self.accum[f'{mode}_y'], self.accum[f'{mode}_preds']
        
        self.accuracy_scorer = self.accuracy_scorer.to(preds.device)
        self.precision_scorer = self.precision_scorer.to(preds.device)
        self.recall_scorer = self.recall_scorer.to(preds.device)
        self.f1_scorer = self.f1_scorer.to(preds.device)
        
        accuracy = self.accuracy_scorer(preds, y)
        precision = self.precision_scorer(preds, y)
        recall = self.recall_scorer(preds, y)
        f1_score = self.f1_scorer(preds, y)

        self.accum[f'{mode}_y'] = torch.tensor([])
        self.accum[f'{mode}_preds'] = torch.tensor([])

        return accuracy, precision, recall, f1_score

    def training_step(self, batch, batch_idx):
        x, y, preds, logits, loss = self._common_step(batch, batch_idx, mode='train')
        lr = self.lr_schedulers().get_last_lr()[-1]
        self.log("lr", lr, prog_bar=True, on_step=False, on_epoch=True, logger=True, sync_dist=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y, preds, logits, loss = self._common_step(batch, batch_idx, mode='val')

    def test_step(self, batch, batch_idx):
        x, y  = batch # input, label, path
        logits = self.forward(x)
        probs = torch.nn.functional.softmax(logits, dim=-1)
        self.accum['test_preds'] = torch.cat([self.accum['test_preds'], probs.detach().cpu()])
        self.accum['test_y'] = torch.cat([self.accum['test_y'], y.detach().cpu()])

    def _make_line_plot(self, x:List[Any], y:List[Any], x_label:str, y_label:str, plot_name:str) -> None:
        pr_fig = sns.lineplot(x=x, y=y).get_figure()
        pr_ax = pr_fig.gca()
        pr_ax.set_xlabel(x_label)
        pr_ax.set_ylabel(y_label)
        plt.close(pr_fig)
        self.logger.experiment.add_figure(plot_name, pr_fig, self.global_step)

    def on_test_epoch_end(self) -> None:
        accuracy, precision, recall, f1_score = self._calc_metric(mode='test')
        self._log_step('test', accuracy, precision, recall, f1_score)
    
    def on_validation_epoch_end(self,):
        accuracy, precision, recall, f1_score = self._calc_metric(mode='val')
        self._log_step('val', accuracy, precision, recall, f1_score)
    
    def on_train_epoch_end(self, ):
        accuracy, precision, recall, f1_score = self._calc_metric(mode='train')
        self._log_step('train', accuracy, precision, recall, f1_score)


    def configure_optimizers(self) -> Any:
        optimizer = instantiate(self.config.optimizer, self.parameters())
        scheduler = instantiate(self.config.scheduler.body, optimizer=optimizer)
        config = {
            'optimizer': optimizer,
            'lr_scheduler': {
                'scheduler': scheduler,
                'interval': self.config.scheduler.pl_cfg.interval
            }
        }
        return config
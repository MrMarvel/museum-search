from torch import nn
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
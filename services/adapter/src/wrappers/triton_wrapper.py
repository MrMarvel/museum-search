import os
from pathlib import Path
from typing import *

import numpy as np
import tritonclient.grpc as grpcclient

from .. import logger


class TritonWrapper:
    def __init__(
        self,
        config: dict = {}
    ):
        self.config = config
        
        for k, v in self.config.items():
            self.__setattr__(k, v)
        
        self.model_version = '1' if not self.model_version else self.model_version
        self.client = self._make_client(self.connect_type)
        logger.info('Config has been loaded')
            
    
    def _make_client(self, client_type: str):
        logger.info('Client has been initialized')
        return grpcclient.InferenceServerClient(url=self.url, verbose=False)
    
    
    def _postprocess(self, inference_res):
        return [
            inference_res.as_numpy(out_name) 
            for out_name in self.output_names
        ]
    
    
    def __call__(self, *inp: np.array) -> Any:
        logger.info('Starting inference...')
        return self.inference(*inp)
    
    
    def inference(self, *inp:np.array):
        inputs = []
        
        for i, name, dt in zip(inp, self.input_names, self.input_dtype):
            inputs.append(grpcclient.InferInput(name, i.shape, dt))
            inputs[-1].set_data_from_numpy(i)
        
        result = self.client.infer(
            self.model_name,
            model_version=self.model_version,
            inputs=inputs
        )
        return self._postprocess(result)
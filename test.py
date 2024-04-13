import requests
import numpy as np
from services.adapter.src.wrappers.triton_wrapper import TritonWrapper
from transformers import Blip2Processor 
from PIL import Image
import yaml
from pathlib import Path

def load_test_image():
    img_url = 'https://gas-kvas.com/grafic/uploads/posts/2023-10/1696502271_gas-kvas-com-p-kartinki-lyubie-5.jpg'
    image = Image.open(requests.get(img_url, stream=True).raw).convert('RGB')
    return image

if __name__ == '__main__':
    config = yaml.safe_load(Path('configs/config.yaml').read_text())
    # text_model = TritonWrapper('./test_cfg.yaml')
    # vis_model = TritonWrapper('./test_cfg_vis.yaml')
    ensemble = TritonWrapper(config['triton_vision_model'])
    # ensemble = TritonWrapper(config['triton_ensemble_classification'])

    image = load_test_image()
    processor = Blip2Processor.from_pretrained('./weights/blip2_t5/model')
    inputs = processor(image, return_tensors="np")
    # res = vis_model(inputs['pixel_values'].astype(np.float16))
    # # res[0] - qformer res[1] - pooled
    # t_res = text_model(res[0])
    res = ensemble(inputs['pixel_values'].astype(np.float16))
    print(res)
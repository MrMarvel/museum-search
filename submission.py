import os
import pandas as pd
import yaml
import numpy as np
from PIL import Image
from pathlib import Path
from transformers import Blip2Processor
from services.adapter.src.wrappers.triton_wrapper import TritonWrapper
TEST_FOLDER = './data/train'

data = {
    "object_id":[],
    "img_name":[],
    "group":[]
}


idx2class = {
    "0": "Археология",
    "1": "Оружие",
    "2": "Прочие",
    "3": "Нумизматика",
    "4": "Фото, негативы",
    "5": "Редкие книги",
    "6": "Документы",
    "7": "Печатная продукция",
    "8": "ДПИ",
    "9": "Скульптура",
    "10": "Графика",
    "11": "Техника",
    "12": "Живопись",
    "13": "Естественнонауч.коллекция",
    "14": "Минералогия"
}


config = yaml.safe_load(Path('./configs/config.yaml').read_text())
model = TritonWrapper(config["triton_ensemble_classification"])
processor = Blip2Processor.from_pretrained('./weights/blip2_t5/model')

for root, dirs, files in os.walk(TEST_FOLDER):
    obj_id = root.split('/')[-1]
    for f in files:
        # make pred
        img_path = os.path.join(root, dirs, f)
        inputs = processor(Image.open(img_path), return_tensors="np")["pixel_values"].astype(np.float16)
        res = model(inputs)[0].argmax(dim=-1)
        data['img_name'].append(f)
        data['object_id'].append(obj_id)
        data['group'].append(idx2class[str(res)]) # or idx2pclass.get_pred

data = pd.DataFrame(data)
data.to_csv('submission.csv', index=False, sep=';', encoding='utf-8')
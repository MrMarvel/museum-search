from pathlib import Path
from typing import *

import pandas as pd
import yaml

from services.adapter.src import RabbitWrapper

if __name__ == '__main__':
    config = yaml.safe_load(Path('configs/config.yaml').read_text())
    broker = RabbitWrapper(config['rabbit'], swap_topics=True)
    
    data = []
    for i, row in pd.read_csv('dataset/train.csv', sep=';').fillna('').iterrows():
        data.append({
            'task': 'insert',
            'image_path': row.img_name,
            'object_id': row.object_id,
            'description': row.description
        })
    broker.publish(data)
import os
import datasets

COCO_DIR = os.path.join(os.getcwd(), "training/datasets/coco")
ds = datasets.load_dataset("ydshieh/coco_dataset_script", "2017", data_dir=COCO_DIR, cache_dir='training/datasets/coco/data')
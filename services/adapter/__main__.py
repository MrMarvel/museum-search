from pathlib import Path
from typing import *

import numpy as np
import yaml
from loguru import logger
from pymilvus import CollectionSchema, DataType, FieldSchema, utility
from .src.wrappers import MilvusWrapper, RabbitWrapper, TritonWrapper
from transformers import Blip2Processor
from PIL import Image
import os

logger.add(f"{__file__.split('/')[-1].split('.')[0]}.log", rotation="50 MB")


class Model:
    
    def __init__(self, config: dict) -> None:
        self.milvus = MilvusWrapper(config['milvus'])
        self.milvus.connect()
        self.milvus.init_collection(config['collection_name'], schema=self.create_schema())
        self.milvus.load()
        state = self.milvus.loaded_state()
        while state == 2:
            state = self.milvus.loaded_state()
        
        self.processor = Blip2Processor.from_pretrained('/weights/blip2_t5/model')
        self.ensemble_caption = TritonWrapper(config['triton_ensemble_caption'])
        # self.ensemble_classify = TritonWrapper(config['triton_ensemble_classify'])
        self.vision_model = TritonWrapper(config['triton_vision_model'])
        self.text_model = TritonWrapper(config['triton_text_model'])
        
        self.threshold = config['retrieval_threshold']
        self.storage_folder = config['storage_folder']
        self.config = config
        
        logger.success('Adapter has been initialized')

    
    def create_schema(self, description='Museum features') -> CollectionSchema:
        img_id = FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )

        image_path = FieldSchema(
            name="image_path",
            dtype=DataType.VARCHAR,
            max_length=100,
            default_value="Unknown"
        )
        
        object_id = FieldSchema(
            name="object_id",
            dtype=DataType.INT64,
        )
        
        description = FieldSchema(
            name="description",
            dtype=DataType.VARCHAR,
            max_length=10000,
            default_value="Unknown"
        )
        
        features = FieldSchema(
            name="features",
            dtype=DataType.FLOAT_VECTOR,
            dim=1408
        )

        schema = CollectionSchema(
            fields=[img_id, image_path, object_id, description, features],
            description='Image retrieval',
            enable_dynamic_field=True
        )
        return schema
    
    
    def postprocess_hits(self, entities):
        result = []
        for hits in entities:
            entity = []
            for hit in hits:
                entity.append(hit['entity']['image_path'])
            result.append(entity)
        return result
    
    
    def retrieval(self, image_path):
        image = self.processor(images=Image.open(image_path).convert('RGB'), return_tensors='np')['pixel_values']
        features = self.vision_model(image.astype(np.float16))[1]
        features = features / np.linalg.norm(features, axis=-1, keepdims=True)
        entities = self.milvus.vector_search(features.astype(np.float32))
        print(entities)
        result = self.postprocess_hits(entities)
        result = {'retrieval': result}
        return result
    
    
    def captioning(self, image_path):
        image = self.processor(images=Image.open(image_path).convert('RGB'), return_tensors='np')['pixel_values']
        captions = self.ensemble_caption(image.astype(np.float16))[0]
        result = {'caption': [cap[0].decode() for cap in captions]}
        return result
    
    
    def classification(self, image_path):
        image = self.processor(images=Image.open(image_path).convert('RGB'), return_tensors='np')['pixel_values']
        class_ = np.argmax(self.ensemble_classify(image.astype(np.float16))[0])
        result = {'class': class_}
        return result

    def __call__(self, task: str, image_path: str = '', object_id: str = '', description: str = '', user_id = None):
        match task:
            case 'classification':
                result = self.classification(image_path)
            case 'retrieval':
                result = self.retrieval(image_path)
            case 'captioning':
                result = self.captioning(image_path)
            case 'all':
                result = {}
                result.update(self.captioning(image_path))
                result.update(self.retrieval(image_path))
                # result.update(self.classification(image_path))
            case 'insert':
                image_path = Path(f'/{self.storage_folder}/{object_id}/{image_path}')
                if not os.path.exists(image_path.with_suffix('.npy')):
                    image = self.processor(images=Image.open(image_path).convert('RGB'), return_tensors='np')['pixel_values']
                    features = self.vision_model(image.astype(np.float16))[1].astype(np.float32)
                    np.save(image_path.with_suffix('.npy'), features)
                    logger.info(f"Features saved to {image_path.with_suffix('.npy')}")
        if user_id:
            result.update({'user_id': user_id})
            output_topic = self.config['bot_topic']
        else:
            output_topic = self.config['backend_topic']
        return result, output_topic


if __name__ == '__main__':
    config = yaml.safe_load(Path('configs/config.yaml').read_text())
    
    model = Model(config)
    
    broker = RabbitWrapper(config['rabbit'])
    broker.listen(pipeline=model)
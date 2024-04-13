import os
from pathlib import Path

import yaml
from pymilvus import Collection, connections, utility

from .. import logger


class MilvusWrapper:
    
    def __init__(
        self, 
        config: dict = {},
        host: str | None = None,
        port: str | int | None = None,
        alias: str | None = None
    ) -> None:
        self.host = host
        self.port = port
        self.alias = alias
        self.config = config
        self._load_config()
    
    
    def _load_config(self):
        if not self.host:
            self.host = os.environ.get('MILVUS_HOST', self.config.get('MILVUS_HOST', None))
        if not self.port:
            self.port = int(os.environ.get('MILVUS_PORT', self.config.get('MILVUS_PORT', None)))
        if not self.alias:
            self.alias = os.environ.get('MILVUS_ALIAS', self.config.get('MILVUS_ALIAS', None)) 

        logger.info('Config has been loaded')
    
    
    def connect(self):
        connections.connect(
            alias=self.alias, 
            host=self.host, 
            port=self.port
        )
        logger.info('Milvus has been connected')
    
    
    def loaded_state(self):
        return utility.load_state(self.collection_name).value
    
    
    def load(self):
        self.collection.load()
    
    
    def create_index(self, nlist = 512):
        if not len(self.collection.indexes):
            self.collection.create_index(
                'features',
                {
                    'index_type': 'IVF_FLAT',
                    'metric_type': 'L2',
                    'nlist': nlist
                },
                index_name='index'
            )
    
    
    def init_collection(self, collection_name, schema = None, shards_num = 2, alias = 'default'):
        self.collection_name = collection_name
        if utility.has_collection(collection_name):
            self.collection = Collection(
                name=collection_name,
            )
            logger.info(f'Collection {collection_name} has been connected')
        else:
            assert schema, f"""Collection {collection_name} doesn't exist.
                               You need to pass schema to create new collection"""

            self.collection = Collection(
                name=collection_name,
                schema=schema,
                using=alias,
                shards_num=shards_num
            )
            logger.info(f'New collection {collection_name} has been added')
    
    
    def insert(self, data):
        try:
            res = self.collection.insert(data)
            if res.err_count > 0:
                logger.error(f'Errors: {res.err_count}')
            return list(res.primary_keys)
        except Exception as e:
            logger.exception(e)
    
    
    def vector_search(
        self, 
        features, 
        output_fields=['image_path'],
        anns_field='features',
        nprobe=32,
        limit=10,
        metric_type="L2"
    ) -> list[dict]:
        search_params = {
            "metric_type": metric_type,
            "params": {"nprobe": nprobe}
        }

        results = self.collection.search(
            data=features, 
            param=search_params,
            limit=limit,
            anns_field=anns_field,
            output_fields=output_fields,
            consistency_level="Bounded"
        )
        
        parsed_results = []
        for hits in results:
            result =  []
            for hit in hits:
                result.append(hit.to_dict())
            parsed_results.append(result)
        return parsed_results
            
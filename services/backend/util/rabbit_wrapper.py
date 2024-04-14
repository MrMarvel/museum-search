import json
import os
import sys
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import *

import amqp
import yaml

from .. import logger

@dataclass
class RabbitAnswer:
    time: float | None
    inputs: dict | None
    result: dict | None
    json: str = field(init=False)
    
    def __post_init__(self):
        self.json = json.dumps(
            {
                'inputs': self.inputs,
                'process_time': self.time,
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'result': self.result
            },
            ensure_ascii=False
        )


class RabbitWrapper:
    
    def __init__(
        self,
        env_path = None,
        url: str | None =  None,
        input_topic: str | None = None,
        output_topic: str | None = None,
        swap_topics: bool = False
    ) -> None:
        self.url = url
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.env = {}
        
        if env_path and os.path.exists(env_path):
            self.env = yaml.safe_load(Path(env_path).read_text())
        self._load_env()
        
        if swap_topics:
            self.input_topic, self.output_topic = self.output_topic, self.input_topic
        
        self._connect()
        
        if self.input_topic:
            self._create_topic(self.input_topic)
            logger.info(f'Input topic {self.input_topic} has been connected')

        if self.output_topics:
            for topic in self.output_topics:
                self._create_topic(topic)
                logger.info(f'Output topic {topic} has been connected')
            self.output_topic = self.output_topics[0]

    
    def _load_config(self):
        if not self.url:
            self.url = os.environ.get('RABBIT_URL', self.env.get('RABBIT_URL', None))
            
        self.host, self.virtual_host = self.url.split('@')[1].split('/')
        _, self.username, self.password = self.url.split('@')[0].split(':')
        self.username = self.username.replace('//', '')
        
        if len(self.virtual_host) == 0:
            self.virtual_host = '/'
        
        if not self.input_topic:
            self.input_topic = os.environ.get('INPUT_TOPIC', self.env.get('INPUT_TOPIC', None)) 
        
        if not self.output_topic:    
            self.output_topic = os.environ.get('OUTPUT_TOPIC', self.env.get('OUTPUT_TOPIC', None))

        logger.info('Envs has been loaded')
    
    
    def _create_topic(self, topic_name):
        self.channel.queue_declare(
            queue=topic_name,
            durable=True,
            exclusive=False,
            auto_delete=False,
            arguments={'x-queue-type=classic': 'classic'}
        )
        logger.debug(f'Topic {topic_name} has been created')
    
    
    def _create_answer(self, time, payload: dict, result: dict | None) -> None:
        return RabbitAnswer(time, payload, result)
    
    
    def _connect(self) -> Any:
        tries = 0
        while True:
            try:
                tries += 1
                logger.info(f'Trying to connect at {tries} time')
                self.connection = amqp.Connection(
                    host=self.host,
                    userid=self.username,
                    password=self.password,
                    virtual_host=self.virtual_host
                )

                self.connection.connect()
                self.channel = self.connection.channel()
                logger.info('Connection successful')
                break
            except Exception as e:
                logger.warning(f'Connection failed. Waiting for a 5 seconds...')
                time.sleep(5)
    
    
    def _process_item(self, pipeline, **payload) -> tuple[dict, float]:
        try:
            logger.info('Start processing an item')
            start_time = time.time()
            result = pipeline(**payload)
            process_time = time.time() - start_time
            logger.info(f'Item has been processed in {process_time}s')
        except Exception as e:
            result = None
            process_time = None
            logger.error(f'{traceback.format_exc()}')
        return result, process_time

    
    def publish(self, data: list[dict] | dict, time = None, payload = None) -> None:
        assert self.output_topic, 'There is output topic needed'
        
        if not isinstance(data, list):
            data = [data]
        
        for item in data:
            if payload:
                answer = self._create_answer(time, payload, item).json
            else:
                answer = json.dumps(item)
            msg = amqp.basic_message.Message(body=answer)
            self.channel.basic_publish(msg, exchange='', routing_key=self.output_topic)
            logger.debug(f'Publish msg to {self.output_topic}')
    
    
    def listen(self, num = -1, pipeline: Callable | None = None, ack: bool = False) -> None:
        assert self.input_topic, 'There is input topic needed'
        
        if pipeline:
            ack = True
            logger.info(f'Consumer gets pipeline: {pipeline.__class__.__name__}')
        
        n = 0
        payloads = []
        logger.info(f'Start consuming on {self.input_topic}')
        while True:
            try:
                message = self.channel.basic_get(queue=self.input_topic)
                if message:
                    logger.debug(f'Got message')
                    if ack:
                        self.channel.basic_ack(delivery_tag=message.delivery_tag)
                        logger.debug(f'Acked on message')
                    payload = json.loads(message.body)
                    
                    if pipeline:
                        result, time = self._process_item(pipeline, **payload)
                        if self.output_topic:
                            self.publish(result, time, payload)
                    else:
                        payloads.append(payload)    
                        if n + 1 == num:
                            return payloads
                    n += 1
                elif not pipeline: 
                    return payloads
            except Exception as e:
                if e == KeyboardInterrupt:
                    self.connection.close()
                    sys.exit()
                logger.error(f'{traceback.format_exc()}')
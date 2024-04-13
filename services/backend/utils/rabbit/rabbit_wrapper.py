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
from loguru import logger
from pika.adapters.blocking_connection import BlockingChannel
from pika.connection import Connection

from services.backend.utils.rabbit import Connector


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


class RabbitClient:

    def __init__(
            self,
            env_path=None,
            url: str | None = None,
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

        if self.output_topic:
            self._create_topic(self.output_topic)
            logger.info(f'Output topic {self.output_topic} has been connected')

    def _load_env(self):
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

    def get(self) -> None:
        """Get exactly one message"""
        con = Connector(
            env_path='configs/rabbit.env'
        )
        while True:
            try:
                #            connection, channel, input_queue, output_queue
                with con as (connection, channel, input_queue, output_queue):
                    connection: Connection
                    channel: BlockingChannel
                    while True:
                        channel.basic_qos(prefetch_count=1)
                        if channel.get_waiting_message_count() < 1:
                            time.sleep(1)
                        x = channel.basic_get(con.input_queue)
                        if x != (None, None, None):
                            channel.basic_ack(x[0].delivery_tag)
                            data = self._filter_data(*x)
                            return data
            except Exception as e:
                logger.error(e)
                logger.info("RECONNECT")

    def _filter_data(self, ch, method, body):
        logger.info("CALLBACK")
        logger.info(ch)
        logger.info(method)
        logger.info(body)
        body_str = body.decode('utf-8')
        body_json = json.loads(body_str)
        return RabbitAnswer.

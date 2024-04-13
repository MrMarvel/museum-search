import aio_pika
import json
import asyncio
import os
import time
from aio_pika.abc import AbstractRobustConnection
from dotenv import dotenv_values
from loguru import logger
from typing import Callable, Optional, Union


class RabbitWrapper:
    def __init__(
            self,
            env_path:Optional[Union[str, os.PathLike]]=None,
            url:Optional[str]=None,
        ) -> None:
        self.url = url
        if env_path:
            self._load_env_from_file(env_path)
        self._load_env_from_os()

    def _load_env_from_os(self):
        if not self.url:
            self.url = os.environ.get('RABBIT_URL')
        logger.info('Envs are loaded')
    
    def _load_env_from_file(self, env_path):
        d = dict(dotenv_values(env_path))
        os.environ['RABBIT_URL'] = d.get('RABBIT_URL')

    
    async def connect(self) -> AbstractRobustConnection | None:
        tries = 0
        while True:
            tries += 1
            try:
                connection = await aio_pika.connect_robust(self.url)
                return connection
            except Exception as e:
                logger.info(f'Connection failed. Waiting for a 5 seconds...')
                time.sleep(5)

    
    async def publish(self, msg: dict, queue_name: str):
        connection = await self.connect()
        async with connection:
            channel = await connection.channel()
            _ = await channel.declare_queue(queue_name, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(msg).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                routing_key=queue_name,
            )

    
    async def consume(
            self,
            listen_queue_name: str,
            publish_queue_name:Optional[str]=None,
            pipeline:Optional[Callable]=None,
            callback_map=None,
        ):
        connection = await self.connect()
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            listen_queue = await channel.declare_queue(listen_queue_name, durable=True, auto_delete=False)
            if publish_queue_name:
                _ = await channel.declare_queue(publish_queue_name, durable=True, auto_delete=False)
            async with listen_queue.iterator() as queue_iter:
                async for message in queue_iter:
                    msg = json.loads(message.body)
                    result = msg
                    # pipeline stuff
                    if pipeline:
                        result = pipeline(**msg)
                    if publish_queue_name:
                        await message.ack()
                        await self.publish(result, publish_queue_name)
                    else:
                        response = msg.get("result")
                        user_session = callback_map.pop(response.get("user_id"), None)
                        if user_session:
                            await message.ack()                            
                            callback = user_session.callback
                            chat_id = user_session.chat_id
                            event_loop = user_session.loop
                            asyncio.run_coroutine_threadsafe(callback(
                                chat_id,
                                response,
                                msg.get("inputs").get("image_path")
                            ), event_loop).result(timeout=60)
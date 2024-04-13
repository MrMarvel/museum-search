import json

from loguru import logger
from threading import Thread, Lock


class VideoConsumerThread(Thread):
    def __init__(self, con, check_lock: Lock, callback_map: dict[int, dict]):
        super().__init__()
        self._check_lock = check_lock
        self._callback_map = callback_map
        self.con = con

    def run(self) -> None:
        while True:
            try:
                with self.con as (connection, channel, input_queue, output_queue):
                    while True:
                            channel.basic_qos(prefetch_size=0, prefetch_count=1, a_global=False)
                            x = channel.basic_get(input_queue)
                            if x:
                                channel.basic_ack(x.delivery_tag)
                                self.callback(x.body)
            except Exception as e:
                logger.error(e)
                logger.info("Can't connect to RabbitMQ. Trying to reconnect")

    def callback(self, body):
        logger.info(f'Get message: {body}')
        body_json = json.loads(body)

        upload_id = int(body_json['upload_id'])
        with self._check_lock:
            callback_json = self._callback_map.pop(upload_id, None)
            
        if not callback_json:
            return
        
        callback = callback_json['callback']
        try:
            if body_json['path']:
                callback(body_json['path'])
        except Exception as e:
            logger.error(e)
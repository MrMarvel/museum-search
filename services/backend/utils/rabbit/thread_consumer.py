import json
import threading
from threading import Thread, Lock, Event
from typing import Callable

from loguru import logger
from pika.adapters.blocking_connection import BlockingChannel
from pika.connection import Connection

from services.backend.utils.rabbit.connector import Connector


class RabbitConsumerThread(Thread):
    def __init__(self, on_message: Callable):
        super().__init__()
        self._check_lock = threading.Lock()
        self._callback_map: dict[str, dict] = {}
        self._new_item_event = Event()

    def add_callback(self, upload_id: str, callback: callable):
        with self._check_lock:
            self._callback_map[upload_id] = {
                'callback': callback
            }
        self._new_item_event.set()

    def run(self) -> None:
        con = Connector(
            env_path='configs/rabbit.env'
        )
        # connection, channel, input_queue, output_queue
        while True:
            try:
                with con as (connection, channel, input_queue, output_queue):
                    connection: Connection
                    channel: BlockingChannel
                    while True:
                        no_items = False
                        with self._check_lock:
                            if len(self._callback_map) <= 0:
                                no_items = True
                        channel.basic_qos(prefetch_count=1)
                        x = channel.basic_get(con.input_queue)
                        if x != (None, None, None):
                            self.filter_call(*x)
                            channel.basic_ack(x[0].delivery_tag)
                            with self._check_lock:
                                self._callback_map.pop(upload_id)
                        if no_items:
                            logger.info("NO ITEMS")
                            self._new_item_event.wait()
                            self._new_item_event.clear()
                            logger.info("UNSET")
            except Exception as e:
                logger.error(e)
                logger.info("RECONNECT")

    def filter_call(self, ch, method, body):
        logger.info("CALLBACK")
        logger.info(ch)
        logger.info(method)
        logger.info(body)
        body_str = body.decode('utf-8')
        body_json = json.loads(body_str)

        callback_json = self._callback_map.pop(upload_id)
        callback = callback_json['callback']
        try:
            process_status = str(body_json['status'])
            if process_status.lower() == 'success':
                callback(ready_file_path)
            else:
                failed = True
        except Exception as e:
            logger.error(e)
            failed = True
        finally:
            if upload_id in self._callback_map:
                self._callback_map.pop(upload_id)
        if failed:
            logger.info("FAILED. RETRY")
            with self._check_lock:
                self._callback_map[upload_id] = callback_json
            # process_file(input_file, upload_id)

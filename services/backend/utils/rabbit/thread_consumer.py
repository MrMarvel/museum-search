import json
import pathlib
import secrets
import threading
from dataclasses import dataclass, field
from threading import Thread, Lock, Event
from typing import Callable, Union

from loguru import logger
from pika.adapters.blocking_connection import BlockingChannel
from pika.connection import Connection

from services.backend.utils.globals import ENV_FILENAME
from services.backend.utils.rabbit.connector import Connector


@dataclass
class RabbitTask:
    task_id: str
    callback: Union[Callable, None]
    in_args: dict
    result: dict

    def __init__(self,  task_id, in_args=None, callback=None, result=None):
        self.task_id = str(task_id)
        if in_args is None:
            in_args = {}
        self.in_args = dict(in_args)
        self.callback = callback
        if result is None:
            result = {}
        self.result = dict(result)


class RabbitConsumerThread(Thread):
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._tasks: dict[str, RabbitTask] = {}
        self._new_item_event = Event()

    def add_task(self, rabbit_task: RabbitTask):
        with self._lock:
            self._tasks[rabbit_task.task_id] = rabbit_task
        self._new_item_event.set()

    def run(self) -> None:
        con = Connector(
            env_path=str(pathlib.Path(ENV_FILENAME))
        )
        # connection, channel, input_queue, output_queue
        while True:
            try:
                with con as (connection, channel, input_queue, output_queue):
                    connection: Connection
                    channel: BlockingChannel
                    while True:
                        no_items = False
                        with self._lock:
                            if len(self._tasks) <= 0:
                                no_items = True
                        channel.basic_qos(prefetch_count=1)
                        x = channel.basic_get(con.input_queue)
                        if x != (None, None, None):
                            task = self.filter_call(*x)
                            channel.basic_ack(x[0].delivery_tag)
                        if no_items:
                            logger.info("NO ITEMS")
                            self._new_item_event.wait()
                            self._new_item_event.clear()
                            logger.info("UNSET")
            except Exception as e:
                logger.error(e)
                logger.info("RECONNECT")

    def filter_call(self, ch, method, body):
        task: RabbitTask | None = None
        try:
            logger.info("CALLBACK")
            logger.info(ch)
            logger.info(method)
            logger.info(body)
            body_str = body.decode('utf-8')
            body_json = json.loads(body_str)

            task_id = str(body_json['task_id'])
            failed = False

            with self._lock:
                task = self._tasks.get(task_id)
                if task is None:
                    return
                task.result = body_json

            callback = task.callback

            process_status = str(body_json['status'])
            if process_status.lower() == 'success':
                ready_file_path = body_json['path']
                callback(ready_file_path)
            else:
                failed = True
            return task
        finally:
            if task is not None:
                with self._lock:
                    self._tasks.pop(task.task_id)
                    logger.info(f"Task {task.task_id} done")

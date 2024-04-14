import os
import pathlib

from ..globals import ENV_FILENAME
from ..rabbit.connector import Connector
from .publisher import RabbitPublisher



def compact_publish_data(data: dict):
    con = Connector(
        env_path=str(pathlib.Path(ENV_FILENAME))
    )
    with con as (connection, channel, input_queue, output_queue):
        pub = RabbitPublisher(
            channel,
            connection,
            output_queue
        )
        pub.publish(data)

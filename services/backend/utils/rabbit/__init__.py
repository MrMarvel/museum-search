import os
import pathlib

from services.backend.utils.globals import ENV_FILENAME
from services.backend.utils.rabbit.connector import Connector
from services.backend.utils.rabbit.publisher import RabbitPublisher



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

import os
import pathlib

from services.backend.utils.rabbit.connector import Connector
from services.backend.utils.rabbit.publisher import RabbitPublisher

env_filepath = str(pathlib.Path(os.environ.get('ENV_FILEPATH', 'configs/rabbit.env')))


def compact_publish_data(data: dict):
    con = Connector(
        env_path=env_filepath
    )
    with con as (connection, channel, input_queue, output_queue):
        pub = RabbitPublisher(
            channel,
            connection,
            output_queue
        )
        pub.publish(data)

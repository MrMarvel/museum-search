import time

import dotenv

from services.backend.utils.globals import *
from utils.rabbit.rabbit_wrapper import RabbitWrapper


def main():
    dotenv.load_dotenv(ENV_FILENAME)
    r = RabbitWrapper(url=os.environ.get('RABBIT_URL'),
                  input_topic=os.environ.get('BACKEND_OUTPUT_QUEUE'),
                  output_topics=[os.environ.get('BACKEND_INPUT_QUEUE')])
    while True:
        time.sleep(1)
        result = r.listen(1, ack=True)
        print(result)
        if result is None or len(result) < 1:
            continue
        r.publish({'test': 'test'}, r.output_topic)


if __name__ == '__main__':
    main()
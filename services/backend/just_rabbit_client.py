import time

import dotenv

from .main import load_yaml
from .utils.globals import *
from .utils.rabbit.rabbit_wrapper import RabbitWrapper


def main():
    load_yaml()
    r = RabbitWrapper(url=os.environ.get('RABBIT_URL'),
                      input_topic=os.environ.get('BACKEND_OUTPUT_QUEUE'),
                      output_topics=[os.environ.get('BACKEND_INPUT_QUEUE')])
    while True:
        time.sleep(1)
        result = r.listen(1, ack=True)
        if result is None or len(result) < 1:
            continue
        print(result)
        if type(result) is list:
            result = result[0]
        r.publish(
            {'inputs': {'task_id': result['task_id']},
             'result': {
                 'class_name': 'cls1',
                 'caption:': 'cool_text',
                 'retrieval': [r"D:\Users\Sergey\Pictures\BlueStacks\photo_2021-10-16_16-09-13.jpg",
                               'https://super.ru/image/rs::384:::/quality:90/plain/s3:/super-static/prod'
                               '/6235e12ba501412aae40dc87-1900x.jpeg']
             }},
            r.output_topic)


if __name__ == '__main__':
    main()

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
        print(result)
        if result is None or len(result) < 1:
            continue
        r.publish(
            {'input':
                 {'task_id': result['task_id']},
             'result': {
                 'class_name': 'cls1',
                 'caption:': 'cool_text',
                 'retrieval': [r'F:\Users\Sergey\Projects\PyProjects\museum-search\storage\85587\20110220.jpg',
                               'https://rutube.ru/api/video/preview/615182ccc47ca640b58c86d9e3369853']
             }},
            r.output_topic)


if __name__ == '__main__':
    main()

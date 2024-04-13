import json
import os
import pathlib
import time

from celery import Celery
from celery.utils.log import get_task_logger

from models import Upload, BlobContainer, Blob, UploadResult, database
from services.backend.utils.rabbit.rabbit_wrapper import RabbitWrapper

logger = get_task_logger(__name__)

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "amqp://localhost:5672")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND",
                                            f"file:///{pathlib.Path('.').absolute()}/tmp/celery")
celery.conf.cache_backend = os.environ.get("CELERY_CACHE_BACKEND",
                                           f"file:///{pathlib.Path('.').absolute()}/tmp/celery")
path = pathlib.Path(celery.conf.result_backend)
if path.parts[0] == 'file:':
    path = pathlib.Path('/'.join(path.parts[1:]))
    if not os.path.exists(path):
        os.makedirs(path)
celery.conf.broker_connection_retry_on_startup = True
celery.conf.worker_pool = 'solo'
celery.conf.worker_prefetch_multiplier = 1
celery.conf.worker_concurrency = 1


@celery.task(name="create_task")
def create_task(task_type):
    logger.info(f"Start {task_type}")
    time.sleep(int(task_type) * 10)
    logger.info(f"Done {task_type}")
    return True


@celery.task(name="process_upload", bind=True)
def process_upload(self, upload_id: int):
    task_id = str(self.request.id)
    with database:
        upload = Upload.get_by_id(upload_id)
        familiar_container = BlobContainer.get_by_name('familiars')
    # send
    RabbitWrapper()
    # wait for the task to finish
    time.sleep(10)
    data = {"familiar_images": [
        r"F:\HEHE\85658\23441576.jpg",
        r"F:\HEHE\familiars\85658\23441576.jpg",
        r"F:\HEHE\familiars\85658\23441576.jpg"],
        "class_name": "Гнига"}
    # change paths
    paths = data['familiar_images']
    blobs_id = []
    for path in paths:
        new_path = str('/'.join(pathlib.Path(path).parts[-2:]))
        logger.info(f"Changed path {path} to {new_path}")
        with database:
            familiar_blob = Blob.get_blob_by_path_in_container(familiar_container, new_path)
        if not familiar_blob:
            logger.warning(f"Blob not found for path {path}. Skip.")
            continue
        blobs_id.append(familiar_blob.get_id())
    data['familiar_images'] = blobs_id
    # save the result
    with database:
        UploadResult.create(upload=upload, data=json.dumps(data, ensure_ascii=False))
    logger.info(f"Saved UploadResult {UploadResult}")

    return {
        'task_id': task_id,
        'text': f"YOU ARE NOT SUPPOSED TO SEE THAT! {data}"
    }  # everyone ignore this value
    # because noone will wait it for fast response


def main():
    for _ in range(10):
        create_task.delay(1)


if __name__ == '__main__':
    main()

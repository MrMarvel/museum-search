import json
import os
import pathlib
import secrets
import threading

import dotenv
import peewee
import requests
import uvicorn
import yaml
from fastapi import FastAPI, UploadFile, File, Request, Body

from .models import create_models, UploadResult
from .models.blob import BlobContainer
from .utils import rabbit
from .utils.globals import DEFAULT_WEBHOOK_URL, UPLOAD_FOLDER, ENV_FILENAME
from .utils.rabbit.thread_consumer import RabbitConsumerThread, RabbitTask
from .utils import *
from .utils.file_utils import create_folders, features_load_blobs, find_trash_items

app = FastAPI()


@app.get("/")
@return_error_response
async def root(request: Request):
    return f"This is api for MinMuseum project. Visit {request.base_url}docs for documentation"


def send_model_to_webhook(data: ResponseModel, webhook: str):
    logger.info(f"Sending {data} to webhook {webhook}")
    requests.post(webhook, json=data.dict)


@app.post('/upload', status_code=201, response_model=ResponseModel)
@return_error_response
async def upload_file(request: Request, file: UploadFile = File(...),
                      webhook_url: str | None = Body(None, embed=True),
                      webhook_request_id: str | None = Body(None, embed=True)):
    logger.info(f"Uploading file {file.filename} with webhook {webhook_url} and request_id {webhook_request_id}")
    if webhook_url.lower() == 'default':
        webhook_url = DEFAULT_WEBHOOK_URL
        logger.info(f'Using default webhook. Replaced with {webhook_url}')
    result = ResponseModel()
    file_random_suffix = str(secrets.token_hex(5))[:5]
    contents = file.file.read()
    file_relative_path = pathlib.Path(file.filename)
    file_relative_path = f'{file_relative_path.stem}_{file_random_suffix}{file_relative_path.suffix}'
    with database:
        container = BlobContainer.get_by_folder_path(UPLOAD_FOLDER)
    blob = Blob(file_path=file_relative_path, container=container)
    upload = Upload(blob=blob)
    file_abs_path = pathlib.Path(upload.resolve_filepath()).absolute()
    if not os.path.exists(file_abs_path.parent):
        os.makedirs(file_abs_path.parent)
    with open(file_abs_path, 'wb') as f:
        f.write(contents)
    with database:
        blob.save()
        upload.save()
    # task = celery_main.process_upload.apply_async(args=[upload.get_id()], expires=60 * 10)
    task = RabbitTask(task_id=upload.get_id())
    task.in_args = {
        'task_id': task.task_id,
        'task': 'all',
        'image_path': str("/storage/83137/20110231.jpg"),
    }
    task_id = str(task.task_id)

    @logger.catch(reraise=True)
    def _callback(result_task: RabbitTask):
        with database:
            upload: Upload = Upload.get_by_id(result_task.task_id)
            familiar_container = BlobContainer.get_by_name('familiars')
        inner_result = result_task.result
        class_name = inner_result.get('class', "Unknown")
        caption = inner_result.get('caption', "")
        familiar_images: list[str] = [str(x) for x in inner_result.get('retrieval', list())]
        data = {
            'class_name': class_name,
            'familiar_images': familiar_images,
            'description': caption,
        }
        paths = data['familiar_images']
        for path_num, path in enumerate(paths.copy()):
            if path.startswith('http'):
                continue
            new_path = str('/'.join(pathlib.Path(path).parts[-2:]))
            logger.info(f"Changed path {path} to {new_path}")
            with database:
                familiar_blob = Blob.get_blob_by_path_in_container(familiar_container, new_path)
            if not familiar_blob:
                logger.warning(f"Blob not found for path {path}. Skip.")
                continue
            blob_id = familiar_blob.get_id()
            paths[path_num] = blob_id
        # save the result
        with database:
            UploadResult.create(upload=upload, data=json.dumps(data, ensure_ascii=False))
        logger.info(f"Saved UploadResult {UploadResult}")

        res_model = make_upload_model(upload, str(request.base_url))
        if webhook_request_id is not None:
            res_model.data['webhook_request_id'] = webhook_request_id
        if webhook_url is not None:
            send_model_to_webhook(res_model, webhook_url)

    task.callback = _callback
    rabbit_consumer_thread.add_task(task)
    rabbit.compact_publish_data(task.in_args)
    result.data = {'task_id': task_id}
    return result


@app.get('/task_status')
@return_error_response
async def task_status(request: Request, task_id: str) -> ResponseModel:
    raise NotImplementedError("Broken now")
    task_result = AsyncResult(id=task_id)
    result = ResponseModel()
    result.data["task_id"] = str(task_id)
    result.data["task_status"] = str(task_result.status)
    if task_result.ready():
        try:
            result.data['task_result'] = json.loads(str(task_result.result))
        except json.JSONDecodeError:
            result.data['task_result'] = str(task_result.result)

    if str(task_result.status).lower() == 'pending':
        result.comment = "Task not found or not done yet"
    return result


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/uploads", response_model=ResponseModel)
@return_error_response
async def get_uploads(request: Request):
    with database:
        uploads: list[Upload] = Upload.select()
    result = {
        'status': 'success',
        'data': {
            'uploads': [u.get_id() for u in uploads]
        }
    }
    return JSONResponse(result)


@app.get("/upload/{upload_id}", response_model=ResponseModel)
@return_error_response
async def get_upload(request: Request, upload_id: int):
    result = ResponseModel()
    try:
        with database:
            upload: Upload = Upload.get_by_id(upload_id)
    except peewee.DoesNotExist:
        # status code via CLASS ENUM
        result.status = ResponseModel.Status.error
        result.error = "Upload not found"
        return fastapi.responses.JSONResponse(content=result.dict, status_code=fastapi.status.HTTP_403_FORBIDDEN)
    # verify skip
    return fastapi.responses.JSONResponse(make_upload_model(upload, str(request.base_url)).dict)


@app.get('/storage/blobs/{container_id}/{blob_id}')
@return_error_response
async def get_blob(request: Request, container_id: str, blob_id: str):
    result = ResponseModel()
    try:
        with database:
            blob: Blob = Blob.get_blob_by_hex(container_id, blob_id)
    except peewee.DoesNotExist:
        result.error = "Blob not found"
        result.status = ResponseModel.Status.error
        return fastapi.responses.JSONResponse(content=result.dict, status_code=fastapi.status.HTTP_404_NOT_FOUND)

    file_path = blob.resolve_path()
    if not os.path.exists(file_path):
        result.error = "File not found"
        result.status = ResponseModel.Status.error
        return fastapi.responses.JSONResponse(content=result.dict, status_code=fastapi.status.HTTP_404_NOT_FOUND)
    return fastapi.responses.FileResponse(file_path)


# cel = celery.Celery(__name__)
# cel.conf.update(celery_main.celery.conf)
# cel.conf.worker_pool = 'threads'


# @cel.task(name="celery_callback")
# def celery_callback(result):
#     time.sleep(10)
#     logger.info(f"Task result: {result}")
#     # logger.info(a)


# def celery_worker():
#     argv = [
#         'worker',
#         '--loglevel=INFO',
#         '--hostname=fastapi_celery'
#     ]
#     cel.worker_main(argv=argv)


# class InfiniChecker(threading.Thread):
#     def __init__(self, parent_thread: threading.Thread = threading.current_thread(), daemon=True, ):
#         super().__init__(daemon=daemon)
#         self._parent_thread = parent_thread
#         self.thread_lock = threading.Lock()
#         self.__callback_maps: list[dict] = list()
#         self._new_item_event = threading.Event()
#
#     def add_callback_map(self, callback_map: dict):
#         with self.thread_lock:
#             self.__callback_maps.append(copy.deepcopy(callback_map))
#             self._new_item_event.set()
#
#     @logger.catch(reraise=True)
#     def run(self):
#         parent = self._parent_thread
#         while True:
#             with self.thread_lock:
#                 callback_maps_shadow = copy.deepcopy(self.__callback_maps)
#             if len(callback_maps_shadow) < 1:
#                 if self._new_item_event.wait(30):
#                     self._new_item_event.clear()
#                 continue
#
#             for callback_map in callback_maps_shadow:
#                 task_id = callback_map['task_id']
#                 callback = callback_map.get('callback', lambda x: None)
#                 task_result = AsyncResult(id=task_id, app=celery_main.celery)
#                 if task_result.ready():
#                     for try_num in range(4):
#                         if try_num >= 3:
#                             logger.warning(f"Task {task_id} done but callback failed 3 times. skip")
#                             break
#                         try:
#                             logger.info(f"Task {task_id} Done. Calling callback with {task_result}")
#                             callback(task_result)
#                         except Exception as e:
#                             logger.exception(e)
#                             parent.join(3)
#                             continue
#                         break
#                     with self.thread_lock:
#                         self.__callback_maps.remove(callback_map)
#                         logger.info(f"Task {task_id} done")
#                     continue
#                 parent.join(1)
#
#
# infiniChecker: InfiniChecker | None = None
rabbit_consumer_thread: RabbitConsumerThread | None = None
@logger.catch(reraise=True)
def main():
    config = yaml.safe_load(pathlib.Path('configs/config.yaml').read_text())
    logger.info(config)
    if 'RABBIT_URL' not in os.environ.keys():
        if 'RABBIT_URL' in config['rabbit']:
            os.environ['RABBIT_URL'] = config['rabbit']['RABBIT_URL']
        if os.environ['RABBIT_URL'] is None:
            raise ValueError("Rabbit URL not found in env or config")
    if 'BACKEND_OUTPUT_QUEUE' not in os.environ.keys():
        if 'INPUT_TOPIC' in config['rabbit']:
            os.environ['BACKEND_OUTPUT_QUEUE'] = config['rabbit']['INPUT_TOPIC']
        if os.environ['BACKEND_OUTPUT_QUEUE'] is None:
            raise ValueError("Output queue not found in env or config")
    if 'BACKEND_INPUT_QUEUE' not in os.environ.keys():
        if 'OUTPUT_TOPICS' in config['rabbit']:
            for queue_name in list(config['rabbit']['OUTPUT_TOPICS']):
                queue_name = str(queue_name)
                if 'backend_output' in queue_name:
                    os.environ['BACKEND_INPUT_QUEUE'] = queue_name
                    break
        if os.environ['BACKEND_INPUT_QUEUE'] is None:
            raise ValueError("Input queue not found in env or config")
    # dotenv.load_dotenv(pathlib.Path(__file__).parent / '.env')
    if 'DEFAULT_WEBHOOK_URL' not in os.environ.keys():
        raise ValueError("DEFAULT_WEBHOOK_URL not found in ENVIRONMENT")
    create_models()
    create_folders()
    threading.Thread(target=features_load_blobs, daemon=True).start()
    threading.Thread(target=find_trash_items, kwargs={'verbose': True}, daemon=True).start()
    global infiniChecker
    # infiniChecker = InfiniChecker(threading.current_thread(), daemon=True)
    # infiniChecker.start()
    global  rabbit_consumer_thread
    rabbit_consumer_thread = RabbitConsumerThread(daemon=True)
    rabbit_consumer_thread.start()
    port = 8102
    logger.info(f"Access: http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=8102)


if __name__ == "__main__":
    main()

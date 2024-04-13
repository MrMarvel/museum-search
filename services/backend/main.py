import asyncio
import datetime
import json
import os
import pathlib
import secrets
import threading
from enum import Enum
from functools import wraps

import fastapi
import peewee
import pydantic
import uvicorn
from celery.result import AsyncResult
from fastapi import FastAPI, UploadFile, File, Request
from loguru import logger
from starlette.responses import JSONResponse

import celery_main
from models import Upload, create_models, database, Blob, BlobContainer

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
FAMILIARS_FOLDER = os.environ.get('FAMILIARS_FOLDER', './familiars')


def create_folders():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(FAMILIARS_FOLDER):
        os.makedirs(FAMILIARS_FOLDER)
        with open(pathlib.Path(FAMILIARS_FOLDER) / 'README.txt', 'w', encoding='utf-8') as f:
            f.write('You should place IMAGE DATASET in that folder.\n'
                    'The dataset should be in the following format:\n'
                    'uploads/im1.jpg\n'
                    'uploads/im2.png\n'
                    '...')
    mounts = [UPLOAD_FOLDER, FAMILIARS_FOLDER]
    for mount in mounts:
        mount_path = pathlib.Path(mount)
        with database:
            if not BlobContainer.select().where(BlobContainer.folder_path == str(mount_path)).exists():
                BlobContainer.create(folder_path=str(mount_path))


def find_trash_items(verbose=False):
    if verbose:
        logger.info("Searching for trash items")
    files_list = []
    files_to_remove = []
    with database:
        containers: list[BlobContainer] = list(BlobContainer.select())

    for container in containers:
        with database:
            blobs: list[Blob] = container.__getattribute__('blobs')
        for blob in blobs:
            files_list.append(pathlib.Path(container.folder_path) / blob.file_path)
    for file in files_list:
        if not file.exists():
            if verbose:
                logger.info(f"Found {file}")
            files_to_remove.append(file)
    # if os.path.exists(UPLOAD_FOLDER):
    #     for file in os.listdir(UPLOAD_FOLDER):
    #         file_path = pathlib.Path(UPLOAD_FOLDER) / file
    #         if file_path not in files_list:
    #             if verbose:
    #                 print(f"Found {file_path}")
    #             files_to_remove.append(file_path)
    return files_to_remove


def features_load_blobs():
    with database:
        container = BlobContainer.get_by_folder_path(FAMILIARS_FOLDER)
        blobs: list[Blob] = container.__getattribute__('blobs')
    logger.info("Loading new blobs")
    new_blobs = []
    blobs_paths = [b.file_path for b in blobs]
    for path in pathlib.Path(FAMILIARS_FOLDER).rglob('*'):
        try:
            if path.is_dir():
                continue
            relative_path = path.relative_to(FAMILIARS_FOLDER)
            if str(relative_path) in blobs_paths:
                continue
            logger.info(f"Found new Blob {path}. Adding")
            blob = Blob(file_path=relative_path, container=container)
            new_blobs.append(blob)
        except Exception as e:
            logger.exception(e)
    if len(new_blobs) > 0:
        with database:
            Blob.bulk_create(new_blobs, batch_size=10)
        logger.info("Finished loading new blobs")
    else:
        logger.info("No new blobs found")


app = FastAPI()


def return_error_response(func):
    if not asyncio.iscoroutinefunction(func):
        raise TypeError("Function must be async")

    @wraps(func)
    async def _wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            return JSONResponse(content=ErrorResponse(error=str(e)).dict,
                                status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR)

    return _wrapper


class ResponseModel(pydantic.BaseModel):
    class Status(str, Enum):
        success = "success"
        error = "error"

    status: Status = Status.success
    data: dict = {}
    error: str = ""
    comment: str | None = None

    @property
    def dict(self, **kwargs) -> dict:
        return self.model_dump(warnings='none', exclude_none=True)


class ErrorResponse(ResponseModel):
    def __init__(self, error: str = None):
        super().__init__()
        self.status = ResponseModel.Status.error
        if error is not None:
            self.error = error


@app.get("/")
@return_error_response
async def root(request: Request):
    return f"This is api for MinMuseum project. Visit {request.base_url}docs for documentation"


@app.post('/upload', status_code=201, response_model=ResponseModel)
@return_error_response
async def upload_file(request: Request, file: UploadFile = File(...)):
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

    # def on_upload_success(result_dict: dict):
    #     if result_dict.get('status', '').lower() != 'success':
    #         return
    #     result = result_dict.get('result')
    #     print(json.dumps(result))
    #     with database:
    #         upload_result = UploadResult(upload=upload, data=json.dumps(result))
    #         upload_result.save()

    task = celery_main.process_upload.apply_async(args=[upload.get_id()], expires=60 * 10)
    result.data = {'task_id': str(task.id)}
    return result


@app.get('/task_status')
@return_error_response
async def task_status(request: Request, task_id: str) -> ResponseModel:
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


def make_upload_response(upload: Upload, base_url: str) -> ResponseModel:
    # verify skip
    result = ResponseModel()
    base_url = str(base_url)
    upload_date: datetime.datetime = upload.upload_date
    with database:
        blob: Blob = upload.blob
    blob_address = blob.blob_address
    extras = {}
    if upload.latest_result is not None:
        extra_item = {
            'class_name': str(upload.latest_result.class_name),
            'familiars': [blob_url(base_url, x) for x in upload.latest_result.familiars],
        }
        extras['detection'] = extra_item
    result.data = {
        'upload_id': upload.get_id(),
        'upload_date': upload_date.strftime('%d.%m.%Y %H:%M:%S'),
        'url': blob_url(base_url, blob),
        'extras': extras,
    }
    return result


def blob_url(base_url: str, blob: Blob) -> str:
    blob_id1, blob_id2 = blob.blob_address
    return f"{str(base_url).removesuffix(r'/')}/storage/blobs/{blob_id1}/{blob_id2}"


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
    return fastapi.responses.JSONResponse(make_upload_response(upload, str(request.base_url)).dict)


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


def main():
    create_models()
    create_folders()
    threading.Thread(target=features_load_blobs, daemon=True).start()
    threading.Thread(target=find_trash_items, kwargs={'verbose': True}, daemon=True).start()
    port = 8102
    logger.info(f"Access: http://127.0.0.1:{port}")
    uvicorn.run(app, host="0.0.0.0", port=8102)


if __name__ == "__main__":
    main()

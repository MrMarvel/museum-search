import json
import os
import pathlib
import secrets
import threading

import fastapi
import peewee
import uvicorn
from celery.result import AsyncResult
from fastapi import FastAPI, UploadFile, File, Request
from loguru import logger
from starlette.responses import JSONResponse

import celery_main
from models import Upload, create_models, database, Blob, BlobContainer
from pydantic_models import ResponseModel
from utils import *
from utils.file_utils import create_folders, features_load_blobs, find_trash_items

app = FastAPI()


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

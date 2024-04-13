import asyncio
import datetime
from functools import wraps

import fastapi
from loguru import logger
from starlette.responses import JSONResponse

from services.backend.models import Upload, database, Blob
from services.backend.pydantic_models import ResponseModel


def make_upload_model(upload: Upload, base_url: str) -> ResponseModel:
    # verify skip
    result = ResponseModel()
    base_url = str(base_url)
    upload_date: datetime.datetime = upload.upload_date
    with database:
        blob: Blob = upload.blob
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

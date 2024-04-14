import datetime
import json
from typing import Union

from peewee import ForeignKeyField, TextField, DateTimeField, CharField

from .base import BaseModel, database
from .blob import Blob


class Upload(BaseModel):
    blob = ForeignKeyField(Blob)
    upload_date = DateTimeField(default=datetime.datetime.now)
    task_id = CharField(null=True)
    webhook_url = CharField(null=True)

    def resolve_filepath(self):
        return self.blob.resolve_path()

    @property
    def latest_result(self) -> Union['UploadResult', None]:
        u: 'UploadResult' = (UploadResult.select().where(UploadResult.upload == self)
                             .order_by(UploadResult.result_date.desc())
                             .get_or_none())
        return u


class UploadResult(BaseModel):
    upload = ForeignKeyField(Upload, backref='results')
    data = TextField()
    result_date = DateTimeField(default=datetime.datetime.now)

    @property
    def familiars(self) -> list[Blob]:
        data = json.loads(str(self.data))
        familiar_blobs_ids: list = data['familiar_images']
        blobs = []
        for i, blob_id in enumerate(familiar_blobs_ids):
            with database:
                blob: Blob | None = Blob.get_by_id(blob_id)
            if blob is None:
                continue
            blobs.append(blob)
        return blobs

    @property
    def class_name(self) -> str:
        return json.loads(str(self.data))['class_name']

    @property
    def description(self) -> str:
        return json.loads(str(self.data))['description']
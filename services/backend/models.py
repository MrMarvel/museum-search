import datetime
import json
import os
import pathlib
import secrets
from typing import Union

from peewee import *

DATABASE_FILENAME = os.environ.get('DATABASE_FILENAME', 'data.db')

database = SqliteDatabase(DATABASE_FILENAME)


# model definitions
class BaseModel(Model):
    class Meta:
        database = database


class BlobContainer(BaseModel):
    hex_id = CharField(default=lambda: secrets.token_hex(8)[:5])
    folder_path = CharField()
    name = CharField(default='untitled')
    creation_date = DateTimeField(default=datetime.datetime.now)

    def __init__(self, folder_path=None, hex_id=None, name=None, creation_date=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if folder_path is not None:
            self.folder_path = str(folder_path)
            self.name = str(pathlib.Path(folder_path))
        if hex_id is not None:
            self.hex_id = hex_id
        if name is not None:
            self.name = str(name)
        if creation_date is not None:
            self.creation_date = creation_date

    @staticmethod
    def get_by_name(name) -> Union['BlobContainer', None]:
        return BlobContainer.get_or_none(BlobContainer.name == name)

    @staticmethod
    def get_by_folder_path(folder_path) -> Union['BlobContainer', None]:
        path = pathlib.Path(folder_path)
        return BlobContainer.get_or_none(BlobContainer.folder_path == str(path))


class Blob(BaseModel):
    container = ForeignKeyField(BlobContainer, backref='blobs')
    hex_id = CharField(default=lambda: secrets.token_hex(8)[:5])
    file_path = CharField()
    creation_date = DateTimeField(default=datetime.datetime.now)

    def __init__(self, container: BlobContainer = None, file_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if container is not None:
            self.container = container
        if file_path is not None:
            self.file_path = str(file_path)

    @staticmethod
    def get_blob_by_hex(hex_folder, hex_blob) -> Union['Blob', None]:
        container = BlobContainer.select().where(BlobContainer.hex_id == hex_folder).get_or_none()
        blob = Blob.select().where(Blob.container == container, Blob.hex_id == hex_blob).get_or_none()
        return blob

    @staticmethod
    def get_blob_by_path_in_container(container: BlobContainer, path: str) -> Union['Blob', None]:
        f_path = str(pathlib.Path(path))
        return Blob.select().where(Blob.container == container, Blob.file_path == f_path).get_or_none()

    def resolve_path(self) -> str:
        return str(pathlib.Path(str(self.container.folder_path)) / self.file_path)

    @property
    def filename(self):
        return pathlib.Path(str(self.file_path)).name

    @property
    def blob_address(self) -> tuple[str, str]:
        return str(self.container.hex_id), str(self.hex_id)


class Upload(BaseModel):
    blob = ForeignKeyField(Blob)
    upload_date = DateTimeField(default=datetime.datetime.now)

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


def create_models():
    database.connect()
    database.create_tables([BlobContainer, Blob], safe=True)
    database.create_tables([Upload, UploadResult], safe=True)
    database.close()


def main():
    u = Upload(filepath='test.jpg')
    print(json.dumps(u))


if __name__ == '__main__':
    main()

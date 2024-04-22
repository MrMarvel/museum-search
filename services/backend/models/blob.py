import datetime
import pathlib
import secrets
from typing import Union

import peewee
from peewee import CharField, DateTimeField, ForeignKeyField

from .base import BaseModel


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
        try:
            blob = Blob.select().where(Blob.container == container, Blob.hex_id == hex_blob).get_or_none()
            return blob
        except peewee.DoesNotExist:
            return None

    @staticmethod
    def get_blob_by_path_in_container(container: BlobContainer, path: str) -> Union['Blob', None]:
        if container is None:
            raise ValueError("container must be provided")
        f_path = str(pathlib.Path(path))
        try:
            return Blob.select().where(Blob.container == container, Blob.file_path == f_path).get_or_none()
        except peewee.DoesNotExist:
            return None

    def resolve_path(self) -> str:
        return str(pathlib.Path(str(self.container.folder_path)) / self.file_path)

    @property
    def filename(self):
        return pathlib.Path(str(self.file_path)).name

    @property
    def blob_address(self) -> tuple[str, str]:
        return str(self.container.hex_id), str(self.hex_id)
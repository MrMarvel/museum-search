import datetime
import json
import os
import pathlib
import secrets
from typing import Union

from peewee import *

# limit public usage

__all__ = ['BlobContainer', 'Blob', 'Upload', 'UploadResult', 'database', 'create_models']

from models.base import database
from models.blob import BlobContainer, Blob
from models.upload import Upload, UploadResult


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

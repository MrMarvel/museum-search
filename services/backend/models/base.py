import os
import pathlib

from peewee import Model, SqliteDatabase

database_folder = pathlib.Path(__file__).parent.parent / 'tmp'
if not database_folder.exists():
    os.makedirs(database_folder)
DATABASE_FILENAME = os.environ.get('DATABASE_FILENAME', database_folder / 'data.db')

database = SqliteDatabase(DATABASE_FILENAME)


class BaseModel(Model):
    class Meta:
        database = database

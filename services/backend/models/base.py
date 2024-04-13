import os

from peewee import Model, SqliteDatabase

DATABASE_FILENAME = os.environ.get('DATABASE_FILENAME', 'data.db')

database = SqliteDatabase(DATABASE_FILENAME)


class BaseModel(Model):
    class Meta:
        database = database

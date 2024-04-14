import os
import pathlib

BACKEND_FOLDER = pathlib.Path(__file__).parent.parent.absolute()

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', BACKEND_FOLDER / 'uploads')
FAMILIARS_FOLDER = os.environ.get('FAMILIARS_FOLDER', BACKEND_FOLDER / 'familiars')
DEFAULT_WEBHOOK_URL = os.environ.get('DEFAULT_WEBHOOK_URL', 'http://localhost:8000/webhook')

ENV_FILENAME = os.environ.get('ENV_FILENAME', '.env')
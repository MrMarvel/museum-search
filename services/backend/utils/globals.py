import os

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
FAMILIARS_FOLDER = os.environ.get('FAMILIARS_FOLDER', './familiars')
DEFAULT_WEBHOOK_URL = os.environ.get('DEFAULT_WEBHOOK_URL', 'http://localhost:8000/webhook')
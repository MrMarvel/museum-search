import os
import tempfile
from pathlib import Path
from threading import Lock

import requests
import uvicorn
from dotenv import dotenv_values
from fastapi import FastAPI, UploadFile
from fastapi.params import Body
from loguru import logger

from rabbit import RabbitConnector, RabbitPublisher

from .util import TempFolder, VideoConsumerThread


def load_folder_envs(env_path):
    d = dict(dotenv_values(env_path))
    temp_folder_name = d['TEMP_FOLDER']
    storage_folder = d['STORAGE_FOLDER']
    return storage_folder, temp_folder_name

tmp_folder = os.path.join(*load_folder_envs('configs/folder.env'))
tmp_path = TempFolder(tmp_folder)

app = FastAPI(
    docs_url='/api/docs',
    on_startup=[tmp_path.make_folder],
    on_shutdown=[tmp_path.delete_folder],
)

callback_map = {}
check_lock = Lock()

con = RabbitConnector()
connection, channel, input_queue, output_queue = con.connect()
publisher = RabbitPublisher(channel, connection, output_queue)
web_server_api_send_video_url = os.environ.get('WEBSITE_URL').rstrip('/') + '/loadVideo'


def send_processed_file(file, upload_id: int):
    with open(file, 'rb') as f:
        result = requests.post(
            web_server_api_send_video_url,
            files={'file': f},
            data={'upload_id': str(upload_id)},
            timeout=10
        )
        logger.info(f'Sent processed video to web server with {result.text}')


@app.post('/api/upload_file')
async def upload_file(
    file: UploadFile,
    upload_id: int = Body(embed=True),
    quality_upgrade: bool = Body(embed=True),
    generate_comments: bool = Body(embed=True)
):
    if file is None:
        return 'Не выбран файл'
    if upload_id is None or upload_id < 0:
        return 'Не указан или неверно введён upload_id'

    file_suffix = Path(file.filename).suffix
    tmp_filename = tempfile.mktemp(dir=tmp_folder, suffix=file_suffix)
    buffered_file = file.file
    with open(tmp_filename, 'wb') as f:
        f.write(buffered_file.read())
    try:
        with check_lock:
            callback_map[upload_id] = {
                'callback': lambda ready_file: send_processed_file(ready_file, upload_id),
                'path': tmp_filename
            }
        
        publisher.publish(tmp_filename, upload_id)
    except Exception as e:
        logger.error(f'Error: {e}')
        return 'failed'
    return 'success'

if __name__ == "__main__":
    video_processed_get_thread = VideoConsumerThread(con, check_lock, callback_map).start()
    uvicorn.run(app, host="0.0.0.0", port=80)
import os
import pathlib

from loguru import logger

from models import database, BlobContainer, Blob
from utils.globals import UPLOAD_FOLDER, FAMILIARS_FOLDER


def create_folders():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(FAMILIARS_FOLDER):
        os.makedirs(FAMILIARS_FOLDER)
        with open(pathlib.Path(FAMILIARS_FOLDER) / 'README.txt', 'w', encoding='utf-8') as f:
            f.write('You should place IMAGE DATASET in that folder.\n'
                    'The dataset should be in the following format:\n'
                    'uploads/im1.jpg\n'
                    'uploads/im2.png\n'
                    '...')
    mounts = [UPLOAD_FOLDER, FAMILIARS_FOLDER]
    for mount in mounts:
        mount_path = pathlib.Path(mount)
        with database:
            if not BlobContainer.select().where(BlobContainer.folder_path == str(mount_path)).exists():
                BlobContainer.create(folder_path=str(mount_path))


def find_trash_items(verbose=False):
    if verbose:
        logger.info("Searching for trash items")
    files_list = []
    files_to_remove = []
    with database:
        containers: list[BlobContainer] = list(BlobContainer.select())

    for container in containers:
        with database:
            blobs: list[Blob] = container.__getattribute__('blobs')
        for blob in blobs:
            files_list.append(pathlib.Path(container.folder_path) / blob.file_path)
    for file in files_list:
        if not file.exists():
            if verbose:
                logger.info(f"Found {file}")
            files_to_remove.append(file)
    # if os.path.exists(UPLOAD_FOLDER):
    #     for file in os.listdir(UPLOAD_FOLDER):
    #         file_path = pathlib.Path(UPLOAD_FOLDER) / file
    #         if file_path not in files_list:
    #             if verbose:
    #                 print(f"Found {file_path}")
    #             files_to_remove.append(file_path)
    return files_to_remove


def features_load_blobs():
    with database:
        container = BlobContainer.get_by_folder_path(FAMILIARS_FOLDER)
        blobs: list[Blob] = container.__getattribute__('blobs')
    logger.info("Loading new blobs")
    new_blobs = []
    blobs_paths = [b.file_path for b in blobs]
    for path in pathlib.Path(FAMILIARS_FOLDER).rglob('*'):
        try:
            if path.is_dir():
                continue
            relative_path = path.relative_to(FAMILIARS_FOLDER)
            if str(relative_path) in blobs_paths:
                continue
            logger.info(f"Found new Blob {path}. Adding")
            blob = Blob(file_path=relative_path, container=container)
            new_blobs.append(blob)
        except Exception as e:
            logger.exception(e)
    if len(new_blobs) > 0:
        with database:
            Blob.bulk_create(new_blobs, batch_size=10)
        logger.info("Finished loading new blobs")
    else:
        logger.info("No new blobs found")
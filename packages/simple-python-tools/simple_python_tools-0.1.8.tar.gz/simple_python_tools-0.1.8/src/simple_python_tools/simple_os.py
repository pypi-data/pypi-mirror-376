import os
from . import simple_logger as logger

def generate_if_not_exists(path: str):
    if not os.path.exists(path):
        logger.info(f'Path {path} not found, creating...')
        os.makedirs(path)
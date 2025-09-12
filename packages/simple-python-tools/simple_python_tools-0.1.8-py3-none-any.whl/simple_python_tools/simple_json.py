import os
import json

from . import simple_os

def save_json(j, path: str):
    directory = os.path.dirname(path)
    simple_os.generate_if_not_exists(directory)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False, indent=4)

def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

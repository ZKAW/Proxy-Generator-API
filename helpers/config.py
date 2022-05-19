import json
import os

from pathlib import Path

# Define working directory
workspace = os.path.dirname(os.path.realpath(__file__))
workspace = str(Path(workspace).parent)

def load_config():
    with open(os.path.join(workspace,"config.json"), 'r') as json_data:
        conf = json.load(json_data)
    return conf

conf = load_config()
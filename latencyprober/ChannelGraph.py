import json


def load_graph(path: str):
    with open(path) as f:
        return json.load(f)
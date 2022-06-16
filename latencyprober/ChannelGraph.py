import json


def load_graph(path: str):
    with open(path) as f:
        return json.load(f)


class Node(dict):
    """
    Convenience class for accessing node data in the LND channel graph.
    """

    def __init__(self, node_info):
        self.update(node_info)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

class Channel(dict):
    """
    Convenience class for accessing channel data in the LND channel graph.
    """

    def __init__(self, channel_info):
        self.update(channel_info)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

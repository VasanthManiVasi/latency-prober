import random

def generate_hops(pub_key, channel_graph, depth):
    if depth <= 1:
        return [pub_key]
    channels = list(channel_graph.getchannels(pub_key).keys())
    return [pub_key] + generate_hops(random.choice(channels), channel_graph, depth-1)

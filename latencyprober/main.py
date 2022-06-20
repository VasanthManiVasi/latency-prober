from ChannelGraph import load_graph, ChannelGraph
from rpc import *
from route import *
from utils import *
import urllib.request
import json

CURRENT_NODE_PUBKEY = get_info().identity_pubkey
GRAPH_PATH = "../lnd8.json"

def initialize():
    node_info = to_dict(get_node_info(
        pub_key=CURRENT_NODE_PUBKEY,
        include_channels=True,
    ))

    ip = urllib.request.urlopen('http://jsonip.com').read()
    ip = json.loads(ip)['ip'] + ':9375'
    ip_address = [{'network': 'tcp', 'addr': ip}]
    node_info['node']['addresses'] = ip_address
    geolocation = geolocate(ip_address[0])

    graph_json = load_graph(GRAPH_PATH)
    graph_json['nodes'].append(node_info['node'])
    channel_graph = ChannelGraph(json=graph_json)

    local_channel_distances = {}
    for channel in list_channels():
        dest = channel_graph.get_node(channel.remote_pubkey)
        distance = geodistance(geolocation, dest.geolocation)
        local_channel_distances[channel.remote_pubkey] = distance

    return channel_graph, local_channel_distances

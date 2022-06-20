import csv
import json
import urllib.request

from rpc import *
from route import *
from utils import *

from ChannelGraph import load_graph, ChannelGraph

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

def extract_result(payment_hash, hops, path_distance, sendroute_response):
    return {
        'payment_hash': payment_hash,
        'start_channel': hops[0],
        'num_hops': len(hops),
        'hops': '->'.join(hops),
        'route_distance': path_distance,
        'round_trip_time': time_taken(sendroute_response)
    }

fieldnames = [
    'payment_hash',
    'start_channel',
    'num_hops',
    'hops',
    'route_distance',
    'round_trip_time',
]

filename = 'data.csv'

if not os.path.isfile(filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

channel_graph, local_channel_distances = initialize()

datas = []
while True:
    for chan in list_channels():
        print("At chan: {} ({})".format(
            chan.remote_pubkey,
            channel_graph.get_node(chan.remote_pubkey).alias
        ))

        num_hops = random.randint(1, 10)
        print('num_hops: {}'.format(num_hops))

        hops = generate_hops(chan.remote_pubkey, channel_graph, num_hops)
        print(*hops, sep=' -> ')

        path_distance = route_distance(hops, channel_graph, local_channel_distances)
        print("route distance: {}".format(path_distance))

        payment_hash = generate_payment_hash()
        print('payment_hash: {}'.format(payment_hash))

        sendroute_response = send_route(
            start_channel=chan,
            hops=hops,
            payment_hash=payment_hash,
            router=router,
            routerstub=routerstub
        )
        result = extract_result(payment_hash, hops, path_distance, sendroute_response)
        print('payment ended in {}s'.format(result['round_trip_time']))
        datas.append(result)

        if len(datas) > len(list_channels()):
            with open(filename, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                for data in datas:
                    writer.writerow(data)

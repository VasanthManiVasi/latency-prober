import csv
import json
import grpc
import urllib.request

from rpc import *
from route import *
from utils import *

from ChannelGraph import load_graph, ChannelGraph

CURRENT_NODE_PUBKEY = get_info().identity_pubkey
GRAPH_PATH = "../lnd8.json"

def initialize():
    ip = urllib.request.urlopen('http://jsonip.com').read()
    ip = json.loads(ip)['ip'] + ':9375'
    ip_address = [{'network': 'tcp', 'addr': ip}]
    geolocation = geolocate(ip_address[0])

    graph_json = load_graph(GRAPH_PATH)
    for node in graph_json['nodes']:
        if node['pub_key'] == CURRENT_NODE_PUBKEY:
            node['addresses'] = ip_address

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
attempt_count = 0
succeeded_count = 0

while True:
    for chan in list_channels():
        print("\nAttempt Count: {}\tSucceeded Count: {}".format(
            attempt_count,
            succeeded_count
        ))
        attempt_count += 1

        print("At chan: {} ({})".format(
            chan.remote_pubkey,
            channel_graph.get_node(chan.remote_pubkey).alias
        ))

        payment_hash = generate_payment_hash()
        num_hops = random.randint(1, 10)
        hops = generate_hops(chan.remote_pubkey, channel_graph, num_hops)
        print('payment_hash: {}'.format(payment_hash))
        print(*hops, sep=' -> ')
        print('num_hops: {}'.format(num_hops))

        path_distance = route_distance(hops, channel_graph, local_channel_distances)
        print("route distance: {}".format(path_distance))

        try:
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
            succeeded_count += 1

        except grpc.RpcError as rpc_error:
            details = rpc_error.details()
            status_code = rpc_error.code()
            if (status_code == grpc.StatusCode.DEADLINE_EXCEEDED):
                    print('Time limit exceeded for payment hash {}'.format(payment_hash))
            elif 'no matching outgoing channel' in details:
                print('Channel graph must be updated')
            else:
                raise grpc.RpcError(details) from rpc_error

        if len(datas) > len(list_channels()):
            print('Saving data to file')
            with open(filename, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                for data in datas:
                    writer.writerow(data)
                datas = []

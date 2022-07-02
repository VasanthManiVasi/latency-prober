import grpc
import json
import random
import urllib.request

from utils import *
from rpc import gRPC
from ChannelGraph import load_graph, ChannelGraph

AMOUNT = 1000
CLTV_DELTA = 20
TIMEOUT = 240
DEFAULT_LND_PORT = 9375

MIN_HOPS = 1
MAX_HOPS = 19

class LatencyProber:
    def __init__(self,
        channel_graph_json: dict = {},
        lnd_port: int = DEFAULT_LND_PORT
    ):
        self.grpc_obj = gRPC()
        self.pub_key = self.grpc_obj.get_info().identity_pubkey

        if not channel_graph_json:
            channel_graph_json = self.grpc_obj.describe_graph()

        # Add the address of our node to the channel graph
        for node in channel_graph_json['nodes']:
            if node['pub_key'] == self.pub_key:
                node['addresses'] = self._get_ip_address(lnd_port)

        channel_graph = ChannelGraph(json=channel_graph_json)
        self.channel_graph = channel_graph


    @classmethod
    def from_channel_graph_path(cls, channel_graph_path: str, lnd_port: int = DEFAULT_LND_PORT):
        channel_graph_json = load_graph(channel_graph_path)
        return cls(channel_graph_json, lnd_port)


    def send_to_route(self,
        start_channel,
        hops,
        payment_hash,
        amount=AMOUNT,
        final_cltv_delta=CLTV_DELTA
    ):
        try:
            sendroute_response = self.grpc_obj.send_to_route(
                amt_msat=amount,
                final_cltv_delta=final_cltv_delta,
                outgoing_chan_id=start_channel.chan_id,
                hop_pubkeys=[bytes.fromhex(hop) for hop in hops],
                payment_hash=bytes.fromhex(payment_hash)
            )

            results = self._extract_results(payment_hash, hops, sendroute_response)
            print('payment ended in {}s'.format(results['round_trip_time']))

            return results

        except grpc.RpcError as rpc_error:
            details = rpc_error.details()
            status_code = rpc_error.code()
            if (status_code == grpc.StatusCode.DEADLINE_EXCEEDED):
                print('Status for {} - Time limit exceeded'.format(payment_hash))
            elif 'no matching outgoing channel' in details:
                print('Status for {} - Channel graph must be updated'.format(payment_hash))
            else:
                raise grpc.RpcError(details) from rpc_error
            return


    def update_latency_information(self, results):
        path = results['hops'].split('->')
        num_hops = results['num_hops']
        round_trip_time = results['round_trip_time']

        print(*path, sep=' -> ')
        print('num_hops: {}'.format(num_hops))
        print("route distance: {}".format(results['route_distance']))

        time = 0.0
        current_node = self.pub_key
        i = 0
        for next_node in path:
            channel = self.channel_graph.get_channels(current_node)[next_node]

            if 'latency' not in channel:
                if i != num_hops-1:
                    raise ValueError("Tried to set latency for channel before previous channel latencies are set.")

                channel.latency = round_trip_time - time
                return {
                    'channel_id': channel.channel_id,
                    'geodistance': channel.geodistance,
                    'latency': channel.latency
                }

            current_node = channel.dest
            time += channel.latency
            i += 1


    def make_random_payment(self, start_channel):
        pub_key = start_channel.remote_pubkey
        print("\nAt chan: {} ({})".format(
            pub_key,
            self.channel_graph.get_node(pub_key).alias
        ))

        payment_hash, hops = self._prepare_random_payment(start_channel)
        route_distance = self.route_distance([self.pub_key] + hops)

        print('payment_hash: {}'.format(payment_hash))
        print(*hops, sep=' -> ')
        print('num_hops: {}'.format(len(hops)))
        print("route distance: {}".format(route_distance))

        return self.send_to_route(start_channel, hops, payment_hash)


    def _prepare_random_payment(self, start_channel, rand=random.Random()):
        payment_hash = generate_payment_hash(rand)
        num_hops = rand.randint(1, 19)
        hops = self.generate_hops(
            start_channel.remote_pubkey,
            num_hops,
            rand=rand
        )

        return (payment_hash, hops)


    def generate_hops(self,
        pub_key: str,
        depth: int = random.randint(MIN_HOPS, MAX_HOPS),
        rand=random.Random()
    ):
        if depth <= 1:
            return [pub_key]

        channels = list(self.channel_graph.get_channels(pub_key).keys())
        next_channel = rand.choice(channels)

        i = 0
        while next_channel not in self.channel_graph.channels :
            # Loop until we get a correct channel
            if i >= len(channels):
                return []
            next_channel = channels[i]
            i += 1

        return [pub_key] + self.generate_hops(next_channel, depth-1, rand=rand)


    def list_channels(self):
        channels = self.grpc_obj.list_channels()
        return [
            channel
            for channel in channels
            if channel.remote_pubkey in self.channel_graph.nodes
        ]

    def route_distance(self, hops):
        channels = self.channel_graph.get_channels(hops[0])
        distance = 0.0
        for next_hop in hops[1:]:
            distance += channels[next_hop]['geodistance']
            channels = self.channel_graph.get_channels(next_hop)
        return distance


    def route_time(self, sendroute_response):
        start_time = sendroute_response.attempt_time_ns
        end_time = sendroute_response.resolve_time_ns
        return (end_time - start_time) / 10**9


    def _get_ip_address(self, lnd_port: int = 9375):
        response = urllib.request.urlopen('http://jsonip.com').read()
        ip_address = json.loads(response)['ip'] + ':' + str(lnd_port)
        return [{'network': 'tcp', 'addr': ip_address}]


    def _extract_results(self, payment_hash, hops, sendroute_response):
        return {
            'payment_hash': payment_hash,
            'start_channel': hops[0],
            'num_hops': len(hops),
            'hops': '->'.join(hops),
            'route_distance': self.route_distance([self.pub_key] + hops),
            'round_trip_time': self.route_time(sendroute_response)
        }
import json
from .utils import geolocate

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

class ChannelGraph:
    def __init__(self, *, path=None, json=None):
        if path:
            json = load_graph(path)
        self.json = json

        self._nodes_json = json['nodes']
        self.nodes = {}

        for node in self._nodes_json:
            addresses = self.filter_invalid_addresses(node['addresses'])
            if not addresses:
                continue

            node['addresses'] = addresses
            geolocation = geolocate(addresses[0])
            if not geolocation:
                continue

            node['geolocation'] = geolocation
            self.nodes[node['pub_key']] = Node(node)

        self.num_nodes = len(self.nodes)

        self._channels_json = json['edges']

        # Maps from source node pub_key to destination pub_keys and their channels
        self.channels = {}

        for channel in self._channels_json:
            nodes = ['node1', 'node2']

            for i in range(len(nodes)):
                src_pubkey = channel[nodes[i] + '_pub']
                dest_pubkey = channel[nodes[i-1] + '_pub']

                if (src_pubkey not in self.nodes
                    or dest_pubkey not in self.nodes):
                    # One of the nodes have invalid address
                    # No channel will be added
                    break

                if (not channel[nodes[i]+'_policy']
                    or channel[nodes[i]+'_policy']['disabled'] is True):
                    # This side of the channel is disabled
                    continue

                # Setting source and dest pub_key for this channel
                channel = dict(channel)
                channel['source'] = src_pubkey
                channel['dest'] = dest_pubkey

                if src_pubkey not in self.channels:
                    self.channels[src_pubkey] = {dest_pubkey: Channel(channel)}
                else:
                    self.channels[src_pubkey][dest_pubkey] = Channel(channel)

        self.num_channels = len(self._channels_json)

    @staticmethod
    def is_onion(address):
        return True if 'onion' in address['addr'] else False

    @staticmethod
    def filter_invalid_addresses(addresses):
        ipv4, ipv6 = 0, 0
        new_addresses = []

        for address in addresses:
            if ChannelGraph.is_onion(address):
                if len(addresses) == 1:
                    # Contains only one onion address and no IP addresses
                    return []
            else:
                # Remove port
                addr = address['addr'][:address['addr'].rfind(':')]
                if ':' in addr:
                    ipv6 += 1
                else:
                    ipv4 += 1
                new_addresses.append(address)

        if ipv4 > 1 or ipv6 > 1:
            # More than one IPv4 or IPv6 address found
            return []

        return new_addresses

    def get_node(self, pubkey: str):
        return self.nodes[pubkey]

    def get_channels(self, pubkey: str):
        return self.channels[pubkey]

    def __repr__(self):
        return f'nodes: {self.num_nodes}\nchannels: {self.num_channels}'

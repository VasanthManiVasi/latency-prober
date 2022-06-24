import json
import networkx as nx

from utils import geolocate, node_distance

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
    """
    Represents the Lightning Network channel graph.

    Nodes and channels are filtered based on network address and announcement.
    """
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
        channels = {}

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
                channel['chan_id'] = int(channel['channel_id']) # Required for gRPC
                channel['geodistance'] = node_distance(
                    self.nodes[src_pubkey],
                    self.nodes[dest_pubkey]
                )

                if src_pubkey not in channels:
                    channels[src_pubkey] = {dest_pubkey: Channel(channel)}
                else:
                    channels[src_pubkey][dest_pubkey] = Channel(channel)

        self.num_channels = len(self._channels_json)
        self.channels = channels

        self.network = nx.MultiDiGraph()
        for source in channels:
            for channel in channels[source].values():
                self.network.add_edge(
                    channel.source, channel.dest, key=channel.channel_id, channel=channel)


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


    def generate_unique_paths(self, root_pubkey):
        def _get_path(dest, parent):
            if dest == 'root':
                return []
            return _get_path(parent[dest], parent) + [dest]

        paths = []
        parent = {root_pubkey: 'root'}
        for (src, dest, _) in nx.edge_bfs(self.network, root_pubkey):
            path = _get_path(src, parent)
            if dest not in parent:
                parent[dest] = src
            paths.append(path + [dest])

        # Ordering based on channels of the root node
        chan_to_paths_map = {}
        for path in paths:
            if path[1] not in chan_to_paths_map:
                chan_to_paths_map[path[1]] = [path]
            else:
                chan_to_paths_map[path[1]].append(path)
        ordered_paths = [channel_paths for channel_paths in chan_to_paths_map.values()]
        return ordered_paths


    def get_node(self, pubkey: str):
        return self.nodes[pubkey]


    def get_channels(self, pubkey: str):
        return self.channels[pubkey]


    def __repr__(self):
        return f'nodes: {self.num_nodes}\nchannels: {self.num_channels}'

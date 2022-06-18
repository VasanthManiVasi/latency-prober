from ChannelGraph import ChannelGraph, load_graph

def no_addresses(nodes):
    return [
        node
        for node in nodes
        if not node['addresses']
    ]

def onion_stats(nodes):
    stats = {
        'has_onion': 0,
        'has_only_onion': 0,
        'has_only_one_onion': 0,
        'has_more_than_one_onion': 0,
        'has_no_onion': 0
    }

    for node in nodes:
        onions = [addr for addr in node['addresses'] if ChannelGraph.is_onion(addr)]

        if not onions:
            stats['has_no_onion'] += 1
            continue

        if len(onions) >= 2:
            stats['has_more_than_one_onion'] += 1

        if len(onions) == len(node['addresses']):
            if len(node['addresses']) == 1:
                stats['has_only_one_onion'] += 1
            stats['has_only_onion'] += 1

        stats['has_onion'] += 1

    return stats

def ip_stats(nodes):
    stats = {
        'has_ip': 0,
        'has_only_ip': 0,
        'has_only_one_ip': 0,
        'has_more_than_one_ip': 0,
        'has_no_ip': 0
    }

    for node in nodes:
        ipv4, ipv6 = 0, 0
        ip_addresses = [
            addr['addr'][:addr['addr'].rfind(':')] # Removing port
            for addr in node['addresses']
            if not ChannelGraph.is_onion(addr)
        ]

        if not ip_addresses:
            stats['has_no_ip'] += 1
            continue

        for addr in ip_addresses:
            if ':' in addr:
                ipv6 += 1
            else:
                ipv4 += 1

        if len(ip_addresses) == len(node['addresses']):
            stats['has_only_ip'] += 1

        if ipv4 <= 1 and ipv6 <= 1:
            stats['has_only_one_ip'] += 1
        else:
            stats['has_more_than_one_ip'] += 1

        stats['has_ip'] += 1

    return stats

if __name__ == '__main__':
    lnd_json = load_graph("../describegraph.json")

    total_nodes = len(lnd_json['nodes'])
    print('total nodes:', total_nodes)

    G = ChannelGraph(json=lnd_json)
    print('filtered nodes:', total_nodes - G.num_nodes)

    ipstats = ip_stats(lnd_json['nodes'])
    assert G.num_nodes == ipstats['has_only_one_ip']

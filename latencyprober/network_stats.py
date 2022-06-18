from ChannelGraph import ChannelGraph

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

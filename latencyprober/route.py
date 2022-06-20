import random

AMOUNT = 1000
CLTV_DELTA = 20
TIMEOUT = 120

def generate_hops(pub_key, channel_graph, depth):
    if depth <= 1:
        return [pub_key]
    channels = list(channel_graph.get_channels(pub_key).keys())
    return [pub_key] + generate_hops(random.choice(channels), channel_graph, depth-1)

def send_route(start_channel, hops, payment_hash, router, routerstub):
    buildroute_request = router.BuildRouteRequest(
        amt_msat=AMOUNT,
        final_cltv_delta=CLTV_DELTA,
        outgoing_chan_id=start_channel.chan_id,
        hop_pubkeys=[bytes.fromhex(hop) for hop in hops]
    )
    route = routerstub.BuildRoute(buildroute_request).route

    sendroute_request = router.SendToRouteRequest(
        payment_hash=bytes.fromhex(payment_hash),
        route=route
    )

    sendroute_response = routerstub.SendToRouteV2(sendroute_request, timeout=TIMEOUT)
    return payment_hash, sendroute_response

def route_distance(hops, channel_graph, local_channel_distances=None):
    chan = channel_graph.get_channels(hops[0])
    distance = 0.0 if not local_channel_distances else local_channel_distances[hops[0]]
    for hop in hops[1:]:
        distance += chan[hop]['geodistance']
        chan = channel_graph.get_channels(hop)
    return distance

def time_taken(sendroute_response):
    return (sendroute_response.resolve_time_ns - sendroute_response.attempt_time_ns) / 10**9
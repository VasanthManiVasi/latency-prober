import random

AMOUNT = 1000
CLTV_DELTA = 20

def generate_hops(pub_key, channel_graph, depth):
    if depth <= 1:
        return [pub_key]
    channels = list(channel_graph.get_channels(pub_key).keys())
    return [pub_key] + generate_hops(random.choice(channels), channel_graph, depth-1)

def send_route(start_channel, hops, router, routerstub):
    buildroute_request = router.BuildRouteRequest(
        amt_msat=AMOUNT,
        final_cltv_delta=CLTV_DELTA,
        outgoing_chan_id=start_channel.chan_id,
        hop_pubkeys=[bytes.fromhex(hop) for hop in hops]
    )

    route = routerstub.BuildRoute(buildroute_request).route
    payment_hash = hex(random.getrandbits(256))[2:]

    sendroute_request = router.SendToRouteRequest(
        payment_hash=bytes.fromhex(payment_hash),
        route=route
    )

    sendroute_response = routerstub.SendToRouteV2(sendroute_request)

    return payment_hash, sendroute_response

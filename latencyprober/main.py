from datetime import datetime

from itertools import chain, zip_longest
from LatencyProber import LatencyProber
from utils import generate_payment_hash, CSVWriter

results_filename = f'results {str(datetime.now())}.csv'
results_fieldnames = [
    'payment_hash',
    'start_channel',
    'num_hops',
    'hops',
    'route_distance',
    'round_trip_time',
]

latency_filename = f'channel_latency_data {str(datetime.now())}.csv'
latency_fieldnames = [
    'channel_id',
    'geodistance',
    'latency'
]

latency_prober = LatencyProber()
result_writer = CSVWriter(results_filename, results_fieldnames)
latency_writer = CSVWriter(latency_filename, latency_fieldnames)

# Deterministic search - stores latency information of each channels in the channel graph
paths = latency_prober.channel_graph.generate_unique_paths(latency_prober.pub_key)
paths = list(filter(None, chain.from_iterable(zip_longest(*paths))))
for path in paths:
    start_channel = latency_prober.channel_graph.get_channels(path[0])[path[1]]
    result = latency_prober.send_to_route(start_channel, path[1:], generate_payment_hash())
    if result:
        latency_information = latency_prober.update_latency_information(result)
        result_writer.write(result)
        latency_writer.write(latency_information)

# Random search - for additional data points
while True:
    data = []
    channels = latency_prober.grpc_obj.list_channels()
    for channel in channels:
        result = latency_prober.make_random_payment(channel)
        if result:
            data.append(result)

    result_writer.write_data(data)
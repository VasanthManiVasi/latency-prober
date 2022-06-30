import datetime
import os
import time
import threading

from itertools import chain, zip_longest

from Queue import Queue
from LatencyProber import LatencyProber
from utils import generate_payment_hash, CSVWriter

current_time = str(datetime.datetime.now())
results_filename = f'results {current_time}.csv'
results_fieldnames = [
    'payment_hash',
    'start_channel',
    'num_hops',
    'hops',
    'route_distance',
    'round_trip_time',
]

latency_filename = f'channel_latency_data {current_time}.csv'
latency_fieldnames = [
    'channel_id',
    'geodistance',
    'latency'
]


def path_producer(latency_prober: LatencyProber, path_queue: Queue):
    # Deterministic path generation to obtain the latency information of each channel in the channel graph
    paths = latency_prober.channel_graph.generate_unique_paths(latency_prober.pub_key)
    paths = list(filter(None, chain.from_iterable(zip_longest(*paths))))
    for (i, path) in enumerate(paths):
        if i % 100 == 0:
            print(f"Pushing path #{i}: {path}")
        path_queue.put(path)

    print("Starting random search...")
    path_queue.random_search_start()

    # Random path generation for additional data points
    while True:
        channels = latency_prober.list_channels()
        for channel in channels:
            path = latency_prober.generate_hops(channel.remote_pubkey)
            path_queue.put([latency_prober.pub_key] + path)


def worker(latency_prober: LatencyProber, path_queue: Queue, result_writer: CSVWriter):
    determinstic_paths_exhausted = False

    while True:
        path = path_queue.get()

        if path is None:
            # All unique routes from a channel has been explored.
            # Pause this worker until random search starts

            if not determinstic_paths_exhausted:
                # Make sure a channel has been fully explored by checking again
                determinstic_paths_exhausted = True
                time.sleep(2)
                continue

            path_queue.wait_for_random_search_start()

        start_channel = latency_prober.channel_graph.get_channels(path[0])[path[1]]
        result = latency_prober.send_to_route(
            start_channel,
            path[1:],
            generate_payment_hash()
        )

        if result:
            # latency_information = latency_prober.update_latency_information(result)
            result_writer.write(result)
            # latency_writer.write(latency_information)

        path_queue.release(path[1]) # Free up the channel to be routed through again

        if determinstic_paths_exhausted:
            determinstic_paths_exhausted = False


print("Setting up latency prober...")
latency_prober = LatencyProber()


channels = latency_prober.list_channels()
num_threads = min(os.cpu_count() - 1, len(channels))

path_queue = Queue(num_threads)

print("Initializing writers...")
result_writer = CSVWriter(results_filename, results_fieldnames)

print("Launching producer thread...")
# Launch producer thread
producer_thread = threading.Thread(
    target=path_producer,
    args=(latency_prober, path_queue)
)
producer_thread.start()

time.sleep(3)
print("Launching worker threads...")
# Launch worker threads
worker_threads = []
for _ in range(num_threads):
    thread = threading.Thread(
        target=worker,
        args=(latency_prober, path_queue, result_writer)
    )
    worker_threads.append(thread)
    thread.start()

print("All threads launched. Joining producer thread...")
producer_thread.join()
for thread in worker_threads:
    thread.join()
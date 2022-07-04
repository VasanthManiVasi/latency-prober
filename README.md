# Latency Prober

Python tool for creating the geodistance-latency dataset.

Manages an LND node for sending payments with invalid payment hashes to nodes in the network using the gRPC API and stores the round-trip time and geographical distances of the paths.

## Setup

#### Installing dependencies
The following dependencies are required to run the tool.
* gRPC
* GeoIP2
* GeoPy

Install them with:
```bash
$ pip install -r requirements.txt
```

#### IP-Geolocation DB
Download the IP to Geolocation database from [db-ip.com](https://db-ip.com/db/download/ip-to-city-lite)
```bash
$ wget https://download.db-ip.com/free/dbip-city-lite-2022-06.mmdb.gz
$ gunzip dbip-city-lite-2022-06.mmdb.gz
```

# Usage
Run the tool with:
```bash
$ python main.py
```
The data will be saved to `results {time_of_launch}.csv`

# Obtaining data points
1. Convert IP to geolocation for nodes
2. Calculate and store channel distances in the channel graph
3. Generate a path with different distances from the graph
4. Build LN Route
5. Send payment with invalid payment hash for the route
6. Measure and store roundtrip-time data

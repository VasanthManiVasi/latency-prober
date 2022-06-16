# Latency Prober

Python tool for creating the geodistance-latency dataset.

Manages an LND node for sending payments with invalid payment hashes to nodes in the network using the gRPC API and stores the round-trip time and geographical distances of the paths.

## Obtaining a single data point
1. Convert IP to geolocation for nodes
2. Calculate and store channel distances in the channel graph
3. Generate a path with different distances from the graph
4. Build LN Route
5. Send payment with invalid payment hash for the route
6. Measure and store roundtrip-time data

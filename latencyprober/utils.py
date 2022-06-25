import os
import csv
import random
import geoip2
import geoip2.database as db

from geopy.distance import geodesic
from google.protobuf.json_format import MessageToDict

geoip = db.Reader('dbip-city-lite-2022-06.mmdb')

class CSVWriter:
    def __init__(self, filename, fieldnames):
        self.filename = filename
        self.fieldnames = fieldnames

        if not os.path.isfile(filename):
            with open(filename, 'w', newline='') as f:
                csv.DictWriter(f, fieldnames=fieldnames).writeheader()


    def write(self, row):
        with open(self.filename, 'a', newline='') as f:
            csv.DictWriter(f, fieldnames=self.fieldnames).writerow(row)


    def write_data(self, data):
        with open(self.filename, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            for row in data:
                writer.writerow(row)


def geolocate(ip_address):
    try:
        addr = ip_address['addr']
        # Remove port
        addr = addr[:addr.rfind(':')]
        if ':' in addr and addr[0] == '[' and addr[-1] == ']':
            # Remove brackets around the IPv6 address
            addr = addr[1:-1]

        location = geoip.city(addr).location

    except geoip2.errors.AddressNotFoundError:
        return None

    return location.latitude, location.longitude


def geodistance(llpair1, llpair2):
    return geodesic(llpair1, llpair2).km


def node_distance(node1, node2):
    return geodesic(node1.geolocation, node2.geolocation).km


def to_dict(rpc_response):
    return MessageToDict(rpc_response, preserving_proto_field_name=True)


def generate_payment_hash(random=random.Random()):
    return hex(random.getrandbits(256))[2:].zfill(64)
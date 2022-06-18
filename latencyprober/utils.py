import geoip2
import geoip2.database as db

geoip = db.Reader('dbip-city-lite-2022-06.mmdb')

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

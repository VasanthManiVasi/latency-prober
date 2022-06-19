import os
import grpc
import codecs
import lightning_pb2 as ln
import lightning_pb2_grpc as lnrpc
import router_pb2 as router
import router_pb2_grpc as routerrpc

os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

with open(os.path.expanduser('~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon'), 'rb') as f:
    macaroon_bytes = f.read()
    macaroon = codecs.encode(macaroon_bytes, 'hex')

def metadata_callback(context, callback):
    callback([('macaroon', macaroon)], None)

cert = open(os.path.expanduser('~/.lnd/tls.cert'), 'rb').read()
cert_creds = grpc.ssl_channel_credentials(cert)
auth_creds = grpc.metadata_call_credentials(metadata_callback)
combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)

channel = grpc.secure_channel('localhost:10009', combined_creds)
stub = lnrpc.LightningStub(channel)
rstub = routerrpc.RouterStub(channel)

import os
import grpc
import codecs
import lightning_pb2 as ln
import lightning_pb2_grpc as lnrpc
import router_pb2 as router
import router_pb2_grpc as routerrpc

from utils import to_dict

os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

# gRPC request time out in seconds
TIMEOUT = 240

MAX_MESSAGE_LENGTH = 1024 * 1024 * 100
GRPC_OPTIONS = [
    ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)
]

class gRPC:
    def __init__(self,
        macaroon_path: str = '~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon',
        tls_path: str = '~/.lnd/tls.cert',
        grpc_address: str = 'localhost:10009',
        timeout: int = TIMEOUT,
        grpc_options: list = GRPC_OPTIONS
    ):
        with open(os.path.expanduser(macaroon_path), 'rb') as f:
            macaroon_bytes = f.read()
            self.macaroon = codecs.encode(macaroon_bytes, 'hex')

        def _metadata_callback(context, callback):
            callback([('macaroon', self.macaroon)], None)

        cert = open(os.path.expanduser(tls_path), 'rb').read()
        cert_creds = grpc.ssl_channel_credentials(cert)
        auth_creds = grpc.metadata_call_credentials(_metadata_callback)
        combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)

        self.channel = grpc.secure_channel(grpc_address, combined_creds, grpc_options)
        self.ln_stub = lnrpc.LightningStub(self.channel)
        self.router_stub = routerrpc.RouterStub(self.channel)
        self.timeout = timeout


    def send_to_route(self,
        amt_msat: int,
        final_cltv_delta: int,
        outgoing_chan_id: int,
        hop_pubkeys: list[bytes],
        payment_hash: bytes
    ):
        buildroute_request = router.BuildRouteRequest(
            amt_msat=amt_msat,
            final_cltv_delta=final_cltv_delta,
            outgoing_chan_id=outgoing_chan_id,
            hop_pubkeys=hop_pubkeys
        )
        route = self.router_stub.BuildRoute(buildroute_request).route

        sendroute_request = router.SendToRouteRequest(
            payment_hash=payment_hash,
            route=route
        )

        sendroute_response = self.router_stub.SendToRouteV2(
            sendroute_request,
            timeout=self.timeout
        )
        return sendroute_response


    def describe_graph(self):
        return to_dict(self.ln_stub.DescribeGraph(ln.ChannelGraphRequest()))


    def get_info(self):
        return self.ln_stub.GetInfo(ln.GetInfoRequest())


    def get_node_info(self, pub_key, include_channels):
        return self.ln_stub.GetNodeInfo(ln.NodeInfoRequest(
            pub_key=pub_key,
            include_channels=include_channels
        ))


    def list_channels(self, active_only=True, public_only=True):
        request = ln.ListChannelsRequest(
            active_only=active_only,
            public_only=public_only
        )
        response = self.ln_stub.ListChannels(request)
        return response.channels


if __name__ == '__main__':
    grpc_obj = gRPC()
    print(*[channel.remote_pubkey for channel in grpc_obj.list_channels()], sep='\n')

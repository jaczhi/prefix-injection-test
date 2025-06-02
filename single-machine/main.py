import asyncio
import os
import signal
import sys
import argparse
from typing import Optional
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.security import NullSigner
from ndn.transport.udp_face import UdpFace
from ndn.encoding import BinaryStr, FormalName, Component, Signer, Name
from prefix_insertion_client import insert_prefix # Assuming this is your custom module
from cert_util import get_signer_from_ndnd_key, parse_ndnd_cert # Assuming this is your custom module

app: Optional[NDNApp] = None

def handle_signal(signal_num, frame) -> None:
    print()
    print('Ctrl-C, stopping')

    if app is not None:
        app.shutdown()
        print('App shut down')

    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal)

    parser = argparse.ArgumentParser(description="NDN Application with Prefix Insertion")
    parser.add_argument(
        '--port',
        type=int,
        default=6363,
        help='UDP port number to listen on (default: 6363)'
    )
    parser.add_argument(
        '--also-register',
        action='store_true',
        default=False,
        help='Also register the prefix with the forwarder (default: False)'
    )
    parser.add_argument(
        '--prefix',
        type=str,
        default='/foo/bar/baz',
        help='NDN prefix to insert and handle (default: /foo/bar/baz)'
    )
    parser.add_argument(
        '--key-path',
        type=str,
        default='./personal-keys/bar.key',
        help='Path to the NDN key file (default: ./personal-keys/bar.key)'
    )
    parser.add_argument(
        '--cert-path',
        type=str,
        default='./personal-keys/bar.cert',
        help='Path to the NDN certificate file (default: ./personal-keys/bar.cert)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duration in seconds to keep the prefix inserted before removal (default: 60)'
    )
    args = parser.parse_args()

    face = UdpFace(port=args.port)

    global app
    app = NDNApp(face)
    app.run_forever(after_start=prefix_insert_test(
        prefix=args.prefix,
        key_path=args.key_path,
        cert_path=args.cert_path,
        also_register=args.also_register,
        duration=args.duration
    ))


async def prefix_insert_test(prefix: str, key_path: str, cert_path: str, duration: int, also_register: bool = False):
    insertion_signer = get_signer_from_ndnd_key(key_path, cert_path)

    with open(cert_path, 'r') as file:
        bar_cert_str = file.read()

    cert_to_staple = parse_ndnd_cert(bar_cert_str)['cert_data']

    await insert_prefix(app, prefix, NullSigner(), insertion_signer, cost=5, stapled_certs=[cert_to_staple])
    if also_register:
        try:
            status = await app.register(prefix)
            print(f'Registration status for {prefix}: {status}')
        except Exception as e:
            print(f"Error registering prefix {prefix}: {e}")

    app.attach_handler(prefix, on_interest_handler_factory(prefix))

    print(f'Ready and listening for prefix: {prefix} for {duration} seconds.')

    await asyncio.sleep(duration)
    await insert_prefix(app, prefix, NullSigner(), insertion_signer, expiration=0, stapled_certs=[cert_to_staple])
    if also_register:
        try:
            status = await app.unregister(prefix)
            print(f'Un-registration status for {prefix}: {status}')
        except Exception as e:
            print(f"Error un-registering prefix {prefix}: {e}")

    print(f'Route for {prefix} removed')
    if app:
        app.shutdown()
        print('App shutdown')

def on_interest_handler_factory(registered_prefix: str):
    def on_interest(name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc, context: PktContext) -> None:
        print(f"Received Interest for: {Name.to_str(name)} under prefix {registered_prefix}")
        content = f"Hello from {registered_prefix}!".encode()
        if app:
            reply(app.make_data(name, content=content, signer=NullSigner()))
        else:
            print("Error: App is not initialized, cannot send Data packet.")
    return on_interest


if __name__ == "__main__":
    main()

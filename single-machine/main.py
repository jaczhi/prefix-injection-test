import asyncio
import os
import signal
import sys
from typing import Optional
from ndn.appv2 import NDNApp, ReplyFunc, PktContext
from ndn.security import NullSigner
from ndn.transport.udp_face import UdpFace
from ndn.encoding import BinaryStr, FormalName, Component, Signer, Name
from prefix_injection_client import inject_prefix
from cert_util import get_signer_from_ndnd_key, parse_ndnd_cert


def handle_signal(signal_num, frame) -> None:
    print()
    print('Ctrl-C, stopping')

    if app is not None:
        app.shutdown()
        print('App shut down')

    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal) # Ctrl+C

    face = UdpFace(port=6363)

    global app
    app = NDNApp(face)
    app.run_forever(after_start=prefix_inject_test())


async def prefix_inject_test():
    injection_signer = get_signer_from_ndnd_key('./personal-keys/bar.key', './personal-keys/bar.cert')

    with open('./personal-keys/bar.cert', 'r') as file:
        bar_cert = file.read()

    cert_to_staple = parse_ndnd_cert(bar_cert)['cert_data']

    await inject_prefix(app, '/foo/bar/baz', NullSigner(), injection_signer, cost=5, stapled_certs=[cert_to_staple])

    app.attach_handler('/foo/bar/baz', on_foo_interest)

    print('Ready and listening')

    await asyncio.sleep(60)
    await inject_prefix(app, '/foo/bar/baz', NullSigner(), injection_signer, expiration=0, stapled_certs=[cert_to_staple])
    print('Route removed')
    app.shutdown()
    print('App shutdown')


def on_foo_interest(name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc, context: PktContext) -> None:
    content = "Hello, world!".encode()
    reply(app.make_data(name, content=content, signer=NullSigner()))


if __name__ == "__main__":
    main()
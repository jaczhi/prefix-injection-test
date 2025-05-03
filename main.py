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
from cert_util import get_signer_from_ndnd_key


def handle_signal(signal_num, frame) -> None:
    if app is not None:
        app.shutdown()

    print()
    print('Ctrl-C, stopping')
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal) # Ctrl+C

    face = UdpFace(port=6363)

    global app
    app = NDNApp(face)
    app.run_forever(after_start=prefix_inject_test())


async def prefix_inject_test():
    injection_signer = get_signer_from_ndnd_key('./ndnd-keys/foo.key', './ndnd-keys/foo.cert')
    await inject_prefix(app, '/foo/bar/baz', NullSigner(), injection_signer, cost=5)

    app.attach_handler('/foo/bar/baz', on_foo_interest)

    print('Ready and listening')


def on_foo_interest(name: FormalName, app_param: Optional[BinaryStr], reply: ReplyFunc, context: PktContext) -> None:
    content = "Hello, world!".encode()
    reply(app.make_data(name, content=content, signer=NullSigner()))


if __name__ == "__main__":
    main()
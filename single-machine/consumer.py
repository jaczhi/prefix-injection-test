import logging
import argparse
from ndn import utils, appv2, types
from ndn import encoding as enc
from ndn.transport.udp_face import UdpFace


logging.basicConfig(format='[{asctime}]{levelname}:{message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    style='{')




async def main(name: str):
    try:
        timestamp = utils.timestamp()
        name = enc.Name.from_str(name)
        print(f'Sending Interest {enc.Name.to_str(name)}, {enc.InterestParam(must_be_fresh=True, lifetime=6000)}')
        # TODO: Write a better validator
        data_name, content, pkt_context = await app.express(
            name, validator=appv2.pass_all,
            must_be_fresh=True, can_be_prefix=False, lifetime=6000)

        print(f'Received Data Name: {enc.Name.to_str(data_name)}')
        print(pkt_context['meta_info'])
        print(bytes(content) if content else None)
    except types.InterestNack as e:
        print(f'Nacked with reason={e.reason}')
    except types.InterestTimeout:
        print(f'Timeout')
    except types.InterestCanceled:
        print(f'Canceled')
    except types.ValidationFailure:
        print(f'Data failed to validate')
    finally:
        app.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NDN Consumer')
    parser.add_argument('--port', type=int, default=6363,
                        help='UDP port number for the face (default: 6363)')
    parser.add_argument(
        '--name',
        type=str,
        default='/foo/bar/baz',
        help='NDN name to consume (default: /foo/bar/baz)'
    )
    args = parser.parse_args()

    global app
    app = appv2.NDNApp(UdpFace(port=args.port))

    app.run_forever(after_start=main(args.name))

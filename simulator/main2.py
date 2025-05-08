import random
import os
import time

from types import FunctionType

from mininet.log import setLogLevel, info
from minindn.minindn import Minindn
from minindn.apps.app_manager import AppManager

from fw import NDNd_FW
import dv_util

def run() -> None:
    try:
        random.seed(0)

        info(f"===================================================\n")
        start = time.time()

        info('Starting forwarder on nodes\n')
        AppManager(ndn, ndn.net.hosts, NDNd_FW)

        dv_util.setup(ndn, hosts=ndn.net.hosts[1:])
        dv_util.converge(ndn.net.hosts[1:])

        # set up first node as forwarder-only
        for intf in ndn.net.hosts[0].intfList():
            other_intf = intf.link.intf2 if intf.link.intf1 == intf else intf.link.intf1
            ndn.net.hosts[0].cmd(f'ndnd fw route-add prefix=/ face=udp4://{other_intf.IP()}:6363')

        # inject on the first node
        # TODO make location pretty.
        # maybe make it an app?

        ndn.net.hosts[0].cmd('(cd /root/prefix-injection-test/single-machine && python main.py &)')

        time.sleep(30)

        for i in range(1, len(ndn.net.hosts)):
            output = ndn.net.hosts[i].cmd('(cd /root/prefix-injection-test/single-machine && python consumer.py)')
            print(f'{ndn.net.hosts[i].name}:\n{output}\n\n')

        info(f'Scenario completed in: {time.time()-start:.2f}s\n')
        info(f"===================================================\n\n")

        # Call all cleanups without stopping the network
        # This ensures we don't recreate the network for each test
        for cleanup in reversed(ndn.cleanups):
            cleanup()
    except Exception as e:
        ndn.stop()
        raise e
    finally:
        # kill everything we started just in case ...
        os.system('pkill -9 ndnd')
        os.system('pkill -9 nfd')

if __name__ == '__main__':
    setLogLevel('info')

    Minindn.cleanUp()
    Minindn.verifyDependencies()

    global ndn
    ndn = Minindn()
    ndn.start()

    run()

    ndn.stop()
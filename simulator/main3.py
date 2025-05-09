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

        dv_util.setup(ndn, pi_security=True)
        dv_util.converge(ndn.net.hosts)

        # inject on the first node
        # TODO make location pretty.
        # maybe make it an app?
        # amsterdam
        node_name = ndn.net.hosts[0].name
        print('homedir', os.path.join(ndn.net.hosts[0].params['params']['homeDir']))
        key_path = os.path.join(ndn.net.hosts[0].params['params']['homeDir'], 'client-keys', f'{node_name}-client.key')
        cert_path = os.path.join(ndn.net.hosts[0].params['params']['homeDir'], 'client-keys', f'{node_name}-client.cert')
        cmd = ndn.net.hosts[0].cmd(f'(cd /root/prefix-injection-test/single-machine && python main.py --port 6363 --prefix minindn/{node_name}/foo --duration 60 --key-path {key_path} --cert-path {cert_path} &)')
        print(cmd)
        time.sleep(10)

        for i in range(1, len(ndn.net.hosts)):
            output = ndn.net.hosts[i].cmd(f'(cd /root/prefix-injection-test/single-machine && python consumer.py --port 6363 --name minindn/{node_name}/foo)')
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

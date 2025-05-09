import os
import json
import subprocess
import shutil

from minindn.apps.application import Application

DEFAULT_NETWORK = '/minindn'

TRUST_ROOT_NAME: str = None
TRUST_ROOT_PATH = '/tmp/mn-dv-root'

class NDNd_DV(Application):
    config: str
    network: str

    def __init__(self, node, network=DEFAULT_NETWORK, pi_security=False):
        Application.__init__(self, node)
        self.network = network

        if not shutil.which('ndnd'):
            raise Exception('ndnd not found in PATH, did you install it?')

        if TRUST_ROOT_NAME is None:
            raise Exception('Trust root not initialized (call NDNDV.init_trust first)')

        self.init_keys()

        config = {
            'dv': {
                'network': network,
                'router': f"{network}/{node.name}",
                'keychain': f'dir://{self.homeDir}/dv-keys',
                'trust_anchors': [TRUST_ROOT_NAME],
                'neighbors': list(self.neighbors()),
                'prefix_injection_schema': f'{TRUST_ROOT_PATH}-inject.tlv',
                'prefix_injection_keychain': f'dir://{self.homeDir}/dv-keys',
                'prefix_injection_trust_anchors': [TRUST_ROOT_NAME],
            }
        } if pi_security else {
            'dv': {
                'network': network,
                'router': f"{network}/{node.name}",
                'keychain': f'dir://{self.homeDir}/dv-keys',
                'trust_anchors': [TRUST_ROOT_NAME],
                'neighbors': list(self.neighbors()),
                'prefix_injection_schema': "insecure",
            }
        }

        self.config = f'{self.homeDir}/dv.config.json'
        with open(self.config, 'w') as f:
            json.dump(config, f, indent=4)

    def start(self):
        Application.start(self, ['ndnd', 'dv', 'run', self.config], logfile='dv.log')

    @staticmethod
    def init_trust(network=DEFAULT_NETWORK) -> None:
        global TRUST_ROOT_NAME
        out = subprocess.check_output(f'ndnd sec keygen {network} ecc secp256r1 > {TRUST_ROOT_PATH}.key', shell=True)
        out = subprocess.check_output(f'ndnd sec sign-cert {TRUST_ROOT_PATH}.key < {TRUST_ROOT_PATH}.key > {TRUST_ROOT_PATH}.cert', shell=True)
        out = subprocess.check_output(f'cat {TRUST_ROOT_PATH}.cert | grep "Name:" | cut -d " " -f 2', shell=True)
        TRUST_ROOT_NAME = out.decode('utf-8').strip()

        schema_path = os.path.join(os.getcwd(), 'inject.tlv')
        out = subprocess.check_output(f'cp {schema_path} {TRUST_ROOT_PATH}-inject.tlv', shell=True)

    def init_keys(self) -> None:
        self.node.cmd(f'rm -rf dv-keys && mkdir -p dv-keys')

        self.node.cmd(f'ndnd sec keygen {self.network}/{self.node.name}/32=DV ecc secp256r1 > dv-keys/{self.node.name}.key')
        self.node.cmd(f'ndnd sec sign-cert {TRUST_ROOT_PATH}.key < dv-keys/{self.node.name}.key > dv-keys/{self.node.name}.cert')

        self.node.cmd(f'ndnd sec keygen {self.network}/{self.node.name}/inject ecc secp256r1 > dv-keys/{self.node.name}-inject.key')
        self.node.cmd(f'ndnd sec sign-cert {TRUST_ROOT_PATH}.key < dv-keys/{self.node.name}-inject.key > dv-keys/{self.node.name}-inject.cert')

        self.node.cmd(f'cp {TRUST_ROOT_PATH}.cert dv-keys/')

        self.node.cmd(f'rm -rf client-keys && mkdir -p client-keys')

        self.node.cmd(f'ndnd sec keygen {self.network}/{self.node.name}/inject/client ecc secp256r1 > client-keys/{self.node.name}-client.key')
        self.node.cmd(f'ndnd sec sign-cert dv-keys/{self.node.name}-inject.key < client-keys/{self.node.name}-client.key > client-keys/{self.node.name}-client.cert')


    def neighbors(self):
        for intf in self.node.intfList():
            other_intf = intf.link.intf2 if intf.link.intf1 == intf else intf.link.intf1
            yield {"uri": f"udp4://{other_intf.IP()}:6363"}

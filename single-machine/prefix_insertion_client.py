from ndn.appv2 import NDNApp
from ndn.encoding import Component, MetaInfo, Name, NonStrictName, Signer, TlvModel, BytesField, UintField, make_data
from ndn.transport.nfd_registerer import NfdRegister
from ndn.transport.prefix_registerer import PrefixRegisterer
from ndn import utils, security, types
from ndn.app_support import nfd_mgmt
import asyncio
import random
import time
from typing import Union, Optional


class InsObjModel(TlvModel):
    expiration = UintField(0x6d)
    cost = UintField(0x6a)

class StapledCertificateModel(TlvModel):
    cert = BytesField(0x216)


def create_insertion_object(name: NonStrictName, ins_signer: Signer,
                            expiration: int = 24 * 3600_000, cost: int = 0) -> Union[bytearray, memoryview]:
    name = Name.normalize(name)

    time_millis = int(time.time() * 1000)
    ins_obj_name = name + [Component.from_str('32=PA'), Component.from_version(time_millis), Component.from_segment(0)]

    ins_obj_model = InsObjModel()
    ins_obj_model.expiration = expiration
    ins_obj_model.cost = cost

    ins_obj = make_data(ins_obj_name,
                        MetaInfo(content_type=5),
                        ins_obj_model.encode(),
                        ins_signer)

    return ins_obj


async def insert_prefix(app: NDNApp, name: NonStrictName, interest_signer: Signer, ins_signer: Signer,
                        expiration: int = 24 * 3600_000, cost: int = 0,
                        stapled_certs: Optional[list[bytes]] = None) -> bool:
    """
    Insert a prefix (unofficial method written as an extension to python-ndn)

    Parameter usage similar to register_prefix.

    Expiration should be in milliseconds(?)

    See (todo)
    """

    # the official way to fix any and all race conditions
    await asyncio.sleep(random.random())

    name = Name.normalize(name)
    registerer_base: PrefixRegisterer = app.registerer
    if not isinstance(registerer_base, NfdRegister):
        raise TypeError('The prefix registerer associated with the app is not an NFD Registerer')

    registerer: NfdRegister = registerer_base

    async def pass_all(_name, _sig, _context):
        return types.ValidResult.PASS

    async with registerer._prefix_register_semaphore:
        for _ in range(10):
            now = utils.timestamp()
            if now > registerer._last_command_timestamp:
                registerer._last_command_timestamp = now
                break
            await asyncio.sleep(0.001)
        try:
            ins_obj = bytearray(create_insertion_object(name, ins_signer, expiration, cost))

            if stapled_certs:
                for cert in stapled_certs:
                    cert_wrapper_model = StapledCertificateModel()
                    cert_wrapper_model.cert = cert
                    cert_wrapper = bytearray(cert_wrapper_model.encode())
                    ins_obj.extend(cert_wrapper)

            _, reply, _ = await app.express(
                name='/routing/insert',
                app_param=ins_obj, signer=interest_signer,
                validator=pass_all,
                lifetime=1000)
            ret = nfd_mgmt.parse_response(reply)
            if ret['status_code'] != 200:
                print(f'Insertion for {Name.to_str(name)} failed: {ret["status_code"]} {ret["status_text"]}', flush=True)
                return False
            else:
                print(f'Insertion for {Name.to_str(name)} succeeded: {ret["status_code"]} {ret["status_text"]}', flush=True)
                return True
        except (types.InterestNack, types.InterestTimeout, types.InterestCanceled, types.ValidationFailure) as e:
            print(f'Insertion for {Name.to_str(name)} failed: {e.__class__.__name__}', flush=True)
            return False

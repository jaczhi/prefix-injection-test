import ndn.app_support.light_versec

with open("./schema/inject.lvs", "r") as file:
    lvs_text = file.read()

lvs_model = ndn.app_support.light_versec.compile_lvs(lvs_text)

with open("./schema/inject.tlv", "wb") as file:
    file.write(lvs_model.encode())

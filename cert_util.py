from ndn.encoding import Name, parse_data
from ndn.security import Ed25519Signer, TpmFile, KeychainSqlite3
from typing import Optional


def get_signer_from_ndnd_key(key_path: str, cert_path: Optional[str]=None) -> Ed25519Signer:
    with open(key_path, "r") as file:
        ndnd_key_content = file.read()

    key_data = parse_ndnd_key(ndnd_key_content)
    assert key_data['sig_type'] == "Ed25519", "Unsupported signature type"

    _, _, der_content, _ = parse_data(key_data['key_data'])

    if cert_path is not None:
        with open(cert_path, "r") as file:
            ndnd_cert_content = file.read()

        cert_data = parse_ndnd_cert(ndnd_cert_content)
        assert key_data['name'] == cert_data['signer_key'], "Cert does not match key"

        key_locator_name = cert_data['name']
    else:
        key_locator_name = key_data['name']

    return Ed25519Signer(key_locator_name, der_content)


def parse_ndnd_key(key_str):
    """
    Parse NDN KEY string format
    Returns a dictionary with the parsed key fields
    """
    from ndn.encoding import Name
    
    # Normalize line endings and split
    key_str = key_str.replace('\r\n', '\n')
    lines = key_str.strip().split('\n')
    
    # Remove header and footer
    if lines[0] == "-----BEGIN NDN KEY-----" and lines[-1] == "-----END NDN KEY-----":
        lines = lines[1:-1]
    
    result = {}
    
    for line in lines:
        if line.startswith("Name: "):
            name_str = line[6:]
            result["name"] = Name.from_str(name_str)
        elif line.startswith("SigType: "):
            result["sig_type"] = line[9:]
    
    # The rest of the lines are likely the key data in Base64
    # Collect them and convert to bytes
    key_data_lines = [line.strip() for line in lines if not line.startswith(("Name:", "SigType:"))]
    key_data_str = ''.join(key_data_lines)
    
    # Convert to bytes
    import base64
    try:
        result["key_data"] = base64.b64decode(key_data_str)
    except:
        # Fallback in case the encoding isn't standard base64
        result["key_data"] = key_data_str.encode('utf-8')
    
    return result


def parse_ndnd_cert(cert_str):
    """
    Parse NDN certificate string format
    Returns a dictionary with the parsed certificate fields
    """
    
    # Normalize line endings and split
    cert_str = cert_str.replace('\r\n', '\n')
    lines = cert_str.strip().split('\n')
    
    # Remove header and footer
    if lines[0] == "-----BEGIN NDN CERT-----" and lines[-1] == "-----END NDN CERT-----":
        lines = lines[1:-1]
    
    result = {}
    
    for line in lines:
        if line.startswith("Name: "):
            name_str = line[6:]
            result["name"] = Name.from_str(name_str)
        elif line.startswith("SigType: "):
            result["sig_type"] = line[9:]
        elif line.startswith("SignerKey: "):
            signer_key_str = line[11:]
            result["signer_key"] = Name.from_str(signer_key_str)
        elif line.startswith("Validity: "):
            validity_str = line[10:]
            result["validity"] = validity_str
    
    # The rest of the lines are likely the certificate data in Base64
    # Collect them and convert to bytes
    cert_data_lines = [line.strip() for line in lines if not line.startswith(("Name:", "SigType:", "SignerKey:", "Validity:"))]
    cert_data_str = ''.join(cert_data_lines)
    
    # Convert to bytes
    import base64
    try:
        result["cert_data"] = base64.b64decode(cert_data_str)
    except:
        # Fallback in case the encoding isn't standard base64
        result["cert_data"] = cert_data_str.encode('utf-8')
    
    return result


# Example usage:
if __name__ == "__main__":
    assert get_signer_from_ndnd_key('./ndnd-keys/foo.key', './ndnd-keys/foo.cert') is not None

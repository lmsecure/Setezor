import os
import ssl
import sys
import OpenSSL.crypto
import json
import aiofiles
from datetime import datetime
#from setezor.exceptions.loggers import get_logger
from typing import Dict

#logger = get_logger(__package__, handlers=[])


class CertInfo:

    @classmethod
    def convert_timestamp(cls, cert_date: bytes):
        datetime_obj = datetime.strptime(cert_date.decode(), '%Y%m%d%H%M%SZ')
        return int(datetime.timestamp(datetime_obj))

    @classmethod
    def get_cert(cls, host: str, port: int) -> str:
        try:
            #logger.debug('Try get cert from  %s:%s ', (host, port))
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_OPTIONAL
            cert = ssl.get_server_certificate((host, port), timeout=1)
            return cert
        except Exception as e:
            #logger.error(f'[-] HOST: {host}, PORT: {port} {type(e).__name__}')
            return None

    @classmethod
    def parse_cert(cls, cert: bytes) -> Dict[str, str]:
        cert: OpenSSL.crypto.X509 = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert)
        cert_data = {
            "subject": ', '.join(['='.join([j.decode() for j in i]) for i in cert.get_subject().get_components()]),
            "issuer": ', '.join(['='.join([j.decode() for j in i]) for i in cert.get_issuer().get_components()]),
            "has-expired": cert.has_expired(),
            "not-after": cls.convert_timestamp(cert.get_notAfter()),
            "not-before": cls.convert_timestamp(cert.get_notBefore()),
            "serial-number": cert.get_serial_number(),
            "serial-number(hex)": hex(cert.get_serial_number()),
            "signature-algorithm": cert.get_signature_algorithm().decode(),
            "version": cert.get_version(),
            "pulic-key-length": cert.get_pubkey().bits()
        }

        for i in range(cert.get_extension_count()):
            inf = cert.get_extension(i)
            cert_data[inf.get_short_name().decode()] = inf.__str__()

        return cert_data

    @classmethod
    def get_cert_and_parse(cls, resource:dict): #certificates_folder: str):
        port = resource.get("port")
        host = resource.get("domain") if resource.get("domain") else resource.get("ip")
        cert = cls.get_cert(host=host, port=port)
        if not cert:
            return []
        #cls.write_to_file(certificates_folder, host, port, cert)
        return cls.parse_cert(cert=cert)

    @classmethod
    # переименовать и поменять формат даты-время
    def write_to_file(cls, certificates_folder: str, host: str, port: int, cert: str):
        date_and_time = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
        filename = f"{host}:{port}_{date_and_time}.crt"
        with open(os.path.join(certificates_folder, filename), mode='w', encoding="utf-8") as file:
            file.write(cert)

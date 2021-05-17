"""
Offline Lightning Network PPV

Usage:
  main.py -c <FILE_PATH> - creates an PPV invoice and encrypts the content stored in <FILE_PATH>
  main.py -d <FILE_PATH> - decrypts the PPV packet stored in <FILE_PATH>
"""

import codecs, grpc, os, sys, textwrap
import rpc_pb2 as lnrpc, rpc_pb2_grpc as rpcstub
from aes import AESCipher
from config import MACAROON_PATH, CERT_PATH


macaroon = codecs.encode(open(MACAROON_PATH, 'rb').read(), 'hex')
os.environ['GRPC_SSL_CIPHER_SUITES'] = 'HIGH+ECDSA'
cert = open(CERT_PATH, 'rb').read()
ssl_creds = grpc.ssl_channel_credentials(cert)
channel = grpc.secure_channel('localhost:10009', ssl_creds)
stub = rpcstub.LightningStub(channel)

packet_start = '--------------- LN-PPV-START ---------------'
middle_line = '--------------------------------------------'
packet_end = '--------------- LN-PPV-END ---------------'

def createInvoice(amount, data_key, expiry=3600):
    preimage = os.urandom(32)
    print('preimage hex', preimage.hex())
    memo = AESCipher( preimage.hex() ).encrypt( data_key.hex() )
    request = lnrpc.Invoice(
            memo=memo,
            value=amount,
            r_preimage=preimage,
            expiry=expiry
        )
    response = stub.AddInvoice(request, metadata=[('macaroon', macaroon)])
    return response

def decodeInvoice(invoice):
    request = lnrpc.PayReqString(
        pay_req=invoice,
    )
    response = stub.DecodePayReq(request, metadata=[('macaroon', macaroon)])
    description = response.description
    request = lnrpc.ListPaymentsRequest(
        include_incomplete=False,
        reversed=True
    )
    response = stub.ListPayments(request, metadata=[('macaroon', macaroon)])
    for payment in response.payments:
        if payment.payment_request == invoice:
            return payment.payment_preimage, description 



def parse_packet(data):
    invoice = data[data.find(packet_start)+len(packet_start):data.find(middle_line)]
    data_enc = data[data.find(middle_line)+len(middle_line):data.find(packet_end)]
    return invoice.replace('\n', ''), data_enc.replace('\n', '')

def create_packet(invoice, enc_data):
    textwrap_len = 40
    print(packet_start)
    print(textwrap.fill(invoice.payment_request, textwrap_len))
    print(middle_line)
    print(textwrap.fill(enc_data.hex(), textwrap_len))
    print(packet_end)

if __name__ == "__main__":
    mode = sys.argv[1]
    file_path = sys.argv[2]
    if mode == '-c':
        data = open(file_path).read()
        amount = int(input("How much should the invoice cost (sats): "))
        data_key = os.urandom(32)
        data_enc = AESCipher( data_key.hex() ).encrypt(data)
        invoice = createInvoice(amount, data_key)
        print('Encrypting data using the key: ', data_key.hex())
        create_packet(invoice, data_enc)
    elif mode == '-d':
        data = open(file_path).read()
        invoice, data_enc = parse_packet(data)
        preimage, data_key_enc = decodeInvoice(invoice)
        data_key = AESCipher( preimage ).decrypt(data_key_enc)
        data = AESCipher( data_key).decrypt(bytearray.fromhex(data_enc))
        print(data)

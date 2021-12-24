from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from struct import pack
import os

import string
import random


class TorchAES:
    '''
        AES 양방향 암호화

        1. pth 파일 암호화한 새로운 파일 생성
    '''

    def __init__(self, key_text):
        hash = SHA256.new()
        hash.update(key_text.encode('utf-8'))
        key = hash.digest()
        self.__key = key[:16]

        iv_text = 'initialvector123'
        hash.update(iv_text.encode('utf-8'))
        iv = hash.digest()
        del iv_text
        self.__iv = iv[:16]

    # pth 파일 암호화 파일 생성
    def encrypt(self, in_path, out_filename, blocksize=65536):
        path, _, filename = in_path.rpartition('/') # {path} '/' {filename}
        os.chdir(path)

        plain_file = open(filename, 'rb')
        filesize = os.path.getsize(in_path)

        aes = AES.new(self.__key, AES.MODE_CBC, self.__iv)

        with open(out_filename, 'wb') as ret:
            ret.write(pack('<Q', filesize))
            while True:
                block = plain_file.read(blocksize)
                if len(block) == 0:
                    break
                elif len(block) % 16 != 0:
                    block += b'0' * (16 - len(block) % 16)
                ret.write(aes.encrypt(block))



def generate_key(length_of_string: int) -> str:
    key = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length_of_string))
    return key



if __name__ == '__main__':
    model_path = '/home/fourind/py36/Sorest_NX_fire detect/20211016_NX_new fire detect_v2/model/fire_model_trt.pth'
    # model_path = '/home/fourind/fire_model_trt.pth'
    new_filename = 'test_c.pth'
    # key = '4industry!'
    key_length = 20

    secret_key = generate_key(key_length)
    print(secret_key)

    encryptor = TorchAES(secret_key)
    encryptor.encrypt(model_path, new_filename)
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
import os
from struct import pack, unpack, calcsize
import zipfile


class TorchAES:
    def __init__(self, keytext):
        hash = SHA256.new()
        hash.update(keytext.encode('utf-8'))
        key = hash.digest()
        self.__key = key[:16]

        iv_text = 'initialvector123'
        hash.update(iv_text.encode('utf-8'))
        iv = hash.digest()
        del iv_text
        self.__iv = iv[:16]


    def encrypt(self, in_path, out_filename, blocksize=65536):
        TorchAES.unzip(in_path)

        # aes = AES.new(self.__key, AES.MODE_CBC, self.__iv)
        # filesize = os.path.getsize(file_path)


    # @staticmethod
    # def decrypt(self, key, in_filename, out_filename, blocksize=65536):
    #     pass

    # pth zip 압축 풀기
    @staticmethod
    def unzip(zip_path):
        filename = zip_path.rpartition('/') # {path} '/' {filename}
        print(filename)
        # zip_file = zipfile.ZipFile(zip_path, )



if __name__=='__main__':
    # aes = TorchAES('helena')
    pth_path = '/home/fourind/py36/YOLOX/yolox_s.pth'
    TorchAES.unzip(pth_path)
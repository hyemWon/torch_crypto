from Crypto.Hash import SHA256
from Crypto.Cipher import AES
import os
from struct import pack, unpack, calcsize
import zipfile


class TorchAES:
    '''
        AES 양방향 암호화

        1. pth zip 파일 unzip
        2. unzip한 폴더 내부의 model 파일 암호화
        3.
    '''

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

        print(self.__key)
        print(self.__iv)


    def encrypt(self, in_path, out_filename, blocksize=65536):
        path, _, filename = in_path.rpartition('/')  # {path} '/' {filename}
        # pth zip파일 압축 해제, 경로 변경
        TorchAES.unzip(path, filename)
        file_path = os.path.join(path, 'archive/data.pkl')  # 압축해제한 폴더로(archive)에서의 pkl 파일 경로
        print(file_path)

        # 파일 암호화
        aes = AES.new(self.__key, AES.MODE_CBC, self.__iv)
        filesize = os.path.getsize(file_path)
        print(filesize)

        with zipfile.ZipFile(in_path) as pthfile:
            with pthfile.open('archive/data.pkl', mode='r') as f: # pth zip파일 안에서의 pkl 열기
                print(f.read())
                with open(file_path, 'wb') as ret:
                    ret.write(pack('<Q', filesize))
                    while True:
                        block = f.read(blocksize)
                        print(block)
                        if len(block) == 0:
                            break
                        elif len(block) % 16 != 0:
                            block += b'0'*(16 - len(block) % 16)
                        ret.write(aes.encrypt(block))

        TorchAES.zip(path, out_filename) # pth로 다시 압축


    @staticmethod
    def decrypt(key, file_path, blocksize=65536):
        hash = SHA256.new()
        hash.update(key.encode('utf-8'))
        key = hash.digest()[:16]

        iv_text = 'initialvector123'
        hash.update(iv_text.encode('utf-8'))
        iv = hash.digest()[:16]
        del iv_text


        with zipfile.ZipFile(file_path) as zip:
            with zip.open('archive/data.pkl', mode='r') as f:
                filesize = unpack('<Q', f.read(calcsize('<Q')))[0]
                aes = AES.new(key, AES.MODE_CBC, iv)
                # with open()



    # path 경로의 filename 압축폴더를 해제
    @staticmethod
    def unzip(path, zip_filename):
        print(path, zip_filename)
        os.chdir(path)

        zip_file = zipfile.ZipFile(zip_filename, 'r')
        zip_file.extractall()
        zip_file.close()


    # path 경로의 archive폴더를 filename으로 압축
    @staticmethod
    def zip(path, new_filename):
        # print(new_filename)
        os.chdir(path)

        target_dir = os.path.join(path, 'archive')

        with zipfile.ZipFile(new_filename, 'w', zipfile.ZIP_DEFLATED) as f:
            for base_path, dirs, files in os.walk(target_dir):
                for file in files:
                    _relpath = os.path.relpath(os.path.join(base_path, file), path)
                    f.write(_relpath)


    # def encrypt_test(self, in_path, out_filename, blocksize=65536):
    #     path, _, filename = in_path.rpartition('/')
    #     os.chdir(path)
    #
    #     myfile = open(filename, 'rb')
    #     filesize = os.path.getsize(in_path)
    #     # print(filesize)
    #     # 파일 암호화
    #     aes = AES.new(self.__key, AES.MODE_CBC, self.__iv)
    #
    #     with open(out_filename, 'wb') as ret:
    #         ret.write(pack('<Q', filesize))
    #         while True:
    #             block = myfile.read(blocksize)
    #             print(block)
    #             if len(block) == 0:
    #                 break
    #             elif len(block) % 16 != 0:
    #                 block += b'0' * (16 - len(block) % 16)
    #             ret.write(aes.encrypt(block))




if __name__=='__main__':
    pth_path = '/home/fourind/py36/Sorest_NX_fire detect/20211016_NX_new fire detect_v2/model/test.pth'
    key = 'helena'
    encryptor = TorchAES(key)
    encryptor.encrypt_test(pth_path, 'test_c')
    # TorchAES.zip('/home/fourind/py36/YOLOX', 'result.pth')
    # TorchAES.decrypt(key, '/home/fourind/py36/YOLOX/result.pth')
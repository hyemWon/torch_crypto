# AES 대칭키 암호
# 파이썬에서 AES를 사용하기 위해서 pycrypto 모듈을 설치
# 사용전 SHA 해시를 사용해 초기화 벡터와 키를 sha로 해싱 후 키로 사용할 것
# 해시는 파이썬 자체 라이브러리 hashlib이 있으나 pycrypto를 이용해서 사용할 것

# 해시
# 빠른 검색을 위해 사용되었다. 계산의 역상이 어렵기 때문에 암호 및 보안에도 이용되다.
# 주로 MD, SHA 계열이 있고, SHA는 버전에 따라서 알고리즘이 다른 경우가 있다.
# 암호로 사용되지 않는 해시도 있다.
# MD5의 경우 이미 해시가 풀려 암호학적으로 이용하기에는 안전하지 않은 해시이다.
# 대부분 느려도 안전한 SHA를 사용하며 이회 다양한 해시 알고리즘이 사용된다.
# 본 예제에서는 SHA256 사용

# from Crypto.Hash import SHA256
# from Crypto.Cipher import AES

# hash = SHA256.new() # sha256 해시 객체 생성

# data = ''
# hash.update(data)  # 해시 데이터 적용
# hash_value = hash.digest() # 해시값(hash value) 반환

# AES.new(key, mode, iv) 
# key : key 값 AES는 128 192 256의 키 길이를 사용할 수 있다.
# mode : 암호 mode, 기본 값이 ECB 모드이다.
# iv : 초기화 벡터를 입력하는 인수 ECB모드와 CTR모드는 사용되지 않는다.

# struct 모듈
# pack, unpack, calcsize 등의 기능 있음.
# 정수, 실수, 문자열을 encode한 것을 bytes 객체로 변환하거나, 반대로 bytes 객체에서 이것을 빼낸다.
# bytes 객체로 변환하려면 서식 지정 문자와 변환할 값은 pack함수에 넘기면 된다.

# IV : 첫번째 블록은 이전 암호화 블록이 없기 때문에 iv사용. 16바이트 크기. 
# 매번 다른 IV를 생성하면 같은 평문이라도 다른 암호문을 생성할 수 있다.

import struct
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from os import path
from struct import pack, unpack, calcsize


class fileAES():
    def __init__(self, keytext, out_filename):
        hash = SHA256.new() # 해시 객체 생성
        hash.update(keytext.encode('utf-8')) # 해시 적용
        key = hash.digest() # 해시값 반환
        self.key = key[:16]

        iv_text = 'initialvector123' # 첫번째 블록은 이전 암호화 블록이 없기 때문에 iv사용
        hash.update(iv_text.encode('utf-8'))
        iv = hash.digest()
        del iv_text
        self.iv = iv[:16] # 16바이트
        
        self.out_filename = out_filename
        print('secret key: ', self.key)
        print('iv: ', self.iv)


    # AES 암호화
    def encrypt_file(self, filename, blocksize=65536):
        aes = AES.new(self.key, AES.MODE_CBC, self.iv)
        filesize = path.getsize(filename)
        if self.out_filename == None:
            out_filename = filename[0:len(filename)-4]+'.aef' # filesize, data
        else:
            out_filename = self.out_filename

        with open(filename, 'rb') as origin:
            with open(out_filename, 'wb') as ret:
                ret.write(pack('<Q', filesize)) # filesize를 c의 구조체 형식으로 저장
                while True:
                    block = origin.read(blocksize) # 블록단위로 파일 읽기. # AES는 128비트(16바이트)의 고정된 블록 단위로 암호화 수행
                    if len(block) == 0:
                        break
                    elif len(block) % 16 != 0:  # 16의 배수가 아니라면 0으로 채운다.
                        block += b'0'*(16 - len(block) % 16)
                    ret.write(aes.encrypt(block))

    
    # 암호된 파일을 복호화하는 메서드
    def decrypt_file(self, filename, file_exp, blocksize = 1024):

        with open(filename, 'rb') as origin: # 암호화 파일
            filesize = unpack('<Q', origin.read(calcsize('<Q')))[0]
            aes = AES.new(self.key, AES.MODE_CBC, self.iv)

            with open(file_exp, 'wb') as ret: # 복호화 파일
                ret.write(aes.decrypt(origin.read(16)))
                while True:
                    block = origin.read(blocksize) # 1024 블록 단위로 복호화 진행. 16의 배수라면 ok
                    if len(block) == 0:
                        break
                    ret.write(aes.decrypt(block))
                    print(aes.decrypt(block))
                ret.truncate(filesize) # filesize 만큼 패딩을 지우기위해 자르는 함수


if __name__=='__main__':
    aes = fileAES('helena', 'test2.pth')
    # aes.encrypt_file('/home/fourind/py36/YOLOX/archive/data.pkl')
    # aes.decrypt_file('data_c.pkl', 'data_d.pkl')
    path= '/home/fourind/py36/Sorest_NX_fire detect/20211016_NX_new fire detect_v2/model/test_c.pth'
    new_path = '/home/fourind/py36/Sorest_NX_fire detect/20211016_NX_new fire detect_v2/model/test_d.pth'
    aes.decrypt_file(path, new_path)
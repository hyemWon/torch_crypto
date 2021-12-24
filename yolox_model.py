#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (c) Megvii, Inc. and its affiliates.

import argparse
import os
import time
from loguru import logger

from lib.init import *
import cv2
import torch

from lib.yolox.data.data_augment import ValTransform
from lib.yolox.utils import get_model_info, postprocess
from lib.yolox.exp import get_exp



class Predictor():
    def __init__(self, exp_file=None, name=None, conf=0.5, nms=0.5, size=640, gpu_id=0):
        self.gpu_id = gpu_id

        if USE_GPU_CNT > 1:
            torch.cuda.device('cuda:{}'.format(self.gpu_id))
        else:
            torch.cuda.set_device('cuda:{}'.format(self.gpu_id))

        if USE_TRT:
            self.device = 'gpu'

        self.exp = get_exp(exp_file, name)
        self.exp.test_conf = conf
        self.exp.nmsthre = nms
        self.exp.test_size = (size, size)

        self.model = self.exp.get_model()
        # print('Yolox Model load...{}'.format(self.model))

        if self.device == 'gpu':
            self.model.to('cuda:{}'.format(self.gpu_id))
        self.model.eval()

        self.trt_file = TRT_FILE_LOAD
        self.model.head.decode_in_inference = False
        self.decoder = self.model.head.decode_outputs

        self.cls_names = COCO_CLASSES
        self.num_classes = self.exp.num_classes

        self.preproc = ValTransform()


        if self.trt_file is not None:
            from torch2trt import TRTModule

            model_trt = TRTModule()

            buffer = self.decrypt()

            model_trt.load_state_dict(torch.load(buffer))
            # model_trt.load_state_dict(torch.load(self.trt_file))

            x = torch.ones(1, 3, self.exp.test_size[0], self.exp.test_size[1]).to('cuda:{}'.format(self.gpu_id))
            self.model(x)
            self.model = model_trt


    # model 복호화
    def decrypt(self):
        import io
        from struct import unpack, calcsize
        from Crypto.Cipher import AES
        from Crypto.Hash import SHA256

        key_text = 'Jgz9IDA6jIBpdPZp16Cf'
        hash = SHA256.new()
        hash.update(key_text.encode('utf-8'))
        key = hash.digest()
        secret_key = key[:16]

        iv_text = 'initialvector123'
        hash.update(iv_text.encode('utf-8'))
        iv = hash.digest()
        del iv_text
        iv = iv[:16]

        blocksize = 1024

        buffer = io.BytesIO()
        with open(self.trt_file, 'rb') as f:
            filesize = unpack('<Q', f.read(calcsize('<Q')))[0]
            aes = AES.new(secret_key, AES.MODE_CBC, iv)

            buffer.write(aes.decrypt(f.read(16)))

            while True:
                block = f.read(blocksize)
                if len(block) == 0:
                    break
                buffer.write(aes.decrypt(block))
                print(aes.decrypt(block))
            buffer.truncate(filesize)
            buffer = io.BytesIO(buffer.getvalue())

        return buffer

        # path = '/home/fourind/py36/Sorest_NX_fire detect/20211016_NX_new fire detect_v2/model/test_c.pth'
        # new_path = '/home/fourind/py36/Sorest_NX_fire detect/20211016_NX_new fire detect_v2/model/test_d.pth'

        # with open(path, 'rb') as origin:  # 암호화 파일
        #     filesize = unpack('<Q', origin.read(calcsize('<Q')))[0]
        #     aes = AES.new(secret_key, AES.MODE_CBC, iv)
        #
        #     with open(new_path, 'wb') as ret:  # 복호화 파일
        #         ret.write(aes.decrypt(origin.read(16)))
        #
        #         while True:
        #             block = origin.read(blocksize)  # 1024 블록 단위로 복호화 진행. 16의 배수라면 ok
        #             if len(block) == 0:
        #                 break
        #             ret.write(aes.decrypt(block))
        #             print(aes.decrypt(block))
        #         ret.truncate(filesize)
        #         print(ret)
        #
        # return new_path


    def detect(self, img):
        self.num_classes = self.exp.num_classes
        self.confthre = self.exp.test_conf
        self.nmsthre = self.exp.nmsthre
        self.test_size = self.exp.test_size

        img_info = {"id": 0}
        if isinstance(img, str):
            img_info["file_name"] = os.path.basename(img)
            img = cv2.imread(img)
        else:
            img_info["file_name"] = None

        height, width = img.shape[:2]
        img_info["height"] = height
        img_info["width"] = width

        ratio = min(self.test_size[0] / img.shape[0], self.test_size[1] / img.shape[1])
        img_info["ratio"] = ratio
        t0 = time.time()
        img, _ = self.preproc(img, None, self.test_size)
        img = torch.from_numpy(img).unsqueeze(0)
        if self.device == "gpu":
            # img = img.to('cuda:{}'.format(self.gpu_id))
            img = img.cuda()

        with torch.no_grad():
            outputs = self.model(img)
            if self.decoder is not None:
                outputs = self.decoder(outputs, dtype=outputs.type())

            outputs = postprocess(
                outputs, self.num_classes, self.confthre,
                self.nmsthre, class_agnostic=True
            )

        results = []
        output = outputs[0]
        if output is not None:

            output = output.cpu()
            bboxes = output[:, 0:4]
            # preprocessing: resize
            bboxes /= ratio
            cls = output[:, 6]
            scores = output[:, 4] * output[:, 5]

            for i, bbox in enumerate(bboxes):
                class_name = COCO_CLASSES[int(cls[i])]
                score = scores[i]
                xmin, ymin, xmax, ymax = bbox
                width = int(xmax - xmin)
                heigth = int(ymax - ymin)
                center_x = xmin + int(width/2)
                center_y = ymin + int(height/2)

                # print(xmin, ymin, xmax, ymax)
                results.append([class_name, score, [int(xmin), int(ymin), int(xmax), int(ymax)]])
                # results.append([class_name, score, [int(center_x), int(center_y), int(width), int(heigth)]])

        return results


# if __name__ == "__main__":
#
#     # main(exp, args)
#     predictor = Predictor(exp_file='model/yolox_m.py', name='yolox_m.py', gpu_id=1)
#     cap = cv2.VideoCapture('DJI_20210831143827_0002_Z.MP4')
#     while True:
#         ret, frame = cap.read()
#
#         if not ret:
#             print('test')
#             break
#         test_time = time.time()
#         results = predictor.detect(frame)
#         print(round(1/(time.time() - test_time), 1))
#         if len(results) > 0:
#             try:
#                 for result in results:
#                     name = result[0]
#                     xmin, ymin, xmax, ymax = result[2]
#
#                     cv2.putText(frame, str(name), (xmin, ymin-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#                     cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
#             except Exception as ex:
#                 print(ex)
#                 pass
#         cv2.imshow('test', frame)
#         cv2.waitKey(1)

# if __name__=='__main__':
#     pd = Predictor()

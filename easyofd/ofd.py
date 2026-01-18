#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: F:\code\easyofd\easyofd
# CREATE_TIME: 2023-10-07
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# note:  ofd 基础类
import base64
import os
import sys
from io import BytesIO
from typing import Union

sys.path.insert(0, os.getcwd())
sys.path.insert(0, "..")

import fitz

from PIL import Image
from loguru import logger

from easyofd.parser_ofd import OFDParser
from easyofd.draw import DrawPDF, OFDWrite


class OFD(object):
    """
    OFD文档处理基础类

    该类提供了一系列方法用于处理OFD（Open Fixed-layout Document）文档，
    包括读取OFD文档、将OFD转换为PDF、将PDF转换为OFD、将OFD转换为图片等功能。

    主要功能：
    - 读取不同格式的OFD文档（路径、base64、二进制、IO流）
    - 将OFD文档转换为PDF格式
    - 将PDF文档转换为OFD格式
    - 将OFD文档转换为图片格式
    - 将图片列表转换为OFD文档

    Attributes:
        data (Any): 存储解析后的OFD文档数据，初始为None
    """

    def __init__(self):
        """
        初始化OFD对象

        创建一个新的OFD实例，初始化数据存储属性
        """
        self.data = None

    def read(
        self,
        ofd_f: Union[str, bytes, BytesIO],
        fmt="b64",
        save_xml=False,
        xml_name="testxml",
    ):
        """
        读取OFD文档并解析

        支持多种输入格式的OFD文档读取，包括文件路径、base64编码字符串、
        二进制数据或BytesIO对象，并将其解析为内部数据结构

        Args:
            ofd_f (Union[str, bytes, BytesIO]): OFD文档数据，可以是文件路径、
                                                base64编码字符串、二进制数据或BytesIO对象
            fmt (str, optional): 输入格式，可选值包括：
                                - "path": 文件路径
                                - "b64": base64编码字符串
                                - "binary": 二进制数据
                                - "io": BytesIO对象
                                默认为"b64"
            save_xml (bool, optional): 是否保存解析的XML文件，默认为False
            xml_name (str, optional): 保存的XML文件名，默认为"testxml"

        Raises:
            Exception: 当fmt参数值不在允许范围内时抛出异常
        """
        if fmt == "path":
            with open(ofd_f, "rb") as f:
                ofd_f = str(base64.b64encode(f.read()), encoding="utf-8")
        elif fmt == "b64":
            pass
        elif fmt == "binary":
            ofd_f = str(base64.b64encode(ofd_f), encoding="utf-8")
        elif fmt == "io":
            ofd_f = str(base64.b64encode(ofd_f.getvalue()), encoding="utf-8")
        else:
            raise "fomat Error: %s" % fmt

        self.data = OFDParser(ofd_f)(save_xml=save_xml, xml_name=xml_name)

    def save(self):
        """
        保存OFD数据到XML文件

        将内存中的OFD数据转换为XML文件格式进行保存。
        注意：此方法当前仅包含基本断言检查，具体实现待完善。

        Raises:
            AssertionError: 当self.data为None时抛出异常
        """
        """
        draw ofd xml
        初始化一个xml 文件
        self.data > file
        """
        assert self.data, f"data is None"

    def pdf2ofd(self, pdfbyte, optional_text=False):
        """
        将PDF字节数据转换为OFD格式

        使用OFDWrite类将PDF文档的字节数据转换为OFD格式

        Args:
            pdfbyte (bytes): PDF文档的字节数据
            optional_text (bool, optional): 是否包含可选文本，默认为False

        Returns:
            bytes: 转换后的OFD文档字节数据

        Raises:
            AssertionError: 当pdfbyte为None时抛出异常
        """
        assert pdfbyte, f"pdfbyte is None"
        logger.info(f"pdf2ofd")
        ofd_byte = OFDWrite()(pdfbyte, optional_text=optional_text)
        return ofd_byte

    def to_pdf(self):
        """
        将OFD数据转换为PDF格式

        将已解析的OFD数据转换为PDF文档的字节数据

        Returns:
            bytes: 转换后的PDF文档字节数据

        Raises:
            AssertionError: 当self.data为None时抛出异常
        """
        assert self.data, f"data is None"
        logger.info(f"to_pdf")
        return DrawPDF(self.data)()

    def pdf2img(self, pdfbytes):
        """
        将PDF字节数据转换为图像列表

        使用fitz库将PDF文档的每一页转换为PIL图像对象

        Args:
            pdfbytes (bytes): PDF文档的字节数据

        Returns:
            list: 包含每一页PDF转换成的PIL图像对象的列表
        """
        image_list = []

        doc = fitz.open(stream=pdfbytes, filetype="pdf")

        for page in doc:
            rotate = int(0)
            zoom_x, zoom_y = 1.6, 1.6
            zoom_x, zoom_y = 2, 2
            mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotate)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            # image = np.ndarray((pix.height, pix.width, 3), dtype=np.uint8, buffer=pix.samples)
            # print(image.shape)
            # print(image[2])
            image_list.append(pil_image)
        logger.info(f"pdf2img")
        return image_list

    def jpg2ofd(self, imglist: list):
        """
        将图像列表转换为OFD格式

        将PIL图像对象列表转换为OFD文档格式

        Args:
            imglist (list): 包含PIL图像对象的列表

        Returns:
            bytes: 转换后的OFD文档字节数据
        """
        """
        imglist: pil image list
        """
        ofd_byte = OFDWrite()(pil_img_list=imglist)
        return ofd_byte

    def jpg2pfd(self, imglist: list):
        """
        将图像列表转换为PDF格式

        将PIL图像对象列表先转换为OFD数据结构，再转换为PDF格式

        Args:
            imglist (list): 包含PIL图像对象的列表

        Returns:
            bytes: 转换后的PDF文档字节数据
        """
        """
        imglist: PIL image list
        1 构建data 
        2 DrawPDF(self.data)()
        """

        data = OFDParser(None).img2data(imglist)
        return DrawPDF(data)()

    def to_jpg(self, format="jpg"):
        """
        将OFD文档转换为图像列表

        将OFD文档先转换为PDF，然后再转换为图像列表

        Args:
            format (str, optional): 图像格式，默认为"jpg"

        Returns:
            list: 包含每一页转换成的PIL图像对象的列表

        Raises:
            AssertionError: 当self.data为None时抛出异常
        """
        assert self.data, f"data is None"
        image_list = []
        pdfbytes = self.to_pdf()
        image_list = self.pdf2img(pdfbytes)
        return image_list

    def del_data(self):
        """
        清空OFD数据

        销毁存储在self.data中的OFD文档数据，释放内存
        """
        """销毁self.data"""
        self.data = None

    def __del__(self):
        """
        析构函数

        在对象被销毁时执行清理操作
        """
        del self

    def disposal(self):
        """
        手动销毁对象

        显式调用析构函数以销毁当前对象
        """
        """销毁对象"""
        self.__del__()


if __name__ == "__main__":
    ofd = OFD()

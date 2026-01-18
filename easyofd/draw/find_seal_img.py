#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: easyofd read_seal_img
# CREATE_TIME: 2024/5/28 14:13
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: renoyuan
# note: 根据 ASN.1 解析签章 拿到 签章图片
"""印章图片提取模块

该模块提供SealExtract类，用于从ASN.1编码的数字签名数据中提取印章图片。
支持从文件路径或Base64编码数据中读取ASN.1数据，并将其解析为图片。
"""
import io
import base64

from PIL import Image, UnidentifiedImageError
from loguru import logger
from pyasn1.codec.der.decoder import decode
from pyasn1.type import univ
from pyasn1.error import PyAsn1Error


class SealExtract(object):
    """印章提取器

    用于从ASN.1编码的数字签名数据中解析并提取印章图片。
    支持从文件路径或Base64编码数据中读取ASN.1数据。
    """

    def __init__(self):
        """初始化印章提取器

        当前构造函数为空实现，可根据需要扩展初始化逻辑。
        """
        pass

    def read_signed_value(self, path="", b64=""):
        """读取并解码ASN.1签名数据

        从文件路径或Base64编码字符串中读取ASN.1编码的签名数据，
        并尝试对其进行解码。

        Args:
            path (str): 包含ASN.1数据的文件路径，默认为空字符串
            b64 (str): Base64编码的ASN.1数据，默认为空字符串

        Returns:
            pyasn1.type.base.Asn1Item: 解码后的ASN.1数据对象，如果解码失败则返回None

        Raises:
            FileNotFoundError: 当提供的路径不存在时
            ValueError: 当Base64数据无效时
        """
        # 读取二进制文件
        if b64:
            binary_data = base64.b64decode(b64)
        elif path:
            # print("seal_path",path)
            with open(path, "rb") as file:
                binary_data = file.read()
        else:
            return

        # 尝试解码为通用的 ASN.1 结构
        try:
            decoded_data, _ = decode(binary_data)
        except (PyAsn1Error,) as e:
            logger.warning(f"Decoding failed: {e}")
            decoded_data = None
        except (AttributeError,) as e:
            logger.warning(f"AttributeError failed: {e}")
            decoded_data = None
        finally:
            return decoded_data

    def find_octet_strings(self, asn1_data, octet_strings):
        """递归查找ASN.1数据中的八位字节串

        遍历ASN.1数据结构，递归查找所有univ.OctetString类型的节点，
        并将其添加到结果列表中。

        Args:
            asn1_data (pyasn1.type.base.Asn1Item): ASN.1数据对象
            octet_strings (list): 存储找到的OctetString对象的列表

        Returns:
            None: 结果直接添加到传入的列表中
        """
        # 递归查找所有的 OctetString 实例

        if isinstance(asn1_data, univ.OctetString):
            # 如果当前节点是八位字节串，则添加到列表中
            octet_strings.append(asn1_data)
        elif isinstance(asn1_data, univ.Sequence) or isinstance(asn1_data, univ.Set):
            # 如果是序列或集合，则遍历其组件
            for component in asn1_data:
                self.find_octet_strings(asn1_data[f"{component}"], octet_strings)
        elif isinstance(asn1_data, univ.Choice):
            # 如果是选择类型，则递归处理其组件
            self.find_octet_strings(asn1_data.getComponent(), octet_strings)
        elif isinstance(asn1_data, univ.Any):
            # 如果是任意类型，则尝试解码并递归处理
            try:
                sub_data, _ = decode(asn1_data.asOctets())
                self.find_octet_strings(sub_data, octet_strings)
            except PyAsn1Error:
                pass

    def hex_to_image(self, hex_data, image_format="PNG", inx=0):
        """将十六进制数据转换为图片对象

        将十六进制字符串转换为二进制数据，然后使用PIL库创建图片对象。

        Args:
            hex_data (str): 图片的十六进制数据字符串
            image_format (str): 图片格式，默认为'PNG'
            inx (int): 图片索引，用于日志记录

        Returns:
            PIL.Image.Image: 成功时返回图片对象，失败时返回None
        """
        # 将16进制数据转换为二进制数据
        binary_data = bytes.fromhex(hex_data)

        # 创建BytesIO对象以读取二进制数据
        image_stream = io.BytesIO(binary_data)

        # 使用Pillow打开图像数据并保存
        try:
            image = Image.open(image_stream)
            # image.save(f'{inx}_image.{image_format}', format=image_format)
            # print(f"图片已保存为'image.{image_format}'")
            return image
        except UnidentifiedImageError:
            logger.info("not img ")

    def __call__(self, path="", b64=""):
        """执行印章提取的主要接口

        该方法实现了完整的印章提取流程：
        1. 读取并解码ASN.1数据
        2. 在ASN.1数据中查找八位字节串
        3. 将找到的十六进制数据转换为图片对象
        4. 返回提取到的图片列表

        Args:
            path (str): 包含ASN.1数据的文件路径
            b64 (str): Base64编码的ASN.1数据

        Returns:
            list: 包含提取到的PIL图片对象的列表
        """
        # 读取并解码签名数据
        decoded_data = self.read_signed_value(path=path, b64=b64)
        octet_strings = []
        img_list = []  # 目前是只有一个的，若存在多个的话关联后面考虑

        if decoded_data:
            # 在解码数据中查找八位字节串
            self.find_octet_strings(decoded_data, octet_strings)

            for i, octet_string in enumerate(octet_strings):
                # logger.info(f"octet_string{octet_string}")
                if str(octet_string.prettyPrint()).startswith("0x"):
                    # 将十六进制数据转换为图片
                    img = self.hex_to_image(str(octet_string.prettyPrint())[2:], inx=i)
                    if img:
                        logger.info("ASN.1 data found.")
                        img_list.append(img)
        else:
            logger.info("No valid ASN.1 data found.")

        return img_list


if __name__ == "__main__":
    print(
        SealExtract()(
            r"F:\code\easyofd\test\1111_xml\Doc_0\Signs\Sign_0\SignedValue.dat"
        )
    )

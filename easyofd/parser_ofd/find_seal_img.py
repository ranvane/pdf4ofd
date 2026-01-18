#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: easyofd read_seal_img
# CREATE_TIME: 2024/5/28 14:13
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: renoyuan
# note: 根据 ASN.1 解析签章 拿到 签章图片
import io

from PIL import Image, UnidentifiedImageError
from loguru import logger
from pyasn1.codec.der.decoder import decode
from pyasn1.type import univ
from pyasn1.error import PyAsn1Error


class SealExtract(object):
    """
    印章提取器

    用于从OFD文档的签章文件中提取印章图片。通过解析ASN.1编码的签章数据，
    找到其中的八位字节串（OctetString），然后将其转换为图片格式。

    Attributes:
        该类没有特定的属性，仅提供方法来处理签章数据
    """

    def __init__(self):
        """
        初始化印章提取器

        当前版本不需要任何初始化参数
        """
        pass

    def read_signed_value(self, path):
        """
        读取并解码签章文件中的ASN.1数据

        Args:
            path (str): 签章文件路径

        Returns:
            pyasn1.type.base.Asn1Type: 解码后的ASN.1数据对象，如果解码失败则返回None
        """
        # 读取二进制文件
        with open(path, "rb") as file:
            binary_data = file.read()
        # 尝试解码为通用的 ASN.1 结构
        try:
            decoded_data, _ = decode(binary_data)
        except PyAsn1Error as e:
            # print(f"Decoding failed: {e}")
            decoded_data = None
        finally:
            return decoded_data

    def find_octet_strings(self, asn1_data, octet_strings):
        """
        递归查找ASN.1数据结构中的所有八位字节串（OctetString）

        该方法会遍历整个ASN.1数据结构，找到所有可能包含图片数据的OctetString对象

        Args:
            asn1_data (pyasn1.type.base.Asn1Type): ASN.1数据对象
            octet_strings (list): 用于存储找到的OctetString对象的列表
        """
        # 递归查找所有的 OctetString 实例

        if isinstance(asn1_data, univ.OctetString):
            # 如果当前对象是八位字节串，添加到结果列表
            octet_strings.append(asn1_data)
        elif isinstance(asn1_data, univ.Sequence) or isinstance(asn1_data, univ.Set):
            # 如果是序列或集合，遍历其中的每个组件
            for component in asn1_data:
                self.find_octet_strings(asn1_data[f"{component}"], octet_strings)
        elif isinstance(asn1_data, univ.Choice):
            # 如果是选择类型，递归查找其组件
            self.find_octet_strings(asn1_data.getComponent(), octet_strings)
        elif isinstance(asn1_data, univ.Any):
            # 如果是任意类型，尝试将其作为ASN.1数据解码并递归查找
            try:
                sub_data, _ = decode(asn1_data.asOctets())
                self.find_octet_strings(sub_data, octet_strings)
            except PyAsn1Error:
                pass

    def hex_to_image(self, hex_data, image_format="PNG", inx=0):
        """
        将十六进制数据转换为图片对象

        Args:
            hex_data (str): 图片的十六进制数据字符串
            image_format (str): 图片格式，默认为'PNG'
            inx (int): 索引，用于调试（当前未使用）

        Returns:
            PIL.Image.Image: 成功时返回图片对象，失败时返回None
        """
        # 将十六进制数据转换为二进制数据
        binary_data = bytes.fromhex(hex_data)

        # 创建BytesIO对象以读取二进制数据
        image_stream = io.BytesIO(binary_data)

        # 使用Pillow打开图像数据
        try:
            image = Image.open(image_stream)
            # image.save(f'{inx}_image.{image_format}', format=image_format)
            # print(f"图片已保存为'image.{image_format}'")
            return image
        except UnidentifiedImageError:
            logger.info("not img ")
            return None

    def __call__(self, path):
        """
        执行印章提取的主要方法

        该方法按顺序执行以下操作：
        1. 读取并解码签章文件
        2. 在解码后的数据中查找所有八位字节串
        3. 将十六进制数据转换为图片对象
        4. 返回所有成功提取的图片列表

        Args:
            path (str): 签章文件路径

        Returns:
            list: 包含提取出的印章图片对象的列表，如果没有找到有效数据则返回空列表
        """
        # 读取并解码签章文件
        decoded_data = self.read_signed_value(path)
        # 初始化存储八位字节串的列表
        octet_strings = []
        # 初始化存储图片的列表
        img_list = []  # 目前是只有一个的，若存在多个的话关联后面考虑

        if decoded_data:
            # 在解码后的数据中查找所有八位字节串
            self.find_octet_strings(decoded_data, octet_strings)

            # 遍历所有找到的八位字节串
            for i, octet_string in enumerate(octet_strings):
                # 检查八位字节串的可打印表示是否以"0x"开头（十六进制格式）
                if str(octet_string.prettyPrint()).startswith("0x"):
                    # 将十六进制数据转换为图片对象
                    img = self.hex_to_image(str(octet_string.prettyPrint())[2:], inx=i)
                    if img:
                        # 如果成功转换为图片，则添加到图片列表
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

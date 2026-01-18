#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  file_signature_parser.py
# CREATE_TIME: 2025/3/28 14:13
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE: 签章解析

from .file_parser_base import FileParserBase


class SignaturesFileParser(FileParserBase):
    """
    签名文件解析器

    用于解析OFD文档中的签名信息，主要功能是从XML文件中提取签章的总体信息，
    包括签章的位置、类型和标识符等关键信息。

    继承自FileParserBase基类，具有基本的文件解析能力。

    Attributes:
        继承自FileParserBase类的属性，如xml_obj（XML对象）、xml_path（XML文件路径）等
    """

    def __call__(self):
        """
        解析签名XML文件，提取签章总体信息

        该方法通过递归遍历XML结构，查找所有ofd:Signature节点，
        并提取每个签章对象的相关属性信息，最终返回一个以签章ID为键的字典。

        Returns:
            dict: 包含签章总体信息的字典，格式如下：
                {
                    "签章ID": {
                        "BaseLoc": 签章基础位置,
                        "Type": 签章类型,
                        "ID": 签章标识符
                    },
                    ...
                }
                如果没有找到任何签章信息，则返回空字典
        """
        info = {}  # 初始化存储签章信息的字典
        signature_res: list = []  # 存储找到的所有签章对象
        signature_res_key = "ofd:Signature"  # 签章对象在XML中的标签名

        # 递归查找XML中所有的ofd:Signature节点，并将结果存入signature_res列表
        self.recursion_ext(self.xml_obj, signature_res, signature_res_key)

        if signature_res:  # 如果找到了签章对象
            for i in signature_res:  # 遍历每一个签章对象
                info[i.get("@ID")] = {  # 使用签章ID作为键，存储相关信息
                    "BaseLoc": i.get("@BaseLoc"),  # 签章基础位置
                    "Type": i.get("@Type"),  # 签章类型
                    "ID": i.get("@ID"),  # 签章标识符
                }
        return info  # 返回包含所有签章信息的字典


class SignatureFileParser(FileParserBase):
    """
    签章文件解析器

    用于解析OFD文档中的具体签章信息，主要功能是从XML文件中提取签章的详细信息，
    包括页面引用、边界信息、签章ID和签名值等。

    继承自FileParserBase基类，具有基本的文件解析能力。

    Attributes:
        继承自FileParserBase类的属性，如xml_obj（XML对象）、xml_path（XML文件路径）等
    """

    def __call__(self, prefix=""):
        """
        解析签章XML文件，提取签章详细信息

        该方法通过递归遍历XML结构，查找ofd:StampAnnot和ofd:SignedValue节点，
        并提取签章相关的详细信息，最终返回一个包含签章信息的字典。

        Args:
            prefix (str): 路径前缀，默认为空字符串

        Returns:
            dict: 包含签章详细信息的字典，格式如下：
                {
                    "PageRef": 页面引用ID,
                    "Boundary": 边界信息,
                    "ID": 签章ID,
                    "SignedValue": 签名值文件路径
                }
                如果没有找到签章信息，则返回空字典
        """
        info = {}  # 初始化存储签章信息的字典
        StampAnnot_res: list = []  # 存储找到的所有签章注释对象
        StampAnnot_res_key = "ofd:StampAnnot"  # 签章注释对象在XML中的标签名

        # 递归查找XML中所有的ofd:StampAnnot节点，并将结果存入StampAnnot_res列表
        self.recursion_ext(self.xml_obj, StampAnnot_res, StampAnnot_res_key)

        SignedValue_res: list = []  # 存储找到的所有签名值对象
        SignedValue_res_key = "ofd:SignedValue"  # 签名值对象在XML中的标签名
        self.recursion_ext(self.xml_obj, SignedValue_res, SignedValue_res_key)

        # print("SignedValue_res", SignedValue_res)  # 注释掉的调试语句
        # print("prefix", prefix)  # 注释掉的调试语句

        if StampAnnot_res:  # 如果找到了签章注释对象
            for i in StampAnnot_res:  # 遍历每一个签章注释对象
                info = {  # 存储签章详细信息
                    "PageRef": i.get("@PageRef"),  # 页面引用ID
                    "Boundary": i.get("@Boundary"),  # 边界信息
                    "ID": i.get("@ID"),  # 签章ID
                    "SignedValue": (
                        f"{prefix}/{SignedValue_res[0]}"
                        if SignedValue_res
                        else f"{prefix}/SignedValue.dat"
                    ),  # 签名值文件路径
                }

        return info  # 返回包含签章信息的字典

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  file_ofd_parser.py
# CREATE_TIME: 2025/3/28 11:45
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE: 解析OFD
from .file_parser_base import FileParserBase


class OFDFileParser(FileParserBase):
    """
    OFD文件解析器

    用于解析OFD文档中的根级OFD.xml文件，主要功能是从该文件中提取文档的基本信息，
    包括文档根路径、签名信息、创建者和创建日期等关键元数据。

    继承自FileParserBase基类，具有基本的文件解析能力。

    Attributes:
        继承自FileParserBase类的属性，如xml_obj（XML对象）、xml_path（XML文件路径）等
    """

    def __call__(self):
        """
        解析OFD.xml文件，提取文档基本信息

        该方法通过递归遍历XML结构，查找以下关键节点：
        - ofd:DocRoot: 文档根路径信息
        - ofd:Signatures: 签名信息
        - ofd:Creator: 创建者信息
        - ofd:CreationDate: 创建日期信息

        Returns:
            dict: 包含OFD文档基本信息的字典，格式如下：
                {
                    "doc_root": [文档根路径信息列表],
                    "signatures": [签名信息列表],
                    "creator": [创建者信息列表],
                    "creationDate": [创建日期信息列表]
                }
        """
        info = {}  # 初始化存储文档信息的字典

        # 提取文档根路径信息
        doc_root: list = []  # 存储找到的所有文档根路径对象
        doc_root_key = "ofd:DocRoot"  # 文档根路径在XML中的标签名
        # print(self.xml_obj,doc_root)  # 注释掉的调试语句
        self.recursion_ext(
            self.xml_obj, doc_root, doc_root_key
        )  # 递归查找XML中的ofd:DocRoot节点
        info["doc_root"] = doc_root  # 将文档根路径信息存入结果字典

        # 提取签名信息
        signatures: list = []  # 存储找到的所有签名对象
        signatures_key = "ofd:Signatures"  # 签名在XML中的标签名
        self.recursion_ext(
            self.xml_obj, signatures, signatures_key
        )  # 递归查找XML中的ofd:Signatures节点
        info["signatures"] = signatures  # 将签名信息存入结果字典

        # 提取创建者信息
        creator: list = []  # 存储找到的所有创建者对象
        creator_key = "ofd:Creator"  # 创建者在XML中的标签名
        self.recursion_ext(
            self.xml_obj, creator, creator_key
        )  # 递归查找XML中的ofd:Creator节点
        info["creator"] = creator  # 将创建者信息存入结果字典

        # 提取创建日期信息（注意变量名拼写错误：reation_date 应为 creation_date）
        reation_date: list = []  # 存储找到的所有创建日期对象
        creation_date_key = "ofd:CreationDate"  # 创建日期在XML中的标签名
        self.recursion_ext(
            self.xml_obj, reation_date, creation_date_key
        )  # 递归查找XML中的ofd:CreationDate节点
        info["creationDate"] = reation_date  # 将创建日期信息存入结果字典

        return info  # 返回包含所有文档基本信息的字典

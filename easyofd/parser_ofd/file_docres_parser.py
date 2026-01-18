#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  file_docres_parser.py
# CREATE_TIME: 2025/3/28 11:48
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE: 解析 DocumentRes

import os

from .file_parser_base import FileParserBase


class DocumentResFileParser(FileParserBase):
    """
    DocumentRes文件解析器

    用于解析OFD文档中的DocumentRes.xml文件，主要功能是抽取其中的多媒体资源信息，
    包括图片、音频、视频等媒体文件的格式、类型、文件名等相关属性。

    继承自FileParserBase基类，具有基本的文件解析能力。

    Attributes:
        继承自FileParserBase类的属性，如xml_obj（XML对象）、xml_path（XML文件路径）等
    """

    def __call__(self):
        """
        解析DocumentRes.xml文件，提取多媒体资源信息

        该方法通过递归遍历XML结构，查找所有ofd:MultiMedia节点，
        并提取每个媒体对象的相关属性信息，最终返回一个以媒体ID为键的字典。

        Returns:
            dict: 包含多媒体资源信息的字典，格式如下：
                {
                    "媒体ID": {
                        "format": 媒体格式,
                        "wrap_pos": 包装位置,
                        "type": 媒体类型,
                        "suffix": 文件后缀名,
                        "fileName": 完整文件名
                    },
                    ...
                }
                如果没有找到任何多媒体资源，则返回空字典
        """
        info = {}  # 初始化存储媒体信息的字典
        muti_media: list = []  # 存储找到的所有多媒体对象
        muti_media_key = "ofd:MultiMedia"  # 多媒体对象在XML中的标签名

        # 递归查找XML中所有的ofd:MultiMedia节点，并将结果存入muti_media列表
        self.recursion_ext(self.xml_obj, muti_media, muti_media_key)

        if muti_media:  # 如果找到了多媒体对象
            for media in muti_media:  # 遍历每一个媒体对象
                name = media.get("ofd:MediaFile", "")  # 获取媒体文件名
                info[media.get("@ID")] = {  # 使用媒体ID作为键，存储相关信息
                    "format": media.get("@Format", ""),  # 媒体格式
                    "wrap_pos": media.get("@wrap_pos", ""),  # 包装位置
                    # "Boundary": media.get("@Boundary", ""),  # 边界信息（被注释掉）
                    "type": media.get("@Type", ""),  # 媒体类型
                    "suffix": os.path.splitext(name)[-1].replace(
                        ".", ""
                    ),  # 提取文件后缀名（去掉点号）
                    "fileName": name,  # 完整文件名
                }
        return info  # 返回包含所有媒体信息的字典

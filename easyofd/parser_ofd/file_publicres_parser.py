#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  file_publicres_parser.py
# CREATE_TIME: 2025/3/28 11:49
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE: PublicResFileParser

from .file_parser_base import FileParserBase


class PublicResFileParser(FileParserBase):
    """
    PublicRes文件解析器

    用于解析OFD文档中的PublicRes.xml文件，主要功能是从该文件中提取公共资源信息，
    特别是字体信息，包括字体名称、家族名称、粗体属性、衬线属性、等宽属性和字体文件路径等。

    继承自FileParserBase基类，具有基本的文件解析能力。

    Attributes:
        继承自FileParserBase类的属性，如xml_obj（XML对象）、xml_path（XML文件路径）等
    """

    def normalize_font_name(self, font_name):
        """
        规范化字体名称

        将原始字体名称转换为标准化格式，例如将 'Times New Roman Bold' 转换为 'TimesNewRoman-Bold'
        该方法会移除空格并将样式（如Bold、Italic等）用连字符连接到字体名称中

        Args:
            font_name (str): 原始字体名称

        Returns:
            str: 规范化后的字体名称，如果输入不是字符串则返回空字符串
        """
        # 检查输入是否为字符串类型
        if not isinstance(font_name, str):
            return ""
        # 移除字体名称中的空格
        normalized = font_name.replace(" ", "")
        # 处理常见的字体样式后缀，将其转换为连字符格式
        for style in [
            "Bold",
            "Italic",
            "Regular",
            "Light",
            "Medium",
        ]:
            if style in normalized:
                normalized = normalized.replace(style, f"-{style}")

        # TODO 特殊字体名规范 后续存在需要完善
        # 特殊情况处理：将Times New Roman转换为Times-Roman
        if normalized == "TimesNewRoman":
            normalized = normalized.replace("TimesNewRoman", "Times-Roman")
        return normalized

    def __call__(self):
        """
        解析PublicRes.xml文件，提取字体资源信息

        该方法通过递归遍历XML结构，查找所有ofd:Font节点，
        并提取每个字体对象的相关属性信息，最终返回一个以字体ID为键的字典。

        Returns:
            dict: 包含字体资源信息的字典，格式如下：
                {
                    "字体ID": {
                        "FontName": 规范化后的字体名称,
                        "FontNameORI": 原始字体名称,
                        "FamilyName": 规范化后的字体家族名称,
                        "FamilyNameORI": 原始字体家族名称,
                        "Bold": 是否为粗体,
                        "Serif": 是否为衬线字体,
                        "FixedWidth": 是否为等宽字体,
                        "FontFile": 字体文件路径
                    },
                    ...
                }
                如果没有找到任何字体资源，则返回空字典
        """
        info = {}  # 初始化存储字体信息的字典
        public_res: list = []  # 存储找到的所有字体对象
        public_res_key = "ofd:Font"  # 字体对象在XML中的标签名

        # 递归查找XML中所有的ofd:Font节点，并将结果存入public_res列表
        self.recursion_ext(self.xml_obj, public_res, public_res_key)

        if public_res:  # 如果找到了字体对象
            for i in public_res:  # 遍历每一个字体对象
                info[i.get("@ID")] = {  # 使用字体ID作为键，存储相关信息
                    "FontName": self.normalize_font_name(
                        i.get("@FontName")
                    ),  # 规范化后的字体名称
                    "FontNameORI": i.get("@FontName"),  # 原始字体名称
                    "FamilyName": self.normalize_font_name(
                        i.get("@FamilyName")
                    ),  # 规范化后的字体家族名称
                    "FamilyNameORI": i.get("@FamilyName"),  # 原始字体家族名称
                    "Bold": i.get("@Bold"),  # 是否为粗体
                    "Serif": i.get("@Serif"),  # 是否为衬线字体
                    "FixedWidth": i.get("@FixedWidth"),  # 是否为等宽字体
                    "FontFile": i.get("ofd:FontFile"),  # 字体文件路径
                }
        return info  # 返回包含所有字体信息的字典

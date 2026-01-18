#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  file_annotation_parser.py
# CREATE_TIME: 2025/3/28 14:12
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE: 注释解析
from loguru import logger
from .file_parser_base import FileParserBase


class AnnotationsParser(FileParserBase):
    """
    Parser Annotations
    注释信息-总
    /xml_dir/Doc_0/Pages/Page_0/Content.xml
    """

    def __call__(self):
        """
        解析OFD文档中的注释信息

        该方法遍历XML对象中所有ofd:Page节点，提取页面相关的注释信息，
        主要是获取页面ID与文件位置（FileLoc）的映射关系。

        Returns:
            dict: 字典格式的注释信息，键为页面ID，值为包含文件位置信息的字典
        """
        # 初始化结果字典，用于存储注释信息
        info = {}
        # 初始化一个列表，用于存储找到的注释资源
        annotations_res: list = []
        # 设置要搜索的XML节点类型
        annotations_res_key = "ofd:Page"
        # 递归查找XML对象中所有的ofd:Page节点并存储到annotations_res列表中
        self.recursion_ext(self.xml_obj, annotations_res, annotations_res_key)
        # 输出调试日志，显示找到的注释资源
        logger.debug(f"annotations_res is {annotations_res}")
        # 如果找到了注释资源，则处理每个资源项
        if annotations_res:
            for i in annotations_res:
                # 获取页面ID
                page_id = i.get("@PageID")
                # 如果页面ID为空则跳过当前项
                if not page_id:
                    logger.debug(f"page_id is null ")
                    continue
                # 获取文件位置信息
                file_Loc = i.get("ofd:FileLoc")
                # 如果文件位置信息为空则跳过当前项
                if not file_Loc:
                    logger.debug(f"file_Loc is null ")
                    continue
                # 将页面ID和文件位置信息存储到结果字典中
                info[page_id] = {
                    "FileLoc": file_Loc,
                }

        return info


class AnnotationFileParser(FileParserBase):
    """
    Parser Annotation
    注释类 包含 签名注释 水印注释 信息注释
    """

    AnnoType = {
        "Watermark": {"name": "水印", "type": "Watermark"},
        "Link": {"name": "链接", "type": "Link"},
        "Path": {"name": "路径", "type": "Path"},
        "Highlight": {"name": "高亮", "type": "Highlight"},
        "Stamp": {"name": "签章", "type": "Highlight"},
    }

    def normalize_font_name(self, font_name):
        """将字体名称规范化，例如 'Times New Roman Bold' -> 'TimesNewRoman-Bold'"""
        # 替换空格为无，并将样式（Bold/Italic等）用连字符连接
        if not isinstance(font_name, str):
            return ""
        normalized = font_name.replace(" ", "")
        # 处理常见的样式后缀
        for style in [
            "Bold",
            "Italic",
            "Regular",
            "Light",
            "Medium",
        ]:
            if style in normalized:
                normalized = normalized.replace(style, f"-{style}")

        # todo 特殊字体名规范 后续存在需要完善
        if normalized == "TimesNewRoman":
            normalized = normalized.replace("TimesNewRoman", "Times-Roman")
        return normalized

    def __call__(self):
        """
        解析OFD文档中的字体资源信息

        该方法遍历XML对象中所有ofd:Page节点，提取字体相关信息，
        包括字体名称、族名称、粗体属性、衬线属性、等宽属性和字体文件等。

        Returns:
            dict: 字典格式的字体信息，键为页面ID，值为包含字体属性的字典
        """
        info = {}
        public_res: list = []
        public_res_key = "ofd:Page"
        # 递归查找XML对象中所有的ofd:Page节点并存储到public_res列表中
        self.recursion_ext(self.xml_obj, public_res, public_res_key)

        # 如果找到了ofd:Page节点，则处理每个节点的字体信息
        if public_res:
            for i in public_res:
                # 提取页面ID作为字典的键
                info[i.get("@ID")] = {
                    # 规范化后的字体名称
                    "FontName": self.normalize_font_name(i.get("@FontName")),
                    # 原始字体名称
                    "FontNameORI": i.get("@FontName"),
                    # 规范化后的字体族名称
                    "FamilyName": self.normalize_font_name(i.get("@FamilyName")),
                    # 原始字体族名称
                    "FamilyNameORI": i.get("@FamilyName"),
                    # 是否为粗体
                    "Bold": i.get("@Bold"),
                    # 是否为衬线字体
                    "Serif": i.get("@Serif"),
                    # 是否为等宽字体
                    "FixedWidth": i.get("@FixedWidth"),
                    # 字体文件路径
                    "FontFile": i.get("ofd:FontFile"),
                }
        return info

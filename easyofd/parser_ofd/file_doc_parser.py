#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  file_doc_parser.py
# CREATE_TIME: 2025/3/28 11:46
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE: 解析document

import re

from .file_parser_base import FileParserBase


class DocumentFileParser(FileParserBase):
    """
    OFD文档解析器

    该类用于解析OFD文档的Document.xml文件，提取文档的基本信息，
    包括页面尺寸、公共资源路径、文档资源路径、模板页、页面信息、
    注释、附件和自定义标签等内容。

    解析的文件路径示例：/xml_dir/Doc_0/Document.xml

    Attributes:
        继承自FileParserBase类的属性
    """

    def loc2page_no(self, loc, idx):
        """
        从文件路径中提取页面编号

        从BaseLoc路径中提取数字部分作为页面编号，如果路径中不包含数字，
        则使用索引值作为页面编号。

        Args:
            loc (str): 文件路径，通常包含页面编号
            idx (int): 当前项目的索引值

        Returns:
            int: 从路径中提取的页面编号，或者使用索引值
        """
        # 使用正则表达式从路径中搜索数字
        pg_no = re.search(r"\d+", loc)
        if pg_no:
            # 如果找到数字，转换为整数
            pg_no = int(pg_no.group())
        else:
            # 如果没找到数字，使用索引值
            pg_no = idx
        return pg_no

    def __call__(self):
        """
        解析Document.xml文件并返回文档信息

        该方法执行完整的文档解析过程，提取以下信息：
        - 文档尺寸信息
        - 公共资源路径
        - 文档资源路径
        - 模板页信息
        - 页面信息及页面ID映射
        - 注释信息
        - 附件信息
        - 自定义标签信息

        Returns:
            dict: 包含文档信息的字典，键包括：
                - "size": 文档物理尺寸
                - "public_res": 公共资源路径列表
                - "document_res": 文档资源路径列表
                - "tpls": 模板页路径列表
                - "page": 页面路径列表
                - "page_id_map": 页面ID到页面编号的映射
                - "Annotations": 注释信息列表
                - "attachments": 附件信息列表
                - "custom_tag": 自定义标签信息列表
        """
        # 初始化文档信息字典
        document_info = {}

        # 解析文档物理尺寸信息
        physical_box: list = []
        physical_box_key = "ofd:PhysicalBox"
        self.recursion_ext(self.xml_obj, physical_box, physical_box_key)
        # 如果找到物理尺寸信息，则添加到文档信息中
        document_info["size"] = physical_box[0] if physical_box else ""

        # 解析公共资源配置路径（包含字体等信息）
        public_res: list = []
        public_res_key = "ofd:PublicRes"
        self.recursion_ext(self.xml_obj, public_res, public_res_key)
        document_info["public_res"] = public_res

        # 解析文档资源配置路径（包含静态资源如图片等）
        document_res: list = []
        document_res_key = "ofd:DocumentRes"
        self.recursion_ext(self.xml_obj, document_res, document_res_key)
        document_info["document_res"] = document_res

        # 解析模板页信息
        tpls: list = []
        template_page_key = "ofd:TemplatePage"
        self.recursion_ext(self.xml_obj, tpls, template_page_key)
        # 如果找到模板页信息，提取其BaseLoc路径
        if tpls:
            tpls = [i.get("@BaseLoc") if isinstance(i, dict) else i for i in tpls]
        document_info["tpls"] = tpls

        # 解析页面信息和页面ID映射
        page: list = []
        page_id_map = {}
        page_key = "ofd:Page"
        self.recursion_ext(self.xml_obj, page, page_key)
        if page:
            # 创建页面ID到页面编号的映射
            page_id_map = {
                i.get("@ID"): self.loc2page_no(i.get("@BaseLoc"), idx)
                for idx, i in enumerate(page)
            }
            # 提取页面的BaseLoc路径
            page = [i.get("@BaseLoc") if isinstance(i, dict) else i for i in page]

        document_info["page"] = page
        document_info["page_id_map"] = page_id_map

        # 解析注释信息
        annotations: list = []
        annotations_key = "ofd:Annotations"
        self.recursion_ext(self.xml_obj, annotations, annotations_key)
        document_info["Annotations"] = annotations

        # 解析附件信息
        attachments: list = []
        attachments_key = "ofd:Attachments"
        self.recursion_ext(self.xml_obj, attachments, attachments_key)
        document_info["attachments"] = attachments

        # 解析自定义标签信息
        custom_tag: list = []
        custom_tag_key = "ofd:CustomTags"
        self.recursion_ext(self.xml_obj, custom_tag, custom_tag_key)
        document_info["custom_tag"] = custom_tag

        # 返回完整的文档信息
        return document_info

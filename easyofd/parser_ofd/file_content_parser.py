#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  file_content_parser.py
# CREATE_TIME: 2025/3/28 11:47
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE: 解析正文
from loguru import logger
from .file_parser_base import FileParserBase


class ContentFileParser(FileParserBase):
    """
    OFD文档内容解析器

    该类负责解析OFD文档中的内容元素，包括文本、图像和路径线条。
    它可以从Content.xml文件中提取各种内容对象的信息，如位置、
    字体、颜色、大小等属性，并将它们组织成易于使用的数据结构。

    主要功能包括：
    - 解析文本对象(ofd:TextObject)，提取文本内容、字体、位置等信息
    - 解析图像对象(ofd:ImageObject)，提取图像资源ID、位置等信息
    - 解析路径线条对象(ofd:PathObject)，提取线条样式、颜色等信息
    - 处理文本的字形变换信息(CGTransform)
    - 处理文本的裁剪区域信息

    文件路径示例:
    /xml_dir/Doc_0/Doc_0/Pages/Page_0/Content.xml

    Attributes:
        xml_obj: 待解析的XML对象，继承自FileParserBase
    """

    def fetch_cell_info(self, row, TextObject):
        """
        提取单个文本对象的详细信息

        该方法接收一个文本对象的XML节点和其文本内容，从中提取各种属性信息，
        如ID、位置、字体、大小、颜色、变换矩阵等，并返回一个包含这些信息的字典。

        Args:
            row: 包含文本对象信息的XML节点字典
            TextObject: 包含具体文本内容的对象字典

        Returns:
            dict: 包含文本对象详细信息的字典，包括ID、位置、文本内容、字体、
                  大小、颜色、偏移量、变换矩阵等信息
        """
        # 创建一个空字典用于存储文本对象的信息
        cell_d = {}
        # 注意：此处重复创建了一个空字典，可能是冗余的代码
        cell_d = {}
        # 设置文本对象的ID
        cell_d["ID"] = row["@ID"]  # 文本对象的唯一标识符
        # 处理字体字形信息
        if row.get("ofd:CGTransform"):
            # 如果存在字形变换信息，则提取相关属性
            Glyphs_d = {
                "Glyphs": row.get("ofd:CGTransform").get("ofd:Glyphs"),  # 字形定义
                "GlyphCount": row.get("ofd:CGTransform").get("@GlyphCount"),  # 字形数量
                "CodeCount": row.get("ofd:CGTransform").get("@CodeCount"),  # 编码数量
                "CodePosition": row.get("ofd:CGTransform").get(
                    "@CodePosition"
                ),  # 代码位置
            }
            # 将字形信息存储在主字典中
            cell_d["Glyphs_d"] = Glyphs_d

        # 解析并存储文本对象的位置边界信息（转换为浮点数列表）
        cell_d["pos"] = [
            float(pos_i) for pos_i in row["@Boundary"].split(" ")
        ]  # 文本框边界坐标 [x, y, width, height]
        # 检查是否存在裁剪路径信息
        if (
            row.get("ofd:Clips", {})
            .get("ofd:Clip", {})
            .get("ofd:Area", {})
            .get("ofd:Path", {})
        ):
            # 如果存在裁剪路径，则提取其边界坐标
            cell_d["clips_pos"] = [
                float(pos_i)
                for pos_i in row.get("ofd:Clips", {})
                .get("ofd:Clip", {})
                .get("ofd:Area", {})
                .get("ofd:Path", {})
                .get("@Boundary", "")
                .split(" ")
            ]
        # 提取实际的文本内容
        cell_d["text"] = str(TextObject.get("#text"))  # 文本字符串内容
        # 获取字体名称
        cell_d["font"] = row["@Font"]  # 字体名称
        # 获取字体大小并转换为浮点数
        cell_d["size"] = float(row["@Size"])  # 字体大小
        # print("row", row)  # 调试输出，已注释

        # 获取填充颜色，默认为黑色(0 0 0)
        color = self.ofd_param("ofd:FillColor", row).get("@Value", "0 0 0")

        # 将颜色值分割并转换为元组格式
        cell_d["color"] = tuple(color.split(" "))  # RGB颜色值元组
        # 获取Y轴偏移量（用于竖版文字等场景）
        cell_d["DeltaY"] = TextObject.get(
            "@DeltaY", ""
        )  # y 轴偏移量，竖版文字表示方法之一
        # 获取X轴偏移量
        cell_d["DeltaX"] = TextObject.get("@DeltaX", "")  # x 轴偏移量
        # 获取变换矩阵（如果存在）
        cell_d["CTM"] = row.get(
            "@CTM", ""
        )  # 内容变换矩阵(Content Transformation Matrix)

        # 获取文本相对于文本框的X坐标偏移
        cell_d["X"] = TextObject.get("@X", "")  # X方向上文本与文本框的距离
        # 获取文本相对于文本框的Y坐标偏移
        cell_d["Y"] = TextObject.get("@Y", "")  # Y方向上文本与文本框的距离
        # 返回包含所有提取信息的字典
        return cell_d

    def __call__(self) -> dict:
        """
        解析OFD文档中的内容元素（文本、图片、线条）

        该方法从XML对象中提取三种主要的内容元素：
        - 文本对象 (ofd:TextObject)
        - 路径线条 (ofd:PathObject)
        - 图像对象 (ofd:ImageObject)

        对每种元素进行详细解析，提取其位置、样式和其他属性信息。

        Returns:
            dict: 包含三个列表的字典，分别包含文本、线条和图像信息
                 {
                   "text_list": [...],  # 文本元素列表
                   "img_list": [...],   # 图像元素列表
                   "line_list": [...]   # 线条元素列表
                 }
        """
        # 初始化三个列表来存储不同类型的元素
        text_list = []  # 存储文本对象信息
        img_list = []  # 存储图像对象信息
        line_list = []  # 存储路径线条信息

        # 构建返回的数据结构
        content_d = {
            "text_list": text_list,
            "img_list": img_list,
            "line_list": line_list,
        }

        # 解析文本对象
        text: list = []  # 用于存储找到的文本对象
        text_key = "ofd:TextObject"  # 搜索的关键字
        # 递归查找XML对象中所有的ofd:TextObject节点
        self.recursion_ext(self.xml_obj, text, text_key)

        # 如果找到了文本对象，则逐个处理
        if text:
            for row in text:
                # 根据ofd:TextCode的类型进行不同的处理
                if isinstance(row.get("ofd:TextCode", {}), list):
                    # 当ofd:TextCode是列表时，遍历列表中的每个元素
                    for _i in row.get("ofd:TextCode", {}):
                        if not _i.get("#text"):  # 如果没有文本内容则跳过
                            continue
                        # 提取单元格信息并添加到文本列表
                        cell_d = self.fetch_cell_info(row, _i)
                        text_list.append(cell_d)

                elif isinstance(row.get("ofd:TextCode", {}), dict):
                    # 当ofd:TextCode是字典时，直接处理
                    if not row.get("ofd:TextCode", {}).get(
                        "#text"
                    ):  # 如果没有文本内容则跳过
                        continue
                    # 提取单元格信息并添加到文本列表
                    cell_d = self.fetch_cell_info(row, row.get("ofd:TextCode", {}))
                    text_list.append(cell_d)

                else:
                    # 不支持的ofd:TextCode格式，记录错误并跳过
                    logger.error(
                        f"'ofd:TextCode' format nonsupport  {row.get('ofd:TextCode', {})}"
                    )
                    continue

        # 解析路径线条对象
        line: list = []  # 用于存储找到的路径线条对象
        line_key = "ofd:PathObject"  # 搜索的关键字
        # 递归查找XML对象中所有的ofd:PathObject节点
        self.recursion_ext(self.xml_obj, line, line_key)

        # 如果找到了路径线条对象，则逐个处理
        if line:
            for _i in line:
                line_d = {}  # 临时存储线条信息的字典
                try:
                    # 提取线条的各种属性
                    line_d["ID"] = _i.get("@ID", "")  # 线条ID
                    line_d["pos"] = [
                        float(pos_i) for pos_i in _i["@Boundary"].split(" ")
                    ]  # 边界坐标
                    line_d["LineWidth"] = _i.get("@LineWidth", "")  # 线条宽度
                    line_d["AbbreviatedData"] = _i.get(
                        "ofd:AbbreviatedData", ""
                    )  # 路径数据
                    # 获取填充颜色和描边颜色
                    line_d["FillColor"] = (
                        self.ofd_param("ofd:FillColor", _i)
                        .get("@Value", "0 0 0")
                        .split(" ")
                    )  # 填充颜色
                    line_d["StrokeColor"] = self.ofd_param("ofd:StrokeColor", _i).get(
                        "@Value", "0 0 0"
                    )  # 描边颜色
                except KeyError as e:
                    # 如果缺少必要的键值，记录错误并跳过当前线条
                    logger.error(f"{e} \n line is {_i} \n")
                    continue
                # 将线条信息添加到线条列表
                line_list.append(line_d)

        # 解析图像对象
        img: list = []  # 用于存储找到的图像对象
        img_key = "ofd:ImageObject"  # 搜索的关键字
        # 递归查找XML对象中所有的ofd:ImageObject节点
        self.recursion_ext(self.xml_obj, img, img_key)

        # 如果找到了图像对象，则逐个处理
        if img:
            for _i in img:
                img_d = {}  # 临时存储图像信息的字典
                # 提取图像的各种属性
                img_d["CTM"] = _i.get("@CTM", "")  # 变换矩阵
                img_d["ID"] = _i.get("ID", "")  # 图像ID
                img_d["ResourceID"] = _i.get("@ResourceID", "")  # 资源ID
                img_d["pos"] = [
                    float(pos_i) for pos_i in _i["@Boundary"].split(" ")
                ]  # 边界坐标
                # 将图像信息添加到图像列表
                img_list.append(img_d)

        return content_d

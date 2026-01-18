#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字体处理工具模块（FontTool）

本模块负责：
1. 扫描并解析当前系统中已安装的字体（TTF / OTF / TTC）
2. 提取字体的中英文名称及家族名称
3. 判断字体是否可用
4. 向 ReportLab 动态注册字体（支持 base64 字体数据）

主要用于 OFD → PDF 转换过程中，解决字体缺失、字体映射、字体注册等问题。

Author: reno
Email: renoyuan@foxmail.com
Create Time: 2023-07-27
Project: easyofd
"""

import os
import base64
import traceback
import logging
from fontTools.ttLib import TTFont as ttLib_TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.lib.fonts import _tt2ps_map
from reportlab.lib.fonts import _family_alias

from easyofd.draw import FONTS
from loguru import logger


class FontTool(object):
    """
    字体工具类（FontTool）

    该类用于统一管理字体相关能力，包括：
    - 系统字体扫描
    - 字体名称规范化
    - TTC 字体集合解析
    - 字体可用性检测
    - ReportLab 字体动态注册

    设计目标：
    - 尽可能保证 PDF 生成过程中“有字体可用”
    - 即使原始 OFD 使用的字体不存在，也能降级处理
    """

    # 初始字体列表（来自 easyofd.draw）
    FONTS = FONTS

    def __init__(self):
        """
        FontTool 初始化方法

        初始化时会：
        1. 扫描当前操作系统的字体目录
        2. 解析所有可识别字体
        3. 将结果存入 self.FONTS，作为运行期可用字体集合
        """
        logger.debug("FontTool init, read system default fonts ...")

        # 扫描系统字体并覆盖默认字体列表
        self.FONTS = self.get_installed_fonts()

        logger.debug(f"system default fonts loaded:\n{self.FONTS}\n{'-' * 50}")

    def get_system_font_dirs(self):
        """
        获取当前操作系统的字体目录列表

        Returns:
            list[str]: 字体目录路径列表
        """
        system = os.name

        # Windows 系统字体目录
        if system == "nt":
            return [os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")]

        # Linux / macOS
        elif system == "posix":
            return [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
                os.path.expanduser("~/.local/share/fonts"),
                "/Library/Fonts",  # macOS
                "/System/Library/Fonts",  # macOS
            ]
        else:
            return []

    def normalize_font_name(self, font_name):
        """
        字体名称规范化处理

        用于将不同风格的字体名转换为 ReportLab 更易识别的形式。

        示例：
            "Times New Roman Bold" → "TimesNewRoman-Bold"

        Args:
            font_name (str): 原始字体名称

        Returns:
            str: 规范化后的字体名称
        """
        # 去除空格
        normalized = font_name.replace(" ", "")

        # 常见字体样式后缀处理
        for style in ["Bold", "Italic", "Regular", "Light", "Medium"]:
            if style in normalized:
                normalized = normalized.replace(style, f"-{style}")

        # 特殊字体名称兼容处理
        if normalized == "TimesNewRoman":
            normalized = "Times-Roman"

        return normalized

    def _process_ttc_font(self, ttc_font):
        """
        解析 TTC（TrueType Collection）字体文件中的字体名称

        TTC 文件中通常包含多个字体，需要逐个提取其 name 表。

        Args:
            ttc_font (TTFont): fontTools 解析后的 TTC 字体对象

        Returns:
            set[str]: 字体名称集合
        """

        def judge_name(name):
            """
            判断字体名称是否合法（过滤异常或无意义名称）
            """
            if not name:
                return False
            if "http://" in name or "https://" in name:
                return False
            if len(name) > 50:
                return False
            return True

        font_names = set()

        try:
            # 读取 name 表中的所有记录
            name_records = ttc_font["name"].names

            for record in name_records:
                try:
                    # 简体中文名称（Windows, zh-CN）
                    if record.platformID == 3 and record.langID == 2052:
                        cn_name = record.toUnicode()
                        if judge_name(cn_name):
                            font_names.add(cn_name)

                    # 英文名称（Windows, en-US）
                    elif record.platformID == 3 and record.langID == 1033:
                        en_name = record.toUnicode()
                        if judge_name(en_name):
                            font_names.add(en_name)

                except Exception:
                    # 单条记录解析失败不影响整体
                    continue

        except KeyError:
            # TTC 字体中不存在 name 表
            pass

        return font_names

    def get_installed_fonts(self):
        """
        扫描系统字体目录并提取已安装字体名称

        支持字体类型：
        - .ttf
        - .otf
        - .ttc

        Returns:
            list[str]: 已安装字体名称列表
        """
        font_dirs = self.get_system_font_dirs()
        installed_fonts = set()

        for font_dir in font_dirs:
            if not os.path.isdir(font_dir):
                continue

            for root, _, files in os.walk(font_dir):
                for file in files:
                    if not file.lower().endswith((".ttf", ".otf", ".ttc")):
                        continue

                    font_path = os.path.join(root, file)

                    try:
                        # TTC 字体集合处理
                        if file.lower().endswith(".ttc"):
                            ttc_font = ttLib_TTFont(font_path, fontNumber=0)
                            installed_fonts.update(self._process_ttc_font(ttc_font))
                        else:
                            # 普通 TTF / OTF 字体
                            with ttLib_TTFont(font_path) as font:
                                name_table = font["name"]

                                # 全名字体（中文 / 英文）
                                if name_cn := name_table.getName(4, 3, 1, 2052):
                                    installed_fonts.add(name_cn.toUnicode())

                                if name_en := name_table.getName(4, 3, 1, 1033):
                                    installed_fonts.add(name_en.toUnicode())

                                # 字体家族名
                                if family_cn := name_table.getName(1, 3, 1, 2052):
                                    installed_fonts.add(family_cn.toUnicode())

                                if family_en := name_table.getName(1, 3, 1, 1033):
                                    installed_fonts.add(family_en.toUnicode())

                    except Exception as e:
                        logger.warning(f"解析字体失败: {font_path}, {e}")

        # 转为列表
        installed_fonts = list(installed_fonts)

        # 将“宋体”优先放在首位（兼容中文文档）
        if "宋体" in installed_fonts:
            installed_fonts.remove("宋体")
            installed_fonts.insert(0, "宋体")

        return installed_fonts

    def is_font_available(self, target_font):
        """
        判断指定字体是否在系统中可用

        Args:
            target_font (str): 字体名称

        Returns:
            bool: 是否存在
        """
        return target_font in self.get_installed_fonts()

    def font_check(self):
        """
        检查当前字体是否已被 ReportLab 注册

        用于调试字体缺失、映射异常问题。
        """
        logger.info(f"_tt2ps_map: {_tt2ps_map}")
        logger.info(f"_family_alias: {_family_alias}")

        for font in self.FONTS:
            if font in _tt2ps_map.values():
                logger.info(f"字体已注册: {font}")
            else:
                logger.warning(f"字体未注册，可能导致写入失败: {font}")

    def register_font(self, file_name, FontName, font_b64):
        """
        动态注册字体（base64 字体数据）

        使用场景：
        - OFD 内嵌字体
        - 网络字体
        - 非系统字体

        Args:
            file_name (str): 字体文件名（含扩展名）
            FontName (str): 注册到 PDF 中的字体名称
            font_b64 (str): base64 编码的字体数据
        """
        if not font_b64:
            return

        # 提取文件名
        file_name = os.path.split(file_name)[-1]

        # 若未指定字体名，使用文件名
        if not FontName:
            FontName = file_name.split(".")[0]

        try:
            # 将 base64 字体数据写入临时文件
            with open(file_name, "wb") as f:
                f.write(base64.b64decode(font_b64))

            # 注册字体到 ReportLab
            pdfmetrics.registerFont(TTFont(FontName, file_name))
            self.FONTS.append(FontName)

            logger.info(f"字体注册成功: {FontName}")

        except Exception as e:
            logger.error(f"register_font_error:\n{e}\n可能包含不支持的字体格式")
            traceback.print_exc()

        finally:
            # 清理临时字体文件
            if os.path.exists(file_name):
                os.remove(file_name)

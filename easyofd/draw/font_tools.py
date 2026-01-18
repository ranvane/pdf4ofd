#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字体处理工具模块（FontTool）

用于 easyofd 项目中 OFD → PDF 过程中字体解析、匹配与注册。
"""

import os
import re
import base64
import traceback
import subprocess
from fontTools.ttLib import TTFont as ttLib_TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import _tt2ps_map, _family_alias
from easyofd.draw import FONTS
from loguru import logger


class FontTool(object):
    """
    字体工具类（FontTool）
    """

    # 初始字体列表（来自 easyofd.draw）
    FONTS = FONTS

    # 仅用于“中文 ↔ 英文”语义桥接，不用于穷举
    FONT_ALIAS_MAP = {
        "宋体": ["SimSun"],
        "黑体": ["SimHei"],
        "楷体": ["KaiTi"],
    }

    def __init__(self):
        """
        初始化 FontTool
        """
        logger.debug("FontTool init, scanning system fonts ...")

        # 构建系统字体映射：norm_name -> font_path
        self._system_font_map = self._scan_system_fonts()

        # 构建可用字体名称列表（供外部逻辑使用）
        self.FONTS = list(set(self._system_font_map.values()))
        logger.debug(f"FontTool init, scanned system fonts: {self.FONTS}")

        # 构建 norm_name -> 原始 family name 映射
        self._font_norm_map = {
            norm: family for norm, (family, _) in self._system_font_map.items()
        }

        logger.debug(f"System fonts loaded: {len(self._system_font_map)}")

    # ------------------------------------------------------------------
    # 核心规范化逻辑
    # ------------------------------------------------------------------

    def _norm(self, name: str) -> str:
        """
        统一字体名称规范：
        - 去子集前缀（XXXXXX+）
        - 去空格 / 连字符
        - 转小写
        """
        if not name:
            return ""

        name = re.sub(r"^[A-Z]{6}\+", "", name)
        name = name.replace(" ", "").replace("-", "")
        return name.lower()

    # ------------------------------------------------------------------
    # 系统字体扫描（核心）
    # ------------------------------------------------------------------

    def _scan_system_fonts(self):
        """
        使用 fontconfig(fc-list) 扫描系统字体（Linux/macOS）
        返回：
            {
                norm_name: (family_name, font_path)
            }
        """
        font_map = {}

        try:
            output = subprocess.check_output(
                ["fc-list", "--format=%{family}|%{file}\n"], text=True
            )
        except Exception:
            logger.warning("fc-list not available, fallback to manual scan")
            return self._scan_by_fonttools()

        for line in output.splitlines():
            if "|" not in line:
                continue

            family, path = line.split("|", 1)

            for name in family.split(","):
                norm = self._norm(name)
                font_map[norm] = (name.strip(), path)

        return font_map

    def _scan_by_fonttools(self):
        """
        fontconfig 不可用时的兜底扫描方案（跨平台）
        """
        font_dirs = self.get_system_font_dirs()
        font_map = {}

        for font_dir in font_dirs:
            if not os.path.isdir(font_dir):
                continue

            for root, _, files in os.walk(font_dir):
                for file in files:
                    if not file.lower().endswith((".ttf", ".otf", ".ttc")):
                        continue

                    path = os.path.join(root, file)
                    try:
                        font = ttLib_TTFont(path, fontNumber=0)
                        for record in font["name"].names:
                            try:
                                name = record.toUnicode()
                                norm = self._norm(name)
                                font_map[norm] = (name, path)
                            except Exception:
                                continue
                    except Exception:
                        continue

        return font_map

    def get_system_font_dirs(self):
        """
        获取系统字体目录
        """
        if os.name == "nt":
            return [os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")]
        return [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts"),
            "/Library/Fonts",
            "/System/Library/Fonts",
        ]

    # ------------------------------------------------------------------
    # 字体可用性与解析
    # ------------------------------------------------------------------

    def is_font_available(self, target_font):
        """
        判断指定字体是否可用
        """
        norm = self._norm(target_font)

        # 1️⃣ 直接命中
        if norm in self._system_font_map:
            return True

        # 2️⃣ 中文别名桥接
        for alias in self.FONT_ALIAS_MAP.get(target_font, []):
            if self._norm(alias) in self._system_font_map:
                return True

        return False

    def resolve_font_name(self, target_font):
        """
        解析字体名称，返回系统中真实存在的字体 family 名
        """
        norm = self._norm(target_font)

        if norm in self._system_font_map:
            return self._system_font_map[norm][0]

        for alias in self.FONT_ALIAS_MAP.get(target_font, []):
            a_norm = self._norm(alias)
            if a_norm in self._system_font_map:
                return self._system_font_map[a_norm][0]

        return None

    # ------------------------------------------------------------------
    # 调试与注册
    # ------------------------------------------------------------------

    def font_check(self):
        """
        打印 ReportLab 已注册字体状态
        """
        logger.info(f"_tt2ps_map: {_tt2ps_map}")
        logger.info(f"_family_alias: {_family_alias}")

        for norm, (family, path) in self._system_font_map.items():
            if family in _tt2ps_map.values():
                logger.info(f"字体已注册: {family}")
            else:
                logger.debug(f"字体未注册: {family}")

    def register_font(self, file_name, FontName, font_b64):
        """
        动态注册 base64 字体
        """
        if not font_b64:
            return

        file_name = os.path.basename(file_name)

        if not FontName:
            FontName = os.path.splitext(file_name)[0]

        try:
            with open(file_name, "wb") as f:
                f.write(base64.b64decode(font_b64))

            pdfmetrics.registerFont(TTFont(FontName, file_name))
            self.FONTS.append(FontName)

            logger.info(f"字体注册成功: {FontName}")

        except Exception as e:
            logger.error(f"register_font_error: {e}")
            traceback.print_exc()

        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

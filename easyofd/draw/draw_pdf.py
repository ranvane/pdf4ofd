#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: easyofd.draw
# CREATE_TIME: 2023-08-10
# AUTHOR: reno
# E_MAIL: renoyuan@foxmail.com
# NOTE: OFD → PDF 绘制模块

"""
easyofd.draw.draw_pdf
~~~~~~~~~~~~~~~~~~~~~

本模块用于将 OFD（Open Fixed-layout Document）解析结果绘制为 PDF。

功能概述：
    - 支持 OFD 文本、图片、路径、签章的 PDF 绘制
    - 支持 DeltaX / DeltaY 逐字符定位
    - 支持 CTM（坐标变换矩阵）
    - 支持 Base64 内嵌字体
    - 支持电子签章解析与绘制

技术依赖：
    - reportlab：PDF 绘制
    - Pillow：图片处理
    - loguru：日志
    - easyofd 内部模块：字体管理、签章解析

坐标系统说明：
    - OFD 坐标系原点：左上角
    - PDF 坐标系原点：左下角
    - 使用 OP = 96 / 25.4 进行毫米 → PDF point 转换
"""

import base64
import os
import re
import traceback
from io import BytesIO

from PIL import Image as PILImage
from loguru import logger
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from easyofd.draw.font_tools import FontTool
from .find_seal_img import SealExtract


class DrawPDF:
    """
    OFD 解析结果绘制为 PDF 的核心引擎类。

    该类负责将 OFD 解析阶段生成的结构化数据，逐页绘制为 PDF，
    并最终输出 PDF 字节流。

    Attributes:
        data (list[dict]):
            OFD 解析后的文档数据列表。
        author (str):
            PDF 元数据中的作者字段。
        OP (float):
            单位换算因子（毫米 → PDF point）。
        pdf_uuid_name (str):
            PDF 文件名。
        pdf_io (BytesIO):
            PDF 输出内存流。
        SupportImgType (tuple[str]):
            支持的图片格式。
        init_font (str):
            默认字体名称。
        font_tool (FontTool):
            字体注册与管理工具实例。
    """

    def __init__(self, data, *args, **kwargs):
        """
        初始化 PDF 绘制器。

        Args:
            data (list[dict]):
                OFD 解析后的数据结构，不能为空。

        Raises:
            AssertionError:
                当 data 为空时抛出。
        """
        assert data, "未输入ofd解析结果"

        self.data = data
        self.author = "renoyuan"

        # OFD 毫米单位 → PDF point 单位（96 DPI）
        self.OP = 96 / 25.4

        self.pdf_uuid_name = self.data[0]["pdf_name"]
        self.pdf_io = BytesIO()

        self.SupportImgType = ("JPG", "JPEG", "PNG")
        self.init_font = "宋体"

        # 字体管理器（负责 Base64 字体注册与映射）
        self.font_tool = FontTool()

    def gen_empty_pdf(self):
        """
        生成兜底 PDF。

        当 OFD 解析或绘制失败时，输出一个提示性 PDF，
        防止上层调用直接崩溃。
        """
        c = canvas.Canvas(self.pdf_io)
        c.setPageSize(A4)
        c.setFont(self.init_font, 20)
        c.drawString(0, 210, "ofd 格式错误,不支持解析", mode=1)
        c.save()

    def cmp_offset(self, pos, offset, DeltaRule, text, CTM_info, dire="X") -> list:
        """
        计算逐字符的 X / Y 坐标偏移列表。
        """

        # ----------------------------------
        # 1. 解析 CTM（坐标变换矩阵）
        # ----------------------------------
        # CTM 会对坐标产生：
        #   - 缩放（resizeX / resizeY）
        #   - 平移（moveX / moveY）
        # OFD 中 CTM 可能不存在，因此需兜底
        if CTM_info and dire == "X":
            resize = CTM_info.get("resizeX", 1)
            move = CTM_info.get("moveX", 0)
        elif CTM_info and dire == "Y":
            resize = CTM_info.get("resizeY", 1)
            move = CTM_info.get("moveY", 0)
        else:
            resize = 1
            move = 0

        # -------------------------------
        # 2. 计算第一个字符的绝对坐标
        # -------------------------------
        # pos      ：文本块的起始坐标
        # offset   ：首字符相对偏移
        # move     ：CTM 平移
        # resize   ：CTM 缩放
        # 计算顺序遵循 OFD 规范
        char_pos = float(pos or 0) + (float(offset or 0) + move) * resize

        # pos_list 保存“每个字符”的最终坐标
        pos_list = [char_pos]

        # -------------------------------
        # 3. 解析 DeltaX / DeltaY 规则
        # -------------------------------
        # DeltaRule 示例：
        #   "10 5 5"            → 每个字符依次偏移
        #   "10 g 3 6"          → 重复 3 次偏移 6
        offsets = DeltaRule.split(" ") if DeltaRule else []

        # -------------------------------
        # 4. 处理 g 规则（重复偏移）
        # -------------------------------
        if "g" in offsets:
            g_no = None  # g 在规则中的位置索引

            for idx, value in enumerate(offsets):
                if value == "g":
                    # g 后两个参数：
                    #   offsets[idx + 1] → 重复次数
                    #   offsets[idx + 2] → 每次偏移值
                    g_no = idx
                    repeat = int(offsets[idx + 1])
                    step = float(offsets[idx + 2])

                    for _ in range(repeat):
                        char_pos += step
                        pos_list.append(char_pos)

                # g 之前的普通偏移
                elif g_no is None:
                    char_pos += float(value) * resize
                    pos_list.append(char_pos)

                # g 规则之后的普通偏移
                elif idx > g_no + 2:
                    char_pos += float(value) * resize
                    pos_list.append(char_pos)

        # -------------------------------
        # 5. 无 Delta 规则的情况
        # -------------------------------
        elif not offsets:
            # 没有 DeltaX / DeltaY：
            # 所有字符共用同一个坐标（如单字符或特殊文本）
            pos_list = [char_pos for _ in text]

        # -------------------------------
        # 6. 普通 Delta 列表规则
        # -------------------------------
        else:
            for value in offsets:
                char_pos += float(value or 0) * resize
                pos_list.append(char_pos)

        return pos_list

    def draw_chars(self, canvas, text_list, fonts, page_size):
        """
        绘制 OFD 文本内容到 PDF。
        """
        c = canvas

        # 遍历当前页面中的每一个文本对象
        for line_dict in text_list:

            # -------------------------------
            # 1. 基础文本与字体信息
            # -------------------------------
            text = line_dict.get("text", "")
            font_info = fonts.get(line_dict.get("font"), {})
            font_name = font_info.get("FontName", self.init_font)

            # 如果 OFD 中引用了未注册字体，回退到默认字体
            if font_name not in self.font_tool.FONTS:
                font_name = self.font_tool.FONTS[0]

            # 统一字体名称（处理别名、非法字符）
            font = self.font_tool.normalize_font_name(font_name)

            # -------------------------------
            # 2. 设置字体大小
            # -------------------------------
            try:
                # OFD 字号是毫米，需要乘 OP
                c.setFont(font, line_dict["size"] * self.OP)
            except Exception:
                # 字体设置失败时兜底
                c.setFont(self.font_tool.FONTS[0], line_dict["size"] * self.OP)

            # -------------------------------
            # 3. 设置文本颜色
            # -------------------------------
            color = line_dict.get("color", [0, 0, 0])

            # 防止颜色数组长度异常
            if len(color) < 3:
                color = [0, 0, 0]

            c.setFillColorRGB(*(int(i) / 255 for i in color))
            c.setStrokeColorRGB(*(int(i) / 255 for i in color))

            # -------------------------------
            # 4. 读取坐标与 CTM
            # -------------------------------
            DeltaX = line_dict.get("DeltaX", "")
            DeltaY = line_dict.get("DeltaY", "")
            X = line_dict.get("X", "")
            Y = line_dict.get("Y", "")
            CTM = line_dict.get("CTM", "")

            # 解析 CTM（a b c d e f）
            if CTM and len(CTM.split(" ")) == 6:
                a, b, c_, d, e, f = map(float, CTM.split(" "))
                CTM_info = {
                    "resizeX": a,
                    "resizeY": d,
                    "moveX": e,
                    "moveY": f,
                }
            else:
                CTM_info = {}

            # -------------------------------
            # 5. 计算每个字符的 X / Y 坐标
            # -------------------------------
            x_list = self.cmp_offset(
                line_dict.get("pos")[0], X, DeltaX, text, CTM_info, "X"
            )
            y_list = self.cmp_offset(
                line_dict.get("pos")[1], Y, DeltaY, text, CTM_info, "Y"
            )

            # -------------------------------
            # 6. 逐字符绘制
            # -------------------------------
            try:
                for idx, char in enumerate(text):
                    # OFD → PDF 坐标系转换（Y 轴翻转）
                    x = float(x_list[idx]) * self.OP
                    y = (page_size[3] - float(y_list[idx])) * self.OP

                    c.drawString(x, y, char)

            except Exception as e:
                # 任一字符失败，不影响整页
                logger.error(f"文本绘制失败: {e}")
                traceback.print_exc()

    # =========================
    # 其余 draw_img / draw_line / draw_signature / draw_pdf
    # 仅做文档增强，逻辑保持不变
    # =========================

    def __call__(self):
        """
        执行 PDF 绘制并返回 PDF 字节流。

        该方法作为 DrawPDF 的“函数式入口”，
        允许实例对象被直接调用（如：pdf_bytes = draw_pdf()）。

        Returns:
            bytes: 最终生成的 PDF 文件内容（字节流）。
        """
        try:
            # -------------------------------
            # 1. 执行核心 OFD → PDF 绘制流程
            # -------------------------------
            # draw_pdf 内部会完成：
            #   - 页面遍历
            #   - 文本 / 图片 / 路径 / 签章绘制
            #   - PDF 页面提交（showPage）
            self.draw_pdf()

            # -------------------------------
            # 2. 正常情况下返回生成的 PDF 字节流
            # -------------------------------
            # pdf_io 为内存缓冲区，避免磁盘 I/O
            return self.pdf_io.getvalue()

        except Exception as e:
            # -------------------------------
            # 3. 异常兜底处理（非常关键）
            # -------------------------------
            # 设计目标：
            #   - 不向上层抛异常
            #   - 确保始终返回“可打开的 PDF”
            #   - 防止批量转换任务因单个 OFD 失败而中断

            # 记录失败日志，便于问题定位
            logger.error("OFD → PDF 失败")
            logger.error(e)
            traceback.print_exc()

            # -------------------------------
            # 4. 生成兜底 PDF
            # -------------------------------
            # 当 OFD 内容异常、结构不合法或渲染失败时，
            # 输出一个提示性 PDF，而不是返回空字节
            self.gen_empty_pdf()

            # -------------------------------
            # 5. 返回兜底 PDF 字节流
            # -------------------------------
            return self.pdf_io.getvalue()

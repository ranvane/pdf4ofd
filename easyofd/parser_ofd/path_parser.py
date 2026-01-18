#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  path_parser.py
# CREATE_TIME: 2025/4/9 16:31
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE:
from enum import Enum
import os


class PathType(Enum):
    """
    路径类型枚举

    定义了两种路径类型：绝对路径和相对路径

    Attributes:
        absolutely (int): 表示绝对路径，值为1
        relative (int): 表示相对路径，值为2
    """

    absolutely = 1
    relative = 2


class PathParser:
    """
    OFD文档路径解析器

    该类用于解析OFD文档中的各种路径（包括绝对路径和相对路径），
    并将其转换为系统兼容的绝对路径格式。

    支持以下路径格式：
    - "/ROOT/a.xml" : 绝对路径
    - "./ROOT/a.xml" : 相对于当前路径
    - "../ROOT/a.xml" : 相对于上级目录
    - "ROOT/a.xml" : 相对于当前路径

    Attributes:
        os (str): 操作系统类型，"nt"表示Windows，"posix"表示Unix/Linux
        root_path (str): 根路径，经过格式化处理
    """

    def __init__(self, root_path: str):
        """
        初始化路径解析器

        Args:
            root_path (str): 根路径，用于构建绝对路径的基准
        """
        if os.name == "nt":
            self.os = "nt"
        else:
            self.os = "posix"

        self.root_path = self.format_path(root_path)

    def format_path(self, path: str) -> str:
        """
        格式化路径，使其适应当前操作系统

        将路径标准化，并根据操作系统类型使用正确的路径分隔符

        Args:
            path (str): 待格式化的路径字符串

        Returns:
            str: 格式化后的路径字符串
        """
        normalized = os.path.normpath(path)
        if self.os == "nt":
            return normalized.replace("/", "\\")
        else:
            return normalized.replace("\\", "/")

    def get_path_type(self, path: str) -> PathType:
        """
        判断路径类型（绝对路径还是相对路径）

        Args:
            path (str): 待检测的路径字符串

        Returns:
            PathType: 路径类型枚举值（absolutely或relative）
        """
        if os.path.isabs(path):
            return PathType.absolutely
        else:
            return PathType.relative

    def __call__(self, cur_path: str, loc_path: str) -> str:
        """
        解析路径并返回绝对路径

        根据当前位置路径和目标路径计算出绝对路径

        Args:
            cur_path (str): 当前位置路径
            loc_path (str): 目标路径（POSIX风格）

        Returns:
            str: 解析后的绝对路径
        """
        """
        loc_path is posix style
        """
        path_type = self.get_path_type(loc_path)
        if path_type == PathType.absolutely:
            return self.format_path(loc_path)
        if path_type == PathType.relative:
            if loc_path.startswith("./"):
                path = os.path.join(cur_path, self.format_path(loc_path[2:]))
            elif loc_path.startswith("../"):
                path = os.path.join(
                    os.path.dirname(cur_path), self.format_path(loc_path[3:])
                )
            else:
                path = os.path.join(
                    os.path.dirname(cur_path), self.format_path(loc_path)
                )
            return path

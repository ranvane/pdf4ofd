#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME:  file_parser_base.py
# CREATE_TIME: 2025/3/28 11:43
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE: base 解析器

import sys

sys.path.insert(0, "..")
import logging
import os
import traceback
import base64
import re
from typing import Any
from .parameter_parser import ParameterParser

logger = logging.getLogger("root")


class FileParserBase(object):
    """
    文件解析器基类

    这是一个通用的XML文件解析器基类，提供了解析OFD文档中各种XML文件的基础功能。
    主要包含初始化方法和递归提取XML节点的功能，供其他具体的解析器类继承使用。

    Attributes:
        ofd_param (ParameterParser): OFD参数解析器实例，用于处理OFD相关参数
        xml_obj (dict): XML对象，通常是由XML文件解析后得到的字典结构
    """

    def __init__(self, xml_obj):
        """
        初始化文件解析器基类

        Args:
            xml_obj: XML对象，通常是解析后的XML文档字典结构

        Raises:
            AssertionError: 当xml_obj为空或None时抛出断言错误
        """
        assert xml_obj  # 确保传入的XML对象不为空
        self.ofd_param = ParameterParser()  # 创建OFD参数解析器实例
        self.xml_obj = xml_obj  # 存储XML对象
        # print(xml_obj)  # 注释掉的调试语句

    def recursion_ext(self, need_ext_obj, ext_list, key):
        """
        递归提取XML对象中指定键的值

        该方法会深度遍历XML对象（字典结构），查找所有匹配指定键的值，
        并将这些值添加到结果列表中。支持嵌套的字典和列表结构。

        Args:
            need_ext_obj (dict or list): 待提取的XML对象（通常是字典结构）
            ext_list (list): 存放提取结果的容器列表
            key (str): 要提取的键名（例如 'ofd:MultiMedia', 'ofd:Page' 等）

        Returns:
            None: 直接修改ext_list参数，不返回值
        """
        # 检查当前对象是否为字典类型
        if isinstance(need_ext_obj, dict):
            # 遍历字典中的所有键值对
            for k, v in need_ext_obj.items():
                # 如果当前键等于目标键
                if k == key:
                    # 根据值的类型进行不同处理
                    if isinstance(v, (dict, str)):
                        # 如果值是字典或字符串，直接添加到结果列表
                        ext_list.append(v)
                    elif isinstance(v, list):
                        # 如果值是列表，将列表中的所有元素扩展到结果列表
                        ext_list.extend(v)
                else:
                    # 如果当前键不是目标键，则继续递归搜索
                    if isinstance(v, dict):
                        # 如果值是字典，递归调用自身
                        self.recursion_ext(v, ext_list, key)
                    elif isinstance(v, list):
                        # 如果值是列表，遍历列表中的每个元素并递归调用
                        for cell in v:
                            self.recursion_ext(cell, ext_list, key)
                    else:
                        # 其他类型则跳过
                        pass
        else:
            # 如果传入的对象不是字典类型，打印其类型（可能是调试用途）
            print(type(need_ext_obj))

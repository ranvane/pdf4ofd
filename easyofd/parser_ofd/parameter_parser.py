#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: easyofd
# CREATE_TIME:
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: renoyuan
# note:参数解析器
from loguru import logger
from typing import List, Dict, Any, Union, Tuple, Optional


class ParameterParser(object):
    """
    OFD文档参数解析器

    该类用于解析OFD文档中的各种参数，提供类型安全的参数提取功能。
    定义了一组预设的参数键及其期望的数据类型，确保从容器中获取的参数符合预期类型。

    Attributes:
        parameter (dict): 参数键与类型的映射表，键为OFD XML元素的属性名，
                         值为元组，包含允许的输入类型和默认返回类型
    """

    parameter = {
        "ofd:FillColor": (dict, dict),  # 填充颜色参数，期望字典类型
        "ofd:StrokeColor": (dict, dict),  # 描边颜色参数，期望字典类型
        "ofd:Test": ((str, int), str),  # 测试参数，可接受字符串或整数，返回字符串类型
        "ofd:Font": (str, str),  # 字体参数，期望字符串类型
        "@Value": (str, str),  # 值参数，期望字符串类型
    }

    def __call__(self, key: str, container: Dict[str, Any]) -> Optional[Any]:
        """
        解析指定键的参数值

        从给定的容器中获取指定键的值，并验证其类型是否符合预定义的类型要求。
        如果类型匹配，则返回该值；否则返回对应类型的默认值。

        Args:
            key (str): 要解析的参数键名
            container (Dict[str, Any]): 包含参数的容器字典

        Returns:
            Optional[Any]: 符合类型要求的参数值，如果键不存在则返回None
        """
        if key in ParameterParser.parameter:
            v = container.get(key, None)
            t = ParameterParser.parameter[key]
            if isinstance(v, t[0]):
                return v
            else:
                return t[1]()
        else:
            logger.warning(f"{key} not in ParameterParser")
            return None

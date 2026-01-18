#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: easyofd img_deal
# CREATE_TIME: 2024/7/18 11:20
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: renoyuan
# note: img 操作
from io import BytesIO


class DealImg(object):
    """
    图像处理类，提供对PIL图像对象的基本操作功能

    该类封装了一些常用的图像处理操作，如调整大小、图像格式转换等，
    主要用于处理OFD文档中的图像资源。
    """

    def __init__(self):
        """
        初始化DealImg类

        当前为空实现，可根据需要扩展图像处理相关的初始化设置
        """
        pass

    def resize(self):
        """
        调整图像大小

        注意：当前为空实现，需进一步开发完成图像缩放功能

        Returns:
            None: 当前无返回值，函数体待实现
        """
        pass

    def pil2bytes(self, image):
        """
        将PIL图像对象转换为字节数组

        此方法将PIL图像对象保存为字节流，便于在网络上传输或存储

        Args:
            image (PIL.Image.Image): 需要转换的PIL图像对象

        Returns:
            bytes: 包含图像数据的字节数组，格式为PNG

        Raises:
            AttributeError: 如果传入的对象不是有效的PIL图像对象
            ValueError: 如果图像格式不被支持
        """
        # 创建一个 BytesIO 对象
        img_bytesio = BytesIO()
        # 将图像保存到 BytesIO 对象
        image.save(img_bytesio, format="PNG")  # 你可以根据需要选择其他图像格式
        # 获取 BytesIO 对象中的字节
        img_bytes = img_bytesio.getvalue()
        # 关闭 BytesIO 对象
        img_bytesio.close()
        return img_bytes

    def pil2bytes_io(self, image):
        """
        将PIL图像对象转换为BytesIO对象

        此方法将PIL图像对象保存到BytesIO对象中，便于后续处理而无需临时文件

        Args:
            image (PIL.Image.Image): 需要转换的PIL图像对象

        Returns:
            io.BytesIO: 包含图像数据的BytesIO对象，格式为PNG

        Raises:
            AttributeError: 如果传入的对象不是有效的PIL图像对象
            ValueError: 如果图像格式不被支持
        """
        # 创建一个 BytesIO 对象
        img_bytesio = BytesIO()
        # 将图像保存到 BytesIO 对象
        image.save(img_bytesio, format="PNG")  # 你可以根据需要选择其他图像格式
        return img_bytesio

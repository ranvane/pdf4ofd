#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: D:\code\easyofd\easyofd\parser
# CREATE_TIME: 2023-07-27
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE:  文件处理
import os
import base64
import shutil
from typing import Any
from uuid import uuid1

import xmltodict
import zipfile
from loguru import logger

from .path_parser import PathParser


class FileRead(object):
    """
    OFD文件读取和处理类

    该类负责将Base64编码的OFD文件进行解压缩、解析，并构建文件树结构。
    支持将XML文件解析为对象，其他文件转换为Base64编码字符串。

    Attributes:
        ofdbyte (bytes): Base64解码后的OFD文件字节内容
        name (str): 临时OFD文件名，使用进程ID和UUID生成
        pdf_name (str): 对应的PDF文件名
        zip_path (str): 临时OFD文件完整路径
        unzip_path (str): 解压缩后的文件夹路径
        file_tree (dict): 存储文件路径与其内容（XML解析对象或Base64编码）的映射关系
    """

    def __init__(self, ofdb64: str):
        """
        初始化FileRead实例

        Args:
            ofdb64 (str): Base64编码的OFD文件内容
        """
        # 将Base64编码的OFD文件内容解码为字节
        self.ofdbyte = base64.b64decode(ofdb64)
        # 获取当前进程ID用于生成唯一的临时文件名
        pid = os.getpid()
        # 使用进程ID和UUID生成唯一的临时文件名
        self.name = f"{pid}_{str(uuid1())}.ofd"
        # 生成对应的PDF文件名
        self.pdf_name = self.name.replace(".ofd", ".pdf")
        # 定义临时OFD文件的完整路径
        self.zip_path = f"{os.getcwd()}/{self.name}"
        # 初始化解压缩路径为空
        self.unzip_path = ""
        # 初始化文件树字典
        self.file_tree = {}

    def unzip_file(self):
        """
        解压缩OFD文件到临时目录

        OFD文件本质上是一个ZIP压缩包，此方法将其解压到临时目录，
        以便后续处理其中的XML和其他资源文件。
        """
        # 将解码后的OFD字节内容写入临时文件
        with open(self.zip_path, "wb") as f:
            f.write(self.ofdbyte)
        # 设置解压缩路径（基于OFD文件名去除扩展名）
        self.unzip_path = self.zip_path.split(".")[0]
        # 解压缩OFD文件到指定目录
        with zipfile.ZipFile(self.zip_path, "r") as f:
            for file in f.namelist():
                f.extract(file, path=self.unzip_path)
        # 如果设置了保存XML选项，则额外提取到指定XML目录
        if self.save_xml:
            print("saving xml {}".format(self.xml_name))
            with zipfile.ZipFile(self.zip_path, "r") as f:
                for file in f.namelist():
                    f.extract(file, path=self.xml_name)

    def buld_file_tree(self):
        """
        构建文件树结构

        遍历解压缩后的目录，将XML文件解析为Python对象，
        其他文件转换为Base64编码字符串，并建立文件路径与内容的映射关系。
        同时清理临时文件。
        """
        # 设置根目录路径
        self.file_tree["root"] = self.unzip_path
        # 设置PDF文件名
        self.file_tree["pdf_name"] = self.pdf_name
        # 遍历解压缩后的目录结构
        for root, dirs, files in os.walk(self.unzip_path):
            for file in files:
                # 获取文件的绝对路径
                abs_path = os.path.join(root, file)
                # 根据文件类型选择处理方式：XML文件解析为对象，其他文件转为Base64编码
                self.file_tree[abs_path] = (
                    str(base64.b64encode(open(f"{abs_path}", "rb").read()), "utf-8")
                    if "xml" not in file
                    else xmltodict.parse(
                        open(f"{abs_path}", "r", encoding="utf-8").read()
                    )
                )
        # 设置文档根路径（OFD.xml文件路径）
        self.file_tree["root_doc"] = (
            os.path.join(self.unzip_path, "OFD.xml")
            if os.path.join(self.unzip_path, "OFD.xml") in self.file_tree
            else ""
        )

        # 清理临时解压缩目录
        if os.path.exists(self.unzip_path):
            shutil.rmtree(self.unzip_path)

        # 清理临时OFD文件
        if os.path.exists(self.zip_path):
            os.remove(self.zip_path)

    def __call__(self, *args: Any, **kwds: Any) -> dict:
        """
        执行OFD文件处理流程

        此方法使类实例可被调用，执行完整的OFD文件解压缩和解析流程，
        并返回构建好的文件树结构。

        Args:
            **kwds: 关键字参数
                - save_xml (bool): 是否保存XML文件到指定目录（默认False）
                - xml_name (str): XML保存目录名（当save_xml=True时有效）

        Returns:
            dict: 包含文件路径与内容映射关系的文件树
        """
        # 从关键字参数中获取保存XML的选项
        self.save_xml = kwds.get("save_xml", False)
        # 从关键字参数中获取XML保存目录名
        self.xml_name = kwds.get("xml_name")

        # 执行解压缩操作
        self.unzip_file()
        # 构建文件树结构
        self.buld_file_tree()
        # 返回构建好的文件树
        return self.file_tree


if __name__ == "__main__":
    with open(r"D:/code/easyofd/test/增值税电子专票5.ofd", "rb") as f:
        ofdb64 = str(base64.b64encode(f.read()), "utf-8")
    a = FileRead(ofdb64)()
    print(list(a.keys()))

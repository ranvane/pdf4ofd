#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: F:\code\easyofd\easyofd\draw
# CREATE_TIME: 2023-10-26
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# note:  写入 xml 目录并打包成ofd 文件
from datetime import datetime
from io import BytesIO
from typing import Optional

from PIL import Image
from loguru import logger

from .ofdtemplate import (
    CurId,
    OFDTemplate,
    DocumentTemplate,
    DocumentResTemplate,
    PublicResTemplate,
    ContentTemplate,
    OFDStructure,
)
from .pdf_parse import DPFParser


class OFDWrite(object):
    """
    OFD文档写入工具类

    该类用于将PDF文档或图像列表转换为OFD（Open Fixed-layout Document）格式文档。
    OFD是中国国家标准的版式文档格式，类似于PDF，用于固定版面的电子文档。

    主要功能包括：
    - 将PDF文档转换为OFD文档
    - 将图像列表转换为OFD文档
    - 构建OFD文档的各个组成部分（入口、文档结构、资源等）
    - 处理文本和图像元素的位置转换

    Attributes:
        OP (float): 单位转换因子，用于将像素坐标转换为OFD文档中的毫米单位
                   默认值为 96/25.4 ≈ 3.779527559，表示96 DPI下的每毫米像素数
    """

    def __init__(self):
        """
        初始化OFDWrite类实例

        该方法主要用于初始化单位转换因子OP（Origin to OFD Pixel），
        用于将PDF文档中的坐标单位（如点或像素）转换为OFD文档中的毫米单位。

        属性说明：
            self.OP: 单位转换因子，值为96/25.4 ≈ 3.779527559
                     计算逻辑：
                     - 96：表示屏幕的DPI（每英寸点数）
                     - 25.4：表示1英寸等于25.4毫米
                     - 因此96/25.4表示每毫米对应的像素数
                     该转换因子用于在PDF和OFD文档之间进行坐标和尺寸的转换
        """
        # self.OP = 200 / 25.4  # 旧的转换因子（已被覆盖）
        self.OP = (
            96 / 25.4
        )  # 当前使用的转换因子：96 DPI转换为毫米单位,转换因子的另一种计算方式:(200 / 25.4) / (200 / 96) = 96 / 25.4 ≈ 3.78

    def build_ofd_entrance(self, id_obj: Optional[CurId] = None):
        """
        构建OFD文档入口结构

        该方法创建OFD文档的根节点结构，包含文档创建时间等基本信息。

        Args:
            id_obj (Optional[CurId]): ID管理器对象，用于生成唯一的元素ID

        Returns:
            OFDTemplate: OFD文档根节点对象
        """
        CreationDate = str(datetime.now())
        ofd_entrance = OFDTemplate(CreationDate=CreationDate, id_obj=id_obj)
        return ofd_entrance

    def build_document(
        self,
        img_len,
        id_obj: Optional[CurId] = None,
        PhysicalBox: Optional[str] = "0 0 140 90",
    ):
        """
        构建OFD文档结构

        该方法创建文档节点，定义页面数量、页面位置等文档结构信息。

        Args:
            img_len (int): 页面数量（通常对应图像数量）
            id_obj (Optional[CurId]): ID管理器对象
            PhysicalBox (Optional[str]): 物理边界框，默认为"0 0 140 90"

        Returns:
            DocumentTemplate: 文档结构对象
        """
        pages = []

        for idx in range(img_len):
            pages.append(
                {"@ID": f"{idx + 1}", "@BaseLoc": f"Pages/Page_{idx}/Content.xml"}
            )
        document = DocumentTemplate(Page=pages, id_obj=id_obj, PhysicalBox=PhysicalBox)
        return document

    def build_document_res(
        self,
        img_len: int = 0,
        id_obj: Optional[CurId] = None,
        pfd_res_uuid_map: Optional[dict] = None,
    ):
        """
        构建文档资源结构

        该方法创建文档资源节点，定义文档中使用的多媒体资源（如图像）。

        Args:
            img_len (int): 图像数量
            id_obj (Optional[CurId]): ID管理器对象
            pfd_res_uuid_map (Optional[dict]): PDF资源UUID映射表

        Returns:
            DocumentResTemplate: 文档资源结构对象
        """
        MultiMedia = []
        DrawParams = []  # todo DrawParams 参数后面有空增加
        if img_len and not pfd_res_uuid_map:
            for num in range(img_len):
                MultiMedia.append(
                    {
                        "@ID": 0,
                        "@Type": "Image",
                        "ofd:MediaFile": f"Image_{num}.jpg",
                        "res_uuid": f"{num}",
                    }
                )
        elif pfd_res_uuid_map and (pfd_img := pfd_res_uuid_map.get("img")):
            for res_uuid in pfd_img.keys():
                name = f"Image_{res_uuid}.jpg"
                MultiMedia.append(
                    {
                        "@ID": 0,
                        "@Type": "Image",
                        "ofd:MediaFile": name,
                        "res_uuid": res_uuid,
                    }
                )

        document_res = DocumentResTemplate(MultiMedia=MultiMedia, id_obj=id_obj)
        return document_res

    def build_public_res(self, id_obj: CurId = None, pfd_res_uuid_map: dict = None):
        """
        构建公共资源结构

        该方法创建公共资源节点，定义文档中使用的字体等公共资源。

        Args:
            id_obj (CurId): ID管理器对象
            pfd_res_uuid_map (dict): PDF资源UUID映射表

        Returns:
            PublicResTemplate: 公共资源结构对象
        """
        fonts = []
        if pfd_res_uuid_map and (pfd_font := pfd_res_uuid_map.get("font")):
            for res_uuid, font in pfd_font.items():
                fonts.append(
                    {
                        "@ID": 0,
                        "@FontName": font,
                        "@FamilyName": font,  # 匹配替代字型
                        "res_uuid": res_uuid,
                        "@FixedWidth": "false",
                        "@Serif": "false",
                        "@Bold": "false",
                        "@Charset": "prc",
                    }
                )
        else:
            pass

        public_res = PublicResTemplate(Font=fonts, id_obj=id_obj)
        return public_res

    def build_content_res(
        self,
        pil_img_list=None,
        pdf_info_list=None,
        id_obj: CurId = None,
        pfd_res_uuid_map: dict = None,
    ):
        """
        构建内容资源结构

        该方法根据输入的图像列表或PDF信息列表，创建页面内容结构，
        包含图像对象、文本对象等元素的位置和属性信息。

        Args:
            pil_img_list (list): PIL图像对象列表
            pdf_info_list (list): PDF解析信息列表
            id_obj (CurId): ID管理器对象
            pfd_res_uuid_map (dict): PDF资源UUID映射表

        Returns:
            list: 内容资源对象列表，每个元素对应一个页面的内容
        """
        PhysicalBox = None
        content_res_list = []
        if pil_img_list:
            for idx, pil_img in enumerate(pil_img_list):
                # print(pil_img)
                # print(idx, pil_img[1], pil_img[2])
                PhysicalBox = f"0 0 {pil_img[1]} {pil_img[2]}"
                ImageObject = [
                    {
                        "@ID": 0,
                        "@CTM": f"{pil_img[1]} 0 0 {pil_img[2]} 0 0",
                        "@Boundary": f"0 0 {pil_img[1]} {pil_img[2]}",
                        "res_uuid": f"{idx}",  # 资源标识
                        "@ResourceID": f"",
                    }
                ]

                conten = ContentTemplate(
                    PhysicalBox=PhysicalBox,
                    ImageObject=ImageObject,
                    CGTransform=[],
                    PathObject=[],
                    TextObject=[],
                    id_obj=id_obj,
                )
                # print(conten)
                content_res_list.append(conten)
        elif (
            pdf_info_list
        ):  # 写入读取后的pdf 结果 # todo 图片id 需要关联得提前定义或者有其他方式反向对齐

            for idx, content in enumerate(pdf_info_list):
                ImageObject = []
                TextObject = []
                PhysicalBox = pfd_res_uuid_map["other"]["page_size"][idx]
                PhysicalBox = f"0 0 {PhysicalBox[0]} {PhysicalBox[1]}"  # page_size 没有的话使用document 里面的
                for block in content:
                    # print(block)

                    bbox = block["bbox"]
                    x0, y0, length, height = (
                        bbox[0] / self.OP,
                        bbox[1] / self.OP,
                        (bbox[2] - bbox[0]) / self.OP,
                        (bbox[3] - bbox[1]) / self.OP,
                    )
                    if block["type"] == "text":

                        count = len(block.get("text"))

                        TextObject.append(
                            {
                                "@ID": 0,
                                "res_uuid": block.get("res_uuid"),  # 资源标识
                                "@Font": "",
                                "ofd:FillColor": {"Value": "156 82 35"},
                                "ofd:TextCode": {
                                    "#text": block.get("text"),
                                    "@X": "0",
                                    "@Y": f"{block.get('size') / self.OP}",
                                    "@DeltaX": f"g {count - 1} {length / count}",
                                },
                                "@size": block.get("size") / self.OP,
                                "@Boundary": f"{x0} {y0} {length} {height}",
                            }
                        )
                    elif block["type"] == "img":
                        ImageObject.append(
                            {
                                "@ID": 0,
                                "res_uuid": block.get("res_uuid"),  # 资源标识
                                "@Boundary": f"{x0} {y0} {length} {height}",
                                "@ResourceID": f"",  # 需要关联public res 里面的结果
                            }
                        )

                # for i in content:
                #     if i["type"] == "img":
                #         ImageObject.append(i)
                #     elif i["type"] == "text":
                #         TextObject.append(i)

                conten = ContentTemplate(
                    PhysicalBox=PhysicalBox,
                    ImageObject=ImageObject,
                    CGTransform=[],
                    PathObject=[],
                    TextObject=TextObject,
                    id_obj=id_obj,
                )
                # print(conten)
                content_res_list.append(conten)
        else:
            pass
        return content_res_list

    def pil_2_bytes(self, image):
        """
        将PIL图像对象转换为字节数据

        该方法将PIL图像对象保存到内存中的字节流，并返回字节数据。

        Args:
            image: PIL图像对象

        Returns:
            bytes: 图像的字节数据
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

    def __call__(self, pdf_bytes=None, pil_img_list=None, optional_text=False):
        """
        执行OFD文档转换的主要方法

        该方法是类的可调用接口，根据输入参数将PDF文档或图像列表转换为OFD文档。
        支持带文本识别的转换（可编辑OFD）或纯图像转换。

        Args:
            pdf_bytes (bytes, optional): PDF文档的字节数据
            pil_img_list (list, optional): PIL图像对象列表
            optional_text (bool): 是否进行文本识别以生成可编辑OFD，默认False

        Returns:
            bytes: 生成的OFD文档字节数据

        Raises:
            Exception: 当输入参数不符合要求时可能抛出异常
        """
        pdf_obj = DPFParser()
        page_pil_img_list = None

        # 插入图片ofd
        if pil_img_list:  # 读取 图片
            page_pil_img_list = [
                (self.pil_2_bytes(_img), _img.size[0] / self.OP, _img.size[1] / self.OP)
                for _img in pil_img_list
            ]
        else:  # 读取 pdf 转图片
            if optional_text:  # 生成可编辑ofd:
                pdf_info_list, pfd_res_uuid_map = pdf_obj.extract_text_with_details(
                    pdf_bytes
                )  # 解析pdf
                logger.debug(
                    f"pdf_info_list: {pdf_info_list} \n pfd_res_uuid_map {pfd_res_uuid_map}"
                )
            else:
                img_list = pdf_obj.to_img(pdf_bytes)
                page_pil_img_list = [
                    (
                        self.pil_2_bytes(
                            Image.frombytes(
                                "RGB", [_img.width, _img.height], _img.samples
                            )
                        ),
                        _img.width / self.OP,
                        _img.height / self.OP,
                    )
                    for _img in img_list
                ]

        id_obj = CurId()

        if page_pil_img_list:  # img 内容转ofd
            res_static = {}  # 图片资源
            pfd_res_uuid_map = {"img": {}}
            PhysicalBox = f"0 0 {page_pil_img_list[0][1]} {page_pil_img_list[0][2]}"
            for idx, pil_img_tuple in enumerate(page_pil_img_list):
                pfd_res_uuid_map["img"][f"{idx}"] = pil_img_tuple[0]
                res_static[f"Image_{idx}.jpg"] = pil_img_tuple[0]
            ofd_entrance = self.build_ofd_entrance(id_obj=id_obj)
            document = self.build_document(
                len(page_pil_img_list), id_obj=id_obj, PhysicalBox=PhysicalBox
            )
            public_res = self.build_public_res(id_obj=id_obj)
            document_res = self.build_document_res(
                len(page_pil_img_list), id_obj=id_obj, pfd_res_uuid_map=pfd_res_uuid_map
            )

            content_res_list = self.build_content_res(
                page_pil_img_list, id_obj=id_obj, pfd_res_uuid_map=pfd_res_uuid_map
            )

        else:
            #  生成的文档结构对象需要传入id实例
            ofd_entrance = self.build_ofd_entrance(id_obj=id_obj)
            document = self.build_document(len(pdf_info_list), id_obj=id_obj)
            public_res = self.build_public_res(
                id_obj=id_obj, pfd_res_uuid_map=pfd_res_uuid_map
            )
            document_res = self.build_document_res(
                len(pdf_info_list), id_obj=id_obj, pfd_res_uuid_map=pfd_res_uuid_map
            )
            content_res_list = self.build_content_res(
                pdf_info_list=pdf_info_list,
                id_obj=id_obj,
                pfd_res_uuid_map=pfd_res_uuid_map,
            )

            res_static = {}  # 图片资源

            print("pfd_res_uuid_map", pfd_res_uuid_map)
            img_dict = pfd_res_uuid_map.get("img")
            if img_dict:
                for key, v_io in img_dict.items():
                    res_static[f"Image_{key}.jpg"] = v_io.getvalue()

        # 生成 ofd 文件
        ofd_byte = OFDStructure(
            "123",
            ofd=ofd_entrance,
            document=document,
            public_res=public_res,
            document_res=document_res,
            content_res=content_res_list,
            res_static=res_static,
        )(test=True)
        return ofd_byte


if __name__ == "__main__":
    pdf_p = r"D:\renodoc\技术栈\GBT_33190-2016_电子文件存储与交换格式版式文档.pdf"
    pdf_p = r"F:\code\easyofd\test"
    with open(pdf_p, "rb") as f:
        content = f.read()

    ofd_content = OFDWrite()(content)

    with open("ofd.ofd", "wb") as f:
        f.write(ofd_content)

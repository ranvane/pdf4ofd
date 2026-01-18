#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: F:\code\easyofd\easyofd\draw
# CREATE_TIME: 2023-10-30
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# note:  ofd 基础结构模板
import tempfile
import os
import abc
import copy
import shutil

from loguru import logger
import xmltodict
import zipfile

"""OFD 模板模块

该模块定义了 OFD (Open Fixed-layout Document) 文件格式的基础结构模板，
包括文档、资源、页面等内容的模板类，用于生成符合 OFD 标准的文档。
"""

__all__ = [
    "CurId",
    "OFDTemplate",
    "DocumentTemplate",
    "DocumentResTemplate",
    "PublicResTemplate",
    "ContentTemplate",
    "OFDStructure",
]
"""
OFD目录结构
    │  OFD.xml
    │  
    └─Doc_0
        │  Document.xml
        │  DocumentRes.xml
        │  PublicRes.xml
        │  
        ├─Annots
        │  │  Annotations.xml
        │  │  
        │  └─Page_0
        │          Annotation.xml
        │          
        ├─Attachs
        │      Attachments.xml
        │      original_invoice.xml
        │      
        ├─Pages
        │  └─Page_0
        │          Content.xml
        │          
        ├─Res
        │      image_80.jb2
        │      
        ├─Signs
        │  │  Signatures.xml
        │  │  
        │  └─Sign_0
        │          Signature.xml
        │          SignedValue.dat
        │          
        ├─Tags
        │      CustomTag.xml
        │      CustomTags.xml
        │      
        └─Tpls
            └─Tpl_0
                    Content.xml
"""


class CurId(object):
    """
    文档内ID控制对象

    用于管理OFD文档中的各种ID，确保每个元素都有唯一的ID标识符。
    同时维护UUID映射表，用于关联资源文件ID。
    """

    def __init__(self):
        """
        初始化ID控制器

        设置初始ID为1，并创建UUID映射表用于资源文件ID管理
        """
        self.id = 1
        self.used = False
        self.uuid_map = (
            {}
        )  # 资源文件生成id的时候手动添加进来后面构建page 可以 匹配ResourceID

    def add_uuid_map(self, k, v):
        """添加UUID映射关系

        Args:
            k: UUID键
            v: 对应的ID值
        """
        # logger.debug(f"uuid_map add {k}: {v}")
        self.uuid_map[k] = v

    def add(self):
        """递增ID计数器"""
        self.id += 1

    def get_id(self):
        """
        获取当前ID
        如果ID已被使用则递增后再返回，否则直接返回当前ID并标记为已使用
        Returns:
            int: 当前可用的ID
        """
        if self.used:
            self.add()
            return self.id
        if not self.used:
            cur_id = self.id
            self.used = True
            return cur_id

    def get_max_id(self):
        """获取最大ID

        Returns:
            int: 最大ID值
        """
        MaxUnitID = self.id + 1
        return MaxUnitID


class TemplateBase(object):
    """模板基类
    所有OFD模板的基类，提供通用的模板操作方法，如ID生成、值修改等
    """

    key_map = {}  # 变量名对应 xml 中形式 映射 如 传入   DocID -> ofd:DocID
    id_keys = []  # 对需要的要素添加 "@ID"
    template_name = ""  # 模板名称

    def __init__(self, *args, **kwargs):
        """初始化模板基类

        Args:
            *args: 位置参数
            **kwargs: 关键字参数，包含id_obj等
        """
        # print(args)
        # print(kwargs)
        self.id_obj: CurId = kwargs.get("id_obj")
        # print("id_obj", self.id_obj)
        self.assemble(*args, **kwargs)

    def assemble(self, *args, **kwargs):
        """对OFD JSON进行组装

        复制模板JSON并根据传入的参数修改相应的值，同时为需要ID的元素生成ID

        Args:
            *args: 位置参数
            **kwargs: 关键字参数，包含要修改的键值对
        """

        self.final_json = copy.deepcopy(self.ofdjson)

        # 往模板里面添加要素值
        if kwargs:
            for k, v in kwargs.items():
                if k in self.key_map:
                    self.modify(self.final_json, self.key_map[k], v)

        # 添加id
        for id_key in self.id_keys:
            # print(f"开始gen_id >> {self.template_name}>>{id_key}")
            # print(f"final_json {self.final_json}")
            self.gen_id(self.final_json, id_key)

    def gen_id(self, ofdjson, id_key):
        """为指定类型的元素生成ID

        遍历JSON结构，为匹配到的元素类型添加ID属性

        Args:
            ofdjson: OFD JSON数据
            id_key: 需要添加ID的元素类型
        """
        # print("id_key ", id_key, "ofdjson ", ofdjson)

        for k, v in ofdjson.items():
            if k == id_key:
                # 添加id
                if isinstance(ofdjson[k], dict):
                    ofdjson[k]["@ID"] = f"{self.id_obj.get_id()}"

                    # logger.info(f"添加id -> {ofdjson[k]}")
                elif isinstance(ofdjson[k], list):
                    for i in ofdjson[k]:
                        i["@ID"] = f"{self.id_obj.get_id()}"

                        # logger.info(f"添加id ->i {i}")

            elif isinstance(v, dict):
                # logger.debug(f"dict_v{v}")
                self.gen_id(v, id_key)

            elif isinstance(v, list):
                for v_cell in v:
                    if isinstance(v_cell, dict):
                        # logger.debug(f"dict_v{v}")
                        self.gen_id(v_cell, id_key)

    def modify(self, ofdjson, key, value):
        """修改指定键的值

        遍历JSON结构，将所有匹配到的键替换为新的值

        Args:
            ofdjson: OFD JSON数据
            key: 要修改的键
            value: 新的值
        """

        for k, v in ofdjson.items():
            if k == key:
                ofdjson[k] = value
            elif isinstance(v, dict):
                self.modify(v, key, value)
            elif isinstance(v, list):
                for v_cell in v:
                    if isinstance(v_cell, dict):
                        self.modify(v_cell, key, value)

    def save(self, path):
        """将最终的JSON保存为XML文件

        Args:
            path: 保存路径
        """
        xml_data = xmltodict.unparse(self.final_json, pretty=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_data)


class OFDTemplate(TemplateBase):
    """
    OFD根节点模板 - 全局唯一 OFD.xml

    定义OFD文档的根结构，包含文档信息和文档根路径等基本信息
    """

    template_name = "OFD"

    # 键映射表，将Python参数名映射到XML标签名
    key_map = {
        "Author": "ofd:Author",
        "DocID": "ofd:DocID",
        "CreationDate": "ofd:CreationDate",
    }

    # OFD XML结构的默认模板
    ofdjson = {
        "ofd:OFD": {
            "@xmlns:ofd": "http://blog.yuanhaiying.cn",
            "@Version": "1.1",
            "@DocType": "OFD",
            "ofd:DocBody": [
                {
                    "ofd:DocInfo": {
                        "ofd:DocID": "0C1D4F7159954EEEDE517F7285E84DC4",
                        "ofd:Creator": "easyofd",
                        "ofd:author": "renoyuan",
                        "ofd:authoremail": "renoyuan@foxmail.com",
                        "ofd:CreatorVersion": "1.0",
                        "ofd:CreationDate": "2023-10-27",
                    },
                    "ofd:DocRoot": "Doc_0/Document.xml",
                }
            ],
        }
    }


class DocumentTemplate(TemplateBase):
    """文档模板 - DOC内唯一 表示DOC内部结构 Document.xml

    定义单个文档的结构信息，包括页面区域、资源引用等
    """

    template_name = "Document"
    # 键映射表
    key_map = {"Page": "ofd:Page", "PhysicalBox": "ofd:PhysicalBox"}
    # 需要添加ID的元素类型
    id_keys = ["ofd:Page"]
    # Document.xml的默认模板
    ofdjson = {
        "ofd:Document": {
            "@xmlns:ofd": "http://blog.yuanhaiying.cn",
            "ofd:CommonData": {
                "ofd:MaxUnitID": 0,
                "ofd:PageArea": {"ofd:PhysicalBox": "0 0 140 90"},
                "ofd:PublicRes": "PublicRes.xml",
                "ofd:DocumentRes": "DocumentRes.xml",
            },
            "ofd:Pages": {
                "ofd:Page": [{"@ID": 0, "@BaseLoc": "Pages/Page_0/Content.xml"}]
            },
        }
    }

    def update_max_unit_id(self, final_json=None):
        """更新最大单元ID

        在文档处理完成后，更新CommonData中的MaxUnitID值

        Args:
            final_json: 要更新的JSON数据，默认为self.final_json
        """
        if not final_json:
            final_json = self.final_json

        for k, v in final_json.items():
            if k == "ofd:MaxUnitID":
                final_json["ofd:MaxUnitID"] = self.id_obj.get_max_id()
                return

            elif isinstance(v, dict):
                self.update_max_unit_id(v)
            elif isinstance(v, list):
                for v_cell in v:
                    if isinstance(v_cell, dict):
                        self.update_max_unit_id(v_cell)

    def update_page(self, page_num):
        """更新页面信息（预留方法）

        Args:
            page_num: 页面数量
        """
        pass


class DocumentResTemplate(TemplateBase):
    """
    文档资源模板 - DOC内唯一 表示多媒体资源信息如图片 DocumentRes.xml

    定义文档专用的多媒体资源（如图片、音频等）的引用信息
    """

    template_name = "DocumentRes"
    # 键映射表
    key_map = {"MultiMedia": "ofd:MultiMedia"}
    # 需要添加ID的元素类型
    id_keys = ["ofd:DrawParam", "ofd:MultiMedia"]
    # DocumentRes.xml的默认模板
    ofdjson = {
        "ofd:Res": {
            "@xmlns:ofd": "http://blog.yuanhaiying.cn",
            "@BaseLoc": "Res",
            "ofd:MultiMedias": {
                "ofd:MultiMedia": [
                    {"@ID": 0, "@Type": "Image", "ofd:MediaFile": "Image_2.jpg"}
                ]
            },
        }
    }

    def gen_id(self, ofdjson, id_key):
        """
        生成ID并维护UUID映射

        重写父类方法，在生成ID的同时维护UUID到ID的映射关系

        Args:
            ofdjson: OFD JSON数据
            id_key: 需要添加ID的元素类型
        """
        # print("id_key ", id_key, "ofdjson ", ofdjson)

        for k, v in ofdjson.items():
            if k == id_key:
                # 添加id
                if isinstance(ofdjson[k], dict):
                    ofdjson[k]["@ID"] = f"{self.id_obj.get_id()}"
                    if res_uuid := ofdjson[k].get("res_uuid"):
                        self.id_obj.add_uuid_map(res_uuid, ofdjson[k]["@ID"])
                    # logger.info(f"添加id -> {ofdjson[k]}")
                elif isinstance(ofdjson[k], list):
                    for i in ofdjson[k]:

                        i["@ID"] = f"{self.id_obj.get_id()}"
                        if res_uuid := i.get("res_uuid"):
                            self.id_obj.add_uuid_map(res_uuid, i["@ID"])
                        # logger.info(f"添加id ->i {i}")

            elif isinstance(v, dict):
                # logger.debug(f"dict_v{v}")
                self.gen_id(v, id_key)

            elif isinstance(v, list):
                for v_cell in v:
                    if isinstance(v_cell, dict):
                        # logger.debug(f"dict_v{v}")
                        self.gen_id(v_cell, id_key)


class PublicResTemplate(TemplateBase):
    """
    公共资源模板 - DOC内唯一 公共配置资源信息如字体、颜色等 PublicRes.xml

    定义文档共享的资源信息，如字体、颜色空间等
    """

    template_name = "PulicRes"
    # 键映射表
    key_map = {"Font": "ofd:Font"}
    # 需要添加ID的元素类型
    id_keys = ["ofd:ColorSpace", "ofd:Font"]
    # PublicRes.xml的默认模板
    ofdjson = {
        "ofd:Res": {
            "@xmlns:ofd": "http://blog.yuanhaiying.cn",
            "@BaseLoc": "Res",
            "ofd:ColorSpaces": {
                "ofd:ColorSpace": {
                    "@ID": 0,
                    "@Type": "RGB",
                    "@BitsPerComponent": "8",
                    "#text": "",
                }
            },
            "ofd:Fonts": {
                "ofd:Font": [
                    {
                        "@ID": 0,
                        "@FontName": "宋体",
                        "@FamilyName": "宋体",
                    }
                ]
            },
        }
    }

    def gen_id(self, ofdjson, id_key):
        """生成ID并维护UUID映射

        重写父类方法，在生成ID的同时维护UUID到ID的映射关系

        Args:
            ofdjson: OFD JSON数据
            id_key: 需要添加ID的元素类型
        """
        # print("id_key ", id_key, "ofdjson ", ofdjson)

        for k, v in ofdjson.items():
            if k == id_key:
                # 添加id
                if isinstance(ofdjson[k], dict):
                    ofdjson[k]["@ID"] = f"{self.id_obj.get_id()}"
                    if res_uuid := ofdjson[k].get("res_uuid"):
                        self.id_obj.add_uuid_map(res_uuid, ofdjson[k]["@ID"])
                    # logger.info(f"添加id -> {ofdjson[k]}")
                elif isinstance(ofdjson[k], list):
                    for i in ofdjson[k]:

                        i["@ID"] = f"{self.id_obj.get_id()}"
                        if res_uuid := i.get("res_uuid"):
                            self.id_obj.add_uuid_map(res_uuid, i["@ID"])
                        # logger.info(f"添加id ->i {i}")

            elif isinstance(v, dict):
                # logger.debug(f"dict_v{v}")
                self.gen_id(v, id_key)

            elif isinstance(v, list):
                for v_cell in v:
                    if isinstance(v_cell, dict):
                        # logger.debug(f"dict_v{v}")
                        self.gen_id(v_cell, id_key)


"""
    "ofd:Font": [

    {
        "@ID": 0,
        "@FontName": "STSong",
        "@FamilyName": "SimSun",
        "@Serif": "true",
        "@FixedWidth": "true",
        "@Charset": "prc"
    }
            "ofd:Area": {
            "ofd:PhysicalBox": "0 0 210 140"
        },
"""


class ContentTemplate(TemplateBase):
    """
    内容模板 - 正文部分 Content.xml

    定义页面的具体内容，包括文本、图像、路径等对象
    """

    # "@Type": "Body",
    template_name = "Content"
    # 键映射表
    key_map = {
        "ImageObject": "ofd:ImageObject",
        "PathObject": "ofd:PathObject",
        "TextObject": "ofd:TextObject",
        "CGTransform": "ofd:CGTransform",
        "PhysicalBox": "ofd:PhysicalBox",
    }
    # 需要添加ID的元素类型
    id_keys = [
        "ofd:Layer",
        "ofd:TextObject",
        "ofd:PathObject",
        "ofd:Clips",
        "ofd:ImageObject",
    ]
    # 相关性映射，定义不同对象类型与其资源ID的关联
    correlate_map = {"ofd:TextObject": "@Font", "ofd:ImageObject": "@ResourceID"}

    # Content.xml的默认模板
    ofdjson = {
        "ofd:Page": {
            "@xmlns:ofd": "http://blog.yuanhaiying.cn",
            "ofd:Content": {
                "ofd:PageArea": {"ofd:PhysicalBox": "0 0 210 140"},
                "ofd:Layer": {
                    "@ID": 0,
                    "@Type": "Foreground",
                    "ofd:TextObject": [
                        {
                            "@ID": 0,
                            "@CTM": "7.054 0 0 7.054 0 134.026",
                            "@Boundary": "69 7 72 7.6749",
                            "@Font": "69",
                            "@Size": "6.7028",
                            "ofd:FillColor": {
                                "@ColorSpace": "4",
                                "@Value": "156 82 35",
                            },
                            "ofd:CGTransform": {
                                "@CodePosition": "0",
                                "@CodeCount": "10",
                                "@GlyphCount": "10",
                                "ofd:Glyphs": "18 10 11 42 60 53 24 11 42 61",
                            },
                            "ofd:TextCode": {
                                "@X": "13.925",
                                "@Y": "10",
                                "@DeltaX": "7 7 7 7 7 7 7 7 7",
                                "#text": "电⼦发票（普通发票）",
                            },
                        }
                    ],
                    "ofd:ImageObject": [],
                },
            },
        }
    }

    def __init__(self, *args, **kwargs):
        """初始化内容模板

        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        # print(args)
        # print(kwargs)
        super().__init__(*args, **kwargs)
        # 关联res_uuid
        for key, targe_key in self.correlate_map.items():
            self.correlate_res_uuid(self.final_json, key, targe_key)

    def correlate_res_uuid(self, ofdjson, key, targe_key):
        """关联资源UUID到实际ID

        将JSON中使用的资源UUID替换为实际的资源ID

        Args:
            ofdjson: OFD JSON数据
            key: 对象类型键
            targe_key: 目标键（如@Font或@ResourceID）
        """
        """correlate_res_uuid"""
        # print("========uuid_map", self.id_obj.uuid_map)
        for k, v in ofdjson.items():
            if k == key:
                if isinstance(v, dict) and (res_uuid := v_cell.pop("res_uuid", None)):

                    v[targe_key] = self.id_obj.uuid_map[res_uuid]
                    logger.debug(f"{targe_key} >>> {v[targe_key]} -- {res_uuid}")
                elif isinstance(v, list):
                    for v_cell in v:
                        if isinstance(v_cell, dict) and (
                            res_uuid := v_cell.pop("res_uuid", None)
                        ):

                            v_cell[targe_key] = self.id_obj.uuid_map[res_uuid]
                            logger.debug(
                                f"{targe_key} >>> {v_cell[targe_key]} -- {res_uuid}"
                            )
                        else:
                            print(f"v_cell {v_cell}")
                    pass
                else:
                    pass
            elif isinstance(v, dict):
                self.correlate_res_uuid(v, key, targe_key)
            elif isinstance(v, list):
                for v_cell in v:
                    if isinstance(v_cell, dict):
                        self.correlate_res_uuid(v_cell, key, targe_key)


"""
                "ofd:PathObject": [{
                        "@ID": 0,
                        "@CTM": "0.3527 0 0 -0.3527 0.35 141.43001",
                        "@Boundary": "-0.35 -0.35 212.33 141.78999",
                        "@LineWidth": "1",
                        "@MiterLimit": "10",
                        "@Stroke": "false",
                        "@Fill": "true",
                        "ofd:FillColor": {
                            "@ColorSpace": "4",
                            "@Value": "255 255 255"
                        },
                        "ofd:StrokeColor": {
                            "@ColorSpace": "4",
                            "@Value": "0 0 0"
                        },
                        "ofd:Clips": {
                            "ofd:Clip": {
                                "ofd:Area": {
                                    "ofd:Path": {
                                        "@ID": 0,
                                        "@Boundary": "0.00766 -0.00763 600 400.00003",
                                        "@Stroke": "false",
                                        "@Fill": "true",
                                        "ofd:AbbreviatedData": "M 0 0 L 600 0 L 600 400.00003 L 0 400.00003 C"
                                    }
                                }
                            }
                        },
                        "ofd:AbbreviatedData": "M -1 401 L 601 401 L 601 -1 L -1 -1 C"
                    },],
                
"ofd:ImageObject": [{
                        "@ID": 0,
                        "@CTM": "19.7512 0 0 19.7512 0 0",
                        "@Boundary": "7.23035 7.40671 19.7512 19.7512",
                        "@ResourceID": "104"
                    }],
"""


class OFDStructure(object):
    """
    OFD结构类

    用于组织和生成完整的OFD文档结构，包括所有必要的XML文件和资源文件
    """

    def __init__(
        self,
        name,
        ofd=None,
        document=None,
        document_res=None,
        public_res=None,
        content_res: list = [],
        res_static: dict = {},
    ):
        """
        初始化OFD结构

        Args:
            name: 文档名称
            ofd: OFD模板实例
            document: 文档模板实例
            document_res: 文档资源模板实例
            public_res: 公共资源模板实例
            content_res: 内容模板实例列表
            res_static: 静态资源字典
        """
        # 初始化的时候会先自动初始化 默认参数值
        id_obj = CurId()
        self.name = name
        self.ofd = ofd if ofd else OFDTemplate(id_obj=id_obj)
        self.document = document if document else DocumentTemplate(id_obj=id_obj)
        self.document_res = (
            document_res if document_res else DocumentResTemplate(id_obj=id_obj)
        )
        self.public_res = public_res if public_res else PublicResTemplate(id_obj=id_obj)
        self.content_res = (
            content_res if content_res else [ContentTemplate(id_obj=id_obj)]
        )
        self.res_static = res_static

    def _clear_dir(self, path: str):
        """
        清空指定目录下的所有内容

        清空目录中的所有文件和子目录，但保留目录本身

        Args:
            path: 要清空的目录路径
        """
        if not os.path.exists(path):
            return

        for entry in os.scandir(path):
            try:
                if entry.is_file() or entry.is_symlink():
                    os.remove(entry.path)
                elif entry.is_dir():
                    shutil.rmtree(entry.path)
            except Exception as e:
                raise RuntimeError(f"清空目录失败: {entry.path}") from e

    def __call__(self, test=False):
        """生成OFD文件并返回其二进制内容

        创建完整的OFD文档结构，将所有组件写入相应文件，然后打包成ZIP格式

        Args:
            test (bool): 是否使用测试模式，测试模式下将文件保存到./test目录而非临时目录

        Returns:
            bytes: OFD文件的二进制内容
        """
        with tempfile.TemporaryDirectory() as t_dir:
            if test:
                temp_dir = r"./test"
                # os.mkdir(temp_dir)
                os.makedirs(
                    temp_dir, exist_ok=True
                )  # 改为 makedirs 并设置 exist_ok=True
            else:
                temp_dir = t_dir
            # ⭐ 新增：清空 temp_dir
            self._clear_dir(temp_dir)

            # 创建OFD文档结构目录
            temp_dir_doc_0 = os.path.join(temp_dir, "Doc_0")
            temp_dir_pages = os.path.join(temp_dir, "Doc_0", "Pages")
            temp_dir_res = os.path.join(temp_dir, "Doc_0", "Res")  # 静态资源路径
            for i in [temp_dir_doc_0, temp_dir_pages, temp_dir_res]:
                # print(i)
                os.mkdir(i)

            # 写入OFD根文件
            self.ofd.save(os.path.join(temp_dir, "OFD.xml"))

            # 更新最大单元ID并写入文档配置文件
            self.document.update_max_unit_id()
            self.document.save(os.path.join(temp_dir_doc_0, "Document.xml"))

            # 写入文档资源配置文件
            self.document_res.save(os.path.join(temp_dir_doc_0, "DocumentRes.xml"))

            # 写入公共资源配置文件
            self.public_res.save(os.path.join(temp_dir_doc_0, "PublicRes.xml"))

            # 写入页面内容文件
            for idx, page in enumerate(self.content_res):
                temp_dir_pages_idx = os.path.join(temp_dir_pages, f"Page_{idx}")
                os.mkdir(temp_dir_pages_idx)
                # os.mkdir(i)
                page.save(os.path.join(temp_dir_pages_idx, "Content.xml"))

            # 写入静态资源文件
            for k, v in self.res_static.items():
                with open(os.path.join(temp_dir_res, k), "wb") as f:
                    f.write(v)

            # 将所有文件打包成OFD格式（ZIP压缩）
            zip = zipfile.ZipFile("test.ofd", "w", zipfile.ZIP_DEFLATED)
            for path, dirnames, filenames in os.walk(temp_dir):
                # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
                fpath = path.replace(temp_dir, "")

                for filename in filenames:
                    zip.write(
                        os.path.join(path, filename), os.path.join(fpath, filename)
                    )
            zip.close()

            # 读取生成的OFD文件内容并清理临时文件
            with open("test.ofd", "rb") as f:
                content = f.read()
            if os.path.exists("test.ofd"):
                os.remove("test.ofd")
            return content


if __name__ == "__main__":
    print("---------")
    # 资源文件
    img_path = r"F:\code\easyofd\test\test_img0.jpg"
    # with open(img_path, "rb") as f:
    #     content = f.read()
    content = b""
    res_static = {"Image_0.jpg": content}

    # 构建数据
    font = [
        {
            "@FontName": "宋体",
            "@FamilyName": "宋体",
        }
    ]

    MultiMedia = [{"@Type": "Image", "ofd:MediaFile": "Image_0.jpg"}]

    ImageObject = [
        {"@CTM": "200 0 0 140 0 0", "@Boundary": "0 0 200 140", "@ResourceID": "55"}
    ]
    TextObject = [
        {
            "@Boundary": "50 5 100 20",
            "@Font": "2",
            "@Size": "5",
            "ofd:FillColor": {"@Value": "156 82 35", "@ColorSpace": "1"},
            "ofd:TextCode": {
                "@X": "5",
                "@Y": "5",
                "@DeltaX": "7 7 7 7 7 7 7 7 7",
                "#text": "电⼦发票（普通发票）",
            },
        },
        {
            "@Boundary": "0 0 100 100",
            "@Font": "2",
            "@Size": "10",
            "ofd:FillColor": {"@Value": "156 82 35"},
            "ofd:TextCode": {"@X": "0", "@Y": "0", "@DeltaX": "0", "#text": "电"},
        },
    ]

    # 实例化模板
    id_obj = CurId()
    print("id_obj实例化", id_obj)

    ofd = OFDTemplate(id_obj=id_obj)
    document = DocumentTemplate(id_obj=id_obj)
    public_res = PublicResTemplate(Font=font, id_obj=id_obj)
    document_res = DocumentResTemplate(MultiMedia=MultiMedia, id_obj=id_obj)
    # ImageObject=ImageObject
    content_res = ContentTemplate(
        CGTransform=[],
        PathObject=[],
        TextObject=TextObject,
        ImageObject=[],
        id_obj=id_obj,
    )

    ofd_byte = OFDStructure(
        "123",
        ofd=ofd,
        document=document,
        public_res=public_res,
        document_res=document_res,
        content_res=[content_res],
        res_static=res_static,
    )(test=True)

    with open("test.ofd", "wb") as f:
        content = f.write(ofd_byte)

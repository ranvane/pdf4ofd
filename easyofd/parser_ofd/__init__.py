from loguru import logger
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont

# from ofd_parser import *


font_map = {
    "simsun.ttc": ["宋体", "SWPMEH+SimSun", "SimSun", "SWDKON+SimSun"],
    "simkai.ttf": ["KaiTi", "楷体", "SWLCQE+KaiTi", "SWHGME+KaiTi", "BWSimKai"],
    # 'STKAITI.TTF':["华文楷体 常规","STKAITI","华文楷体"],
    "couri.ttf": [
        "CourierNewPSMT",
        "CourierNew",
        "SWCRMF+CourierNewPSMT",
        "SWANVV+CourierNewPSMT",
    ],
    "courbd.ttf": ["Courier New"],
    "simhei.ttf": ["SimHei", "hei", "黑体"],
}
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

# 初始化字体
for font, names in font_map.items():
    for name in names:
        try:
            pdfmetrics.registerFont(TTFont(name, font))
        except:
            logger.warning(f"FONT  registerFont failed {font}: {name}")

from easyofd.parser_ofd.ofd_parser import OFDParser

_OP = (
    96 / 25.4
)  # 当前使用的转换因子：96 DPI转换为毫米单位,转换因子的另一种计算方式:(200 / 25.4) / (200 / 96) = 96 / 25.4 ≈ 3.78

__all__ = ["OFDParser"]

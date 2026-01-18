from reportlab.pdfbase import pdfmetrics
from easyofd.parser_ofd import *

FONTS = [
    "宋体",
    "SWPMEH+SimSun",
    "SimSun",
    "KaiTi",
    "楷体",
    "STKAITI",
    "SWLCQE+KaiTi",
    "Courier New",
    "STSong-Light",
    "CourierNew",
    "SWANVV+CourierNewPSMT",
    "CourierNewPSMT",
    "BWSimKai",
    "hei",
    "黑体",
    "SimHei",
    "SWDKON+SimSun",
    "SWCRMF+CourierNewPSMT",
    "SWHGME+KaiTi",
]
from .font_tools import FontTool
from .draw_pdf import DrawPDF
from .draw_ofd import OFDWrite


# OP = 200 / 25.4  # 旧的转换因子（已被覆盖）

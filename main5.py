# main.py
import sys
import os
import base64
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot, QObject, QEvent
from easyofd import OFD
from ui_main import (
    Ui_MainWindow,
)  # 确保 ui_main.py 是用 pyuic5 -x main.ui -o ui_main.py 生成的
from loguru import logger


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.ofd = OFD()
        self.update_convert_button_text()
        # 允许 QLineEdit 接受拖拽
        self.file_path.setAcceptDrops(True)
        # 安装事件过滤器
        self.file_path.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.file_path:
            if event.type() == QEvent.DragEnter:
                mime = event.mimeData()
                if mime.hasUrls():
                    self.file_path.clear()
                    event.acceptProposedAction()
                    return True

            elif event.type() == QEvent.Drop:
                mime = event.mimeData()
                if mime.hasUrls():
                    file_path = mime.urls()[0].toLocalFile()
                    self.file_path.setText(file_path)
                    event.acceptProposedAction()
                    return True

        return super().eventFilter(obj, event)

    def check_file(self, name, endswith: str):
        if name.lower().endswith(endswith):
            return True

    def save_img(self, name, img_np):
        for inx, img in enumerate(img_np):
            # im = Image.fromarray(img)
            img.save(name.format(inx))

    def save_file(self, name, _bytes):
        with open(name, "wb") as f:
            if isinstance(_bytes, list):
                _bytes = _bytes[0]
            f.write(_bytes)

    def read_ofd(self, path):
        with open(path, "rb") as f:
            ofdb64 = str(base64.b64encode(f.read()), "utf-8")
        return ofdb64

    def read_pfd(self, path):
        with open(path, "rb") as f:
            pfd_byte = f.read()
        return pfd_byte

    def swap_pdf_ofd_path(self, file_path: str) -> str:
        if not isinstance(file_path, str):
            raise TypeError("file_path 必须是字符串")

        base, ext = os.path.splitext(file_path)
        ext_lower = ext.lower()

        if ext_lower == ".pdf":
            return base + ".ofd"
        elif ext_lower == ".ofd":
            return base + ".pdf"
        else:
            raise ValueError(f"不支持的文件扩展名: '{ext}'，仅支持 .pdf 或 .ofd")

    @pyqtSlot()
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "",
            "PDF/OFD 文件 (*.pdf *.ofd);;PDF 文件 (*.pdf);;OFD 文件 (*.ofd);;所有文件 (*)",
        )
        if file_path:
            self.file_path.setText(file_path)
            self.update_convert_button_text(file_path)

    @pyqtSlot()
    def update_convert_button_text(self, file_path=None):
        if file_path is None:
            file_path = self.file_path.text().strip()

        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".ofd":
                self.convertButton.setText("转换为 PDF")
                # self.convertImageButton.setText("转换为 PDF(图片方式)")
            elif ext == ".pdf":
                self.convertButton.setText("转换为 OFD")
                # self.convertImageButton.setText("转换为 OFD(图片方式)")
            else:
                self.convertButton.setText("转换文件")
                # self.convertImageButton.setText("转换文件(图片方式)")
        else:
            self.convertButton.setText("转换文件")
            # self.convertImageButton.setText("转换文件(图片方式)")


    @pyqtSlot()
    def convert_file(self):
        path = self.file_path.text().strip()
        if not path:
            QMessageBox.warning(self, "警告", "请先选择一个文件！")
            return

        if not os.path.isfile(path):
            QMessageBox.critical(self, "错误", "所选文件不存在！")
            return

        msg = ""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            try:
                logger.info(f"将 {path} 转换为 OFD 文件!")
                self.statusbar.showMessage(f"开始转换...", 3000)
                output = self.swap_pdf_ofd_path(path)
                if os.path.isfile(output):
                    QMessageBox.critical(self, "错误", "OFD文件存在！")
                    return

                pfdbyte = self.read_pfd(path)
                ofd_byte = self.ofd.pdf2ofd(pfdbyte)
                self.save_file(output, ofd_byte)
                logger.info(f"PDF转OFD模式： {output} completed")
                msg = f"{output} 转换完成！"
                self.statusbar.showMessage(f"{output} 转换完成!")
            except Exception as e:
                logger.exception(f"PDF 转 OFD 出错:{e}")
                self.statusbar.showMessage("PDF转OFD出错！")
                QMessageBox.critical(self, "错误", "PDF转OFD出错！")
                return

        elif ext == ".ofd":
            try:
                logger.info(f"将 {path} 转换为 PDF 文件!")
                self.statusbar.showMessage("开始转换...")

                output = self.swap_pdf_ofd_path(path)
                if os.path.isfile(output):
                    QMessageBox.critical(self, "错误", "PDF文件存在！")
                    return

                ofdb64 = self.read_ofd(path)
                self.ofd.read(ofdb64)
                pdf_bytes = self.ofd.to_pdf()
                self.save_file(output, pdf_bytes)
                logger.info(f"OFD转PDF模式： {output} completed")
                self.statusbar.showMessage(f"{output} 转换完成!")
                msg = f"{output} 转换完成！"
            except Exception as e:
                logger.exception(f"OFD 转 PDF 转换出错:{e}")
                self.statusbar.showMessage("OFD 转 PDF 转换出错！")
                QMessageBox.critical(self, "错误", "OFD 转 PDF 转换出错！")

                return

        else:
            QMessageBox.warning(self, "不支持", "仅支持 .pdf 或 .ofd 文件！")
            self.statusbar.showMessage("仅支持 .pdf 或 .ofd 文件！")
            msg = "仅支持 .pdf 或 .ofd 文件！"
            return

        QMessageBox.information(self, "成功!", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())  # 注意：PyQt5 是 exec_()，不是 exec()

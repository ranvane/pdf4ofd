# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLayout,
    QLineEdit, QMainWindow, QPushButton, QSizePolicy,
    QStatusBar, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setEnabled(False)
        MainWindow.resize(831, 197)
        MainWindow.setMinimumSize(QSize(800, 0))
        MainWindow.setMaximumSize(QSize(850, 16777215))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layoutWidget = QWidget(self.centralwidget)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(20, 30, 791, 51))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.layoutWidget)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(80, 30))
        self.label.setMaximumSize(QSize(80, 30))

        self.horizontalLayout.addWidget(self.label)

        self.file_path = QLineEdit(self.layoutWidget)
        self.file_path.setObjectName(u"file_path")
        self.file_path.setMinimumSize(QSize(600, 30))
        self.file_path.setMaximumSize(QSize(600, 30))

        self.horizontalLayout.addWidget(self.file_path)

        self.selectFileButton = QPushButton(self.layoutWidget)
        self.selectFileButton.setObjectName(u"selectFileButton")
        self.selectFileButton.setMinimumSize(QSize(60, 30))
        self.selectFileButton.setMaximumSize(QSize(60, 30))

        self.horizontalLayout.addWidget(self.selectFileButton)

        self.widget = QWidget(self.centralwidget)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(250, 90, 308, 42))
        self.horizontalLayout_2 = QHBoxLayout(self.widget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.convertButton = QPushButton(self.widget)
        self.convertButton.setObjectName(u"convertButton")
        self.convertButton.setMinimumSize(QSize(130, 40))
        self.convertButton.setMaximumSize(QSize(130, 40))

        self.horizontalLayout_2.addWidget(self.convertButton)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.selectFileButton.clicked.connect(MainWindow.select_file)
        self.convertButton.clicked.connect(MainWindow.convert_file)
        self.file_path.textChanged.connect(MainWindow.update_convert_button_text)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"PDF\u3001OFD\u6587\u4ef6\u4e92\u76f8\u8f6c\u6362", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u8bf7\u9009\u62e9\u6587\u4ef6\uff1a", None))
        self.selectFileButton.setText(QCoreApplication.translate("MainWindow", u"\u9009\u62e9", None))
        self.convertButton.setText(QCoreApplication.translate("MainWindow", u"\u8f6c\u6362\u6587\u4ef6", None))
    # retranslateUi


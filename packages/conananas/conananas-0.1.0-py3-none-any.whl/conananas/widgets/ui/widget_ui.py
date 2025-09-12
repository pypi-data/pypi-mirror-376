# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widget.ui'
##
## Created by: Qt User Interface Compiler version 6.8.3
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListView,
    QPushButton, QSizePolicy, QTableView, QVBoxLayout,
    QWidget)

class Ui_Ananas(object):
    def setupUi(self, Ananas):
        if not Ananas.objectName():
            Ananas.setObjectName(u"Ananas")
        Ananas.resize(1142, 659)
        self.verticalLayout = QVBoxLayout(Ananas)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayoutPacakge = QHBoxLayout()
        self.horizontalLayoutPacakge.setObjectName(u"horizontalLayoutPacakge")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.labelRemote = QLabel(Ananas)
        self.labelRemote.setObjectName(u"labelRemote")

        self.horizontalLayout_3.addWidget(self.labelRemote)

        self.comboBoxRemote = QComboBox(Ananas)
        self.comboBoxRemote.setObjectName(u"comboBoxRemote")

        self.horizontalLayout_3.addWidget(self.comboBoxRemote)

        self.pushButtonRefresh = QPushButton(Ananas)
        self.pushButtonRefresh.setObjectName(u"pushButtonRefresh")

        self.horizontalLayout_3.addWidget(self.pushButtonRefresh)

        self.horizontalLayout_3.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.listViewPackages = QListView(Ananas)
        self.listViewPackages.setObjectName(u"listViewPackages")
        self.listViewPackages.setMinimumSize(QSize(300, 0))

        self.verticalLayout_2.addWidget(self.listViewPackages)

        self.listViewVersions = QListView(Ananas)
        self.listViewVersions.setObjectName(u"listViewVersions")

        self.verticalLayout_2.addWidget(self.listViewVersions)

        self.horizontalLayoutRevisions = QHBoxLayout()
        self.horizontalLayoutRevisions.setObjectName(u"horizontalLayoutRevisions")
        self.labelRevision = QLabel(Ananas)
        self.labelRevision.setObjectName(u"labelRevision")

        self.horizontalLayoutRevisions.addWidget(self.labelRevision)

        self.comboBoxRevision = QComboBox(Ananas)
        self.comboBoxRevision.setObjectName(u"comboBoxRevision")

        self.horizontalLayoutRevisions.addWidget(self.comboBoxRevision)

        self.horizontalLayoutRevisions.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayoutRevisions)

        self.verticalLayout_2.setStretch(1, 5)
        self.verticalLayout_2.setStretch(2, 3)

        self.horizontalLayoutPacakge.addLayout(self.verticalLayout_2)

        self.verticalLayoutDetails = QVBoxLayout()
        self.verticalLayoutDetails.setObjectName(u"verticalLayoutDetails")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.labelPackage = QLabel(Ananas)
        self.labelPackage.setObjectName(u"labelPackage")

        self.horizontalLayout_2.addWidget(self.labelPackage)

        self.comboBoxPackage = QComboBox(Ananas)
        self.comboBoxPackage.setObjectName(u"comboBoxPackage")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBoxPackage.sizePolicy().hasHeightForWidth())
        self.comboBoxPackage.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.comboBoxPackage)


        self.verticalLayoutDetails.addLayout(self.horizontalLayout_2)

        self.tableViewDetails = QTableView(Ananas)
        self.tableViewDetails.setObjectName(u"tableViewDetails")

        self.verticalLayoutDetails.addWidget(self.tableViewDetails)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.pushButtonOpenRecipeFolder = QPushButton(Ananas)
        self.pushButtonOpenRecipeFolder.setObjectName(u"pushButtonOpenRecipeFolder")

        self.gridLayout.addWidget(self.pushButtonOpenRecipeFolder, 0, 2, 1, 1)

        self.labelRecipeFolder = QLabel(Ananas)
        self.labelRecipeFolder.setObjectName(u"labelRecipeFolder")

        self.gridLayout.addWidget(self.labelRecipeFolder, 0, 0, 1, 1)

        self.lineEditRecipeFolder = QLineEdit(Ananas)
        self.lineEditRecipeFolder.setObjectName(u"lineEditRecipeFolder")

        self.gridLayout.addWidget(self.lineEditRecipeFolder, 0, 1, 1, 1)

        self.labelPackageFolder = QLabel(Ananas)
        self.labelPackageFolder.setObjectName(u"labelPackageFolder")

        self.gridLayout.addWidget(self.labelPackageFolder, 1, 0, 1, 1)

        self.lineEditPackageFolder = QLineEdit(Ananas)
        self.lineEditPackageFolder.setObjectName(u"lineEditPackageFolder")
        self.lineEditPackageFolder.setReadOnly(True)

        self.gridLayout.addWidget(self.lineEditPackageFolder, 1, 1, 1, 1)

        self.pushButtonOpenPackageFolder = QPushButton(Ananas)
        self.pushButtonOpenPackageFolder.setObjectName(u"pushButtonOpenPackageFolder")

        self.gridLayout.addWidget(self.pushButtonOpenPackageFolder, 1, 2, 1, 1)


        self.verticalLayoutDetails.addLayout(self.gridLayout)


        self.horizontalLayoutPacakge.addLayout(self.verticalLayoutDetails)

        self.horizontalLayoutPacakge.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayoutPacakge)


        self.retranslateUi(Ananas)

        QMetaObject.connectSlotsByName(Ananas)
    # setupUi

    def retranslateUi(self, Ananas):
        Ananas.setWindowTitle(QCoreApplication.translate("Ananas", u"Ananas", None))
        self.labelRemote.setText(QCoreApplication.translate("Ananas", u"Remote:", None))
        self.labelRevision.setText(QCoreApplication.translate("Ananas", u"Revision:", None))
        self.labelPackage.setText(QCoreApplication.translate("Ananas", u"Package:", None))
        self.labelRecipeFolder.setText(QCoreApplication.translate("Ananas", u"Recipe:", None))
        self.labelPackageFolder.setText(QCoreApplication.translate("Ananas", u"Package:", None))
    # retranslateUi


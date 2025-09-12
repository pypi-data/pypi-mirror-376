""" packages model """
from PySide6 import QtCore, QtGui
from conananas.ananas import Ananas
from conananas.model.model_base import ModelBase


# pylint: disable=invalid-name
class PackageModel(QtCore.QAbstractTableModel, ModelBase):
    """ conan package model """

    rows_changed = QtCore.Signal()
    path_changed = QtCore.Signal()

    # model data
    ananas:Ananas
    row_count = 0
    keys = []
    values = []
    title_rows = []
    double_span_rows = []

    def __init__(self, ananas):
        super().__init__()

        self.ananas = ananas

    def package_ready(self):
        """ set list of packages """
        self.row_count = 0
        self.keys = []
        self.values = []
        self.title_rows = []
        self.double_span_rows = []

        # calculate title rows
        if self.ananas.package_available():
            try:
                package = self.ananas.get_package()
                self.row_count = 0
                self.title_rows = []
                for group in package:
                    details = package[group]
                    self.keys.append(group.upper())
                    self.values.append(None)
                    self.title_rows.append(self.row_count)
                    self.double_span_rows.append(self.row_count)
                    if isinstance(details, list):
                        for detail in details:
                            self.keys.append(detail)
                            self.values.append(None)
                        self.double_span_rows.extend(
                            range(self.row_count + 1, self.row_count + 1 + len(details)))
                    else:
                        for key in details:
                            self.keys.append(key)
                            self.values.append(details[key])
                    self.row_count += len(details) + 1

                self.rows_changed.emit()
            except Exception as _ex:
                pass

        self.ananas.get_package_path()
        self.path_changed.emit()

    def rowCount(self, _parent=QtCore.QModelIndex()):
        """ QAbstractTableModel.rowCount override """
        return self.row_count

    def columnCount(self, _parent=QtCore.QModelIndex()):
        """ QAbstractTableModel.columnCount override """
        return 2

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """ QAbstractTableModel.data override """
        if not self.ananas.package_available():
            return None

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            try:
                row = index.row()
                col = index.column()
                return self.keys[row] if col == 0 else self.values[row]
            except Exception as _ex:
                print(f"name: {self.ananas.name}, version: {self.ananas.version} - ex: {str(_ex)}")

        elif role == QtCore.Qt.ItemDataRole.FontRole:
            row = index.row()
            col = index.column()
            if row in self.title_rows:
                font = QtGui.QFont()
                font.setBold(True)
                return font

        elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            row = index.row()
            col = index.column()
            if row in self.title_rows:
                return QtCore.Qt.AlignmentFlag.AlignCenter

        return None

    def flags(self, index):
        """ QAbstractTableModel.flags override """
        flags = super().flags(index)

        row = index.row()
        if row in self.title_rows:
            flags &= ~QtCore.Qt.ItemFlag.ItemIsEnabled

        return flags

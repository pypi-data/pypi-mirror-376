""" names model """
from PySide6 import QtCore
from conananas.ananas import Ananas
from conananas.model.model_base import ModelBase


# pylint: disable=invalid-name
class NamesModel(QtCore.QAbstractListModel, ModelBase):
    """ conan package names model """

    name_changed = QtCore.Signal(str)

    # model data
    ananas:Ananas

    def __init__(self, ananas):
        super().__init__()

        self.ananas = ananas

    def rowCount(self, _parent=QtCore.QModelIndex()):
        """ QAbstractListModel.rowCount override """
        if self.ananas.remote_available():
            return self.ananas.get_names_count()

        return 0

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """ QAbstractListModel.data override """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()
            if -1 < row < self.ananas.get_names_count():
                key = self.ananas.get_names()[row]
                return key

        return None

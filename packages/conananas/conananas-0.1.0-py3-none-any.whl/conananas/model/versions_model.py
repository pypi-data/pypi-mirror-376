""" versions model """
from PySide6 import QtCore
from conananas.ananas import Ananas
from conananas.model.model_base import ModelBase


# pylint: disable=invalid-name
class VersionsModel(QtCore.QAbstractListModel, ModelBase):
    """ conan package version model """

    version_changed = QtCore.Signal(str)

    # model data
    ananas:Ananas

    def __init__(self, ananas):
        super().__init__()

        self.ananas = ananas

    def rowCount(self, _parent=QtCore.QModelIndex()):
        """ QAbstractListModel.rowCount override """
        return self.ananas.get_versions_count()

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """ QAbstractListModel.data override """
        if role == QtCore.Qt.ItemDataRole.DisplayRole and self.ananas.name_available():
            row = index.row()
            if row > -1:
                versions = self.ananas.get_versions()
                if row < len(versions):
                    return versions[row]

        return None

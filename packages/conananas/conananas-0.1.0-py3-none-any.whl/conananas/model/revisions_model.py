""" revisions model """
from PySide6 import QtCore
from conananas.ananas import Ananas
from conananas.model.model_base import ModelBase


# pylint: disable=invalid-name
class RevisionsModel(QtCore.QAbstractListModel, ModelBase):
    """ conan package revisions model """

    # model data
    ananas:Ananas

    def __init__(self, ananas):
        super().__init__()

        self.ananas = ananas

    def rowCount(self, _parent=QtCore.QModelIndex()):
        """ QAbstractListModel.rowCount override """
        return self.ananas.get_revisions_count()

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """ QAbstractListModel.data override """
        if role == QtCore.Qt.ItemDataRole.DisplayRole and self.ananas.version_available():
            try:
                row = index.row()
                if row > -1:
                    revisions = self.ananas.get_revisions()
                    if row < len(revisions):
                        return list(revisions)[row]
            except Exception as _ex:
                print(f"name: {self.ananas.name}, version: {self.ananas.version} - ex: {str(_ex)}")

        return None

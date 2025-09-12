""" packages model """
from PySide6 import QtCore
from conananas.ananas import Ananas
from conananas.model.model_base import ModelBase


# pylint: disable=invalid-name
class PackagesModel(QtCore.QAbstractListModel, ModelBase):
    """ conan packages model """

    package_changed = QtCore.Signal(str)

    # model data
    ananas:Ananas

    def __init__(self, ananas):
        super().__init__()

        self.ananas = ananas

    @QtCore.Slot(int)
    def index_changed(self, index):
        """ slot to forward selectionChanged signal from selection model to VersionsModel """
        try:
            package_hash = self.data(self.index(index, 0), QtCore.Qt.ItemDataRole.UserRole)

            self.package_changed.emit(package_hash)
        except Exception as _ex:
            pass

    def rowCount(self, _parent=QtCore.QModelIndex()):
        """ QAbstractListModel.rowCount override """
        return self.ananas.get_packages_count()

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """ QAbstractListModel.data override """
        if (role in [QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.UserRole]
            and self.ananas.name and self.ananas.version):
            try:
                row = index.row()
                if row > -1:
                    detailed = role == QtCore.Qt.ItemDataRole.DisplayRole
                    packages = self.ananas.get_packages(detailed=detailed)
                    if row < len(packages):
                        return list(packages)[row]
            except Exception as _ex:
                print(f"name: {self.ananas.name}, version: {self.ananas.version} - ex: {str(_ex)}")

        return None

""" widget """
from pathlib import Path
from PySide6 import QtWidgets, QtGui, QtCore
from conananas.widgets.ui.widget_ui import Ui_Ananas
from conananas.model.controller import Controller


class AnanasWidget(QtWidgets.QWidget, Ui_Ananas):
    """ ananas main widget """

    start_get_revisions = QtCore.Signal(str)

    controller:Controller

    def __init__(self, parent=None):
        super().__init__(parent)
        super().setupUi(self)

        self.controller = Controller(self)

        self.controller.remotes_ready.connect(self._remotes_updated)

        # setup button icons
        icon_dir = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon)
        icon_refresh = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload)
        self.pushButtonOpenRecipeFolder.setIcon(icon_dir)
        self.pushButtonOpenPackageFolder.setIcon(icon_dir)
        self.pushButtonRefresh.setIcon(icon_refresh)

        self.pushButtonRefresh.clicked.connect(self.controller.load_remotes)

        self.comboBoxRemote.currentTextChanged.connect(self.controller.remote_changed)

        self.controller.package_model.rows_changed.connect(self._update_col_span)
        self.controller.package_model.path_changed.connect(self._update_path)
        self.tableViewDetails.setModel(self.controller.package_model)

        self.comboBoxPackage.setModel(self.controller.packages_model)
        self.comboBoxPackage.currentIndexChanged.connect(
            self.controller.packages_model.index_changed)
        self.controller.packages_model.package_changed.connect(
            self.controller.package_changed)

        self.comboBoxRevision.setModel(self.controller.revisions_model)
        self.comboBoxRevision.currentTextChanged.connect(
            self.controller.revision_changed)

        self.listViewVersions.setModel(self.controller.versions_model)
        self.listViewVersions.selectionModel().currentChanged.connect(
            self.controller.version_changed)

        self.listViewPackages.setModel(self.controller.names_model)
        self.listViewPackages.selectionModel().currentChanged.connect(
            self.controller.name_changed)

        # setup table
        self.tableViewDetails.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tableViewDetails.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tableViewDetails.verticalHeader().hide()
        self.tableViewDetails.horizontalHeader().hide()
        self.tableViewDetails.setSelectionBehavior(
            QtWidgets.QTableView.SelectionBehavior.SelectRows)

        self.pushButtonOpenRecipeFolder.clicked.connect(self._open_path)
        self.pushButtonOpenPackageFolder.clicked.connect(self._open_path)

        self.controller.load_remotes()

    def on_close(self):
        """ QtCore.QWidget.closeEvent override """
        self.controller.close()

    @QtCore.Slot()
    def _update_col_span(self):
        row = 0
        while row < self.controller.package_model.row_count:
            if row in self.controller.package_model.double_span_rows:
                self.tableViewDetails.setSpan(row, 0, 1, 2)
            elif self.tableViewDetails.columnSpan(row, 0) != 1:
                self.tableViewDetails.setSpan(row, 0, 1, 1)
            row += 1

    @QtCore.Slot()
    def _update_path(self):
        recipe_path = self.controller.ananas.recipe_path
        self.lineEditRecipeFolder.setText(recipe_path if recipe_path else "")
        package_path = self.controller.ananas.package_path
        self.lineEditPackageFolder.setText(package_path if package_path else "")

    @QtCore.Slot()
    def _open_path(self):
        try:
            path = Path(
                self.lineEditPackageFolder.text()
                if self.sender() == self.pushButtonOpenPackageFolder
                else self.lineEditRecipeFolder.text())
            if path.is_dir():
                QtGui.QDesktopServices.openUrl(path.as_uri())
        except Exception as _ex:
            pass

    @QtCore.Slot()
    def _remotes_updated(self):
        self.comboBoxRemote.clear()
        self.comboBoxRemote.addItems(self.controller.ananas.get_remotes())
        c = self.comboBoxRemote.count()
        disabled_remotes = self.controller.ananas.get_disabled_remotes()
        self.comboBoxRemote.addItems(disabled_remotes)
        model = self.comboBoxRemote.model()
        while c < model.rowCount():
            item = model.item(c)
            item.setEnabled(False)
            c += 1

    @QtCore.Slot(str)
    def _version_changed(self, new_version):
        self.start_get_revisions.emit(new_version)

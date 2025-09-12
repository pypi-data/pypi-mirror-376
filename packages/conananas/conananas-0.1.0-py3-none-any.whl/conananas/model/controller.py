""" model controller """
from enum import Enum
from PySide6 import QtCore
from PySide6 import QtWidgets
from conananas.model.names_model import NamesModel
from conananas.model.versions_model import VersionsModel
from conananas.model.revisions_model import RevisionsModel
from conananas.model.packages_model import PackagesModel
from conananas.model.package_model import PackageModel
from conananas.ananas import Ananas


class ModelType(Enum):
    """ enum to iterate over model types """
    NAMES_MODEL = 4
    VERSIONS_MODEL = 3
    REVISIONS_MODEL = 2
    PACKAGES_MODEL = 1
    PACKAGE_MODEL = 0

class Worker(QtCore.QObject):
    """ threaded worker """

    remotes_ready = QtCore.Signal()
    names_ready = QtCore.Signal()
    versions_ready = QtCore.Signal()
    revisions_ready = QtCore.Signal()
    packages_ready = QtCore.Signal()

    ananas:Ananas

    def __init__(self, parent, ananas:Ananas):
        super().__init__(parent)
        self.ananas = ananas

    def read_remotes(self):
        """ threaded read remotes """
        self.ananas.read_remotes()
        self.remotes_ready.emit()

    def read_names(self, current_remote):
        """ threaded read names """
        self.ananas.read_all_packages(current_remote)
        self.names_ready.emit()

    def read_versions(self, current_name):
        """ threaded read versions """
        if self.ananas.set_name(current_name):
            self.ananas.get_versions()
        self.versions_ready.emit()

    def read_revisions(self, new_version):
        """ threaded read revisions """
        if self.ananas.set_version(new_version):
            self.ananas.get_revisions()
        self.revisions_ready.emit()

    def read_packages(self, new_revision):
        """ threaded read packages """
        if self.ananas.set_revision(new_revision):
            self.ananas.get_packages()
        self.packages_ready.emit()

class Controller(QtCore.QObject):
    """ model controller """

    read_remotes = QtCore.Signal()
    remotes_ready = QtCore.Signal()
    read_names = QtCore.Signal(str)
    read_versions = QtCore.Signal(str)
    read_revisions = QtCore.Signal(str)
    read_packages = QtCore.Signal(str)

    window:QtWidgets.QWidget
    last_focus:QtWidgets.QWidget|None
    worker_thread = QtCore.QThread()

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.window = parent

        self.ananas = Ananas()
        self.names_model = NamesModel(self.ananas)
        self.versions_model = VersionsModel(self.ananas)
        self.revisions_model = RevisionsModel(self.ananas)
        self.packages_model = PackagesModel(self.ananas)
        self.package_model = PackageModel(self.ananas)

        self.worker = Worker(None, self.ananas)
        self.worker.remotes_ready.connect(self._remotes_ready)
        self.worker.names_ready.connect(self._names_ready)
        self.worker.versions_ready.connect(self._versions_ready)
        self.worker.revisions_ready.connect(self._revisions_ready)
        self.worker.packages_ready.connect(self._packages_ready)

        self.read_remotes.connect(self.worker.read_remotes)
        self.read_names.connect(self.worker.read_names)
        self.read_versions.connect(self.worker.read_versions)
        self.read_revisions.connect(self.worker.read_revisions)
        self.read_packages.connect(self.worker.read_packages)

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

    def close(self):
        """ called once widget is closed """
        self.worker_thread.quit()
        self.worker_thread.wait()

    @QtCore.Slot()
    def load_remotes(self):
        """ load remotes """
        self._set_enabled(False)
        self.read_remotes.emit()

    @QtCore.Slot(str)
    def remote_changed(self, current_remote):
        """ slot to forward a remote changed """
        self._set_enabled(False)
        self._begin_reset_model(ModelType.NAMES_MODEL)
        self.read_names.emit(current_remote)

    @QtCore.Slot(str)
    def package_changed(self, package):
        """ slot to forward a package change in PackagesModel """
        self.ananas.set_package(package)
        self._begin_reset_model(ModelType.PACKAGE_MODEL)
        self.package_model.package_ready()
        self._end_reset_model(ModelType.PACKAGE_MODEL)

    @QtCore.Slot(str)
    def revision_changed(self, revision):
        """ slot to forward a revision change in RevisionsModel """
        self._set_enabled(False)
        self._begin_reset_model(ModelType.PACKAGES_MODEL)
        self.read_packages.emit(revision)

    @QtCore.Slot(str)
    def version_changed(self, current, _previous):
        """ slot to forward a version change in VerionsModel """
        self._set_enabled(False)
        self._begin_reset_model(ModelType.REVISIONS_MODEL)
        self.read_revisions.emit(current.data())

    @QtCore.Slot(str)
    def name_changed(self, current, _previous):
        """ slot to forward a package name change in PackageModel """
        self._set_enabled(False)
        self._begin_reset_model(ModelType.VERSIONS_MODEL)
        self.read_versions.emit(current.data())

    @QtCore.Slot()
    def _remotes_ready(self):
        self._set_enabled(True)
        self.remotes_ready.emit()

    @QtCore.Slot()
    def _names_ready(self):
        self._set_enabled(True)
        self._end_reset_model(ModelType.NAMES_MODEL)

    @QtCore.Slot()
    def _versions_ready(self):
        self._set_enabled(True)
        self._end_reset_model(ModelType.VERSIONS_MODEL)

    @QtCore.Slot()
    def _revisions_ready(self):
        self._set_enabled(True)
        self._end_reset_model(ModelType.REVISIONS_MODEL)

    @QtCore.Slot()
    def _packages_ready(self):
        self._set_enabled(True)
        self._end_reset_model(ModelType.PACKAGES_MODEL)
        self.package_model.package_ready()

    def _set_enabled(self, enabled):
        if enabled:
            self.window.setEnabled(True)
            if self.last_focus:
                self.last_focus.setFocus()
        else:
            self.last_focus = QtWidgets.QApplication.focusWidget()
            self.window.setEnabled(False)

    def _begin_reset_model(self, model_type: ModelType):
        if model_type.value > ModelType.VERSIONS_MODEL.value:
            self.names_model.try_begin_reset_model()

        if model_type.value > ModelType.REVISIONS_MODEL.value:
            self.versions_model.try_begin_reset_model()

        if model_type.value > ModelType.PACKAGES_MODEL.value:
            self.revisions_model.try_begin_reset_model()

        if model_type.value > ModelType.PACKAGE_MODEL.value:
            self.packages_model.try_begin_reset_model()

        self.package_model.try_begin_reset_model()

    def _end_reset_model(self, model_type: ModelType):
        if model_type.value > ModelType.VERSIONS_MODEL.value:
            self.names_model.try_end_reset_model()

        if model_type.value > ModelType.REVISIONS_MODEL.value:
            self.versions_model.try_end_reset_model()

        if model_type.value > ModelType.PACKAGES_MODEL.value:
            self.revisions_model.try_end_reset_model()

        if model_type.value > ModelType.PACKAGE_MODEL.value:
            self.packages_model.try_end_reset_model()

        self.package_model.try_end_reset_model()

""" conananas application """
from PySide6 import QtWidgets
from conananas.widgets.widget import AnanasWidget


# inherits public methods from QDialog, Qt uses pascalCase
# pylint: disable=too-few-public-methods,invalid-name

class AnanasDialog(QtWidgets.QDialog):
    """ ananas dialog """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CONANanas")
        self.resize(1000, 600)
        layout = QtWidgets.QHBoxLayout()
        self.widget = AnanasWidget()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget)
        self.setLayout(layout)

    def closeEvent(self, event):
        """ QtCore.QDialog.closeEvent override """
        self.widget.on_close()
        return super().closeEvent(event)

def start_application():
    """ start QApplication and show dialog """
    app = QtWidgets.QApplication([])
    dialog = AnanasDialog()
    dialog.show()
    app.exec()

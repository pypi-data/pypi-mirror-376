""" base model """


class ModelBase():
    """ conan model base class """

    reset_in_progress = 0
    """
    counter how many times try_begin_reset_model has been called,
    only call endResetModel in try_end_reset_model if the count is 1
    """

    def try_begin_reset_model(self):
        """ only call beginResetModel if not already in progress """
        if self.reset_in_progress < 1:
            # pylint: disable-next=no-member
            self.beginResetModel()

        self.reset_in_progress += 1

    def try_end_reset_model(self):
        """ call endResetModel if only one reset_in_progress remainig """
        if self.reset_in_progress == 1:
            # pylint: disable-next=no-member
            self.endResetModel()

        self.reset_in_progress -= 1

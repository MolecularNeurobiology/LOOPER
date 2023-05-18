# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 23:54:57 2023

@author: wardc
"""
import ccac
import ccac_controller
import ccac_model

import sys
from PyQt5 import QtWidgets

__version__ = "1.0.1"


# %% define main
def main():
    # create the application

    app = QtWidgets.QApplication(sys.argv)

    MainWindow = QtWidgets.QMainWindow()

    ui = ccac_controller.ccac_main_window(MainWindow, ccac_model.ccac_model)
    ui.model.version_info = {
        "ccac launcher": __version__,
        "ccac model": ccac_model.__version__,
        "ccac gui": ccac_controller.__version__,
        "ccac functions": ccac.__version__,
    }

    # show the gui
    MainWindow.show()

    sys.exit(app.exec_())


# %% run main
if __name__ == "__main__":
    main()

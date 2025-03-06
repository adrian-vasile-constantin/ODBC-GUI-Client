import sys
from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QGroupBox,
        QStyleOptionGroupBox,
        QListWidget,
        QLabel,
        QLineEdit,
        QGridLayout)
import traits
import pyodbc

MAIN_WINDOW_WIDTH = 700                 # Windows 10 system requirements include monitor resolution of 800x600
MAIN_WINDOW_HEIGHT = 525                # Allow 40 - 70 pixels for Windows taskbar

def resizeMainWindow(mainWindow):
    wndSize = mainWindow.size()

    if wndSize.width() < MAIN_WINDOW_WIDTH:
        wndSize.setWidth(MAIN_WINDOW_WIDTH)

    if wndSize.height() < MAIN_WINDOW_HEIGHT:
        wndSize.setHeight(MAIN_WINDOW_HEIGHT)

    mainWindow.resize(wndSize)

def main(argv):
    mainApp = QApplication(argv)
    mainWindow = QMainWindow()
    mainWindow.setCentralWidget(QWidget(mainWindow))

    driverList = QListWidget(mainWindow.centralWidget())
    dsnList = QListWidget(mainWindow.centralWidget())

    resizeMainWindow(mainWindow)

    driverList.addItems(pyodbc.drivers())
    dsnList.addItems(val for key, val in enumerate(pyodbc.dataSources()))

    grid = QGridLayout(mainWindow.centralWidget())

    manualConnectionFrame = QGroupBox(mainApp.tr('Manual connection string'), mainWindow.centralWidget())
    # manualConnectionFrame.setStyleSheet('QGroupBox { border: 1px solid light-grey; } QGroupBox::title { left: 1ex, top: -0.5ex; }')

    subgrid = QGridLayout(manualConnectionFrame)

    subgrid.addWidget(QLabel(mainApp.tr('New Name:'), manualConnectionFrame), 0, 0)
    subgrid.addWidget(QLineEdit(manualConnectionFrame), 1, 0)
    subgrid.setColumnStretch(0, 1)

    subgrid.addWidget(QLabel(mainApp.tr('Connection String:'), manualConnectionFrame), 0, 2)
    subgrid.addWidget(QLineEdit(manualConnectionFrame), 1, 2)
    subgrid.setColumnStretch(2, 5)

    grid.addWidget(manualConnectionFrame, 0, 0, 1, 3)

    grid.addWidget(QLabel(mainApp.tr('ODBC Drivers:'), mainWindow.centralWidget()), 1, 0)
    grid.addWidget(driverList, 2, 0)

    grid.addWidget(QLabel(mainApp.tr('Data Sources:'), mainWindow.centralWidget()), 1, 2)
    grid.addWidget(dsnList, 2, 2)

    grid.setRowStretch(2, 1)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(2, 1)

    mainWindow.show()
    sys.exit(mainApp.exec())

if __name__ == "__main__":
    main(sys.argv)

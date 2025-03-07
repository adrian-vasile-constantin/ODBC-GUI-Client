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
        QPushButton,
        QGridLayout)
import traits
import pyodbc
import keyring

MAIN_WINDOW_WIDTH = 700                 # Windows 10 system requirements include monitor resolution of 800x600
MAIN_WINDOW_HEIGHT = 525                # Allow 40 - 70 pixels for Windows taskbar

def resizeMainWindow(mainWindow):
    wndSize = mainWindow.size()

    if wndSize.width() < MAIN_WINDOW_WIDTH:
        wndSize.setWidth(MAIN_WINDOW_WIDTH)

    if wndSize.height() < MAIN_WINDOW_HEIGHT:
        wndSize.setHeight(MAIN_WINDOW_HEIGHT)

    mainWindow.resize(wndSize)

class MainPanel(QWidget):
    def __init__(self, parentWidget = None):
        super().__init__(parentWidget)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape and not ev.modifiers():
            self.parent().close()

        super().keyPressEvent(ev)

def main(argv):
    mainApp = QApplication(argv)
    mainWindow = QMainWindow()
    mainWindow.setCentralWidget(MainPanel(mainWindow))

    driverList = QListWidget(mainWindow.centralWidget())
    dsnList = QListWidget(mainWindow.centralWidget())

    resizeMainWindow(mainWindow)

    driverList.addItems(pyodbc.drivers())
    dsnList.addItems(val for key, val in enumerate(pyodbc.dataSources()))

    grid = QGridLayout(mainWindow.centralWidget())

    manualConnectionFrame = QGroupBox(mainApp.tr('Manual connection string'), mainWindow.centralWidget())
    # manualConnectionFrame.setStyleSheet('QGroupBox { border: 1px solid light-grey; } QGroupBox::title { left: 1ex, top: -0.5ex; }')

    subgrid = QGridLayout(manualConnectionFrame)

    subgrid.addWidget(QLabel(mainApp.tr('New name:'), manualConnectionFrame), 0, 0)
    subgrid.addWidget(QLineEdit(manualConnectionFrame), 1, 0)
    subgrid.setColumnStretch(0, 1)

    subgrid.addWidget(QLabel(mainApp.tr('Connection string:'), manualConnectionFrame), 0, 2)
    subgrid.addWidget(QLineEdit(manualConnectionFrame), 1, 2)
    subgrid.setColumnStretch(2, 5)

    grid.addWidget(manualConnectionFrame, 0, 0, 1, 3)

    subgrid = QGridLayout()
    subgrid.addWidget(QLabel(mainApp.tr('Username:'), mainWindow.centralWidget()), 0, 0)
    subgrid.addWidget(QLineEdit(mainWindow.centralWidget()), 1, 0)

    subgrid.addWidget(QLabel(mainApp.tr('Password:'), mainWindow.centralWidget()), 0, 2)
    subgrid.addWidget(QLineEdit(mainWindow.centralWidget()), 1, 2)

    connectButton = QPushButton(mainApp.tr("Connect"), mainWindow.centralWidget())
    connectButton.default = True
    quitButton = QPushButton(mainApp.tr("Quit"), mainWindow.centralWidget())

    quitButton.pressed.connect(lambda: mainWindow.close())

    subgrid.addWidget(connectButton, 1, 4)
    subgrid.addWidget(quitButton, 1, 6)
    subgrid.setColumnStretch(0, 1)
    subgrid.setColumnStretch(2, 1)
    subgrid.setColumnStretch(3, 2)

    grid.addLayout(subgrid, 1, 0, 1, 3)

    grid.addWidget(QLabel(mainApp.tr('ODBC Drivers:'), mainWindow.centralWidget()), 2, 0)
    grid.addWidget(driverList, 3, 0)

    grid.addWidget(QLabel(mainApp.tr('Data Sources:'), mainWindow.centralWidget()), 2, 2)
    grid.addWidget(dsnList, 3, 2)

    grid.setRowStretch(3, 1)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(2, 1)

    mainWindow.show()
    sys.exit(mainApp.exec())

if __name__ == "__main__":
    main(sys.argv)

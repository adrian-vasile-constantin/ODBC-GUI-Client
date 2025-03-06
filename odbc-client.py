import sys
from PySide6 import QtCore, QtGui, QtQuick
import traits
import pyodbc

def main(argv):
    for ds in pyodbc.dataSources():
        print("Data Source: " + ds)

    print("")

    for drv in pyodbc.drivers():
        print("Driver: " + drv)

    mainApp = QtGui.QGuiApplication(argv)
    mainWindow = QtQuick.QQuickView()

    mainWindow.show()
    sys.exit(mainApp.exec())

if __name__ == "__main__":
    main(sys.argv)

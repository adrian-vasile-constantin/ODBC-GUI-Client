import sys, ctypes
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
        QCheckBox,
        QPushButton,
        QGridLayout,
        QMessageBox)
import traits
import pyodbc
import keyring

from src.ODBC import ODBC
from src.ODBCInst import ODBCInst
from src.DatabaseView import DatabaseView

def readDataSourceName(connectionString):
    for prop in connectionString.split(';'):
        [ key, val ] = prop.split('=', 1)

        if key.lstrip().lower() == 'dsn':
            return val.lstrip()

    return None

def splitConnectionString(connectionString):
    properties = [ ]
    dsn = None
    dsnProp = None

    for prop in connectionString.split(';'):
        if prop.lstrip():
            [ key, val ]= prop.split('=', 1)

            if key.lstrip().lower() == 'dsn':
                dsn = val.lstrip()
            else:
                if key.lstrip().lower() == 'pwd' or key.lstrip().lower() == 'password':
                    pass
                else:
                    properties.append(key.lstrip() + '=' + val.lstrip())

    return dsn, ';'.join(properties)

def updateDataSource(mainWindow, dataSourceName, connectionString, username, password, credentialsCheckbox):
    if dataSourceName and connectionString:
        DriverName = None
        connection = { }

        for prop in connectionString.split(';'):
            [ key, val ] = prop.split('=', 1)

            if key.lstrip().lower() == 'driver':
                DriverName = val
            else:
                connection[key.lstrip()] = val.lstrip()

        if DriverName is not None:
            connectionString = ''

            if username:
                connection['UID'] = username

            if password:
                connection['PWD'] = password

            for key, val in connection.items():
                connectionString += key + '=' + val + ';'

            connectionString = 'DSN=' + dataSourceName + ';' + connectionString
            connectionString = connectionString.rstrip(';')

            addDsnSuccess = ODBCInst.SQLConfigDataSource(int(mainWindow.effectiveWinId()), ODBCInst.ODBC_ADD_DSN, DriverName, connectionString.replace(';', '\000') + '\000\000')

            if not addDsnSuccess:
                QMessageBox.warning(
                        mainWindow,
                        mainWindow.tr('ODBC Client'),
                        mainWindow.tr('Unable to add new data source {} with driver {}\nTry using the system ODBC Data Source Administrator instead (Manage DSNs button)').format(dataSourceName, DriverName),
                        QMessageBox.Ok)

            if credentialsCheckbox:
                keyring.set_password('odbc:' + dataSourceName, username, password)

dbViews = [ ]
autoLoadCredentials = True

def closeDbView(databaseView):
    global dbViews

    dbViews.remove(databaseView)

def newConnection(mainWindow, dataSourceName, connectionString, username, password, credentialsCheckbox):
    dataSourceName = dataSourceName.text()
    connectionString = connectionString.text()
    username = username.text()
    password = password.text()
    credentialsCheckbox = credentialsCheckbox.isChecked()

    if dataSourceName:
        updateDataSource(mainWindow, dataSourceName, connectionString, username, password, credentialsCheckbox)

    if connectionString:
        kwArgs = { }

        if username:
            kwArgs['UID'] = username

        if password:
            kwArgs['PWD'] = password

        connection = pyodbc.connect(connectionString, autocommit=True, **kwArgs)

        global autoLoadCredentials
        global dbViews

        if not dataSourceName and not autoLoadCredentials and (username or password) and credentialsCheckbox:
            dataSourceName = readDataSourceName(connectionString)

            if dataSourceName:
                keyring.set_password('odbc:' + dataSourceName, username, password)

        dsn, extraConnectionString = splitConnectionString(connectionString)

        dbViews.append(DatabaseView(connection, dsn, extraConnectionString))
        dbViews[-1].closeView.connect(lambda databaseView: closeDbView(databaseView))

def replaceDriverAndDsn(connectionString, newKey, newVal):
    props = connectionString.text().split(';')
    connection = [ ]

    for propStr in props:
        if propStr.strip():
            [ key, val ] = propStr.split('=', 1)

            if not key.lstrip().lower() == 'driver' and not key.lstrip().lower() == 'dsn':
                connection.append([ key, val ])

    connection.insert(0, [ newKey, newVal ])

    newString = ''

    for key, val in connection:
        if val is None:
            newString += key + ';'
        else:
            newString += key + '=' + val + ';'

    newString = newString.rstrip(';')

    if not newString == connectionString.text():
        connectionString.setText(newString)

def removeDriverOrDsn(connectionString, oldKey, oldVal):
    props = connectionString.text().split(';')
    connection = [ ]

    for propStr in props:
        if propStr.strip():
            [ key, val ] = propStr.split('=', 1)

            if not key.lstrip().lower() == oldKey.lower() or not val.lstrip().lower() == oldVal.lower():
                connection.append([ key, val ])

    newString = ''

    for key, val in connection:
        if val is None:
            newString += key + ';'
        else:
            newString += key + '=' + val + ';'

    newString = newString.rstrip(';')

    if not newString == connectionString.text():
        connectionString.setText(newString)

def checkEnableDisableSourceList(dataSourceName, dsnList):
    if dataSourceName.text():
        if dsnList.isEnabled():
            dsnList.setEnabled(False)
            dsnList.setCurrentRow(-1)
    else:
        if not dsnList.isEnabled():
            dsnList.setEnabled(True)

def checkAutoLoadCredentials(usernameEdit, passwordEdit):
    global autoLoadCredentials

    if autoLoadCredentials:
        if usernameEdit.text() or passwordEdit.text():
            autoLoadCredentials = False
    else:
        if not usernameEdit.text() and not passwordEdit.text():
            autoLoadCredentials = True

def loadCredentials(dsnList, usernameEdit, passwordEdit):
    global autoLoadCredentials

    clearLocalCredentials = True

    if autoLoadCredentials and dsnList.isEnabled():
        if dsnList.selectedItems():
            credential = keyring.get_credential('odbc:' + dsnList.currentItem().text(), None)

            if credential:
                usernameEdit.setText(credential.username)
                passwordEdit.setText(credential.password)
                clearLocalCredentials = False

        if clearLocalCredentials:
            if usernameEdit.text():
                usernameEdit.setText('')

            if passwordEdit.text():
                passwordEdit.setText('')

def fillDsnAndCredentials(connectionString, driverList, dsnList, usernameEdit, passwordEdit, removeButton, configButton):
    if dsnList.selectedItems():
        replaceDriverAndDsn(connectionString, 'DSN', dsnList.currentItem().text())
        driverList.setCurrentRow(-1)

        if not removeButton.isEnabled():
            removeButton.setEnabled(True)

        if not configButton.isEnabled():
            configButton.setEnabled(True)
    else:
        if removeButton.isEnabled():
            removeButton.setEnabled(False)

        if configButton.isEnabled():
            configButton.setEnabled(False)

        if dsnList.currentItem():
            removeDriverOrDsn(connectionString, 'DSN', dsnList.currentItem().text())

    loadCredentials(dsnList, usernameEdit, passwordEdit)

def fillDriverName(connectionString, driverList, dsnList):
    if driverList.selectedItems():
        replaceDriverAndDsn(connectionString, 'Driver', driverList.currentItem().text())
        dsnList.setCurrentRow(-1)
    else:
        if driverList.currentItem():
            removeDriverOrDsn(connectionString, 'Driver', driverList.currentItem().text())

def updateListWidget(listWidget, newItemList):
    modified = not listWidget.count() == len(newItemList)

    if not modified:
        for row in range(listWidget.count()):
            if not listWidget.item(row).text() == newItemList[row]:
                modified = True
                break

    if modified:
        listWidget.clear()
        listWidget.addItems(newItemList)

def odbcAdministrator(mainWindow, driverList, dsnList):

    if not ODBCInst.SQLManageDataSources(int(mainWindow.effectiveWinId())):
        QMessageBox.warning(mainWindow, mainWindow.tr('ODBC Client'), mainWindow.tr('Unable to run ODBC Data Source Administrator'), QMessageBox.Ok)

    updateListWidget(driverList, pyodbc.drivers())
    updateListWidget(dsnList, [ val for key, val in enumerate(pyodbc.dataSources()) ])

def removeDsn(mainWindow, dsnList):
    dataSourceName = dsnList.currentItem().text()

    if QMessageBox.warning(mainWindow, mainWindow.tr('ODBC Client'), mainWindow.tr('Delete data source {} ?').format(dsnList.currentItem().text()), QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
        driverDescription = pyodbc.dataSources()[dataSourceName]

        if driverDescription:
            result = ODBCInst.SQLConfigDataSource(int(mainWindow.effectiveWinId()), ODBCInst.ODBC_REMOVE_DSN, driverDescription, 'DSN=' + dataSourceName)

            if not result:
                QMessageBox.warning(mainWindow, mainWindow.tr('ODBC Client'), mainWindow.tr('Unable to remove data source.\nTry the system ODBC Data Source Administrator (Manage DSNs ... button)'), QMessageBox.Ok)

        newDataSourceList = [ val for key, val in enumerate(pyodbc.dataSources()) ]

        updateListWidget(dsnList, newDataSourceList)

        if not dataSourceName in newDataSourceList:
            credential = keyring.get_credential('odbc:' + dataSourceName, None)

            if credential:
                keyring.delete_password('odbc:' + dataSourceName, credential.username)

def configureDsn(mainWindow, dsnList):
    dataSourceName = dsnList.currentItem().text()

    driverDescription = pyodbc.dataSources()[dataSourceName]

    if driverDescription:
        result = ODBCInst.SQLConfigDataSource(int(mainWindow.effectiveWinId()), ODBCInst.ODBC_CONFIG_DSN, driverDescription, 'DSN=' + dataSourceName)

    updateListWidget(dsnList, [ val for key, val in enumerate(pyodbc.dataSources()) ])


MAIN_WINDOW_WIDTH = 700                 # Windows 10 system requirements include monitor resolution of 800x600
MAIN_WINDOW_HEIGHT = 550                # Allow 50 pixels for Windows taskbar

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

def enumerateDataSourceNames(hEnv, enumerationType, targetDict):
    dsn_names = [ ]
    dsn_drivers = [ ]

    dsn_name_len = ODBC.SQLSMALLINT()
    driver_name_len = ODBC.SQLSMALLINT()

    sqlResult = ODBC.SQLDataSources(hEnv, enumerationType, None, 0, ctypes.byref(dsn_name_len), None, 0, ctypes.byref(driver_name_len))

    while sqlResult == ODBC.SQL_SUCCESS or sqlResult == ODBC.SQL_SUCCESS_WITH_INFO:
        dsn_names.append(ctypes.create_unicode_buffer(dsn_name_len.value + 1))
        dsn_drivers.append(ctypes.create_unicode_buffer(driver_name_len.value + 1))
        sqlResult = ODBC.SQLDataSources(hEnv, ODBC.SQL_FETCH_NEXT, None, 0, ctypes.byref(dsn_name_len), None, 0, ctypes.byref(driver_name_len))

    if sqlResult != ODBC.SQL_NO_DATA:
        print('Error {} enumerating Data Source Names'.format(sqlResult), file = sys.stderr)
    else:
        index = 0
        sqlResult = ODBC.SQLDataSources(hEnv, enumerationType, dsn_names[index] , ctypes.sizeof(dsn_names[index]), ctypes.byref(dsn_name_len), dsn_drivers[index], ctypes.sizeof(dsn_drivers[index]), ctypes.byref(driver_name_len))

        while sqlResult == ODBC.SQL_SUCCESS or sqlResult == ODBC.SQL_SUCCESS_WITH_INFO:
            targetDict[dsn_names[index].value[:dsn_name_len.value]] = dsn_drivers[index].value[:driver_name_len.value]
            index = index + 1

            if index < len(dsn_names):
                sqlResult = ODBC.SQLDataSources(hEnv, ODBC.SQL_FETCH_NEXT, dsn_names[index] , ctypes.sizeof(dsn_names[index]), ctypes.byref(dsn_name_len), dsn_drivers[index], ctypes.sizeof(dsn_drivers[index]), ctypes.byref(driver_name_len))
            else:
                break

def dataSourceNames():
    hEnv = ODBC.SQLHANDLE()

    sqlReturn = ODBC.SQLAllocHandle(ODBC.SQL_HANDLE_ENV, ODBC.SQL_NULL_HANDLE, ctypes.byref(hEnv))

    if sqlReturn != ODBC.SQL_SUCCESS and sqlReturn != ODBC.SQL_SUCCESS_WITH_INFO:
        print('Error allocating ODBC environment handle\n', file = sys.stderr)
    else:
        try:
            sqlReturn = ODBC.SQLSetEnvAttr(hEnv, ODBC.SQL_ATTR_ODBC_VERSION, ctypes.cast(ODBC.SQL_OV_ODBC3_80, ODBC.SQLPOINTER), 0)

            if sqlReturn != ODBC.SQL_SUCCESS and sqlReturn != ODBC.SQL_SUCCESS_WITH_INFO:
                print('Error {} setting ODBC environment attributes\n'.format(sqlReturn), file = sys.stderr)
            else:
                result = { 'user': { }, 'system': { } }

                enumerateDataSourceNames(hEnv, ODBC.SQL_FETCH_FIRST_USER, result['user'])

                for name, driver in result['user'].items():
                    print('User DSN: {}, Driver: {}'.format(name, driver))

                enumerateDataSourceNames(hEnv, ODBC.SQL_FETCH_FIRST_SYSTEM, result['system'])

                for name, driver in result['system'].items():
                    print('System DSN: {}, Driver: {}'.format(name, driver))

                return result
        finally:
            sqlReturn = ODBC.SQLFreeHandle(ODBC.SQL_HANDLE_ENV, hEnv)

            if sqlReturn != ODBC.SQL_SUCCESS and sqlReturn != ODBC.SQL_SUCCESS_WITH_INFO:
                print('Error deallocating ODBC environment handle\n', file = sys.stderr)

def main(argv):
    mainApp = QApplication(argv)
    mainApp.setOrganizationName('')
    mainApp.setOrganizationDomain('org.free-and-open-source-software')
    mainApp.setApplicationName('ODBC Client')
    mainApp.setApplicationDisplayName(mainApp.tr('ODBC Client'))

    mainWindow = QMainWindow()
    mainWindow.setCentralWidget(MainPanel(mainWindow))
    mainWindow.setWindowTitle(mainWindow.tr('ODBC Client'))

    driverList = QListWidget(mainWindow.centralWidget())
    dsnList = QListWidget(mainWindow.centralWidget())

    resizeMainWindow(mainWindow)

    pyodbc.pooling = False

    driverList.addItems(pyodbc.drivers())
    dsnList.addItems(val for key, val in enumerate(pyodbc.dataSources()))

    dataSourceNames()

    grid = QGridLayout(mainWindow.centralWidget())

    manualConnectionFrame = QGroupBox(mainApp.tr('Manual connection string'), mainWindow.centralWidget())
    # manualConnectionFrame.setStyleSheet('QGroupBox { border: 1px solid light-grey; } QGroupBox::title { left: 1ex, top: -0.5ex; }')

    subgrid = QGridLayout(manualConnectionFrame)

    dataSourceName = QLineEdit(manualConnectionFrame)
    subgrid.addWidget(QLabel(mainApp.tr('Add new DSN:'), manualConnectionFrame), 0, 0)
    subgrid.addWidget(dataSourceName, 1, 0)
    subgrid.setColumnStretch(0, 1)

    connectionString = QLineEdit(manualConnectionFrame)
    subgrid.addWidget(QLabel(mainApp.tr('Connection string:'), manualConnectionFrame), 0, 2)
    subgrid.addWidget(connectionString, 1, 2)
    subgrid.setColumnStretch(2, 5)

    grid.addWidget(manualConnectionFrame, 0, 0, 1, 3)

    subgrid = QGridLayout()
    usernameEdit = QLineEdit(mainWindow.centralWidget())
    subgrid.addWidget(QLabel(mainApp.tr('Username:'), mainWindow.centralWidget()), 0, 0)
    subgrid.addWidget(usernameEdit, 1, 0)

    passwordEdit = QLineEdit(mainWindow.centralWidget())
    passwordEdit.setEchoMode(QLineEdit.Password)
    subgrid.addWidget(QLabel(mainApp.tr('Password:'), mainWindow.centralWidget()), 0, 2)
    subgrid.addWidget(passwordEdit, 1, 2)

    connectButton = QPushButton(mainApp.tr('Connect'), mainWindow.centralWidget())
    connectButton.default = True
    quitButton = QPushButton(mainApp.tr('Quit'), mainWindow.centralWidget())

    subgrid.addWidget(connectButton, 1, 4)
    subgrid.addWidget(quitButton, 1, 6)
    subgrid.setColumnStretch(0, 30)
    subgrid.setColumnStretch(2, 30)
    subgrid.setColumnStretch(3, 34)

    credentialsCheckbox = QCheckBox('Save credentials in keyring / credential store', mainWindow.centralWidget())
    credentialsCheckbox.setChecked(True)
    subgrid.addWidget(credentialsCheckbox, 2, 0, 1, 3)
    subgrid.addWidget(QLabel('', mainWindow.centralWidget()), 3, 0)

    quitButton.pressed.connect(lambda: mainWindow.close())
    connectButton.pressed.connect(lambda: newConnection(mainWindow, dataSourceName, connectionString, usernameEdit, passwordEdit, credentialsCheckbox))

    grid.addLayout(subgrid, 1, 0, 1, 3)

    grid.addWidget(QLabel(mainApp.tr('Installed ODBC Drivers:'), mainWindow.centralWidget()), 2, 0)
    grid.addWidget(driverList, 3, 0, 2, 1)

    grid.addWidget(QLabel(mainApp.tr('Data Source Names (DSNs):'), mainWindow.centralWidget()), 2, 2)
    grid.addWidget(dsnList, 3, 2)

    subgrid = QGridLayout()
    dsnManageButton = QPushButton(mainApp.tr('Manage DSNs ...'), mainWindow.centralWidget())
    subgrid.addWidget(dsnManageButton, 0, 2)
    dsnConfigButton = QPushButton(mainApp.tr('Configure DSN ...'), mainWindow.centralWidget())
    dsnConfigButton.setEnabled(False)
    subgrid.addWidget(dsnConfigButton, 0, 4)
    dsnRemoveButton = QPushButton(mainApp.tr('Remove DSN'), mainWindow.centralWidget())
    dsnRemoveButton.setEnabled(False)
    subgrid.addWidget(dsnRemoveButton, 0, 6)
    subgrid.setColumnStretch(0, 1)

    grid.setRowStretch(3, 1)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(2, 1)

    grid.addLayout(subgrid, 4, 2)

    dataSourceName.editingFinished.connect(lambda: checkEnableDisableSourceList(dataSourceName, dsnList))
    usernameEdit.editingFinished.connect(lambda: checkAutoLoadCredentials(usernameEdit, passwordEdit))
    passwordEdit.editingFinished.connect(lambda: checkAutoLoadCredentials(usernameEdit, passwordEdit))

    dsnList.itemSelectionChanged.connect(lambda: fillDsnAndCredentials(connectionString, driverList, dsnList, usernameEdit, passwordEdit, dsnRemoveButton, dsnConfigButton))
    driverList.itemSelectionChanged.connect(lambda: fillDriverName(connectionString, driverList, dsnList))

    dsnManageButton.clicked.connect(lambda: odbcAdministrator(mainWindow, driverList, dsnList))
    dsnRemoveButton.clicked.connect(lambda: removeDsn(mainWindow, dsnList))
    dsnConfigButton.clicked.connect(lambda: configureDsn(mainWindow, dsnList))

    mainWindow.show()
    sys.exit(mainApp.exec())

if __name__ == "__main__":
    main(sys.argv)

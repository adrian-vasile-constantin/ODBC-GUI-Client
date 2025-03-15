from crc import Calculator, Crc64
import pyodbc

from PySide6.QtCore import Qt, QObject, Signal, QSettings, QStandardPaths, QDir, QByteArray
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
        QWidget,
        QToolButton,
        QTreeWidget,
        QTreeWidgetItem,
        QTextEdit,
        QTabBar,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QAbstractItemView,
        QTextEdit,
        QSplitter,
        QSplitterHandle,
        QMainWindow)

class DbViewMainWindow(QMainWindow):
    def __init__(self, parentObj):
        super().__init__()
        self.parentObj = parentObj

    def closeEvent(self, ev):
        self.parentObj.closeView.emit(self.parentObj)
        ev.accept()

class SQLEditorWidget(QTextEdit):
    executeStatement = None       # signal to execute current statement
    executeScript = None

    def __init__(self, parent = None):
        super().__init__(parent)
        self.filename = ''

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Enter or ev.key() == Qt.Key_Return:
            if ev.modifiers() == Qt.ControlModifier:
                self.executeStatement.emit(self, self.textCursor().selectedText())
                self.textCursor().setPosition(self.textCursor().selectionEnd())     # un-select query text
                ev.accept()
            else:
                if ev.modifiers() == Qt.ControlModifier | Qt.AltModifier:
                    self.executeScript.emit(self, self.toPlainText())
                    ev.accept()

        super().keyPressEvent(ev)

SQLEditorWidget.executeStatement = Signal(SQLEditorWidget, str)
SQLEditorWidget.executeScript = Signal(SQLEditorWidget, str)

class DatabaseView(QObject):
    MAIN_WINDOW_WIDTH = 700                 # Windows 10 system requirements include monitor resolution of 800x600
    MAIN_WINDOW_HEIGHT = 550                # Allow 50 pixels for Windows taskbar

    closeView = None                        # Signal(DatabaseView)

    def __init__(self, connection, dataSourceName, extraConnectionString):
        super().__init__()

        self.mainWindow = DbViewMainWindow(self)
        self.mainSplitter = QSplitter(Qt.Horizontal, self.mainWindow)
        self.resultSplitter = QSplitter(Qt.Vertical, self.mainSplitter)
        self.mainWindow.setCentralWidget(self.mainSplitter)
        self.dbTree = QTreeWidget(self.mainSplitter)
        self.dbTree.setAlternatingRowColors(True)
        self.dbTree.setHeaderHidden(True)
        self.sqlScripts = SQLEditorWidget(self.resultSplitter)
        self.sqlScripts.setWordWrapMode(QTextOption.NoWrap)
        self.sqlTab = QTabWidget(self.resultSplitter)
        self.resultTab = QTabWidget(self.resultSplitter)
        self.queryResult = QTableWidget(self.resultSplitter)
        self.queryResult.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sqlOutput = QTextEdit(self.resultTab)
        self.sqlOutput.setReadOnly(True)

        self.sqlTab.addTab(self.sqlScripts, self.mainWindow.tr('SQL', 'tab-title'))
        self.sqlTab.addTab(QWidget(), '')
        self.resultTab.addTab(self.sqlOutput, self.mainWindow.tr('Output', 'tab-title'))
        self.resultTab.addTab(self.queryResult, self.mainWindow.tr('Result', 'tab-title'))

        self.nb = QToolButton()
        self.nb.setText('+') # you could set an icon instead of text
        self.nb.setAutoRaise(True)
        # self.nb.clicked.connect(self.new_tab)
        self.sqlTab.tabBar().setTabButton(1, QTabBar.RightSide, self.nb)
        self.sqlTab.setTabsClosable(True)
        self.sqlTab.setUsesScrollButtons(True)
        self.resultSplitter.addWidget(self.sqlTab)
        self.resultSplitter.addWidget(self.resultTab)

        self.resultSplitter.setStretchFactor(0, 1)
        self.resultSplitter.setStretchFactor(1, 3)

        self.mainSplitter.addWidget(self.dbTree)
        self.mainSplitter.addWidget(self.resultSplitter)

        self.mainSplitter.setStretchFactor(0, 1)
        self.mainSplitter.setStretchFactor(1, 2)

        wndSize = self.mainWindow.size()

        if wndSize.width() < DatabaseView.MAIN_WINDOW_WIDTH:
            wndSize.setWidth(DatabaseView.MAIN_WINDOW_WIDTH)

        if wndSize.height() < DatabaseView.MAIN_WINDOW_HEIGHT:
            wndSize.setHeight(DatabaseView.MAIN_WINDOW_HEIGHT)

        self.mainWindow.resize(wndSize)

        readOnly = connection.getinfo(pyodbc.SQL_DATA_SOURCE_READ_ONLY)

        dbmsName = connection.getinfo(pyodbc.SQL_DBMS_NAME)
        dbmsVersion = connection.getinfo(pyodbc.SQL_DBMS_VER)

        if dataSourceName:
            if extraConnectionString:
                title = dataSourceName + ', ...'
            else:
                title = dataSourceName

            if readOnly:
                title += ' - ' + 'Read Only'
        else:
            dbName = connection.getinfo(pyodbc.SQL_DATABASE_NAME)

            if readOnly:
                title = dbName + ' - ' + 'Read Only'
            else:
                title = dbName

        title += ' - ' + dbmsName + ' ' + dbmsVersion

        self.mainWindow.setWindowTitle(title)

        self.extraConnectionString = extraConnectionString
        self.conn = connection
        self.populateDatabaseObjects()

        self.sqlScripts.setFocus()
        self.sqlScripts.executeStatement.connect(lambda editorWidget, queryStr: self.runQuery(queryStr, False, self.conn, self.sqlOutput, self.queryResult))
        self.sqlScripts.executeScript.connect(lambda editorWidget, queryStr: self.runQuery(queryStr, True, self.conn, self.sqlOutput, self.queryResult))

        self.loadSettings(dataSourceName, extraConnectionString)

        self.closeView.connect(lambda dbView: dbView.saveSettings())

        self.mainWindow.show()

    WIDGET_TYPE_STATIC_LABEL = 0
    WIDGET_TYPE_CATALOG = 1
    WIDGET_TYPE_SCHEMA = 2
    WIDGET_TYPE_TABLE_CATEGORY = 3
    WIDGET_TYPE_TABLE = 4
    WIDGET_TYPE_PROC = 5

    def getTypeNode(self, containerEntry, typeName):
        if not typeName in containerEntry['typeNodes']:
            containerEntry['typeNodes'][typeName] = QTreeWidgetItem(containerEntry['item'], [ typeName ], DatabaseView.WIDGET_TYPE_STATIC_LABEL);

        return containerEntry['typeNodes'][typeName]

    def getContainerNode(self, containerEntry, name, widgetType, dbTypeName = None):
        if not name:
            return containerEntry

        if not name in containerEntry['containers']:
            if dbTypeName:
                containerEntry['containers'][name] = { 'item': QTreeWidgetItem(self.getTypeNode(containerEntry, dbTypeName), [ name ], widgetType), 'containers': { }, 'typeNodes': { } }
            else:
                containerEntry['containers'][name] = { 'item': QTreeWidgetItem(containerEntry['item'], [ name ], widgetType), 'containers': { }, 'typeNodes': { } }

        return containerEntry['containers'][name]


    def addTableToDbTree(self, catalog, schema, typ, name, desc):
        catalogNode = self.getContainerNode(self.containerNodes, catalog, DatabaseView.WIDGET_TYPE_CATALOG, 'Catalog')
        schemaNode = self.getContainerNode(catalogNode, schema, DatabaseView.WIDGET_TYPE_SCHEMA, 'Schema')
        tableTypeNode = self.getContainerNode(schemaNode, typ.title(), DatabaseView.WIDGET_TYPE_TABLE_CATEGORY)

        QTreeWidgetItem(tableTypeNode['item'], [ name ], DatabaseView.WIDGET_TYPE_TABLE)

    def addProcToDbTree(self, row, listContainer):
        catalog, schema, name, input_params, output_params, num_result_sets, desc, typ = row[0], row[1], row[2].rstrip('()') + '()', row[3], row[4], row[5], row[6], row[7]
        catalogNode = self.getContainerNode(self.containerNodes, catalog, DatabaseView.WIDGET_TYPE_CATALOG, 'Catalog')
        schemaNode = self.getContainerNode(catalogNode, schema, DatabaseView.WIDGET_TYPE_SCHEMA, 'Schema')
        procNode = self.getContainerNode(schemaNode, 'Procedure', DatabaseView.WIDGET_TYPE_STATIC_LABEL)

        if not [ catalog, schema, name ] in listContainer:
            QTreeWidgetItem(procNode['item'], [ name ], DatabaseView.WIDGET_TYPE_PROC)
            listContainer.append([ catalog, schema, name ])

    def expandDbTree(self, containerEntry):
        itemList = [ containerEntry['item'] ]

        if containerEntry['typeNodes']:
            itemList.extend([ val for key, val in containerEntry['typeNodes'].items() ])

        for item in itemList:
            # do not expand system tables and views
            if item.childCount() <= 10 and item.type() == DatabaseView.WIDGET_TYPE_TABLE_CATEGORY and item.text(0) in [ 'System View', 'System Table', 'System' ]:
                break;

            # Expand all nodes with 10 children or less, and expand all 'Schema' and 'Catalog' nodes
            if item.childCount() <= 10 or (item.type() == DatabaseView.WIDGET_TYPE_STATIC_LABEL and item.text(0) in [ 'Catalog', 'Schema' ]):
                item.setExpanded(True)

            # Expand 'Table' nodes with 100 children or less
            if item.childCount() <= 100 and item.type() == DatabaseView.WIDGET_TYPE_TABLE_CATEGORY and item.text(0) == 'Table':
                item.setExpanded(True)

            if item.childCount() < 25 and item.type() == DatabaseView.WIDGET_TYPE_TABLE_CATEGORY and item.text(0) in [ 'Global Temporary', 'Local Temporary', 'Global Temporary Table', 'Local Temporary Table' ]:
                item.setExpanded(True)

        for name in containerEntry['containers']:
            self.expandDbTree(containerEntry['containers'][name])

    def populateDatabaseObjects(self):
        self.containerNodes = { 'item': self.dbTree.invisibleRootItem(), 'containers': { }, 'typeNodes': { } }

        for catalog, schema, name, typ, desc in self.conn.cursor().tables():
            self.addTableToDbTree(catalog, schema, typ, name, desc)

        listContainer = [ ]

        rows = self.conn.cursor().procedures()
        for row in rows:
            self.addProcToDbTree(row, listContainer)

        self.expandDbTree(self.containerNodes)

    def runQuery(self, queryStr, isFullScript, conn, outputWidget, resultWidget):
        print("Run query " + queryStr)

        if not isFullScript:
            cursor = conn.cursor()
            cursor.execute(queryStr)

            if cursor.messages:
                for [ msgType, msgLine ] in cursor.messages:
                    outputWidget.append(msgType + ' ' + msgLine)

            if cursor.description:
                resultWidget.setColumnCount(len(cursor.description))
                resultWidget.setHorizontalHeaderLabels([ col[0] for col in cursor.description ])

                rowNumber = 0
                columnRange = range(len(cursor.description))

                for row in cursor:
                    if resultWidget.rowCount() <= rowNumber:
                        resultWidget.insertRow(rowNumber)

                    for col in columnRange:
                        resultWidget.setItem(rowNumber, col, QTableWidgetItem(str(row[col])))

                    rowNumber = rowNumber + 1

                    if rowNumber >= 1000:
                        break

                resultWidget.setRowCount(rowNumber)

            if cursor.description:
                self.resultTab.setCurrentIndex(1)
            else:
                resultWidget.clear()
                resultWidget.setColumnCount(0)
                resultWidget.setRowCount(0)
                self.resultTab.setCurrentIndex(0)

    def loadSettings(self, dataSourceName, extraConnectionString):
        appDataPath = QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)

        if appDataPath:
            appDataPath = appDataPath[0];

            self.configBasename = ''

            if dataSourceName:
                self.configBasename += dataSourceName
            else:
                self.configBasename += 'conn'

            if extraConnectionString:
                self.configBasename += '-' + hex(Calculator(Crc64.CRC64).checksum(extraConnectionString.encode()))[2:].zfill(16)

            self.settings = QSettings(appDataPath + '/ODBC Client/' + self.configBasename + '.ini', QSettings.IniFormat)

            mainWindowGeometry = self.settings.value('DatabaseView/geometry', QByteArray())

            if mainWindowGeometry:
                self.mainWindow.restoreGeometry(mainWindowGeometry)

            mainWindowState = self.settings.value('DatabaseView/windowState', QByteArray())

            if mainWindowState:
                self.mainWindow.restoreState(mainWindowState)

    def saveSettings(self):
        if self.settings:
            self.settings.setValue('DatabaseView/geometry', self.mainWindow.saveGeometry())
            self.settings.setValue('DatabaseView/windowState', self.mainWindow.saveState())

DatabaseView.closeView = Signal(DatabaseView)

import os, re
from crc import Calculator, Crc64
import pyodbc

from PySide6.QtCore import (
        Qt,
        QStringConverter,
        QObject,
        Signal,
        QSettings,
        QStandardPaths,
        QDir,
        QByteArray,
        QFileInfo,
        QFile,
        QTextStream)
from PySide6.QtWidgets import QApplication
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
        self.sqlTab = QTabWidget(self.resultSplitter)
        self.sqlTab.setMovable(True)
        self.sqlTab.setTabsClosable(True)
        self.sqlTab.setUsesScrollButtons(True)
        self.resultTab = QTabWidget(self.resultSplitter)
        self.queryResult = QTableWidget(self.resultSplitter)
        self.queryResult.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sqlOutput = QTextEdit(self.resultTab)
        self.sqlOutput.setReadOnly(True)

        self.resultTab.addTab(self.sqlOutput, self.mainWindow.tr('Output', 'tab-title'))
        self.resultTab.addTab(self.queryResult, self.mainWindow.tr('Result', 'tab-title'))

        self.resultSplitter.addWidget(self.sqlTab)
        self.resultSplitter.addWidget(self.resultTab)

        self.resultSplitter.setStretchFactor(0, 1)
        self.resultSplitter.setStretchFactor(1, 3)

        self.mainSplitter.addWidget(self.dbTree)
        self.mainSplitter.addWidget(self.resultSplitter)

        self.mainSplitter.setStretchFactor(0, 1)
        self.mainSplitter.setStretchFactor(1, 2)

        readOnly = connection.getinfo(pyodbc.SQL_DATA_SOURCE_READ_ONLY)

        self.dbmsName = connection.getinfo(pyodbc.SQL_DBMS_NAME)
        self.dbmsVersion = connection.getinfo(pyodbc.SQL_DBMS_VER)

        versionMatch = re.match('^([0-9.]+)\\s+([^0-9]+)\\s+([0-9.]+)$', self.dbmsVersion)   # '11.00.0007 Mimer SQL 10.0.7'

        if self.dbmsName == 'Mimer SQL' and versionMatch and versionMatch.group(2) == self.dbmsName:
            self.dbmsVersion = versionMatch.group(3)

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

        title += ' - ' + self.dbmsName + ' ' + self.dbmsVersion

        self.mainWindow.setWindowTitle(title)

        self.extraConnectionString = extraConnectionString
        self.conn = connection
        self.populateDatabaseObjects()

        self.loadSettings(dataSourceName, extraConnectionString)
        self.loadSqlScripts()

        self.closeView.connect(lambda dbView: dbView.saveSettings())

        self.mainWindow.show()

        self.sqlTab.tabBar().addTab('')
        self.nb = QToolButton()
        self.nb.setText('+') # you could set an icon instead of text
        self.nb.setAutoRaise(True)
        # self.nb.clicked.connect(self.new_tab)
        lastTabIndex = self.sqlTab.tabBar().count() - 1
        self.sqlTab.tabBar().setTabButton(lastTabIndex, QTabBar.LeftSide,  None)
        self.sqlTab.tabBar().setTabButton(lastTabIndex, QTabBar.RightSide, None)
        self.sqlTab.tabBar().setTabButton(lastTabIndex, QTabBar.RightSide, self.nb)

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

        if self.dbmsName != 'DBASE':
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
                    if rowNumber > 1000:
                        self.resultTab.setTabText(1, self.mainWindow.tr('Result rows 1-1000', 'tab-title'))
                        break

                    if resultWidget.rowCount() <= rowNumber:
                        resultWidget.insertRow(rowNumber)

                    for col in columnRange:
                        resultWidget.setItem(rowNumber, col, QTableWidgetItem(str(row[col])))

                    rowNumber = rowNumber + 1

                resultWidget.setRowCount(rowNumber if rowNumber <= 1000 else 1000)

            if cursor.description:
                self.resultTab.setCurrentIndex(1)
            else:
                resultWidget.clear()
                resultWidget.setColumnCount(0)
                resultWidget.setRowCount(0)
                self.resultTab.setCurrentIndex(0)

    def loadSqlFile(self, fileName, sqlEditor):
        file = QFile(fileName)

        if file.open(QFile.ReadOnly | QFile.Text):
            fileStream = QTextStream(file)
            fileStream.setEncoding(QStringConverter.Utf8)
            fileStream.setAutoDetectUnicode(True)       # Check for Unicode BOM character (Byte Order Mark)

            while not fileStream.atEnd():
                line = fileStream.readLine()
                sqlEditor.append(line)

            if file.error() != QFile.NoError:
                print('Error loading script file {}: '.format(fileName) + file.errorString())

            fileStream = None
            file.close()
        else:
            print('Error loading script file {}: '.format(fileName) + file.errorString())

    def loadSqlScripts(self):
        self.sqlScriptFiles = self.settings.value('DatabaseView/sqlScriptFiles', defaultValue = [ ], type = list)

        pathPrefix = self.appDataPath + '/' + self.configBasename + '-SQLEditor'

        if self.sqlScriptFiles:
            self.sqlScripts = [ ]

            for [ index, sqlScript ] in enumerate(self.sqlScriptFiles):
                sqlScriptFile = QFileInfo(sqlScript).fileName()

                if sqlScriptFile.startswith(pathPrefix):
                    tabTitle = self.mainWindow.tr('SQL', 'tab-title')
                else:
                    tabTitle = QFileInfo(sqlScript).baseName()

                sqlEditor = SQLEditorWidget(self.sqlTab)
                self.sqlScripts.append(sqlEditor)

                self.loadSqlFile(sqlScript, sqlEditor)
        else:
            self.sqlScripts = [ SQLEditorWidget(self.sqlTab) ]
            self.sqlScripts[0].document().setModified(True)
            self.sqlScriptFiles = [ self.appDataPath + '/' + self.configBasename + '-SQLEditor1.sql' ]

        for [ index, script ] in enumerate(self.sqlScripts):
            script.setWordWrapMode(QTextOption.NoWrap)
            script.setAcceptRichText(False)
            self.sqlTab.insertTab(index, script, self.mainWindow.tr('SQL', 'tab-title'))

        currentScript = self.settings.value('DatabaseView/currentSql', defaultValue = 0, type = int)
        currentScript = int(currentScript)

        if currentScript < 0 or currentScript >= len(self.sqlScripts):
            currentScript = 0

        self.sqlTab.setCurrentIndex(currentScript)
        self.sqlScripts[currentScript].setFocus()

        for script in self.sqlScripts:
            script.executeStatement.connect(lambda editorWidget, queryStr: self.runQuery(queryStr, False, self.conn, self.sqlOutput, self.queryResult))
            script.executeScript.connect(lambda editorWidget, queryStr: self.runQuery(queryStr, True, self.conn, self.sqlOutput, self.queryResult))

    def loadSettings(self, dataSourceName, extraConnectionString):
        if 'APPDATA' in os.environ:
            self.appDataPath = os.environ['APPDATA'].replace('\\', '/') + '/' + QApplication.instance().applicationName()
        else:
            self.appDataPath = QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)

            if self.appDataPath:
                self.appDataPath = self.appDataPath[0];

        if self.appDataPath:
            self.configBasename = ''

            if dataSourceName:
                self.configBasename += dataSourceName
            else:
                self.configBasename += 'conn'

            if extraConnectionString:
                self.configBasename += '-' + hex(Calculator(Crc64.CRC64).checksum(extraConnectionString.encode()))[2:].zfill(16)

            self.settings = QSettings(self.appDataPath + '/' + self.configBasename + '.ini', QSettings.IniFormat)

            mainWindowGeometry = self.settings.value('DatabaseView/geometry', QByteArray())

            if mainWindowGeometry:
                self.mainWindow.restoreGeometry(mainWindowGeometry)
            else:
                wndSize = self.mainWindow.size()

                if wndSize.width() < DatabaseView.MAIN_WINDOW_WIDTH:
                    wndSize.setWidth(DatabaseView.MAIN_WINDOW_WIDTH)

                if wndSize.height() < DatabaseView.MAIN_WINDOW_HEIGHT:
                    wndSize.setHeight(DatabaseView.MAIN_WINDOW_HEIGHT)

                self.mainWindow.resize(wndSize)

            mainWindowState = self.settings.value('DatabaseView/windowState', QByteArray())

            if mainWindowState:
                self.mainWindow.restoreState(mainWindowState)

    def saveSqlFile(self, fileName, sqlEditor):
        file = QFile(fileName)

        if file.open(QFile.WriteOnly | QFile.Text):
            fileStream = QTextStream(file)
            fileStream.generateByteOrderMark()
            fileStream.setEncoding(QStringConverter.Utf8)
            fileStream << sqlEditor.toPlainText()
            fileStream = None

            if file.error()!= QFile.NoError:
                print('Error saving script file {}: '.format(fileName) + file.errorString())

            file.close()
        else:
            print('Error saving script file ' + fileName)

    def saveSqlScripts(self):
        for [ index, sqlEditor ] in enumerate(self.sqlScripts):
            if sqlEditor.document().isModified():
                self.saveSqlFile(self.sqlScriptFiles[index], sqlEditor)

        self.settings.setValue('DatabaseView/currentSql', self.sqlTab.currentIndex())
        self.settings.setValue('DatabaseView/sqlScriptFiles', self.sqlScriptFiles)

    def saveSettings(self):
        if self.settings:
            self.settings.setValue('DatabaseView/geometry', self.mainWindow.saveGeometry())
            self.settings.setValue('DatabaseView/windowState', self.mainWindow.saveState())
            self.saveSqlScripts()
            self.settings.sync()

DatabaseView.closeView = Signal(DatabaseView)

import pyodbc

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
        QWidget,
        QToolButton,
        QTreeWidget,
        QTreeWidgetItem,
        QTextEdit,
        QTabBar,
        QTabWidget,
        QTableWidget,
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

class DatabaseView(QObject):
    MAIN_WINDOW_WIDTH = 700                 # Windows 10 system requirements include monitor resolution of 800x600
    MAIN_WINDOW_HEIGHT = 550                # Allow 50 pixels for Windows taskbar

    closeView = None                        # Signal(DatabaseView)

    def __init__(self, connection, dataSourceName):
        super().__init__()

        self.mainWindow = DbViewMainWindow(self)
        self.mainSplitter = QSplitter(Qt.Horizontal, self.mainWindow)
        self.resultSplitter = QSplitter(Qt.Vertical, self.mainSplitter)
        self.mainWindow.setCentralWidget(self.mainSplitter)
        self.dbTree = QTreeWidget(self.mainSplitter)
        self.sqlScripts = QTextEdit(self.resultSplitter)
        self.sqlTab = QTabWidget(self.resultSplitter)
        self.sqlOutput = QTextEdit(self.sqlTab)
        self.sqlOutput.setReadOnly(True)

        self.sqlTab.addTab(self.sqlScripts, 'SQL')
        self.sqlTab.addTab(QWidget(), '')

        self.nb = QToolButton()
        self.nb.setText('+') # you could set an icon instead of text
        self.nb.setAutoRaise(True)
        # self.nb.clicked.connect(self.new_tab)
        self.sqlTab.tabBar().setTabButton(1, QTabBar.RightSide, self.nb)
        self.sqlTab.setTabsClosable(True)
        self.sqlTab.setUsesScrollButtons(True)
        self.resultSplitter.addWidget(self.sqlTab)
        self.resultSplitter.addWidget(self.sqlOutput)

        self.mainSplitter.addWidget(self.dbTree)
        self.mainSplitter.addWidget(self.resultSplitter)

        self.mainSplitter.setStretchFactor(0, 2)
        self.mainSplitter.setStretchFactor(1, 3)

        wndSize = self.mainWindow.size()

        if wndSize.width() < DatabaseView.MAIN_WINDOW_WIDTH:
            wndSize.setWidth(DatabaseView.MAIN_WINDOW_WIDTH)

        if wndSize.height() < DatabaseView.MAIN_WINDOW_HEIGHT:
            wndSize.setHeight(DatabaseView.MAIN_WINDOW_HEIGHT)

        self.mainWindow.resize(wndSize)

        if dataSourceName:
            self.mainWindow.setWindowTitle(dataSourceName)

        self.mainWindow.show()
        self.conn = connection
        self.populateDatabaseObjects()

    def getTypeNode(self, rootNode, containerType):
        if not containerType in self.typeNodes:
            self.typeNodes[containerType] = QTreeWidgetItem(rootNode, [ containerType ], 0);

        return self.typeNodes[containerType]

    def getContainerNode(self, rootNode, subcontainers, name, widgetType, containerType):
        if not name:
            return rootNode, subcontainers

        if not name in subcontainers:
            subcontainers[name] = { 'item': QTreeWidgetItem(self.getTypeNode(rootNode, containerType), [ name ], widgetType), 'containers': { } }

        return subcontainers[name]['item'], subcontainers[name]['containers']


    def addTableToDbTree(self, catalog, schema, typ, name, desc):
        treeRoot = self.dbTree.invisibleRootItem()
        catalogNode, schemas = self.getContainerNode(treeRoot, self.containerNodes, catalog, 1, 'Catalog')
        schemaNode, tableTypes = self.getContainerNode(catalogNode, schemas, schema, 2, 'Schema')
        typeNode, tables = self.getContainerNode(schemaNode, tableTypes, typ.title(), 3, 'Object type')

        QTreeWidgetItem(typeNode, [ name ], 4)

    def populateDatabaseObjects(self):
        self.containerNodes = { }
        self.typeNodes = { }

        for catalog, schema, name, typ, desc in self.conn.cursor().tables():
            self.addTableToDbTree(catalog, schema, typ, name, desc)

DatabaseView.closeView = Signal(DatabaseView)

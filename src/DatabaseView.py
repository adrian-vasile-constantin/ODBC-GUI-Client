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
        self.dbTree.setAlternatingRowColors(True)
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

DatabaseView.closeView = Signal(DatabaseView)

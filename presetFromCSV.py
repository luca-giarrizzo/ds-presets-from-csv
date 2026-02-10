from typing import Any

from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QToolBar, QDialog, QVBoxLayout
from PySide6.QtCore import Qt, QRect, QPoint

from sd.api.sdpackagemgr import SDPackageMgr
from sd.api.sdgraph import SDGraph

from .utilities import getLogger

# ---

class PresetsFromCSVToolbar(QToolBar):
    def __init__(self, parent, pkgMgr: SDPackageMgr, graph: SDGraph):
        super().__init__(parent=parent)
        self.setObjectName("PresetsFromCSVToolbar")
        self.__pkgMgr = pkgMgr
        self.graph = graph
        self.package = self.graph.getPackage()

        self.optionsDialog = PresetsFromCSVDialog()

        # Add actions or widgets to the toolbar as needed
        # For example, you can add a button to load presets from a CSV file
        optionsAction = QtGui.QAction("Options", self)
        optionsAction.triggered.connect(self.displayOptions)
        self.addAction(optionsAction)

        createPresetsAction = QtGui.QAction("Load Presets from CSV", self)
        createPresetsAction.triggered.connect(self.createPresetsFromCSV)
        self.addAction(createPresetsAction)

    def createPresetsFromCSV(self) -> None:
        # Implement the logic to create presets from a CSV file
        # This is just a placeholder function
        getLogger().info("Creating presets from CSV...")
        csvFilePaths: list[str] | None = self.findCSVResourcesInPackage()
        if not csvFilePaths:
            getLogger().info("No CSV resources found.")
            return
        elif len(csvFilePaths) > 1:
            getLogger().info(f"Multiple CSV resources found: {', '.join(csvFilePaths)}")
        else:
            getLogger().info(f"CSV resource found: {csvFilePaths[0]}")

    def findCSVResourcesInPackage(self) -> list[str] | None:
        resourcePaths: list[str] = []
        for resource in self.package.getChildrenResources(isRecursive=True):
            resourceFilepath: str = resource.getFilePath()
            if resourceFilepath.endswith(".csv"):
                resourcePaths.append(resourceFilepath)
        return resourcePaths if resourcePaths else None

    def getCSVResourceFilePath(self, resourcePkgPath) -> str | None:
        resource = self.package.findResourceFromUrl(resourcePkgPath)
        if not resource:
            getLogger().warning(f"Resource not found: {resourcePkgPath}")
            return None
        resourceFilePath: str = resource.getFilePath()
        if resourceFilePath.endswith(".csv"):
            return resourceFilePath
        else:
            getLogger().warning(f"Resource is not a CSV file: {resourcePkgPath}")
            return None

    def displayOptions(self):
        # zip() function pairs elements by position, sum() adds each pair
        # and map() applies sum() to all pairs for element-wise tuple addition.
        self.position = tuple(map(sum, zip(self.mapToGlobal(QPoint(0, 0)).toTuple(), (0, 20))))

        self.optionsDialog.setGeometry(QRect(*self.position, *self.optionsDialog.size))
        self.optionsDialog.show()


class PresetsFromCSVDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.csvOptions: dict[str, Any] = {
            "colorRow": "1",
            "colorSeparator": "-",
            "colorValueFormat": float,
            "hasAlpha": False,
            "hasHeader": True,
            "labelRow": "0",
            "csvDialect": "excel"
        }

        self.setWindowTitle("Presets from CSV")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

        self.mainLayout = QVBoxLayout()
        self.addCSVOptions()
        self.addColorSeparatorOption()
        self.addColorValueFormatOption()
        self.addHasAlphaOption()
        self.addHasHeaderOption()
        self.addLabelRowOption()
        self.addCSVDialectOption()

        self.setLayout(self.mainLayout)

        self.size = (200, 200)
        self.setFixedSize(*self.size)

    def addCSVOptions(self):
        colorRowLayout = QtWidgets.QHBoxLayout()
        colorRowLabel = QtWidgets.QLabel("Color row:")

        colorRow = OptionTextEdit(self, "colorRow", onlyNumbers=True)
        colorRow.setText(self.csvOptions["colorRow"])  # Initialise default value

        colorRowLayout.addWidget(colorRowLabel)
        colorRowLayout.addWidget(colorRow)

    def addColorSeparatorOption(self) -> None:
        colorSeparatorLayout = QtWidgets.QHBoxLayout()
        colorSeparatorLabel = QtWidgets.QLabel("Color separator:")

        colorSeparator = OptionTextEdit(self, "colorSeparator", onlyNumbers=False)
        colorSeparator.setText(self.csvOptions["colorSeparator"])  # Initialise default value

        colorSeparatorLayout.addWidget(colorSeparatorLabel)
        colorSeparatorLayout.addWidget(colorSeparator)
        self.mainLayout.addLayout(colorSeparatorLayout)

    def addColorValueFormatOption(self) -> None:
        colorValueFormatLayout = QtWidgets.QHBoxLayout()
        colorValueFormatLabel = QtWidgets.QLabel("Color value format:")
        colorValueFormat = QtWidgets.QComboBox()

        colorValueFormat.addItem("Float", userData=float)
        colorValueFormat.addItem("Integer", userData=int)

        colorValueFormat.currentIndexChanged.connect(
            lambda: self.updateOptions(key="colorValueFormat", value=colorValueFormat.itemData(colorValueFormat.currentIndex())))
        colorValueFormat.setCurrentIndex(colorValueFormat.findData(self.csvOptions["colorValueFormat"]))  # Initialise default value

        colorValueFormatLayout.addWidget(colorValueFormatLabel)
        colorValueFormatLayout.addWidget(colorValueFormat)
        self.mainLayout.addLayout(colorValueFormatLayout)

    def addHasAlphaOption(self) -> None:
        hasAlphaLayout = QtWidgets.QHBoxLayout()
        hasAlphaLabel = QtWidgets.QLabel("Has alpha:")

        hasAlpha = QtWidgets.QCheckBox()
        hasAlpha.toggled.connect(lambda: self.updateOptions("hasAlpha", hasAlpha.isChecked()))
        hasAlpha.setChecked(self.csvOptions["hasAlpha"])  # Initialise default value

        hasAlphaLayout.addWidget(hasAlphaLabel)
        hasAlphaLayout.addWidget(hasAlpha)
        self.mainLayout.addLayout(hasAlphaLayout)

    def addHasHeaderOption(self) -> None:
        hasHeaderLayout = QtWidgets.QHBoxLayout()
        hasHeaderLabel = QtWidgets.QLabel("Has header:")

        hasHeader = QtWidgets.QCheckBox()
        hasHeader.toggled.connect(lambda: self.updateOptions("hasHeader", hasHeader.isChecked()))
        hasHeader.setChecked(self.csvOptions["hasHeader"])  # Initialise default value

        hasHeaderLayout.addWidget(hasHeaderLabel)
        hasHeaderLayout.addWidget(hasHeader)
        self.mainLayout.addLayout(hasHeaderLayout)

    def addLabelRowOption(self) -> None:
        # TODO Make label row optional and generate label from color values if not provided
        labelRowLayout = QtWidgets.QHBoxLayout()
        labelRowLabel = QtWidgets.QLabel("Label row:")

        labelRow = OptionTextEdit(self, "labelRow", onlyNumbers=True)
        labelRow.setText(self.csvOptions["labelRow"])  # Initialise default value

        labelRowLayout.addWidget(labelRowLabel)
        labelRowLayout.addWidget(labelRow)
        self.mainLayout.addLayout(labelRowLayout)

    def addCSVDialectOption(self) -> None:
        csvDialectLayout = QtWidgets.QHBoxLayout()
        csvDialectLabel = QtWidgets.QLabel("CSV dialect:")
        csvDialect = QtWidgets.QComboBox()

        csvDialect.addItem("Excel", userData="excel")
        csvDialect.addItem("Excel Tab", userData="excel-tab")
        csvDialect.addItem("Unix", userData="unix")

        csvDialect.currentIndexChanged.connect(
            lambda: self.updateOptions(key="colorValueFormat", value=csvDialect.itemData(csvDialect.currentIndex())))
        csvDialect.setCurrentIndex(csvDialect.findData(self.csvOptions["csvDialect"]))  # Initialise default value

        csvDialectLayout.addWidget(csvDialectLabel)
        csvDialectLayout.addWidget(csvDialect)
        self.mainLayout.addLayout(csvDialectLayout)

    def updateOptions(self, key: str, value: Any) -> None:
        self.csvOptions[key] = value
        getLogger().info(f"Updated option {key}: {value}")


class OptionTextEdit(QtWidgets.QTextEdit):
    def __init__(
            self, presetDialog: PresetsFromCSVDialog, optionIdentifier: str, onlyNumbers: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.fontMetrics().height())  # Set height to fit a single line of text
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.optionIdentifier = optionIdentifier
        self.presetDialog = presetDialog
        self.onlyNumbers = onlyNumbers

    def focusOutEvent(self, e):
        # TODO Set option value to default if text is empty
        # TODO Add visual feedback for invalid input (e.g. red border) without losing focus
        self.presetDialog.updateOptions(self.optionIdentifier, self.toPlainText())
        super().focusOutEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Return or e.key() == Qt.Key.Key_Enter:
            self.clearFocus()  # Trigger focusOutEvent to save the option value
        elif e.key() == Qt.Key.Key_Backspace:
            self.clear()
        elif self.onlyNumbers == e.text().isdigit():
            self.setText(e.text())

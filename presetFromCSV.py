from typing import Any

from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QToolBar, QDialog, QVBoxLayout, QComboBox, QTextEdit, QCheckBox, QPushButton
from PySide6.QtCore import Qt, QRect, QPoint, QSize

from sd.api.sdbasetypes import ColorRGBA
from sd.api.sdpackagemgr import SDPackageMgr
from sd.api.sdgraph import SDGraph

from .utilities import getLogger, generatePresetsFromColors, extractColorsFromCSV, gatherGraphColorParameters

# ---

class PresetsFromCSVToolbar(QToolBar):

    CSV_OPTIONS_DEFAULTS: dict[str, Any] = {
        "csvDialect": "excel",
        "labelRow": "0",
        "colorRow": "1",
        "colorSeparator": "-",
        "colorValueFormat": int,
        "hasAlpha": False,
        "hasHeader": True
    }

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
        # TODO Manage presets generation when multiple CSV resources are found
        #   (e.g. generate presets from the first one, or display a list to choose from)
        # TODO Manage presets generation when multiple compatible graph inputs are found
        getLogger().info("Creating presets from CSV...")
        csvFilePaths: list[str] | str | None = self.findCSVResourcesInPackage()
        if not csvFilePaths:
            getLogger().info("No CSV resources found.")
            return None
        elif isinstance(csvFilePaths, list):
            getLogger().info(f"Multiple CSV resources found: {', '.join(csvFilePaths)}")
            return None

        getLogger().info(f"CSV resource found: {csvFilePaths}")
        colorsList: list[tuple[str, Any]] | None = extractColorsFromCSV(csvFilePaths, self.optionsDialog.csvOptions)
        if colorsList:
            getLogger().info(f"Found {len(colorsList)} colors: " + ", ".join([color[0] for color in colorsList]))
            colorInputProps = gatherGraphColorParameters(self.graph, self.optionsDialog.csvOptions["hasAlpha"])
            if colorInputProps:
                for inputProp in colorInputProps:
                    generatePresetsFromColors(self.graph, colorsList, inputProp)
                    break
            return None
        else:
            getLogger().info("No colors extracted from CSV.")
            return None

    def findCSVResourcesInPackage(self) -> list[str] | str | None:
        resourcePaths: list[str] = []
        for resource in self.package.getChildrenResources(isRecursive=True):
            resourceFilepath: str = resource.getFilePath()
            if resourceFilepath.endswith(".csv"):
                resourcePaths.append(resourceFilepath)
        if resourcePaths:
            if len(resourcePaths) > 1:
                return resourcePaths
            else:
                return resourcePaths[0]
        else:
            return None

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

        self.csvOptions: dict[str, Any] = {key: value for key, value in PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS.items()}

        self.setObjectName("presets-from-csv-dialog")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

        self.mainLayout = QVBoxLayout()
        self.csvDialectOption: QComboBox = self.addCSVDialectOption()
        self.labelRowOption: QTextEdit = self.addLabelRowOption()
        self.colorRowOption: QTextEdit = self.addColorRowOption()
        self.colorSeparatorOption: QTextEdit = self.addColorSeparatorOption()
        self.colorValueFormatOption: QComboBox = self.addColorValueFormatOption()
        self.hasAlphaOption: QCheckBox = self.addHasAlphaOption()
        self.hasHeaderOption: QCheckBox = self.addHasHeaderOption()
        self.resetButton: QPushButton = self.addResetToDefaultButton()

        self.setLayout(self.mainLayout)

        self.size = (200, 200)
        self.setFixedSize(*self.size)

    def addColorRowOption(self) -> QTextEdit:
        colorRowLayout = QtWidgets.QHBoxLayout()
        colorRowLabel = QtWidgets.QLabel("Color row:")

        colorRow = OptionTextEdit(self, "colorRow", onlyNumbers=True)
        colorRow.setText(self.csvOptions["colorRow"])  # Initialise default value

        colorRowLayout.addWidget(colorRowLabel)
        colorRowLayout.addWidget(colorRow)
        self.mainLayout.addLayout(colorRowLayout)

        return colorRow

    def addColorSeparatorOption(self) -> QTextEdit:
        colorSeparatorLayout = QtWidgets.QHBoxLayout()
        colorSeparatorLabel = QtWidgets.QLabel("Color separator:")

        colorSeparator = OptionTextEdit(self, "colorSeparator", onlyNumbers=False)
        colorSeparator.setText(self.csvOptions["colorSeparator"])  # Initialise default value

        colorSeparatorLayout.addWidget(colorSeparatorLabel)
        colorSeparatorLayout.addWidget(colorSeparator)
        self.mainLayout.addLayout(colorSeparatorLayout)

        return colorSeparator

    def addColorValueFormatOption(self) -> QComboBox:
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

        return colorValueFormat

    def addHasAlphaOption(self) -> QCheckBox:
        hasAlphaLayout = QtWidgets.QHBoxLayout()
        hasAlphaLabel = QtWidgets.QLabel("Has alpha:")

        hasAlpha = QtWidgets.QCheckBox()
        hasAlpha.toggled.connect(lambda: self.updateOptions("hasAlpha", hasAlpha.isChecked()))
        hasAlpha.setChecked(self.csvOptions["hasAlpha"])  # Initialise default value

        hasAlphaLayout.addWidget(hasAlphaLabel)
        hasAlphaLayout.addWidget(hasAlpha)
        self.mainLayout.addLayout(hasAlphaLayout)

        return hasAlpha

    def addHasHeaderOption(self) -> QCheckBox:
        hasHeaderLayout = QtWidgets.QHBoxLayout()
        hasHeaderLabel = QtWidgets.QLabel("Has header:")

        hasHeader = QtWidgets.QCheckBox()
        hasHeader.toggled.connect(lambda: self.updateOptions("hasHeader", hasHeader.isChecked()))
        hasHeader.setChecked(self.csvOptions["hasHeader"])  # Initialise default value

        hasHeaderLayout.addWidget(hasHeaderLabel)
        hasHeaderLayout.addWidget(hasHeader)
        self.mainLayout.addLayout(hasHeaderLayout)

        return hasHeader

    def addLabelRowOption(self) -> QTextEdit:
        # TODO Make label row optional and generate label from color values if not provided
        labelRowLayout = QtWidgets.QHBoxLayout()
        labelRowLabel = QtWidgets.QLabel("Label row:")

        labelRow = OptionTextEdit(self, "labelRow", onlyNumbers=True)
        labelRow.setText(self.csvOptions["labelRow"])  # Initialise default value

        labelRowLayout.addWidget(labelRowLabel)
        labelRowLayout.addWidget(labelRow)
        self.mainLayout.addLayout(labelRowLayout)

        return labelRow

    def addCSVDialectOption(self) -> QComboBox:
        csvDialectLayout = QtWidgets.QHBoxLayout()
        csvDialectLabel = QtWidgets.QLabel("CSV dialect:")
        csvDialect = QComboBox()

        csvDialect.addItem("Excel", userData="excel")
        csvDialect.addItem("Excel Tab", userData="excel-tab")
        csvDialect.addItem("Unix", userData="unix")

        csvDialect.currentIndexChanged.connect(
            lambda: self.updateOptions(key="csvDialect", value=csvDialect.itemData(csvDialect.currentIndex())))
        csvDialect.setCurrentIndex(csvDialect.findData(self.csvOptions["csvDialect"]))  # Initialise default value

        csvDialectLayout.addWidget(csvDialectLabel)
        csvDialectLayout.addWidget(csvDialect)
        self.mainLayout.addLayout(csvDialectLayout)

        return csvDialect

    def addResetToDefaultButton(self) -> QPushButton:
        buttonWidth = 30
        resetToDefaultLayout = QtWidgets.QHBoxLayout()

        resetToDefaultButton = QtWidgets.QPushButton("R")
        resetToDefaultButton.setFixedSize(QSize(buttonWidth, buttonWidth))
        resetToDefaultButton.clicked.connect(self.resetOptions)

        resetToDefaultLayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        resetToDefaultLayout.addWidget(resetToDefaultButton)
        self.mainLayout.addLayout(resetToDefaultLayout)

        return resetToDefaultButton

    def resetOptions(self) -> None:
        self.csvDialectOption.setCurrentIndex(self.csvDialectOption.findData(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["csvDialect"]))
        self.labelRowOption.setText(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["labelRow"])
        self.colorRowOption.setText(
            str(PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["colorRow"]))
        self.colorSeparatorOption.setText(
            str(PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["colorSeparator"]))
        self.colorValueFormatOption.setCurrentIndex(self.colorValueFormatOption.findData(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["colorValueFormat"]))
        self.hasHeaderOption.setChecked(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["hasHeader"])
        self.hasAlphaOption.setChecked(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["hasAlpha"])

        self.csvOptions = {key: value for key, value in PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS.items()}

        getLogger().info("CSV options have been reset.")
        self.__logCurrentOptions()

    def updateOptions(self, key: str, value: Any) -> None:
        self.csvOptions[key] = value
        getLogger().info(f"Updated option {key}: {value}")
        self.__logCurrentOptions()

    def __logCurrentOptions(self):
        optionsPrettyPrint = "\n".join([f"  - {key}: {value}" for key, value in self.csvOptions.items()])
        getLogger().info(f"Current options:\n{optionsPrettyPrint}")

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
        # TODO Add visual feedback for invalid input (e.g. red border) without losing focus
        if self.toPlainText():
            self.presetDialog.updateOptions(self.optionIdentifier, self.toPlainText())
        else:  # Set option value to default if text is empty
            self.presetDialog.updateOptions(
                self.optionIdentifier, PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS[self.optionIdentifier])
        super().focusOutEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Return or e.key() == Qt.Key.Key_Enter:
            self.clearFocus()  # Trigger focusOutEvent to save the option value
        elif e.key() == Qt.Key.Key_Backspace:
            self.clear()
        elif self.onlyNumbers == e.text().isdigit():
            self.setText(e.text())

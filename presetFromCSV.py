from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QToolBar, QDialog, QVBoxLayout, QComboBox, QTextEdit, QCheckBox, QPushButton, QSpinBox
from PySide6.QtCore import Qt, QRect, QPoint

from sd.api.sdpackagemgr import SDPackageMgr

from .utilities import *

# ---

class PresetsFromCSVToolbar(QToolBar):

    CSV_OPTIONS_DEFAULTS: dict[str, Any] = {
        "csvDialect": "excel",
        "hasLabel": True,
        "labelRow": 0,
        "colorRow": 1,
        "colorSeparator": "-",
        "colorValueFormat": int,
        "hasAlpha": False,
        "hasHeader": True
    }

    def __init__(self, parent, pkgMgr: SDPackageMgr, graph: SDSBSCompGraph):
        super().__init__(parent=parent)
        self.setObjectName("PresetsFromCSVToolbar")
        self.__pkgMgr = pkgMgr
        self.graph = graph
        self.package = self.graph.getPackage()

        self.optionsDialog = CSVOptionsDialog()
        self.presetsFromCSVDialog = PresetsFromCSVDialog()
        self.presetsFromCSVDialog.createPresetsButton.clicked.connect(self.createPresetsFromCSV)

        optionsAction = QtGui.QAction("Options", self)
        optionsAction.triggered.connect(self.displayOptions)
        self.addAction(optionsAction)

        createPresetsAction = QtGui.QAction("Create presets", self)
        createPresetsAction.triggered.connect(self.displayPresetsFromCSVDialog)
        self.addAction(createPresetsAction)

    def createPresetsFromCSV(self) -> None:
        # TODO Handle update of existing presets
        csvFilePath: dict[str, str] = self.presetsFromCSVDialog.csvResourceCombobox.currentData()
        colorInputProp: str = self.presetsFromCSVDialog.graphColorCombobox.currentText()
        colorsList: list[tuple[str, Any]] | None = extractColorsFromCSV(csvFilePath, self.optionsDialog.csvOptions)

        if colorsList:
            getLogger().info(f"Found {len(colorsList)} colors: " + ", ".join([color[0] for color in colorsList]))
            getLogger().info("Creating presets...")
            generatePresetsFromColors(self.graph, colorsList, colorInputProp)
        else:
            getLogger().info("No colors found in CSV.")

    def displayOptions(self):
        # zip() function pairs elements by position, sum() adds each pair
        # and map() applies sum() to all pairs for element-wise tuple addition.
        self.position = tuple(map(sum, zip(self.mapToGlobal(QPoint(0, 0)).toTuple(), (0, 20))))

        self.optionsDialog.setGeometry(QRect(*self.position, *self.optionsDialog.size))
        self.optionsDialog.show()

    def displayPresetsFromCSVDialog(self):
        self.position = tuple(map(sum, zip(self.mapToGlobal(QPoint(0, 0)).toTuple(), (0, 20))))

        self.presetsFromCSVDialog.csvResourcesFilepaths = gatherCSVResourcesPathsInPackage(self.package)
        self.presetsFromCSVDialog.graphColorParameters = gatherGraphColorParameters(
            self.graph, hasAlpha=self.optionsDialog.csvOptions["hasAlpha"])
        self.presetsFromCSVDialog.refreshComboboxesLists()

        self.presetsFromCSVDialog.setGeometry(QRect(*self.position, *self.optionsDialog.size))
        self.presetsFromCSVDialog.show()


class CSVOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.csvOptions: dict[str, Any] = {key: value for key, value in PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS.items()}

        self.setObjectName("csv-options-dialog")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

        self.mainLayout = QVBoxLayout()
        self.csvDialectOption: QComboBox = self.addCSVDialectOption()
        self.labelRowOption: QTextEdit = self.addLabelRowOption()
        self.colorRowOption: QTextEdit = self.addColorRowOption()
        self.labelRowOption: QSpinBox = self.addLabelRowOption()
        self.colorRowOption: QSpinBox = self.addColorRowOption()
        self.colorSeparatorOption: QTextEdit = self.addColorSeparatorOption()
        self.colorValueFormatOption: QComboBox = self.addColorValueFormatOption()
        self.hasAlphaOption: QCheckBox = self.addHasAlphaOption()
        self.hasHeaderOption: QCheckBox = self.addHasHeaderOption()
        self.resetButton: QPushButton = self.addResetToDefaultButton()

        self.setLayout(self.mainLayout)

    def addColorRowOption(self) -> QSpinBox:
        colorRowLayout = QtWidgets.QHBoxLayout()
        colorRowLabel = QtWidgets.QLabel("Color row:")

        colorRow = RowSpinBox(presetDialog=self, optionIdentifier="colorRow", parent=self)

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

    def addLabelRowOption(self) -> QSpinBox:
        # TODO Make label row optional and generate label from color values if not provided
        labelRowLayout = QtWidgets.QHBoxLayout()
        labelRowLabel = QtWidgets.QLabel("Label row:")

        labelRow = RowSpinBox(presetDialog=self, optionIdentifier="labelRow", parent=self)

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
        self.labelRowOption.setValue(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["labelRow"])
        self.colorRowOption.setValue(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["colorRow"])
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
            self, presetDialog: CSVOptionsDialog, optionIdentifier: str, parent=None):
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
        super().keyPressEvent(e)


class RowSpinBox(QtWidgets.QSpinBox):
    def __init__(self, presetDialog: CSVOptionsDialog, optionIdentifier: str, parent=None):
        super().__init__(parent)
        self.setSingleStep(1)
        self.setMinimum(0)

        self.presetDialog = presetDialog
        self.optionIdentifier = optionIdentifier

        self.setValue(presetDialog.csvOptions[optionIdentifier])  # Initialise default value

    def focusOutEvent(self, e):
        self.presetDialog.updateOptions(
            self.optionIdentifier, self.value())
        super().focusOutEvent(e)


class PresetsFromCSVDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("presets-from-csv-dialog")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.size = (200, 200)
        self.setFixedSize(*self.size)

        self.csvResourcesFilepaths: dict[str, str] = {}
        self.graphColorParameters: dict[str, SDProperty] = {}

        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.csvResourceCombobox: QComboBox = self.addCSVResourceOption()
        self.graphColorCombobox: QComboBox = self.addGraphColorParametersCombobox()
        self.createPresetsButton: QPushButton = self.addCreatePresetsButton()
        self.refreshComboboxesLists()

    def addCSVResourceOption(self) -> QComboBox:
        csvResourceLayout = QtWidgets.QHBoxLayout()
        csvResourceLabel = QtWidgets.QLabel("CSV resource:")
        csvResourceCombobox = QtWidgets.QComboBox()

        csvResourceLayout.addWidget(csvResourceLabel)
        csvResourceLayout.addWidget(csvResourceCombobox)
        self.mainLayout.addLayout(csvResourceLayout)

        return csvResourceCombobox

    def addGraphColorParametersCombobox(self) -> QComboBox:
        graphColorLayout = QtWidgets.QHBoxLayout()
        graphColorLabel = QtWidgets.QLabel("Color parameter:")
        graphColorCombobox = QtWidgets.QComboBox()

        graphColorLayout.addWidget(graphColorLabel)
        graphColorLayout.addWidget(graphColorCombobox)
        self.mainLayout.addLayout(graphColorLayout)

        return graphColorCombobox

    def refreshComboboxesLists(self):
        self.graphColorCombobox.clear()
        self.csvResourceCombobox.clear()

        if not self.graphColorParameters or not self.csvResourcesFilepaths:
            return

        for graphColorParameter in self.graphColorParameters:
            parameterLabel = self.graphColorParameters[graphColorParameter].getLabel()
            if parameterLabel:
                self.graphColorCombobox.addItem(parameterLabel, userData=self.graphColorParameters[graphColorParameter])
            else:
                self.graphColorCombobox.addItem(graphColorParameter, userData=self.graphColorParameters[graphColorParameter])
        self.graphColorCombobox.setCurrentIndex(0)

        for resourceId, resource in self.csvResourcesFilepaths.items():
            self.csvResourceCombobox.addItem(resourceId, userData=resource)
        self.csvResourceCombobox.setCurrentIndex(0)

    def addCreatePresetsButton(self) -> QPushButton:
        buttonWidth = 30
        createPresetsLayout = QtWidgets.QHBoxLayout()

        createPresetsButton = QtWidgets.QPushButton("Create presets")
        createPresetsButton.setFixedSize(QSize(buttonWidth, buttonWidth))

        createPresetsLayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        createPresetsLayout.addWidget(createPresetsButton)
        self.mainLayout.addLayout(createPresetsLayout)

        return createPresetsButton

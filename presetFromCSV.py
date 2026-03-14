from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QToolBar, QDialog, QVBoxLayout, QComboBox, QTextEdit, QCheckBox, QPushButton, QSpinBox
from PySide6.QtCore import Qt, QRect, QPoint

from sd.api import SDResourceBitmap
from sd.api.sdresource import EmbedMethod
from sd.api.sdpackagemgr import SDPackageMgr

from os import path

from .utilities import *
from .ui_strings import *

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
        self.packageDir, self.packageName = path.split(self.package.getFilePath())
        self.packageResourcesDir = path.join(self.packageDir, path.splitext(self.packageName)[0] + ".resources")

        self.optionsDialog = CSVOptionsDialog()
        self.presetsFromCSVDialog = PresetsFromCSVDialog()
        self.presetsFromCSVDialog.createPresetsButton.clicked.connect(self.createPresetsFromCSV)
        self.presetsFromCSVDialog.createPaletteButton.clicked.connect(self.createPaletteFromCSV)

        self.optionsAction = QtGui.QAction("Options", self)
        self.optionsAction.triggered.connect(self.displayOptions)
        self.addAction(self.optionsAction)

        self.createPresetsAction = QtGui.QAction("Create presets", self)
        self.createPresetsAction.triggered.connect(self.displayPresetsFromCSVDialog)
        self.addAction(self.createPresetsAction)

    def createPresetsFromCSV(self) -> None:
        # TODO Handle update of existing presets
        csvFilePath: str = self.presetsFromCSVDialog.csvResourceCombobox.currentData()
        colorInputProp: str = self.presetsFromCSVDialog.graphColorCombobox.currentText()
        colorsList: list[tuple[str, ColorRGB | ColorRGBA]] | None = extractColorsFromCSV(csvFilePath, self.optionsDialog.csvOptions)

        if colorsList:
            getLogger().info(f"Found {len(colorsList)} colors: " + ", ".join([color[0] for color in colorsList]))
            getLogger().info("Creating presets...")
            generatePresetsFromColors(self.graph, colorsList, colorInputProp)
        else:
            getLogger().info("No colors found in CSV.")

    def createPaletteFromCSV(self) -> SDResourceBitmap | None:
        csvFilePath: str = self.presetsFromCSVDialog.csvResourceCombobox.currentData()
        colorsList: list[tuple[str, ColorRGB | ColorRGBA]] | None = extractColorsFromCSV(csvFilePath, self.optionsDialog.csvOptions)

        if colorsList:
            getLogger().info(f"Found {len(colorsList)} colors: " + ", ".join([color[0] for color in colorsList]))
            getLogger().info("Creating palette bitmap...")
            paletteImage = generatePaletteFromColors(colorsList)
            paletteImageFilePath = path.join(self.packageResourcesDir, self.presetsFromCSVDialog.csvResourceCombobox.currentText() + "_palette.png")
            paletteImage.save(paletteImageFilePath)
            paletteBitmapResource = SDResourceBitmap.sNewFromFile(self.package, paletteImageFilePath, EmbedMethod.Linked)  # TODO Use 'Resources' folder instead of package root
            return paletteBitmapResource
        else:
            getLogger().info("No colors found in CSV.")
            return None

    def displayOptions(self):
        # zip() function pairs elements by position, sum() adds each pair
        # and map() applies sum() to all pairs for element-wise tuple addition.
        self.position = tuple(map(sum, zip(self.mapToGlobal(QPoint(0, 0)).toTuple(), (0, self.size().height()))))

        self.optionsDialog.setGeometry(QRect(*self.position, *self.optionsDialog.size().toTuple()))
        self.optionsDialog.show()

    def displayPresetsFromCSVDialog(self):
        # TODO Spawn dialog under toolbar action
        self.position = tuple(map(sum, zip(self.mapToGlobal(QPoint(0, 0)).toTuple(), (0, self.size().height()))))

        self.presetsFromCSVDialog.csvResourcesFilepaths = gatherCSVResourcesPathsInPackage(self.package)
        self.presetsFromCSVDialog.graphColorParameters = gatherGraphColorParameters(
            self.graph, hasAlpha=self.optionsDialog.csvOptions["hasAlpha"])
        self.presetsFromCSVDialog.refreshComboboxesLists()

        self.presetsFromCSVDialog.createPresetsButton.setEnabled(
            len(self.presetsFromCSVDialog.csvResourcesFilepaths) > 0 and len(self.presetsFromCSVDialog.graphColorParameters) > 0)

        self.presetsFromCSVDialog.setGeometry(QRect(*self.position, *self.presetsFromCSVDialog.size().toTuple()))
        self.presetsFromCSVDialog.show()


class CSVOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.csvOptions: dict[str, Any] = {key: value for key, value in PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS.items()}

        self.setObjectName("csv-options-dialog")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setFixedSize(200, 250)

        self.mainLayout = QVBoxLayout()
        self.csvDialectOption: QComboBox = self.addCSVDialectOption()
        self.hasLabelOption: QCheckBox = self.addHasLabelOption()
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
        colorRowLabel = QtWidgets.QLabel(UIStr_colorRowLabel)

        colorRow = RowSpinBox(presetDialog=self, optionIdentifier="colorRow", parent=self)

        colorRowLayout.addWidget(colorRowLabel)
        colorRowLayout.addWidget(colorRow)
        self.mainLayout.addLayout(colorRowLayout)

        return colorRow

    def addColorSeparatorOption(self) -> QTextEdit:
        colorSeparatorLayout = QtWidgets.QHBoxLayout()
        colorSeparatorLabel = QtWidgets.QLabel(UIStr_colorSeparatorLabel)

        colorSeparator = OptionTextEdit(
            presetDialog=self, optionIdentifier="colorSeparator", parent=self)


        colorSeparatorLayout.addWidget(colorSeparatorLabel)
        colorSeparatorLayout.addWidget(colorSeparator)
        self.mainLayout.addLayout(colorSeparatorLayout)

        return colorSeparator

    def addColorValueFormatOption(self) -> QComboBox:
        colorValueFormatLayout = QtWidgets.QHBoxLayout()
        colorValueFormatLabel = QtWidgets.QLabel(UIStr_colorFormatLabel)
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
        hasAlphaLabel = QtWidgets.QLabel(UIStr_hasAlphaLabel)

        hasAlpha = QtWidgets.QCheckBox()
        hasAlpha.toggled.connect(lambda: self.updateOptions("hasAlpha", hasAlpha.isChecked()))
        hasAlpha.setChecked(self.csvOptions["hasAlpha"])  # Initialise default value

        hasAlphaLayout.addWidget(hasAlphaLabel)
        hasAlphaLayout.addWidget(hasAlpha)
        self.mainLayout.addLayout(hasAlphaLayout)

        return hasAlpha

    def addHasLabelOption(self) -> QCheckBox:
        hasLabelLayout = QtWidgets.QHBoxLayout()
        hasLabelLabel = QtWidgets.QLabel(UIStr_hasLabelLabel)

        hasLabel = QtWidgets.QCheckBox()
        hasLabel.toggled.connect(lambda: self.updateOptions("hasLabel", hasLabel.isChecked()))
        hasLabel.toggled.connect(lambda: self.labelRowOption.setEnabled(hasLabel.isChecked()))
        hasLabel.setChecked(self.csvOptions["hasLabel"])

        hasLabelLayout.addWidget(hasLabelLabel)
        hasLabelLayout.addWidget(hasLabel)
        self.mainLayout.addLayout(hasLabelLayout)

        return hasLabel

    def addHasHeaderOption(self) -> QCheckBox:
        hasHeaderLayout = QtWidgets.QHBoxLayout()
        hasHeaderLabel = QtWidgets.QLabel(UIStr_hasHeaderLabel)

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
        labelRowLabel = QtWidgets.QLabel(UIStr_labelRowLabel)

        labelRow = RowSpinBox(presetDialog=self, optionIdentifier="labelRow", parent=self)

        labelRowLayout.addWidget(labelRowLabel)
        labelRowLayout.addWidget(labelRow)
        self.mainLayout.addLayout(labelRowLayout)

        return labelRow

    def addCSVDialectOption(self) -> QComboBox:
        csvDialectLayout = QtWidgets.QHBoxLayout()
        csvDialectLabel = QtWidgets.QLabel(UIStr_csvDialectLabel)
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
        resetToDefaultLayout = QtWidgets.QHBoxLayout()
        resetToDefaultLayout.setAlignment(Qt.AlignmentFlag.AlignRight)

        resetToDefaultButton = QtWidgets.QPushButton("R")
        resetToDefaultButton.setFixedSize(20, 20)
        resetToDefaultButton = QtWidgets.QPushButton(UIStr_optionsResetButton)
        resetToDefaultButton.clicked.connect(self.resetOptions)

        resetToDefaultLayout.addStretch()
        resetToDefaultLayout.addWidget(resetToDefaultButton)
        self.mainLayout.addLayout(resetToDefaultLayout)

        return resetToDefaultButton

    def resetOptions(self) -> None:
        self.csvDialectOption.setCurrentIndex(self.csvDialectOption.findData(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["csvDialect"]))
        self.hasLabelOption.setChecked(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["hasLabel"])
        self.labelRowOption.setValue(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["labelRow"])
        self.colorRowOption.setValue(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["colorRow"])
        self.colorSeparatorOption.setText(
            PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS["colorSeparator"])
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

        self.presetDialog = presetDialog
        self.optionIdentifier = optionIdentifier

        self.setText(presetDialog.csvOptions[optionIdentifier])  # Initialise default value

    def focusOutEvent(self, e):
        # TODO Add visual feedback for invalid input (e.g. red border) without losing focus
        plainText = self.toPlainText()
        if plainText:
            self.presetDialog.updateOptions(self.optionIdentifier, plainText)
        else:  # Set option value to default if text is empty
            self.presetDialog.updateOptions(
                self.optionIdentifier, PresetsFromCSVToolbar.CSV_OPTIONS_DEFAULTS[self.optionIdentifier])
        super().focusOutEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Return or e.key() == Qt.Key.Key_Enter:
            self.clearFocus()  # Trigger focusOutEvent to save the option value
        elif e.key() == Qt.Key.Key_Backspace:
            self.clear()
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
        self.setFixedSize(200, 180)

        self.csvResourcesFilepaths: dict[str, str] = {}
        self.graphColorParameters: dict[str, SDProperty] = {}

        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.csvResourceCombobox: QComboBox = QtWidgets.QComboBox()
        self.addCSVResourceSection()

        self.graphColorCombobox: QComboBox = QtWidgets.QComboBox()
        self.createPresetsButton: QPushButton = QtWidgets.QPushButton(UIStr_createPresetsButton)
        self.addCreatePresetsSection()

        self.createPaletteButton: QPushButton = QtWidgets.QPushButton(UIStr_createPaletteButton)
        self.addCreatePaletteSection()

        self.csvResourceCombobox.currentTextChanged.connect(self.refreshButtonStates)
        self.graphColorCombobox.currentTextChanged.connect(self.refreshButtonStates)

        self.refreshComboboxesLists()
        self.refreshButtonStates()

    def addCSVResourceSection(self) -> None:
        csvResourceLayout = QtWidgets.QHBoxLayout()

        # CSV resource combobox
        csvResourceLabel = QtWidgets.QLabel(UIStr_csvResourceLabel)
        csvResourceLayout.addWidget(csvResourceLabel)
        csvResourceLayout.addWidget(self.csvResourceCombobox)

        self.mainLayout.addLayout(csvResourceLayout)

    def refreshComboboxesLists(self):
        self.graphColorCombobox.clear()
        self.csvResourceCombobox.clear()

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

    def refreshButtonStates(self) -> None:
        if not self.csvResourceCombobox.currentText():
            self.createPresetsButton.setEnabled(False)
            self.createPaletteButton.setEnabled(False)
        else:
            self.createPaletteButton.setEnabled(True)
            if not self.graphColorCombobox.currentText():
                self.createPresetsButton.setEnabled(False)
            else:
                self.createPresetsButton.setEnabled(True)

    def addCreatePresetsSection(self) -> None:
        createPresetsLayout = QtWidgets.QVBoxLayout()

        # Title
        createPresetsLabel = QtWidgets.QLabel("<b>" + UIStr_createPresetsSection + "</b>")
        createPresetsLayout.addWidget(createPresetsLabel)

        # Graph input combobox
        graphColorLayout = QtWidgets.QHBoxLayout()
        graphColorLabel = QtWidgets.QLabel(UIStr_colorParameterLabel)
        graphColorLayout.addWidget(graphColorLabel)
        graphColorLayout.addWidget(self.graphColorCombobox)
        createPresetsLayout.addLayout(graphColorLayout)

        # Create presets button
        createPresetsLayout.addWidget(self.createPresetsButton)

        self.mainLayout.addLayout(createPresetsLayout)

    def addCreatePaletteSection(self) -> None:
        createPaletteLayout = QtWidgets.QVBoxLayout()

        # Title
        createPaletteLabel = QtWidgets.QLabel("<b>" + UIStr_createPaletteSection + "</b>")
        createPaletteLayout.addWidget(createPaletteLabel)

        # Create palette button
        createPaletteButton = self.createPaletteButton
        createPaletteLayout.addWidget(createPaletteButton)

        self.mainLayout.addLayout(createPaletteLayout)

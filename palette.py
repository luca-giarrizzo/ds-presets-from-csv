from sd.api import SDValueColorRGB
from sd.api.sdbasetypes import ColorRGB
from sd.api.sdvaluestring import SDValueString

import csv
from typing import Any, cast

from utilities import getLogger

# ---

class PaletteColor:

    HEXCODE_ALLOWLIST = {"A", "B", "C", "D", "E", "F"}

    def __init__(
        self, rgbValues: tuple[int, int, int] | None = None, hexCode: str | None = None, name: str | None = None):

        if rgbValues and hexCode:
            getLogger().warning("Both RGB values and hex code provided. Hex code will be ignored.")

        if rgbValues:
            self.rgbValues = clampRGBValue(rgbValues)  # RGB Values are clamped to [0, 255] range.
            self.hex = RGBToHex(self.rgbValues)
        elif hexCode:
            hexCode = hexCode.upper()  # Hex code may be lowercase
            if validateHexCode(hexCode):
                self.hex = hexCode
                self.rgbValues = hexToRGB(self.hex)
            else:
                getLogger().error(f"Invalid hex code: {hexCode}")
                self.hex = None
                self.rgbValues = None

        if self.rgbValues:
            self.r, self.g, self.b = self.rgbValues
        else:
            self.r, self.g, self.b = None, None, None

        if name:
            self.name = name
        elif self.hex:
            self.name = self.hex
        else:
            self.name = None

    def toFloat(self) -> tuple[float, float, float] | None:
        return self.r / 255.0, self.g / 255.0, self.b / 255.0 if self.rgbValues else None

    def colorToSDValueRGB(self) -> SDValueColorRGB | None:
        return SDValueColorRGB.sNew(ColorRGB(*self.toFloat())) if self.rgbValues else None

    def nameToSDValue(self) -> SDValueString | None:
        return SDValueString.sNew(self.name) if self.name else None

# ---

def intToHex(intValue: int) -> str | None:
    if intValue < 10:
        return str(intValue)
    elif intValue == 10:
        return "A"
    elif intValue == 11:
        return "B"
    elif intValue == 12:
        return "C"
    elif intValue == 13:
        return "D"
    elif intValue == 14:
        return "E"
    elif intValue == 15:
        return "F"
    else:
        return None

def hexToInt(hexValue: str) -> int | None:
    if hexValue.isdigit() and int(hexValue) < 10:
        return int(hexValue)
    elif hexValue == "A":
        return 10
    elif hexValue == "B":
        return 11
    elif hexValue == "C":
        return 12
    elif hexValue == "D":
        return 13
    elif hexValue == "E":
        return 14
    elif hexValue == "F":
        return 15
    else:
        return None

def RGBToHex(rgbValues: tuple[int, int, int]) -> str:
    hexCode = "#"
    for channel in rgbValues:
        channelIntDiv = channel // 16
        channelHex = intToHex(channelIntDiv) + intToHex(channel - channelIntDiv * 16)
        hexCode += channelHex
    return hexCode

def hexToRGB(hexCode: str) -> tuple[int, int, int]:
    hexCode = hexCode[1:]
    return (
        hexToInt(hexCode[0]) * 16 + hexToInt(hexCode[1]),
        hexToInt(hexCode[2]) * 16 + hexToInt(hexCode[3]),
        hexToInt(hexCode[4]) * 16 + hexToInt(hexCode[5])
    )

def validateHexCode(hexCode: str) -> bool:
    if hexCode.startswith("#"):
        for character in hexCode[1:]:
            if not (character.isdigit() or character in PaletteColor.HEXCODE_ALLOWLIST):
                return False
    else:
        return False
    return True

def clampRGBValue(rgbValues: tuple[int, int, int]) -> tuple[int, int, int]:
    """
    Clamps a tuple of RGB values to the [0, 255] range.
    :param rgbValues: The tuple of RGB values that should be clamped.
    :return: The clamped RGB values.
    """
    return (
        min(255, max(0, rgbValues[0])),
        min(255, max(0, rgbValues[1])),
        min(255, max(0, rgbValues[2]))
    )

def extractColorsFromCSV(csvFilePath: str, csvOptions: dict[str, Any]) -> dict[str, PaletteColor] | None:
    colors: dict[str, PaletteColor] = {}

    try:
        with open(csvFilePath, "r", encoding="utf-8", newline="") as csvFile:
            csvReader = csv.reader(csvFile, delimiter=",", dialect=csvOptions["csvDialect"])
            csvValues = [row for row in csvReader]
    except Exception as e:
        getLogger().error("ERROR:" + str(e))
        return None

    if csvOptions["hasHeader"]:
        csvValues = csvValues[1:]  # Skip header row

    for index, row in enumerate(csvValues):

        # Channels split into multiple columns
        if "," in csvOptions["colorRow"]:
            colorValueList: list[int] = []
            colorColumns = csvOptions["colorRow"].split(",")
            if not len(colorColumns) == 3:
                getLogger().error(f"Amount of color columns should be 3.")
                return None
            for columnIndex in colorColumns:
                if not columnIndex.isdigit():
                    getLogger().error(f"Row index {columnIndex} is not a digit.")
                    return None
                columnIndex = int(columnIndex)
                if columnIndex >= len(row):
                    getLogger().error(f"Row index {columnIndex} is out of range for CSV row with length {len(row)}.")
                    return None
                colorValueList.append(int(row[columnIndex]))

        # Channels in a single column
        else:
            columnIndex = csvOptions["colorRow"]
            if not columnIndex.isdigit():
                getLogger().error(f"Row index {columnIndex} is not a digit.")
                return None
            columnIndex = int(columnIndex)
            if columnIndex >= len(row):
                getLogger().error(f"Row index {columnIndex} is out of range for CSV row with length {len(row)}.")
                return None
            colorValueList = [int(v) for v in row[columnIndex].split(csvOptions["colorSeparator"])]

        # Convert list of values to tuple
        colorValues = cast(tuple[int, int,int], tuple(*colorValueList))

        if csvOptions["hasLabel"]:
            label = row[int(csvOptions["labelRow"])]
        else:
            label = RGBToHex(colorValues)
        colors[label] = PaletteColor(rgbValues=colorValues, name=label)

    return colors


# ---

if "__main__" == __name__:
    color_01_rgb = (136, 202, 34)
    color_01 = PaletteColor(rgbValues=color_01_rgb)
    print(f"TEST: {color_01.name} / Input: {color_01_rgb} / Output: {color_01.hex}")

    color_02_hex = "#a3ff4c"
    color_02 = PaletteColor(hexCode=color_02_hex)
    print(f"TEST: {color_02.name} / Input: {color_02_hex} / Output: R {color_01.r}, G {color_02.g}, B {color_02.b}")

    color_03_rgb = (316, -27, 256)
    color_03 = PaletteColor(rgbValues=color_03_rgb, name="My out-of-range color")
    print(f"TEST: {color_03.name} / Input: {color_03_rgb} / Output: {color_03.hex}")

from typing import Any

import sd
from sd.api import SDValueColorRGBA
from sd.api.sdbasetypes import ColorRGBA, float4
from sd.api.sbs.sdsbscompgraph import SDSBSCompGraph

import csv
import logging

# --- Initialise logger ---

__gLogger = None
def getLogger():
    """
    Get the global logger.
    The logger is created the first time the function is called.
    """
    global __gLogger
    if not __gLogger:
        __gLogger = logging.getLogger("PresetsFromCSV")
        __gLogger.addHandler(sd.getContext().createRuntimeLogHandler())
        __gLogger.propagate = False
        __gLogger.setLevel(logging.DEBUG)
    return __gLogger

# ---

def generateColorRGBAPresetsFromCSV(
        graph: SDSBSCompGraph, colorList: list[tuple[str, ColorRGBA]] | None, graphInputIdentifier: str) -> None:
  if not colorList:
    getLogger().warning("No colors to generate presets from.")
    return None
  for color in colorList:
    preset = graph.newPreset(color[0])
    preset.addInput(graphInputIdentifier, SDValueColorRGBA.sNew(color[1]))
    getLogger().info(f"Generated preset: {color[0]}")

def extractColorRGBAFromCSV(
        csvFilePath: str, csvOptions: dict[str, Any]) -> list[tuple[str, ColorRGBA]] | None:
  if not (csvOptions["colorValueFormat"] is float or csvOptions["colorValueFormat"] is int):
    getLogger().error("Invalid color value format specified:", str(csvOptions["colorValueFormat"]))
    return None
  colors: list[tuple[str, ColorRGBA]] = []
  try:
    with open(csvFilePath, "r", encoding="utf-8", newline="") as csvFile:
      csvReader = csv.reader(csvFile, delimiter=",", dialect=csvOptions["csvDialect"])
      csvValues = [row for row in csvReader]
      if csvOptions["hasHeader"]:
        csvValues = csvValues[1:]  # Skip header row
      for index, row in enumerate(csvValues):
        colorValueList = []
        if isinstance(csvOptions["colorRow"], set):
          for rowIndex in csvOptions["colorRow"]:
            if rowIndex >= len(row):
              getLogger().error(f"Row index {rowIndex} is out of range for CSV row with length {len(row)}.")
              return None
            colorValueList.append(float(row[rowIndex]))
        else:
          colorValueList = [float(v) for v in row[int(csvOptions["colorRow"])].split(csvOptions["colorSeparator"])]
        if csvOptions["colorValueFormat"] is int:
          colorValueList = [colorValue / 255.0 for colorValue in colorValueList]
        if not csvOptions["hasAlpha"]:
          colorValueList.append(1)  # Add alpha value
        colors.append((row[int(csvOptions["labelRow"])], ColorRGBA(*colorValueList)))
    return colors
  except Exception as e:
    getLogger().error("ERROR:" + str(e))
    return None

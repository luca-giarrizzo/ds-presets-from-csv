import sd
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
        graph: SDSBSCompGraph, csvFilePath: str, graphInputIdentifier: str) -> None:
  colorList = extractColorRGBAFromCSV(csvFilePath, 1, hasHeader=True)
  for color in colorList:
    preset = graph.newPreset(color[0])
    preset.addInput(graphInputIdentifier, color[1])

def extractColorRGBAFromCSV(
        csvFilePath: str, colorRow: int | set[int], colorSeparator: str = "-", colorValueFormat: type = float,
        hasAlpha: bool = False, hasHeader: bool = True, labelRow: int = 0, csvDialect: str = "excel"
) -> list[tuple[str, ColorRGBA]] | None:
  if not (colorValueFormat is float or colorValueFormat is int):
    getLogger().error("Invalid color value format specified:", str(colorValueFormat))
    return None
  colors: list[tuple[str, ColorRGBA]] = []
  try:
    with open(csvFilePath, "r", encoding="utf-8", newline="") as csvFile:
      csvReader = csv.reader(csvFile, delimiter=",", dialect=csvDialect)
      csvValues = [row for row in csvReader]
      if hasHeader:
        csvValues = csvValues[1:]  # Skip header row
      for index, row in enumerate(csvValues):
        colorValueList = []
        if isinstance(colorRow, set):
          for rowIndex in colorRow:
            if rowIndex >= len(row):
              getLogger().error(f"Row index {rowIndex} is out of range for CSV row with length {len(row)}.")
              return None
            colorValueList.append(float(row[rowIndex]))
        else:
          colorValueList = [float(v) for v in row[colorRow].split(colorSeparator)]
        if colorValueFormat is int:
          colorValueList = [colorValue / 255.0 for colorValue in colorValueList]
        if not hasAlpha:
          colorValueList.append(1)  # Add alpha value
        colors.append((row[labelRow], ColorRGBA.sNew(float4(*colorValueList))))
    return colors
  except Exception as e:
    getLogger().error("ERROR:" + str(e))
    return None

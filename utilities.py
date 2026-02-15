from typing import Any

import sd
from sd.api.sdpackage import SDPackage
from sd.api.sdproperty import SDProperty, SDPropertyCategory
from sd.api.sbs.sdsbscompgraph import SDSBSCompGraph
from sd.api.sdbasetypes import ColorRGBA, ColorRGB
from sd.api.sdtypefloat3 import SDTypeFloat3
from sd.api.sdtypefloat4 import SDTypeFloat4
from sd.api.sdvaluestring import SDValueString
from sd.api import SDValueColorRGBA, SDValueColorRGB

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

def generatePresetsFromColors(
        graph: SDSBSCompGraph,
        colorList: list[tuple[str, Any]] | None,
        graphInputIdentifier: str
) -> None:
  if not colorList:
    getLogger().warning("No colors to generate presets from.")
    return None
  for color in colorList:
    getLogger().info("Generating presets for color: " + color[0])
    if isinstance(color[1], ColorRGBA):
      colorValue = SDValueColorRGBA.sNew(color[1])
    elif isinstance(color[1], ColorRGB):
      colorValue = SDValueColorRGB.sNew(color[1])
    else :
      getLogger().warning(f"Incorrect type for color {color[0]} ({str(color[1])}) / Skipping...")
      continue
    preset = graph.newPreset(color[0])
    preset.addInput(graphInputIdentifier, colorValue)
    getLogger().info(f"Generated preset: {color[0]} / {str(color[1])}")

def gatherGraphColorParameters(graph: SDSBSCompGraph, hasAlpha: bool = False) -> dict[str, SDProperty]:
  graphColorParameters: dict[str, SDProperty] = {}
  targetType = SDTypeFloat4 if hasAlpha else SDTypeFloat3

  for inputProperty in graph.getProperties(SDPropertyCategory.Input):
    inputPropertyEditor: SDValueString | None = graph.getPropertyAnnotationValueFromId(inputProperty, "editor")
    inputPropertyEditorValue: str = inputPropertyEditor.get() if inputPropertyEditor else ""
    if isinstance(inputProperty.getType(), targetType) and inputPropertyEditorValue == "color":
      graphColorParameters[inputProperty.getId()] = inputProperty

  if graphColorParameters:
    getLogger().info(
      "Color inputs:\n" + "\n".join([f"  - {key}: {value}" for key, value in graphColorParameters.items()]))
    return graphColorParameters
  else:
    getLogger().info("No color inputs found.")

  return graphColorParameters

def gatherCSVResourcesPathsInPackage(package: SDPackage) -> dict[str, str]:
    csvResources: dict[str, str] = {}
    for resource in package.getChildrenResources(isRecursive=True):
        resourceFilepath: str = resource.getFilePath()
        if resourceFilepath.endswith(".csv"):
            csvResources[resource.getIdentifier()] = resourceFilepath
    return csvResources

def getCSVResourceFilePath(self, package: SDPackage, resourcePkgPath : str) -> str | None:
    resource = package.findResourceFromUrl(resourcePkgPath)
    if not resource:
        getLogger().warning(f"Resource not found: {resourcePkgPath}")
        return None
    resourceFilePath: str = resource.getFilePath()
    if resourceFilePath.endswith(".csv"):
        return resourceFilePath
    else:
        getLogger().warning(f"Resource is not a CSV file: {resourcePkgPath}")
        return None


def extractColorsFromCSV(
        csvFilePath: str, csvOptions: dict[str, Any]) -> list[tuple[str, Any]] | None:
  if not (csvOptions["colorValueFormat"] is float or csvOptions["colorValueFormat"] is int):
    getLogger().error("Invalid color value format specified:", str(csvOptions["colorValueFormat"]))
    return None
  colors: list[tuple[str, Any]] = []
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
          if int(csvOptions["colorRow"]) >= len(row):
            getLogger().error(f"Row index {rowIndex} is out of range for CSV row with length {len(row)}.")
            return None
          colorValueList = [float(v) for v in row[int(csvOptions["colorRow"])].split(csvOptions["colorSeparator"])]
        if csvOptions["hasLabel"]:
          colorLabel = row[int(csvOptions["labelRow"])]
        else:
          colorLabel = colorValueList[index]
        if csvOptions["colorValueFormat"] is int:
          colorValueList = [colorValue / 255.0 for colorValue in colorValueList]
        if csvOptions["hasAlpha"]:
          colors.append((colorLabel, ColorRGBA(*colorValueList)))
        else:
          colors.append((colorLabel, ColorRGB(*colorValueList)))
    return colors
  except Exception as e:
    getLogger().error("ERROR:" + str(e))
    return None

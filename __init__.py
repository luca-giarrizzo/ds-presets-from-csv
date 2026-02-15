import sd
from sd.api import SDSBSCompGraph
from sd.api.qtforpythonuimgrwrapper import QtForPythonUIMgrWrapper
from sd.api.sdpackagemgr import SDPackageMgr
from sd.api.sdgraph import SDGraph

from PySide6.QtGui import QIcon, QPixmap

from os import path

from functools import partial

from .utilities import getLogger
from .presetFromCSV import PresetsFromCSVToolbar
from .ui_strings import UIStr_toolbarToggleTooltip

# ---

CALLBACK_IDS: list[int] = []

# ---

def onGraphViewCreated(graphViewId: int, uiMgrQt: QtForPythonUIMgrWrapper, pkgMgr: SDPackageMgr) -> None:
    graph: SDGraph = uiMgrQt.getGraphFromGraphViewID(graphViewId)
    if not isinstance(graph, SDSBSCompGraph):
        return
    presetToolbar = PresetsFromCSVToolbar(parent=uiMgrQt.getMainWindow(), pkgMgr=pkgMgr, graph=graph)
    getLogger().info("Preset toolbar created:", presetToolbar)
    getLogger().info("Preset toolbar options:", presetToolbar.optionsDialog.csvOptions)
    toolbarIcon = QIcon(QPixmap(path.join(path.split(__file__)[0], "icons", "substance_designer.png")))
    uiMgrQt.addToolbarToGraphView(graphViewId, presetToolbar, toolbarIcon, UIStr_toolbarToggleTooltip)
    getLogger().info(f"Added toolbar to Graph view (ID={graphViewId})")

def initializeSDPlugin():
    global CALLBACK_IDS

    getLogger().info("Initializing 'Presets from CSV' plugin...")

    app = sd.getContext().getSDApplication()
    uiMgrQt = app.getQtForPythonUIMgr()
    pkgMgr = app.getPackageMgr()

    callbackId = uiMgrQt.registerGraphViewCreatedCallback(partial(onGraphViewCreated, uiMgrQt=uiMgrQt, pkgMgr=pkgMgr))
    CALLBACK_IDS.append(callbackId)

def uninitializeSDPlugin():
    global CALLBACK_IDS

    getLogger().info("Uninitializing 'Presets from CSV' plugin...")

    app = sd.getContext().getSDApplication()
    uiMgrSd = app.getUIMgr()

    for callbackId in CALLBACK_IDS:
        uiMgrSd.unregisterGraphViewCreatedCallback(callbackId)
    CALLBACK_IDS.clear()

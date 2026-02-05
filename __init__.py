import sd
from sd.api.qtforpythonuimgrwrapper import QtForPythonUIMgrWrapper
from sd.api.sdpackagemgr import SDPackageMgr
from sd.api.sdgraph import SDGraph

from functools import partial

from .utilities import getLogger
from .ui import toolbarIconFactory
from .presetFromCSV import PresetsFromCSVToolbar
from .ui_strings import UIStr_toolbarToggleTooltip

# ---

CALLBACK_IDS: list[int] = []

# ---

def onGraphViewCreated(graphViewId: int, uiMgrQt: QtForPythonUIMgrWrapper, pkgMgr: SDPackageMgr) -> None:
    graph: SDGraph = uiMgrQt.getGraphFromGraphViewID(graphViewId)
    presetToolbar = PresetsFromCSVToolbar(pkgMgr=pkgMgr, graph=graph)
    toolbarIcon = toolbarIconFactory()
    uiMgrQt.addToolbarToGraphView(graphViewId, presetToolbar, toolbarIcon, UIStr_toolbarToggleTooltip)

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

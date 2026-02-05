from PySide6 import QtWidgets
from PySide6.QtWidgets import QToolBar
from sd.api.sdpackagemgr import SDPackageMgr
from sd.api.sdgraph import SDGraph
from .utilities import getLogger

# ---

class PresetsFromCSVToolbar(QToolBar):
    def __init__(self, pkgMgr: SDPackageMgr, graph: SDGraph):
        super().__init__()
        self.setObjectName("PresetsFromCSVToolbar")
        self.__pkgMgr = pkgMgr
        self.graph = graph
        self.package = self.graph.getPackage()

        # Add actions or widgets to the toolbar as needed
        # For example, you can add a button to load presets from a CSV file
        createPresetsAction = QtWidgets.QAction("Load Presets from CSV", self)
        createPresetsAction.triggered.connect(self.createPresetsFromCSV)
        self.addAction(createPresetsAction)

    def createPresetsFromCSV(self):
        # Implement the logic to load presets from a CSV file
        # This is just a placeholder function
        getLogger().info("Creating presets from CSV...")

    def getCSVResourceFilePath(self, resourcePkgPath) -> str | None:
        resource = self.package.findResourceFromUrl(resourcePkgPath)
        if not resource:
            getLogger().warning("Resource not found:", resourcePkgPath)
            return None
        resourceFilePath: str = resource.getFilePath()
        if resourceFilePath.endswith(".csv"):
            return resourceFilePath
        else:
            getLogger().warning("Resource is not a CSV file:", resourcePkgPath)
            return None

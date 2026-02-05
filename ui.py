from PySide6.QtGui import QIcon

from .ui_strings import *

# ---

def toolbarIconFactory() -> QIcon:
    # Create a simple icon for the toolbar toggle button
    # In a real implementation, you would load an actual icon file
    icon = QIcon()
    return icon

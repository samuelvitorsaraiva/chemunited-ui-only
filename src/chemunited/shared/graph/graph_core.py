from PyQt5.QtWidgets import (
    QGraphicsView,
)
from PyQt5.QtGui import QPixmap, QCursor, QPainter
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from .scene_core import SceneCore
from typing import TYPE_CHECKING, Any
from chemunited.shared.enums import SetupStepMode


class GraphCore(QGraphicsView):
    MODE: SetupStepMode = SetupStepMode.DESIGN    
    
    def __init__(self, scene: SceneCore | None = None, parent=None):
        super().__init__(parent)
        if scene is None:
            self.scene_attribute = SceneCore(self)
        else:
            self.scene_attribute = scene
        self.setScene(self.scene_attribute)

    # === Mouse Events ===
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        # Control zoom functionality
        super().wheelEvent(event)

    def contextMenuEvent(self, event):
        # Show custom right-click menus
        super().contextMenuEvent(event)

    # === Keyboard Events ===
    def keyPressEvent(self, event):
        # Handle key downs
        super().keyPressEvent(event)
        
    def keyReleaseEvent(self, event):
        # Handle key ups
        super().keyReleaseEvent(event)

    # === Rendering ===
    def drawBackground(self, painter: QPainter, rect):
        # Customize the background (e.g. to draw a grid lattice layout)
        super().drawBackground(painter, rect)

    # === Utility ===
    def recenter_view(self):
        """
        Centralize the view according to the items currently present in the scene.
        """
        if self.scene():
            # Get the bounding box of all items
            items_rect = self.scene().itemsBoundingRect()
            
            # Optionally update the scene dimensions to match
            self.scene().setSceneRect(items_rect)
            
            # Fit the view to this rect, maintaining aspect ratio
            self.fitInView(items_rect, Qt.KeepAspectRatio)
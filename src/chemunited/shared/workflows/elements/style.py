from qfluentwidgets import isDarkTheme
from enum import StrEnum
from PyQt5.QtGui import QColor


class WorkflowColorStyle(StrEnum):
    CONTOUR_DARK = "RGB(29, 29, 29)"
    SOLID_DARK = "RGB(45, 45, 45)"
    EVIDENCE_DARK = "RGB(249, 249, 249)"

    CONTOUR_DARK_BRIGHTER = "RGB(100, 100, 100)"
    SOLID_DARK_BRIGHTER = "RGB(130, 130, 130)"

    CONTOUR_LIGHT = "RGB(200, 200, 200)"
    SOLID_LIGHT = "RGB(229, 229, 229)"
    EVIDENCE_LIGHT = "RGB(39, 39, 39)"

    CONTOUR_LIGHT_DARKER = "RGB(170, 170, 170)"
    SOLID_LIGHT_DARKER = "RGB(130, 130, 130)"
    
    @classmethod
    def solid(cls) -> QColor:
        return QColor(cls.SOLID_DARK if isDarkTheme() else cls.SOLID_LIGHT)
    
    @classmethod
    def contour(cls) -> QColor:
        return QColor(cls.CONTOUR_DARK if isDarkTheme() else cls.CONTOUR_LIGHT)

    @classmethod
    def contour_brighter(cls) -> QColor:
        return QColor(cls.CONTOUR_DARK_BRIGHTER if isDarkTheme() else cls.CONTOUR_LIGHT_DARKER)
    
    @classmethod
    def solid_brighter(cls) -> QColor:
        return QColor(cls.SOLID_DARK_BRIGHTER if isDarkTheme() else cls.SOLID_LIGHT_DARKER)
    
    @classmethod
    def evidence(cls) -> QColor:
        return QColor(cls.EVIDENCE_DARK if isDarkTheme() else cls.EVIDENCE_LIGHT)
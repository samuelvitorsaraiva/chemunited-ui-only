"""Minimal single-window harness for BaseModeEditorWidget.

Run from the chemunited-ui-only root:

    python -m chemunited.shared.widgets.base_mode_editor.simple_example

Model covers every card type in one small form so any flash can be attributed
to a specific card rather than the full ProcessParameters model.
"""

from __future__ import annotations

import sys
from typing import Annotated

from PyQt5.QtWidgets import QApplication, QMainWindow
from pydantic import BaseModel, Field
from qfluentwidgets import setTheme, Theme

from chemunited_core.utils import ChemQuantityValidator, ChemUnitQuantity

from chemunited.shared.widgets.base_mode_editor import BaseModeEditorWidget


class SimpleModel(BaseModel):
    name: Annotated[str, Field(
        default="test",
        title="Name",
        description="A short label.",
        min_length=1,
        json_schema_extra={"group": "Basic"},
    )]
    count: Annotated[int, Field(
        default=3,
        ge=1,
        le=10,
        title="Count",
        json_schema_extra={"group": "Basic"},
    )]
    ratio: Annotated[float, Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        title="Ratio",
        json_schema_extra={"group": "Basic", "step": 0.05},
    )]
    enabled: Annotated[bool, Field(
        default=True,
        title="Enabled",
        json_schema_extra={"group": "Flags"},
    )]
    mode: Annotated[str, Field(
        default="A",
        title="Mode",
        json_schema_extra={"group": "Flags", "Options": ["A", "B", "C"]},
    )]
    tags: Annotated[list[str], Field(
        default_factory=lambda: ["alpha", "beta"],
        title="Tags",
        json_schema_extra={"group": "Lists"},
    )]
    volume: Annotated[ChemUnitQuantity, ChemQuantityValidator("ml"), Field(
        default=ChemUnitQuantity("5 ml"),
        title="Volume",
        json_schema_extra={"group": "Quantities"},
    )]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)

    window = QMainWindow()
    window.setWindowTitle("BaseModeEditorWidget — simple example")
    window.resize(520, 700)

    editor = BaseModeEditorWidget(
        SimpleModel,
        instance=SimpleModel(),
        parent=window,
    )
    window.setCentralWidget(editor)

    editor.saved.connect(lambda m: print("[saved]", m.model_dump_json(indent=2)))
    editor.cancelled.connect(lambda: print("[cancelled]"))

    window.show()
    sys.exit(app.exec())

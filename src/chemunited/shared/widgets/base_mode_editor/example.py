"""Example exercising all BaseModeEditorWidget capabilities.

Run from the chemunited-ui-only root:

    python -m chemunited.shared.widgets.base_mode_editor.example

Covers:
  - All seven card types (str, bool, int, float, choice, list, quantity)
  - Ge / Le / MinLen / MaxLen constraints surfaced as validation errors
  - Group separators via json_schema_extra["group"]
  - visible=False  — card absent from the scroll area
  - editable=False — card present but greyed out
  - Pre-populated instance passed at construction
  - save() — emits patched model, printed to the result panel
  - cancel() — resets cards to the original instance values
"""

from __future__ import annotations

import sys
from typing import Annotated

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget
from pydantic import BaseModel, Field
from qfluentwidgets import BodyLabel, CardWidget, SmoothScrollArea, StrongBodyLabel

from chemunited_core.utils import ChemQuantityValidator, ChemUnitQuantity

from chemunited.shared.widgets.base_mode_editor import BaseModeEditorWidget


# ---------------------------------------------------------------------------
# Comprehensive Pydantic model — one field per card type
# ---------------------------------------------------------------------------

class ProcessParameters(BaseModel):
    """Full demonstration model; every field exercises a different card type."""

    # ── Identification ──────────────────────────────────────────────────────

    experiment_name: Annotated[str, Field(
        default="Run-01",
        title="Experiment name",
        description="Human-readable label for this run.",
        min_length=3,
        max_length=64,
        json_schema_extra={"group": "Identification"},
    )]

    operator: Annotated[str, Field(
        default="",
        title="Operator",
        description="Name of the person running this experiment.",
        json_schema_extra={"group": "Identification"},
    )]

    # ── Reactor settings ────────────────────────────────────────────────────

    reactor_volume: Annotated[ChemUnitQuantity, ChemQuantityValidator("ml"), Field(
        default=ChemUnitQuantity("10 ml"),
        title="Reactor volume",
        description="Internal volume of the reactor.",
        json_schema_extra={"group": "Reactor"},
    )]

    residence_time: Annotated[ChemUnitQuantity, ChemQuantityValidator("s"), Field(
        default=ChemUnitQuantity("60 s"),
        title="Residence time",
        description="Target mean residence time.",
        json_schema_extra={"group": "Reactor"},
    )]

    back_pressure: Annotated[ChemUnitQuantity, ChemQuantityValidator("bar"), Field(
        default=ChemUnitQuantity("2 bar"),
        title="Back pressure",
        description="Setpoint for the back-pressure regulator.",
        json_schema_extra={"group": "Reactor"},
    )]

    flow_rate: Annotated[ChemUnitQuantity, ChemQuantityValidator("ml/min"), Field(
        default=ChemUnitQuantity("1 ml/min"),
        title="Flow rate",
        description="Pump flow rate setpoint.",
        json_schema_extra={"group": "Reactor"},
    )]

    # ── Run parameters ──────────────────────────────────────────────────────

    repetitions: Annotated[int, Field(
        default=3,
        ge=1,
        le=20,
        title="Repetitions",
        description="How many times to repeat the run.",
        json_schema_extra={"group": "Run parameters"},
    )]

    sample_interval: Annotated[float, Field(
        default=0.5,
        ge=0.1,
        le=60.0,
        title="Sample interval (s)",
        description="Time between data-point recordings.",
        json_schema_extra={"group": "Run parameters", "step": 0.1},
    )]

    collect_samples: Annotated[bool, Field(
        default=True,
        title="Collect samples",
        description="Enable automatic fraction collection.",
        json_schema_extra={"group": "Run parameters"},
    )]

    # ── Analysis ────────────────────────────────────────────────────────────

    detection_mode: Annotated[str, Field(
        default="UV",
        title="Detection mode",
        description="Primary analytical channel.",
        json_schema_extra={
            "group": "Analysis",
            "Options": ["UV", "MS", "NMR", "IR", "Conductivity"],
        },
    )]

    wavelengths: Annotated[list[float], Field(
        default_factory=lambda: [254.0, 280.0],
        title="UV wavelengths (nm)",
        description="Wavelengths to record when UV detection is active.",
        json_schema_extra={"group": "Analysis"},
    )]

    target_compounds: Annotated[list[str], Field(
        default_factory=lambda: ["product", "starting_material"],
        title="Target compounds",
        description="Compound names expected in the chromatogram.",
        json_schema_extra={"group": "Analysis"},
    )]

    # ── Notifications ────────────────────────────────────────────────────────

    notify_on_completion: Annotated[bool, Field(
        default=False,
        title="Notify on completion",
        json_schema_extra={"group": "Notifications"},
    )]

    # hidden field — card must not appear in the scroll area
    _schema_version: Annotated[str, Field(
        default="1.0",
        title="Schema version",
        json_schema_extra={"group": "Notifications", "visible": False},
    )] = "1.0"

    # read-only field — card appears but is greyed out
    instrument_id: Annotated[str, Field(
        default="SYN-01",
        title="Instrument ID",
        description="Fixed instrument identifier (read-only).",
        json_schema_extra={"group": "Notifications", "editable": False},
    )]


# ---------------------------------------------------------------------------
# Pre-populated instance
# ---------------------------------------------------------------------------

INITIAL = ProcessParameters(
    experiment_name="Suzuki-A01",
    operator="A. Chemist",
    reactor_volume=ChemUnitQuantity("5 ml"),
    residence_time=ChemUnitQuantity("120 s"),
    back_pressure=ChemUnitQuantity("3 bar"),
    flow_rate=ChemUnitQuantity("0.5 ml/min"),
    repetitions=5,
    sample_interval=1.0,
    collect_samples=True,
    detection_mode="UV",
    wavelengths=[254.0, 310.0],
    target_compounds=["product", "byproduct"],
    notify_on_completion=True,
    instrument_id="SYN-01",
)


# ---------------------------------------------------------------------------
# Simple result panel
# ---------------------------------------------------------------------------

class _ResultPanel(CardWidget):
    """Displays the last saved model instance as pretty-printed JSON."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        scroll = SmoothScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.enableTransparentBackground()

        inner = QWidget(scroll)
        from PyQt5.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

        self._heading = StrongBodyLabel("Saved model")
        layout.addWidget(self._heading)

        self._body = BodyLabel("(press Save to see the emitted instance)")
        self._body.setWordWrap(True)
        self._body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._body)

        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def show_model(self, instance: BaseModel) -> None:
        self._heading.setText(f"Saved — {type(instance).__name__}")
        self._body.setText(instance.model_dump_json(indent=2))

    def show_cancelled(self) -> None:
        self._heading.setText("Cancelled")
        self._body.setText("Editor was reset to the original values.")


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class DemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BaseModeEditorWidget — full capability demo")
        self.resize(1100, 760)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left: editor — pass central as parent so it is never a top-level window
        self._editor = BaseModeEditorWidget(
            ProcessParameters,
            instance=INITIAL,
            parent=central,
        )
        layout.addWidget(self._editor, stretch=3)

        # Right: result panel — same reason
        self._result = _ResultPanel(central)
        layout.addWidget(self._result, stretch=2)

        self._editor.saved.connect(self._on_saved)
        self._editor.cancelled.connect(self._on_cancelled)

    def _on_saved(self, instance: ProcessParameters) -> None:
        print("[saved]", instance.model_dump_json(indent=2))
        self._result.show_model(instance)

    def _on_cancelled(self) -> None:
        print("[cancelled]")
        self._result.show_cancelled()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec())

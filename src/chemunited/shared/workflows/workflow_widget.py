from chemunited.shared.workflows.workflow_frames import WorkflowGraph
from chemunited.shared.workflows.process_workflow import ProcessWorkflow
from chemunited.shared.enums import WindowCategory
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from qfluentwidgets import StrongBodyLabel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chemunited.ui.GuiSetup import GuiSetup


class WorkflowsWidget(QWidget):

    def __init__(self, parent: "GuiSetup | None" = None, window: WindowCategory = WindowCategory.SETUP):
        super().__init__(parent=parent)
        self._parent = parent
        self._window = window
        self.workflows: dict[str, WorkflowGraph] = {}
        self.actual_process: str = ""
        self.label_process = StrongBodyLabel(text="")
        self.__build_ui()

    def __getitem__(self, item) -> "WorkflowGraph | None":
        return self.workflows.get(item, None)

    def clearWorkflows(self):
        """Clear completely and properly delete old graph widgets to free memory"""
        for item in self.workflows.values():
            item.clear_workflow()
            self.stacked_graphs.removeWidget(item)
            item.deleteLater()
        self.workflows.clear()
        self.select_process(None)

    def recenter_view(self):
        for wf in self.workflows.values():
            wf.recenter_view()

    def __build_ui(self):
        self.vBoxlayout = QVBoxLayout(self)
        self.vBoxlayout.setSpacing(0)
        self.vBoxlayout.setContentsMargins(0, 0, 0, 0)

        # Top Button Toolbar Placeholder
        self.widget_buttons = QWidget()
        self.vBoxlayout.addWidget(self.widget_buttons)
        self.hBoxLayoutButtons = QHBoxLayout(self.widget_buttons)
        self.hBoxLayoutButtons.setSpacing(0)
        self.hBoxLayoutButtons.setContentsMargins(0, 0, 0, 0)

        # Process Label Header
        font = QFont()
        font.setBold(True)
        self.label_process.setFont(font)
        self.label_process.setTextColor("#1B5E20", "#BDCDBE")
        self.vBoxlayout.addWidget(
            self.label_process, alignment=Qt.AlignHCenter  # type: ignore[attr-defined]
        )

        # The core stacked widget natively handling visual switching
        self.stacked_graphs = QStackedWidget(self)
        self.vBoxlayout.addWidget(self.stacked_graphs)
        self.vBoxlayout.setStretchFactor(self.stacked_graphs, 1)

    def add_process(self, name: str, graph: ProcessWorkflow):
        # Guard clause in case a workflow of the same name already exists
        if name in self.workflows:
            self.remove_process(name)

        self.workflows[name] = WorkflowGraph(
            parent=self._parent, 
            graph=graph,
            window_container=self._window
        )
        self.stacked_graphs.addWidget(self.workflows[name])
        self.select_process(name)

    def rename_process(self, name: str, new_name: str):
        if name not in self.workflows:
            return
            
        self.workflows[new_name] = self.workflows.pop(name)
        self.workflows[new_name].graph.rename_process(new_name)
        
        # Keep label updated if we just renamed the active screen
        if self.actual_process == name:
            self.actual_process = new_name
            self.label_process.setText(new_name)

    def remove_process(self, name: str):
        if name not in self.workflows:
            return
            
        graph_widget = self.workflows.pop(name)
        self.stacked_graphs.removeWidget(graph_widget)
        graph_widget.deleteLater() # Completely release PyQt C++ memory
        
        # If we accidentally deleted the active process, fallback to next existing process
        if self.actual_process == name:
            next_process = next(iter(self.workflows.keys()), None) if self.workflows else None
            self.select_process(next_process)

    def select_process(self, name: str | None):
        """Reroutes view instantly using QStackedWidget instead of looping .setVisible()"""
        if name is None or name not in self.workflows:
            self.stacked_graphs.hide()
            self.actual_process = ""
            self.label_process.setText("")
            return

        self.stacked_graphs.setCurrentWidget(self.workflows[name])
        self.stacked_graphs.show()
        
        self.actual_process = name
        self.label_process.setText(name)

    def closeEvent(self, event):
        if self._parent is None:
            for process_name, workflow in self.workflows.items():
                print(f"ProcessWorkflow[{process_name}]: {workflow.graph}")
                print(f"  nodes={list(workflow.graph.nodes(data=True))}")
                print(f"  edges={list(workflow.graph.edges(data=True))}")
        super().closeEvent(event)

    def clear_progress(self):
        for workflow in self.workflows.values():
            workflow.clear_progress()


if __name__ == "__main__":
    """ Example """
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    graph = ProcessWorkflow()
    window = WorkflowsWidget(parent=None, window=WindowCategory.SETUP)
    window.add_process(name="process", graph=graph)
    window.resize(920, 620)
    window.show()
    sys.exit(app.exec())

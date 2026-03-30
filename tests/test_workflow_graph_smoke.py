# ruff: noqa: E402

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

from chemunited.shared.enums import WindowCategory
from chemunited.shared.enums.protocols_enum import ProtocolBlock
from chemunited.shared.workflows.controller import WorkflowController
from chemunited.shared.workflows.process_workflow import ProcessWorkflow
from chemunited.shared.workflows.workflow_frames import WorkflowGraph


class WorkflowGraphSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = APP

    def test_graph_builds_from_controller_and_persists_editor_changes(self):
        controller = WorkflowController(ProcessWorkflow())
        graph = WorkflowGraph(
            window_container=WindowCategory.SETUP,
            controller=controller,
            parent=None,
        )

        self.assertIn("start", graph._nodes)
        self.assertIn("end", graph._nodes)

        start_node = graph._nodes["start"]
        start_node.setPos(QPointF(250.0, 260.0))
        self.app.processEvents()
        self.assertEqual(controller.model.get_block("start").pos, (250.0, 260.0))

        graph.remove_node("start")
        self.assertIn("start", controller.model)

        graph.add_block(ProtocolBlock.SCRIPT, QPointF(420.0, 260.0))
        self.app.processEvents()
        self.assertIn("script_1", graph._nodes)

        start_port = graph._nodes["start"].output_ports
        input_port = graph._nodes["script_1"].input_ports
        self.assertIsNotNone(start_port)
        self.assertIsNotNone(input_port)

        graph._handle_access_point_click(start_port)
        graph._handle_access_point_click(input_port)
        self.app.processEvents()
        self.assertTrue(controller.model.has_connection("start", "script_1"))
        self.assertIn(("start", "script_1"), graph._connections)

        connection = graph._connections[("start", "script_1")]
        connection.set_inflection_point(0, QPointF(310.0, 220.0))
        self.app.processEvents()
        self.assertEqual(
            controller.model.get_connection("start", "script_1").inflection_points,
            [(310.0, 220.0)],
        )

        graph.build_from_model()
        self.assertEqual(
            graph._connections[("start", "script_1")].inflection_points[0].x(),
            310.0,
        )


if __name__ == "__main__":
    unittest.main()

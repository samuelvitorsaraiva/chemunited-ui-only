import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt5.QtCore import QCoreApplication

from chemunited.shared.enums.protocols_enum import ProtocolBlock
from chemunited.shared.workflows.controller import WorkflowController
from chemunited.shared.workflows.exceptions import WorkflowRuleViolation
from chemunited.shared.workflows.process_workflow import ProcessWorkflow


class WorkflowControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_add_block_and_connect_emit_signals(self):
        controller = WorkflowController(ProcessWorkflow())
        events: list[tuple[str, str | tuple[str, str]]] = []

        controller.block_added.connect(lambda name: events.append(("block_added", name)))
        controller.connection_added.connect(
            lambda start, end: events.append(("connection_added", (start, end)))
        )

        block = controller.add_block(ProtocolBlock.SCRIPT, (400.0, 300.0))
        controller.connect_nodes("start", block.name, "right")

        self.assertIn(("block_added", block.name), events)
        self.assertIn(("connection_added", ("start", block.name)), events)
        self.assertTrue(controller.model.has_connection("start", block.name))

    def test_protected_block_removal_raises(self):
        controller = WorkflowController(ProcessWorkflow())

        with self.assertRaises(WorkflowRuleViolation):
            controller.remove_block("start")


if __name__ == "__main__":
    unittest.main()

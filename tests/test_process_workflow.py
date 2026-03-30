import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chemunited.shared.enums.protocols_enum import ProtocolBlock
from chemunited.shared.workflows.exceptions import WorkflowRuleViolation
from chemunited.shared.workflows.process_workflow import ProcessWorkflow


class ProcessWorkflowTests(unittest.TestCase):
    def test_terminal_blocks_exist_and_are_protected(self):
        workflow = ProcessWorkflow()

        self.assertIn("start", workflow)
        self.assertIn("end", workflow)
        self.assertTrue(workflow.is_protected_block("start"))
        self.assertTrue(workflow.is_protected_block("end"))

    def test_terminal_blocks_are_movable_but_not_removable(self):
        workflow = ProcessWorkflow()

        workflow.move_block("start", (321.0, 654.0))
        self.assertEqual(workflow.get_block("start").pos, (321.0, 654.0))

        with self.assertRaises(WorkflowRuleViolation):
            workflow.remove_block("start")

    def test_add_remove_move_block_updates_model_state(self):
        workflow = ProcessWorkflow(process="demo")
        workflow.add_block(
            name="script_1",
            pos=(10.0, 20.0),
            block_tag=ProtocolBlock.SCRIPT,
            call_function="main",
        )
        workflow.move_block("script_1", (30.0, 40.0))

        block = workflow.get_block("script_1")
        self.assertIsNotNone(block)
        self.assertEqual(block.pos, (30.0, 40.0))
        self.assertEqual(block.call_function, "main")

        topology = workflow.as_networkx()
        self.assertEqual(topology.nodes["script_1"]["pos"], (30.0, 40.0))

        workflow.remove_block("script_1")
        self.assertNotIn("script_1", workflow)

    def test_add_and_update_connection_geometry(self):
        workflow = ProcessWorkflow()
        workflow.add_block(name="script_1", pos=(10.0, 20.0))

        workflow.add_connection(
            "start",
            "script_1",
            start_role="right",
            condition=True,
        )
        workflow.update_connection_geometry(
            "start",
            "script_1",
            [(100.0, 200.0), (140.0, 220.0)],
        )

        connection = workflow.get_connection("start", "script_1")
        self.assertIsNotNone(connection)
        self.assertEqual(
            connection.inflection_points,
            [(100.0, 200.0), (140.0, 220.0)],
        )


if __name__ == "__main__":
    unittest.main()

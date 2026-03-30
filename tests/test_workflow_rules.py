import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chemunited.shared.enums.protocols_enum import ProtocolBlock
from chemunited.shared.workflows.exceptions import WorkflowRuleViolation
from chemunited.shared.workflows.workflow_rules import (
    derive_connection_attributes,
    generate_block_name,
    incoming_port_count,
    resolve_render_start_role,
    validate_connection_request,
)


class WorkflowRulesTests(unittest.TestCase):
    def test_generate_block_name_uses_block_prefix(self):
        name = generate_block_name({"script_1", "script_2"}, ProtocolBlock.SCRIPT)
        self.assertEqual(name, "script_3")

    def test_validate_connection_request_rejects_invalid_cases(self):
        with self.assertRaises(WorkflowRuleViolation):
            validate_connection_request(
                start_name="node",
                end_name="node",
                start_block_tag=ProtocolBlock.SCRIPT,
                start_role="right",
                end_role="left",
                existing_connection=False,
                has_outgoing_loopback=False,
            )

        with self.assertRaises(WorkflowRuleViolation):
            validate_connection_request(
                start_name="loop_1",
                end_name="script_1",
                start_block_tag=ProtocolBlock.LOOP,
                start_role="top",
                end_role="left",
                existing_connection=False,
                has_outgoing_loopback=True,
            )

    def test_derive_connection_attributes_for_special_blocks(self):
        loopback = derive_connection_attributes(ProtocolBlock.LOOP, "top")
        conditional = derive_connection_attributes(ProtocolBlock.IF, "top")

        self.assertTrue(loopback["loopback"])
        self.assertFalse(conditional["condition"])

    def test_incoming_port_count_ignores_loopbacks(self):
        self.assertEqual(incoming_port_count([False, True, False]), 2)

    def test_resolve_render_start_role_uses_fallbacks(self):
        self.assertEqual(
            resolve_render_start_role(
                ProtocolBlock.IF,
                start_role=None,
                loopback=False,
                trigger_on=False,
                condition=False,
            ),
            "top",
        )


if __name__ == "__main__":
    unittest.main()

from chemunited.shared.enums.protocols_enum import ProtocolBlock
from networkx import DiGraph
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path


@dataclass
class ScriptMetadata:
    name: str
    process: str
    file: Optional[str] = None
    pos: tuple[int, int] = field(default=(0, 0))
    block_tag: ProtocolBlock = ProtocolBlock.SCRIPT
    ports_numbers: int = 1
    file_path: Optional[Path] = None
    call_function: str = ""
    docstring: str = ""


class ProcessWorkflow(DiGraph):
    def __init__(self, process: str = ""):
        super().__init__()
        self._process = process
        #self.parameters: BaseModeParameters = BaseModeParameters()
        self._scripts_metadata: dict[str, ScriptMetadata] = {}

    def add_block(
        self,
        name: str,
        file: Optional[str] = None,
        pos: tuple[int, int] = (0, 0),
        block_tag: ProtocolBlock = ProtocolBlock.SCRIPT,
        ports_numbers: int = 1,
        **kwargs,
    ):
        metadata_kwargs = {
            key: kwargs[key]
            for key in ("file_path", "call_function", "docstring")
            if key in kwargs
        }
        self._scripts_metadata[name] = ScriptMetadata(
            name=name,
            process=self._process,
            file=file,
            pos=pos,
            block_tag=block_tag,
            ports_numbers=ports_numbers,
            **metadata_kwargs,
        )
        self.add_node(
            name,
            process=self._process,
            file=file,
            pos=pos,
            block_tag=block_tag,
            ports_numbers=ports_numbers,
            **kwargs,
        )

    def rename_process(self, name: str):
        self._process = name
        for mdata in self._scripts_metadata.values():
            mdata.process = name
        for node in self.nodes:
            self.nodes[node]["process"] = name

    def remove_node(self, n):
        if n in self._scripts_metadata:
            del self._scripts_metadata[n]
        return super().remove_node(n)

    def clear(self):
        self._scripts_metadata.clear()
        return super().clear()

    def get_file(self, node: str) -> str:
        return (  # type:ignore[return-value]
            self._scripts_metadata[node].file  # type:ignore[return-value]
            if self._scripts_metadata[node].file  # type:ignore[return-value]
            else ""  # type:ignore[return-value]
        )  # type:ignore[return-value]

    def get_file_path(self, node: str) -> Path:
        return (  # type:ignore[return-value]
            self._scripts_metadata[node].file_path  # type:ignore[return-value]
            if self._scripts_metadata[node].file_path  # type:ignore[return-value]
            else Path("")  # type:ignore[return-value]
        )  # type:ignore[return-value]

    def get_call_function(self, node: str):
        return self._scripts_metadata[node].call_function

    def get_docstring(self, node: str) -> str:
        return self._scripts_metadata.get(node, ScriptMetadata(node, "")).docstring

    def export_script_attributes(self, name: str):
        result = ""
        for key, value in self._scripts_metadata.get(
            name, ScriptMetadata(name, "")
        ).__dict__.items():
            if value is None or key in {"process", "file_path"}:
                continue
            if isinstance(value, str):
                value = f"'{value}'"
            result += f"{key}={value},"
        return result

    def update_attribute(self, node: str, key: str, value: Any):
        if node in self._scripts_metadata:
            setattr(self._scripts_metadata[node], key, value)
        if node in self.nodes:
            self.nodes[node][key] = value

    def get_metadata(self, node: str) -> Optional[ScriptMetadata]:
        return self._scripts_metadata.get(node)

    def iter_metadata(self):
        return self._scripts_metadata.items()

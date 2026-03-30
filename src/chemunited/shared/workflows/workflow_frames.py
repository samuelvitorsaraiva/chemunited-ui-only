from chemunited.shared.graph import GraphCore, SceneCore
from chemunited.shared.enums import SetupStepMode, WindowCategory
from chemunited.shared.enums.protocols_enum import ProtocolBlock
from chemunited.shared.icon import OrchestratorIcon
from chemunited.shared.workflows.process_workflow import ProcessWorkflow

from chemunited.shared.workflows.elements.work_node import WorkflowNode
from chemunited.shared.workflows.elements.work_connection import WorkflowConnection
from chemunited.shared.workflows.elements.access_point import WorkflowAccessPoints

from PyQt5.QtWidgets import QFrame, QGraphicsItem, QGraphicsView
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import QRectF, Qt, QPointF
from qfluentwidgets import isDarkTheme, RoundMenu, Action
from functools import partial


class WorkflowGraph(GraphCore):
    """
    A graph view for workflows.
    """
    WINDOW_CONTAINER: WindowCategory = WindowCategory.SETUP
    MODE: SetupStepMode = SetupStepMode.DESIGN
    
    TERMINAL_NODES = {
        "start": {"block_tag": ProtocolBlock.START, "pos": (200, 300)},
        "end": {"block_tag": ProtocolBlock.END, "pos": (800, 300)}
    }

    def __init__(
        self, 
        window_container: WindowCategory, 
        graph: ProcessWorkflow | None = None,
        parent=None
    ):
        super().__init__(parent)
        self.parent_ref = parent
        self.window_container = window_container
        self.scene_attribute = SceneCore(self)
        self.setScene(self.scene_attribute)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.StrongFocus) # type: ignore[attr-defined]
        
        # Make the zoom focus on the mouse pointer!
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.graph = graph if graph is not None else ProcessWorkflow()

        self._nodes: dict[str, WorkflowNode] = {}
        self._connections: dict[tuple[str, str], WorkflowConnection] = {}
        self._selected_port: WorkflowAccessPoints | None = None
        self.build_from_graph()

    def drawBackground(self, painter: QPainter, rect: QRectF):
        background = QColor(39, 39, 39) if isDarkTheme() else QColor(249, 249, 249)
        grid = QColor(255, 255, 255, 18) if isDarkTheme() else QColor(0, 0, 0, 16)
        painter.fillRect(rect, background)
        painter.setPen(QPen(grid, 1))

        step = 28
        left = int(rect.left()) - (int(rect.left()) % step)
        top = int(rect.top()) - (int(rect.top()) % step)

        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += step

        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += step

    def wheelEvent(self, event):
        zoom_factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self.scale(zoom_factor, zoom_factor)

    def doubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, WorkflowNode):
            self._handle_node_double_click(item)
            event.accept()
            return
        super().doubleClickEvent(event)

    def _handle_node_double_click(self, node: WorkflowNode):
        if self.window_container != WindowCategory.SETUP:
            return

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.LeftButton:  # type: ignore[attr-defined]
            item = self.itemAt(event.pos())
            access_point = self._resolve_access_point_target(item)
            if access_point is not None:
                self._handle_access_point_click(access_point)
                event.accept()
                return
            if self._selected_port:
                self._clear_selected_port()

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self.window_container != WindowCategory.SETUP:
            return
        if event.key() == Qt.Key_Delete:  # type: ignore[attr-defined]
            if self._delete_selected_items():
                event.accept()
                return
            if self._selected_port:
                self._clear_selected_port()
                event.accept()
                return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        if self.window_container != WindowCategory.SETUP:
            super().contextMenuEvent(event)
            return
        item = self.itemAt(event.pos())
        context_target = self._resolve_context_target(item)

        if isinstance(context_target, WorkflowNode):
            self._build_node_menu(context_target).exec(event.globalPos())
            event.accept()
            return

        if isinstance(context_target, WorkflowConnection):
            self._build_connection_menu(context_target).exec(event.globalPos())
            event.accept()
            return

        if not item:
            scene_pos = self.mapToScene(event.pos())
            self._build_add_menu(scene_pos).exec(event.globalPos())
            event.accept()
            return
        super().contextMenuEvent(event)

    def _build_add_menu(self, scene_pos: QPointF) -> RoundMenu:
        menu = RoundMenu(parent=self)

        actions = (
            ("Add Script", ProtocolBlock.SCRIPT, OrchestratorIcon.PYTHON.icon()),
            ("Add Loop", ProtocolBlock.LOOP, OrchestratorIcon.LOOP.icon()),
            ("Add Conditional", ProtocolBlock.IF, OrchestratorIcon.IF.icon()),
        )
        for text, block_tag, icon in actions:
            action = Action(self)
            action.setText(text)
            action.setIcon(icon)
            action.triggered.connect(partial(self.add_block, block_tag, scene_pos))
            menu.addAction(action)

        return menu

    def _build_node_menu(self, node: WorkflowNode) -> RoundMenu:
        menu = RoundMenu(parent=self)

        delete_action = Action(self)
        delete_action.setText("Delete block")
        delete_action.setIcon(OrchestratorIcon.TRASH.icon())
        delete_action.setEnabled(not node.is_terminal)
        delete_action.triggered.connect(partial(self.remove_node, node.node_name))
        menu.addAction(delete_action)

        return menu

    def _build_connection_menu(self, connection: WorkflowConnection) -> RoundMenu:
        menu = RoundMenu(parent=self)

        add_second_action = Action(self)
        add_second_action.setText(
            "Add inflection point"
            if not connection.inflection_points
            else "Add second inflection point"
        )
        add_second_action.setEnabled(len(connection.inflection_points) < 2)
        add_second_action.triggered.connect(connection.add_inflection_point)
        menu.addAction(add_second_action)

        remove_second_action = Action(self)
        remove_second_action.setText("Remove second inflection point")
        remove_second_action.setEnabled(len(connection.inflection_points) == 2)
        remove_second_action.triggered.connect(connection.remove_last_inflection_point)
        menu.addAction(remove_second_action)

        reset_action = Action(self)
        reset_action.setText("Reset inflection points")
        reset_action.setEnabled(bool(connection.inflection_points))
        reset_action.triggered.connect(connection.clear_inflection_points)
        menu.addAction(reset_action)

        delete_action = Action(self)
        delete_action.setText("Delete connection")
        delete_action.setIcon(OrchestratorIcon.TRASH.icon())
        delete_action.triggered.connect(
            partial(self.remove_connection, connection.start_node, connection.end_node)
        )
        menu.addAction(delete_action)

        return menu

    def _resolve_context_target(
        self, item: QGraphicsItem | None
    ) -> WorkflowNode | WorkflowConnection | None:
        current_item = item
        while current_item is not None:
            if isinstance(current_item, (WorkflowNode, WorkflowConnection)):
                return current_item
            current_item = current_item.parentItem()
        return None

    def _resolve_access_point_target(
        self, item: QGraphicsItem | None
    ) -> WorkflowAccessPoints | None:
        current_item = item
        while current_item is not None:
            if isinstance(current_item, WorkflowAccessPoints):
                return current_item
            current_item = current_item.parentItem()
        return None

    def build_from_graph(self):
        self._ensure_terminal_nodes()
        self._clear_scene_objects()

        for name, metadata in self.graph.iter_metadata():
            self._add_node_from_graph(
                name=name,
                block_tag=metadata.block_tag,
                pos=metadata.pos,
                ports_numbers=metadata.ports_numbers,
            )

        for start, end, data in self.graph.edges(data=True):
            start_port = self._resolve_start_port(self._nodes.get(start), data)
            end_node = self._nodes.get(end)
            end_port = end_node.input_ports if end_node else None
            if start_port and end_port:
                self._create_connection(
                    start_port,
                    end_port,
                    mirror_graph=False,
                    edge_data=dict(data),
                    inflection_points=data.get("inflection_points"),
                    bend_point=data.get("bend_point"),
                )

    def _clear_scene_objects(self):
        self.scene_attribute.clear()
        self._nodes = {}
        self._connections = {}
        self._selected_port = None

    def _display_text(self, name: str, block_tag: ProtocolBlock) -> tuple[str, str]:
        labels = {
            ProtocolBlock.START: ("Start", "Entry"),
            ProtocolBlock.END: ("End", "Exit"),
            ProtocolBlock.SCRIPT: (name, "Module"),
            ProtocolBlock.LOOP: (name, "Repeat"),
            ProtocolBlock.IF: (name, "Branch"),
        }
        return labels[block_tag]

    def _ensure_terminal_nodes(self):
        for node_name, config in self.TERMINAL_NODES.items():
            metadata = self.graph.get_metadata(node_name)
            pos = config["pos"]
            if node_name in self.graph:
                pos = self.graph.nodes[node_name].get("pos", pos)
            if metadata is None:
                self.graph.add_block(name=node_name, pos=pos, block_tag=config["block_tag"])

    def _delete_selected_items(self) -> bool:
        selected_nodes: set[str] = set()
        selected_connections: set[tuple[str, str]] = set()

        for item in self.scene_attribute.selectedItems():
            target = self._resolve_context_target(item)
            if isinstance(target, WorkflowNode):
                selected_nodes.add(target.node_name)
            elif isinstance(target, WorkflowConnection):
                selected_connections.add((target.start_node, target.end_node))

        if not selected_nodes and not selected_connections:
            return False

        for start_node, end_node in selected_connections:
            self.remove_connection(start_node, end_node)

        for node_name in selected_nodes:
            self.remove_node(node_name)

        return True

    def _generate_block_name(self, block_tag: ProtocolBlock) -> str:
        prefix = {
            ProtocolBlock.SCRIPT: "script",
            ProtocolBlock.LOOP: "loop",
            ProtocolBlock.IF: "conditional",
        }[block_tag]
        index = 1
        while f"{prefix}_{index}" in self.graph:
            index += 1
        return f"{prefix}_{index}"

    def _add_node_from_graph(
        self,
        name: str,
        block_tag: ProtocolBlock,
        pos: tuple[int, int] | tuple[float, float],
        ports_numbers: int = 1,
    ) -> WorkflowNode:
        title, subtitle = self._display_text(name, block_tag)
        node = WorkflowNode(
            node_name=name,
            block_tag=block_tag,
            title=title,
            subtitle=subtitle,
            ports_numbers=ports_numbers,
        )
        node.setPos(QPointF(*pos))
        self.scene_attribute.addItem(node)
        self._nodes[name] = node
        self._sync_input_ports(name)
        return node

    def add_block(
        self,
        block_tag: ProtocolBlock,
        scene_pos: QPointF,
        ports_numbers: int = 1,
    ):
        name = self._generate_block_name(block_tag)
        pos = (scene_pos.x(), scene_pos.y())
        self.graph.add_block(name=name, pos=pos, block_tag=block_tag, ports_numbers=ports_numbers)
        self._add_node_from_graph(
            name=name,
            block_tag=block_tag,
            pos=pos,
            ports_numbers=ports_numbers,
        )

    def _handle_access_point_click(self, port: WorkflowAccessPoints):
        if self.window_container != WindowCategory.SETUP:
            return
        if self._selected_port is None:
            if port.can_start_connection:
                self._set_selected_port(port)
            return

        if port is self._selected_port:
            self._clear_selected_port()
            return

        if port.can_start_connection:
            self._set_selected_port(port)
            return

        if not port.can_end_connection:
            self._clear_selected_port()
            return

        if self._selected_port.node is port.node:
            self._clear_selected_port()
            return

        if self._has_connection(self._selected_port, port):
            self._clear_selected_port()
            return

        if self._is_loopback_port(self._selected_port) and self._has_outgoing_loopback(
            self._selected_port.node.node_name
        ):
            self._clear_selected_port()
            return

        self._create_connection(self._selected_port, port, mirror_graph=True)
        self._clear_selected_port()

    def _set_selected_port(self, port: WorkflowAccessPoints):
        if self.window_container != WindowCategory.SETUP:
            return
        if self._selected_port:
            self._selected_port.set_selected(False)
        self._selected_port = port
        self._selected_port.set_selected(True)

    def _clear_selected_port(self):
        if self._selected_port:
            self._selected_port.set_selected(False)
        self._selected_port = None

    def _is_loopback_port(self, port: WorkflowAccessPoints) -> bool:
        node = port.node
        return (
            node is not None
            and node.block_tag == ProtocolBlock.LOOP
            and port.role in {"top", "bottom"}
        )

    def _has_outgoing_loopback(self, node_name: str) -> bool:
        if node_name not in self.graph:
            return False
        return any(
            data.get("loopback") is True
            for _, _, data in self.graph.out_edges(node_name, data=True)
        )

    def _has_connection(
        self, start_port: WorkflowAccessPoints, end_port: WorkflowAccessPoints
    ) -> bool:
        key = (start_port.node.node_name, end_port.node.node_name)
        return key in self._connections

    def _edge_metadata_for_port(
        self, start_port: WorkflowAccessPoints
    ) -> dict[str, object]:
        metadata: dict[str, object] = {"start_role": start_port.role}
        node = start_port.node
        block_tag = node.block_tag if node else None

        if block_tag == ProtocolBlock.LOOP and start_port.role in {"top", "bottom"}:
            metadata["loopback"] = True
            metadata["trigger_on"] = False
            return metadata

        if block_tag == ProtocolBlock.IF:
            metadata["condition"] = start_port.role != "top"
            return metadata

        metadata["condition"] = True
        return metadata

    def _create_connection(
        self,
        start_port: WorkflowAccessPoints,
        end_port: WorkflowAccessPoints,
        mirror_graph: bool,
        edge_data: dict[str, object] | None = None,
        inflection_points: list[tuple[float, float] | QPointF] | None = None,
        bend_point: tuple[float, float] | QPointF | None = None,
    ) -> WorkflowConnection:
        payload = dict(edge_data or self._edge_metadata_for_port(start_port))
        payload.setdefault("start_role", start_port.role)
        connection = WorkflowConnection(
            start_port,
            end_port,
            inflection_points=inflection_points,
            bend_point=bend_point,
            edge_data=payload,
        )
        key = (connection.start_node, connection.end_node)
        self._connections[key] = connection
        self.scene_attribute.addItem(connection)
        connection.updateConnection()
        if mirror_graph and not self.graph.has_edge(connection.start_node, connection.end_node):
            self.graph.add_edge(connection.start_node, connection.end_node, **payload)
        self.sync_connection_inflection_points(connection)
        self._sync_input_ports(connection.end_node)
        return connection

    def _incoming_edge_count(self, node_name: str) -> int:
        if node_name not in self.graph:
            return 0
        return sum(
            1
            for _, _, data in self.graph.in_edges(node_name, data=True)
            if data.get("loopback") is not True
        )

    def _sync_input_ports(self, node_name: str):
        node = self._nodes.get(node_name)
        if node is None:
            return
        node.set_input_port_count(max(1, self._incoming_edge_count(node_name)))
        self.update_connections()

    def remove_connection(self, start_node: str, end_node: str):
        connection = self._connections.pop((start_node, end_node), None)
        if connection is None:
            return

        self.scene_attribute.removeItem(connection)
        if self.graph.has_edge(start_node, end_node):
            self.graph.remove_edge(start_node, end_node)
        self._sync_input_ports(end_node)

    def remove_node(self, node_name: str):
        node = self._nodes.get(node_name)
        if node is None:
            return

        if node.is_terminal:
            return

        if self._selected_port and self._selected_port.node is node:
            self._clear_selected_port()

        attached_connections = [
            key for key in list(self._connections) if node_name in key
        ]
        for start_node, end_node in attached_connections:
            self.remove_connection(start_node, end_node)

        self.scene_attribute.removeItem(node)
        del self._nodes[node_name]

        if node_name in self.graph:
            self.graph.remove_node(node_name)

    def _resolve_start_port(
        self,
        node: WorkflowNode | None,
        edge_data: dict,
    ) -> WorkflowAccessPoints | None:
        if node is None:
            return None
        start_role = edge_data.get("start_role")
        if start_role == "top":
            return node.top_ports
        if start_role == "bottom":
            return node.bottom_ports
        if start_role == "right" and node.output_ports:
            return node.output_ports

        if edge_data.get("loopback") is True:
            trigger_on = bool(edge_data.get("trigger_on", False))
            if trigger_on and node.top_ports:
                return node.top_ports
            if not trigger_on and node.bottom_ports:
                return node.bottom_ports
            return node.top_ports or node.bottom_ports or node.output_ports

        if node.block_tag == ProtocolBlock.IF:
            condition = bool(edge_data.get("condition", True))
            if not condition and node.top_ports:
                return node.top_ports
            if condition and node.bottom_ports:
                return node.bottom_ports
            return node.top_ports or node.bottom_ports or node.output_ports

        if node.output_ports:
            return node.output_ports
        condition = edge_data.get("condition")
        if condition is False and node.top_ports:
            return node.top_ports
        if condition is True and node.bottom_ports:
            return node.bottom_ports
        return node.top_ports or node.bottom_ports

    def sync_node_position(self, node: WorkflowNode):
        self.graph.update_attribute(
            node.node_name,
            "pos",
            (node.pos().x(), node.pos().y()),
        )

    def sync_connection_inflection_points(self, connection: WorkflowConnection):
        if not self.graph.has_edge(connection.start_node, connection.end_node):
            return
        edge_data = self.graph.edges[connection.start_node, connection.end_node]
        edge_data.pop("bend_point", None)
        if not connection.inflection_points:
            edge_data.pop("inflection_points", None)
            return
        edge_data["inflection_points"] = [
            (point.x(), point.y()) for point in connection.inflection_points
        ]

    def update_connections(self):
        for connection in self._connections.values():
            connection.updateConnection()

    def start_progress(self, node_name: str):
        node = self._nodes.get(node_name)
        if node is None:
            return
        node.start_progress()

    def stop_progress(self, node_name: str):
        node = self._nodes.get(node_name)
        if node is None:
            return
        node.stop_progress()

    def clear_progress(self):
        for node in self._nodes.values():
            node.stop_progress()

    def clear_workflow(self):
        self._clear_selected_port()
        self.graph.clear()
        self.build_from_graph()

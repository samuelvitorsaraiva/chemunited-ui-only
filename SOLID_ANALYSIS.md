# SOLID Principles Analysis — chemunited-ui-only

> Conducted: 2026-03-30
> Scope: All Python files under `src/chemunited/shared/`
> Purpose: Identify structural weaknesses and prioritize the highest-value refactoring investments.

---

## 1. Single Responsibility Principle (SRP)

### Compliant
- **`ProcessWorkflow`** (`shared/workflows/process_workflow.py`): Pure graph model. Wraps NetworkX `DiGraph` with domain-specific operations. No UI code.
- **`SceneCore` / `GraphCore`** (`shared/graph/`): Clean separation — scene owns rendering setup; view owns zoom/pan interaction.
- **`FrameLoggings`** (`shared/widgets/loggings_widget.py`): Focused on log display. Well-segmented into friendly vs. developer logging modes.
- **`WorkflowColorStyle`** (`elements/style.py`): Pure color/theme lookup. Single concern.

### Violations
- **`WorkflowGraph`** (`shared/workflows/workflow_frames.py`, 610 lines) — **Critical violation**. This class simultaneously owns:
  1. Qt view rendering (inherits `GraphCore`)
  2. Mouse/keyboard/context-menu event handling
  3. Graph modification commands (add node, remove node, connect, disconnect)
  4. Visual ↔ model synchronization (`sync_node_position`, `sync_connection_inflection_points`)
  5. Node/edge factory (creates `WorkflowNode`, `WorkflowConnection`)
  6. Progress state management (`start_progress`, `stop_progress`, `clear_progress`)
  7. Background grid drawing (`drawBackground`)

  A change to connection routing and a change to the right-click menu live in the same file.

- **`WorkflowConnection`** (`elements/work_connection.py`, 596 lines): Mixes visual path rendering, Bezier/orthogonal routing math, inflection handle management, and edge label display. Routing geometry should be its own concern.

- **`WorkflowNode`** (`elements/work_node.py`, 320 lines): Mixes graphical layout (body, icon, title, subtitle stacking) with port-count business logic and progress bar lifecycle.

---

## 2. Open/Closed Principle (OCP)

### Compliant
- `ProcessWorkflow.add_block()` accepts `ProtocolBlock` enum variants — new block types are addable without changing the method signature.
- `WorkflowColorStyle` enum is extensible for new themes.

### Violations
- **`WorkflowGraph.add_block()`** contains branching logic keyed on `ProtocolBlock` values. Adding a new block type (e.g., `PARALLEL`) means editing `WorkflowGraph`, `WorkflowNode`, and `ProtocolBlock` simultaneously.
- **`WorkflowNode.__init__`** branches on `ProtocolBlock.START / END` (via `is_terminal`) to suppress input ports. This block-type-specific logic is hardcoded into the generic node class instead of being injected.
- No factory or registry pattern exists. `WorkflowGraph` directly calls `WorkflowNode(...)` and `WorkflowConnection(...)` constructors — adding a new visual representation requires modifying `WorkflowGraph`.

---

## 3. Liskov Substitution Principle (LSP)

### Compliant
- `SceneCore(QGraphicsScene)` and `GraphCore(QGraphicsView)` are proper substitutes; they add behavior without violating Qt contracts.
- `WorkflowGraph(GraphCore)` correctly overrides standard Qt extension points (`drawBackground`, `wheelEvent`, `keyPressEvent`, `contextMenuEvent`, `mousePressEvent`).
- `ProcessWorkflow(DiGraph)` preserves NetworkX semantics; `add_block` and `remove_node` delegate to super properly.

### Latent Risks
- `GraphCore.MODE` and `GraphCore.WINDOW_CONTAINER` are class-level sentinel variables with no enforcement contract. A subclass that forgets to set `MODE` silently inherits `SetupStepMode.NONE`, causing invisible behavioral differences. There is no abstract property or runtime check.
- `WorkflowNode` is not uniformly substitutable across `block_tag` variants — `START`/`END` nodes silently ignore `set_input_port_count`, which can surprise any code that holds a list of `WorkflowNode` and calls that method uniformly.

---

## 4. Interface Segregation Principle (ISP)

> No `Protocol` or `ABC` definitions exist in the codebase. All contracts are structural/implicit.

### Violations
- **`WorkflowGraph` as a fat interface**: `WorkflowsWidget` holds a `dict[str, WorkflowGraph]` and implicitly depends on the entire 610-line surface area of that class.
- **`WorkflowAccessPoints`** exposes `can_start_connection` / `can_end_connection` correctly (good), but the `node` back-reference creates bidirectional coupling: access points know about nodes, and nodes own access points.
- `WorkflowsWidget` has a `TYPE_CHECKING`-only import of `GuiSetup` — a real dependency hidden from static analysis.

---

## 5. Dependency Inversion Principle (DIP)

### Partially Compliant
- `WorkflowGraph.__init__` receives a `ProcessWorkflow` via constructor injection — the model is not fetched globally. ✓
- `WorkflowsWidget.add_process(name, graph: ProcessWorkflow)` — model injected from outside. ✓

### Violations
- **`WorkflowGraph` directly instantiates `WorkflowNode` and `WorkflowConnection`** — the canonical DIP violation. The high-level orchestrator creates its own concrete dependencies with no factory seam. Adding a `SimulationNode` subclass requires subclassing `WorkflowGraph` and overriding the factory method.
- **`WorkflowGraph` directly imports `OrchestratorIcon`** — icon selection for block types is hardcoded in the view, not injected or configured.
- **No abstraction layer between `ProcessWorkflow` and `WorkflowGraph`**: the view calls `self.graph.add_block(...)`, `self.graph.remove_node(...)` directly on the NetworkX model. A command/ViewModel layer would decouple mutation from rendering.

---

## 6. Modularity Assessment

| Component | Extractable Today? | Blocker |
|---|---|---|
| `ProcessWorkflow` | ✅ Yes | No Qt imports — usable headlessly in tests/CLI |
| `WorkflowColorStyle`, `NodeState` | ✅ Yes | Pure Python |
| `FrameLoggings` | ✅ Yes | Self-contained Qt widget |
| `WorkflowGraph` | ❌ No | Hard-coupled to concrete `WorkflowNode`/`WorkflowConnection`/`OrchestratorIcon` classes; no factory seam |
| Connection routing math | ❌ No | Bezier/orthogonal geometry buried inside `QGraphicsPathItem` — untestable without Qt |
| Instrument drivers | ⚠️ Not yet written | `connectivity/`, `execution/`, `protocols/`, `simulation/` are empty — no contract exists to prevent future coupling |

---

## Top 3 Prioritized Improvements

### #1 — Extract a `WorkflowElementFactory` (fixes DIP + OCP)

**Problem**: `WorkflowGraph` hard-constructs `WorkflowNode(block_tag, ...)` and `WorkflowConnection(...)`. Adding a new block type or visual variant requires editing the orchestration class.

**Fix**: A registry dict `{ProtocolBlock: NodeConstructor}` injected into `WorkflowGraph.__init__`. New block types register themselves; `WorkflowGraph` never needs editing.

**Benefits**:
- New block types without touching `WorkflowGraph`
- `SimulationGraph` / `ExecutionGraph` subclasses can use different visual nodes by swapping the factory
- Node creation becomes unit-testable without Qt

**Files**: `shared/workflows/workflow_frames.py` + new `shared/workflows/elements/factory.py`

```python
# sketch — elements/factory.py
from typing import Protocol, Type
from .work_node import WorkflowNode
from ..enums import ProtocolBlock

NodeCtor = Callable[[str, ProtocolBlock, str, str, int], WorkflowNode]

DEFAULT_REGISTRY: dict[ProtocolBlock, NodeCtor] = {
    ProtocolBlock.SCRIPT: WorkflowNode,
    ProtocolBlock.START:  WorkflowNode,
    ProtocolBlock.END:    WorkflowNode,
    ProtocolBlock.LOOP:   WorkflowNode,
    ProtocolBlock.IF:     WorkflowNode,
}

class WorkflowElementFactory:
    def __init__(self, registry: dict[ProtocolBlock, NodeCtor] = DEFAULT_REGISTRY):
        self._registry = registry

    def create_node(self, block_tag: ProtocolBlock, **kwargs) -> WorkflowNode:
        ctor = self._registry[block_tag]
        return ctor(**kwargs)
```

---

### #2 — Decompose `WorkflowGraph` into View + Controller (fixes SRP + ISP)

**Problem**: 610-line class conflates event handling, command execution, view sync, and grid rendering.

**Fix**: Extract `WorkflowController` that owns all graph mutation logic. `WorkflowGraph` retains only:
- Qt event methods — delegates to controller
- Visual sync (`build_from_graph`, `update_connections`, `drawBackground`)
- Progress state (purely visual)

The controller holds `ProcessWorkflow` and issues structured commands. Commands become testable without Qt and the door opens to undo/redo.

**Files**: `shared/workflows/workflow_frames.py` + new `shared/workflows/workflow_controller.py`

```python
# sketch — workflow_controller.py
class WorkflowController:
    def __init__(self, graph: ProcessWorkflow):
        self._graph = graph

    def add_block(self, block_tag: ProtocolBlock, pos: tuple, ports: int = 1) -> str:
        name = self._generate_name(block_tag)
        self._graph.add_block(name, pos=pos, block_tag=block_tag, ports_numbers=ports)
        return name

    def remove_node(self, name: str) -> None:
        self._graph.remove_node(name)

    def connect(self, source: str, target: str) -> None:
        self._graph.add_edge(source, target)
```

---

### #3 — Define `Protocol` contracts before instrument drivers land (fixes DIP + LSP)

**Problem**: `connectivity/`, `execution/`, `protocols/` are empty. When instrument drivers arrive, there is no contract to code against — they will likely be imported concretely into workflow logic, repeating the same coupling pattern seen in `WorkflowGraph`.

**Fix**: Before any driver is written, define PEP 544 `Protocol` classes.

**Files**: New `shared/protocols/instrument.py`

```python
# shared/protocols/instrument.py
from typing import Any, Protocol, runtime_checkable
from enum import Enum

class DeviceStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    DISCONNECTED = "disconnected"

@runtime_checkable
class InstrumentDriver(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def execute(self, command: str) -> Any: ...
    def status(self) -> DeviceStatus: ...

@runtime_checkable
class WorkflowExecutor(Protocol):
    def run(self, workflow: "ProcessWorkflow") -> None: ...
    def pause(self) -> None: ...
    def stop(self) -> None: ...
```

The execution engine codes against `InstrumentDriver`, not concrete classes. Simulation and real drivers are interchangeable via `isinstance(driver, InstrumentDriver)`.

---

## Verification Checklist

- [ ] **Factory**: Instantiate `WorkflowGraph` with a mock factory, assert `WorkflowNode` creation is delegated (no Qt app required).
- [ ] **Controller**: Call `WorkflowController.add_block(...)` in a pytest unit test, assert `ProcessWorkflow` state changes without running a Qt event loop.
- [ ] **Protocols**: Use `runtime_checkable` + `isinstance` to verify any new driver satisfies `InstrumentDriver` at test time.
- [ ] **Regression**: Run the full application — add/remove nodes, draw connections, verify visual sync is intact after refactoring.

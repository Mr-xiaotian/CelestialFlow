# demo/demo_network.py

> 📅 Last Updated: 2026/10/30

## Objective

Demonstrate how to use `TaskCross` to construct a multi-layer neural network topology (2→3→1 fully connected), and assign different weight parameters to each node through a closure factory function, showcasing CelestialFlow's graph expression capability in neural-network-like scenarios.

This file evolves `demo_network` in `demo_structure.py` for the first time: the operation at each node is replaced from the fixed `add_one_sleep` (`x + 1`) to a configurable linear function `y = w * x + b`, so that each node has its own weight and bias.

## Demo Content

### `demo_network_step1`

```mermaid
flowchart LR
    subgraph Input["Input Layer"]
        A1["A1<br/>y = 0.5 * x"]
        A2["A2<br/>y = 2.0 * x"]
    end
    subgraph Hidden["Hidden Layer"]
        B1["B1<br/>y = 1.0 * x"]
        B2["B2<br/>y = 1.0 * x"]
        B3["B3<br/>y = 1.0 * x"]
    end
    subgraph Output["Output Layer"]
        C["C<br/>y = 1.0 * x"]
    end

    A1 --> B1
    A1 --> B2
    A1 --> B3
    A2 --> B1
    A2 --> B2
    A2 --> B3
    B1 --> C
    B2 --> C
    B3 --> C
```

#### Construction Method

- Use `TaskCross` to build the 2-3-1 three-layer topology, `graph_mode="thread"`
- **Input layer**: `A1(x) = 0.5x`, `A2(x) = 2.0x`, each receiving different input ranges
- **Hidden layer**: `B1..B3(x) = 1.0x`, three nodes process the Fan-in results from both input layers in parallel
- **Output layer**: `C(x) = 1.0x`, aggregating all results from B1~B3
- After running, `C.get_success_pairs()` is used to collect the first 10 `(input → output)` pairs and print them; this method is only available when the node **runs standalone** (`executor.run(...))`. Under graph-level scheduling via `TaskCross.run(...)`, records go to the graph-level lifecycle store, and the node itself has no lifecycle store path, so it actually returns an empty list

#### Core Function

**`linear(w, b)`**: A closure factory function that returns `_forward(x) -> w * x + b`. It satisfies `TaskExecutor`'s constraint that `func` accepts only one positional argument; by using a closure to fix the weight and bias, no separate function needs to be defined for every weight combination.

```python
def linear(w: float, b: float):
    def _forward(x):
        return w * x + b
    return _forward
```

## Key Configuration

| Node | Function | Weight w | Bias b | max_workers | Input |
|------|------|:------:|:------:|:-----------:|------|
| A1 | `linear(0.5, 0.0)` | 0.5 | 0.0 | 2 | `[1, 2, 3, 4, 5]` |
| A2 | `linear(2.0, 0.0)` | 2.0 | 0.0 | 2 | `[11, 12, 13, 14, 15]` |
| B1~B3 | `linear(1.0, 0.0)` | 1.0 | 0.0 | 2 | Fan-in from A1/A2 |
| C | `linear(1.0, 0.0)` | 1.0 | 0.0 | 2 | Fan-in from B1~B3 |

- All Stages use `execution_mode="thread"`, and `TaskCross` as a whole uses `graph_mode="thread"`
- Output layer C calls `get_success_pairs()` after running; because this demo schedules via `TaskCross.run(...)`, the method returns an empty list (see above and "Potential Issues")

## Design Intent

This file is positioned as **Step 1**—keeping the 2-3-1 topology of `demo_network` from `demo_structure.py` unchanged, but upgrading each node's function from a fixed hard-coded operation to a parameterized linear transformation. Subsequent steps can extend on this basis:

- Activation functions (ReLU / Sigmoid)
- Sample pairing (the same input index from A1 and A2 corresponds to the same sample)
- Loss calculation and backpropagation

## Potential Issues

1. **No assertions**: This is a demo script; successful execution only means the graph construction and scheduling are correct, and does not verify the weights or computation results.
2. **No sample pairing**: A1's and A2's tasks are processed independently, and the "same original sample being processed by A1 and A2 separately and then aggregated at the same B node" pairing logic has not been implemented yet.
3. **No sleep**: The `linear` function contains no delay, so execution is very fast (microsecond-level), with no noticeable waiting like other demos.
4. **Limited result collection**: A1 (5 tasks) × 3 hidden nodes + A2 (5 tasks) × 3 hidden nodes = 30 hidden layer outputs, all of which are processed by C, but `C.get_success_pairs()` returns an empty list under graph-level scheduling, so the terminal prints "C received 0 tasks in total" and the `(input → output)` details are empty. If you need C's results, you can add `PrintObserver` to C, or switch to standalone execution / query the graph-level lifecycle store.

## How to Run

```bash
python demo/demo_network.py
```

## Expected Behavior

After running, the script prints node configuration information and the input → output mappings collected by node C:

```
─── Step 1: Each node y = w*x + b ───

  A1(x) = 0.5 * x,  Input: [1, 2, 3, 4, 5]
  A2(x) = 2.0 * x,  Input: [11, 12, 13, 14, 15]
  B1..B3(x) = 1.0 * x
  C(x) = 1.0 * x
  Running...
  C received 0 tasks in total

  C's (input → output), first 10 entries:
```

> `C received 0 tasks in total` is the actual output of the current source code under `TaskCross` graph-level scheduling: C actually processed 30 tasks, but `get_success_pairs()` only reads the node's own lifecycle store, and that path is empty under graph-level scheduling, so it returns an empty list and prints no `(input → output)` lines.
> Since all hidden nodes have a weight of 1.0, C's output values normally equal the input values (e.g., `0.5 → 0.5`).

## Dependencies

- `celestialflow` (`TaskCross`, `TaskExecutor`)

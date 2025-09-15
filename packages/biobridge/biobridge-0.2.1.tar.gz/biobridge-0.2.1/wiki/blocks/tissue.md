# Tissue Class

## Overview
The `Tissue` class simulates the behavior and properties of biological tissue, including cell growth, division, mutation, repair, and response to external factors. It is designed to model the dynamic processes of tissue metabolism, wound healing, and cancer risk.

---

## Class Definition

```python
class Tissue:
    def __init__(self, name: str, tissue_type: str, cells: Optional[List[Cell]] = None, cancer_risk: float = 0.001, mutation_rate: float = 0.05):
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name of the tissue. |
| `tissue_type` | `str` | The type of tissue (e.g., "epithelial", "connective"). |
| `cells` | `List[Cell]` | A list of `Cell` objects in the tissue. |
| `growth_rate` | `float` | The rate at which the tissue grows (default: `0.05`). |
| `healing_rate` | `float` | The rate at which the tissue heals (default: `0.1`). |
| `cancer_risk` | `float` | The probability of a cell becoming cancerous (default: `0.001`). |
| `mutation_rate` | `float` | The probability of a mutation occurring during cell division (default: `0.05`). |
| `mutation_threshold` | `int` | The number of mutations required for a cell to become cancerous (default: `3`). |

---

## Methods

### Initialization
- **`__init__(self, name: str, tissue_type: str, cells: Optional[List[Cell]] = None, cancer_risk: float = 0.001, mutation_rate: float = 0.05)`**
  Initializes a new `Tissue` instance with the specified name, type, and optional list of cells.

---

### Cell Management
- **`add_cell(self, cell: Cell) -> None`**
  Adds a `Cell` object to the tissue.

- **`remove_cell(self, cell: Cell) -> None`**
  Removes a `Cell` object from the tissue.

- **`get_cell_count(self) -> int`**
  Returns the number of cells in the tissue.

- **`get_average_cell_health(self) -> float`**
  Calculates and returns the average health of all cells in the tissue.

---

### Simulation Methods
- **`mutate(self)`**
  Simulates mutations in all cells of the tissue.

- **`tissue_metabolism(self) -> None`**
  Simulates the metabolism of all cells in the tissue.

- **`tissue_repair(self, amount: float) -> None`**
  Repairs all cells in the tissue by restoring a specified amount of health.

- **`simulate_cell_division(self) -> None`**
  Simulates cell division, including regulated mutations. Healthy cells (health > 70) have a 10% chance to divide.

- **`apply_mutation(self, cell: Cell) -> int`**
  Applies a random mutation to a cell and returns the total mutation count.

- **`simulate_time_step(self, external_factors: List[tuple] = None) -> None`**
  Simulates one time step in the tissue's life, including growth, healing, mutations, and external factors.

- **`apply_stress(self, stress_amount: float) -> None`**
  Applies stress to the tissue, potentially damaging cells.

- **`remove_dead_cells(self) -> None`**
  Removes cells with zero health from the tissue.

- **`simulate_growth(self) -> None`**
  Simulates tissue growth by adding new cells.

- **`simulate_wound_healing(self, wound_size: int) -> None`**
  Simulates wound healing by regenerating cells.

- **`apply_external_factor(self, factor: str, intensity: float) -> None`**
  Applies an external factor (e.g., radiation, toxin, nutrient) to the tissue, affecting cell health.

---

### Utility Methods
- **`describe(self) -> str`**
  Provides a detailed description of the tissue.

- **`to_json(self) -> str`**
  Returns a JSON representation of the tissue.

- **`from_json(cls, json_str: str) -> 'Tissue'`**
  Loads a `Tissue` object from a JSON string.

- **`visualize_tissue(self)`**
  Creates a 2D visual representation of the tissue using `matplotlib`.

- **`get_state(self)`**
  Returns the state of the tissue as a tuple.

- **`calculate_molecular_weight(self, custom_weights: dict = None) -> float`**
  Calculates the total molecular weight of the tissue in Daltons.

- **`__str__(self) -> str`**
  Returns a string representation of the tissue.

---

## Example Usage

```python
# Create a tissue
tissue = Tissue(name="Skin", tissue_type="epithelial")

# Add cells
tissue.add_cell(Cell("Cell_0001", "95"))
tissue.add_cell(Cell("Cell_0002", "90"))

# Simulate a time step
tissue.simulate_time_step(external_factors=[("nutrient", 0.5)])

# Visualize the tissue
tissue.visualize_tissue()

# Print tissue description
print(tissue.describe())
```

---

## Notes
- The `Tissue` class depends on the `Cell` class for cell-level operations.
- The `visualize_tissue` method requires `matplotlib` for visualization.
- The `calculate_molecular_weight` method uses default weights for tissue components unless custom weights are provided.

---

## Dependencies
- `random`
- `typing`
- `biobridge.blocks.cell` (for `Cell`, `math`, `plt`, `patches`)
- `json` (for serialization)


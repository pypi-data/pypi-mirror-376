# Cell Class

## Overview
The `Cell` class simulates the structure and behavior of a biological cell, including its organelles, proteins, DNA, metabolism, division, and response to external signals. It supports both mitosis and meiosis, mutation, repair, and visualization.

---

## Class Definition

```python
class Cell:
    def __init__(self, name: str, cell_type: Optional[str] = None, receptors: Optional[List[Protein]] = None,
                 surface_proteins: Optional[List[Protein]] = None, dna: Optional['DNA'] = None, health: Optional[int] = None,
                 age: Optional[int] = 0, metabolism_rate: Optional[float] = 1.0, ph: float = 7.0, osmolarity: float = 300.0,
                 ion_concentrations: Optional[Dict[str, float]] = None, id: Optional[int] = None,
                 chromosomes: Optional[List[Chromosome]] = None, structural_integrity: float = 100.0,
                 mutation_count: Optional[int] = 0, growth_rate: Optional[float] = 1.0, repair_rate: Optional[float] = 1.0,
                 max_divisions: Optional[int] = 50):
        ...
```

---

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Name of the cell. |
| `cell_type` | `Optional[str]` | Type of the cell (e.g., "neuron", "muscle cell"). |
| `receptors` | `List[Protein]` | List of receptor proteins on the cell surface. |
| `surface_proteins` | `List[Protein]` | List of proteins expressed on the cell surface. |
| `internal_proteins` | `List[Protein]` | List of proteins inside the cell. |
| `dna` | `Optional[DNA]` | DNA object representing the cell's DNA. |
| `health` | `int` | Health of the cell (0-100). |
| `age` | `int` | Age of the cell. |
| `metabolism_rate` | `float` | Rate of metabolism. |
| `ph` | `float` | pH level of the cell. |
| `osmolarity` | `float` | Osmolarity of the cell (mOsm/L). |
| `ion_concentrations` | `Dict[str, float]` | Dictionary of ion concentrations (mmol/L). |
| `id` | `Optional[int]` | Unique identifier for the cell. |
| `chromosomes` | `List[Chromosome]` | List of chromosomes in the cell. |
| `organelles` | `Dict[str, List[Organelle]]` | Dictionary of organelles by type. |
| `structural_integrity` | `float` | Structural integrity of the cell (0-100). |
| `mutation_count` | `int` | Number of mutations in the cell. |
| `growth_rate` | `float` | Growth rate of the cell. |
| `repair_rate` | `float` | Repair rate of the cell. |
| `division_count` | `int` | Number of times the cell has divided. |
| `max_divisions` | `int` | Maximum number of divisions allowed. |

---

## Methods

### Initialization
- **`__init__(self, name: str, cell_type: Optional[str] = None, receptors: Optional[List[Protein]] = None, surface_proteins: Optional[List[Protein]] = None, dna: Optional['DNA'] = None, health: Optional[int] = None, age: Optional[int] = 0, metabolism_rate: Optional[float] = 1.0, ph: float = 7.0, osmolarity: float = 300.0, ion_concentrations: Optional[Dict[str, float]] = None, id: Optional[int] = None, chromosomes: Optional[List[Chromosome]] = None, structural_integrity: float = 100.0, mutation_count: Optional[int] = 0, growth_rate: Optional[float] = 1.0, repair_rate: Optional[float] = 1.0, max_divisions: Optional[int] = 50)`**
  Initializes a new `Cell` instance with the specified attributes.

---

### Organelle Management
- **`add_organelle(self, organelle: Organelle, quantity: int = 1) -> None`**
  Adds an organelle to the cell.

- **`remove_organelle(self, organelle_type: str, quantity: int = 1) -> None`**
  Removes an organelle from the cell.

- **`add_mitochondrion(self, efficiency: float = 1.0, health: int = 100, quantity: int = 1) -> None`**
  Adds a mitochondrion to the cell.

- **`remove_mitochondrion(self, quantity: int = 1) -> None`**
  Removes a mitochondrion from the cell.

---

### Protein Management
- **`add_receptor(self, receptor: Protein) -> None`**
  Adds a receptor protein to the cell.

- **`add_surface_protein(self, protein: Protein) -> None`**
  Adds a surface protein to the cell.

- **`remove_surface_protein(self, protein: Protein) -> None`**
  Removes a surface protein from the cell.

- **`add_internal_protein(self, protein: Protein) -> None`**
  Adds an internal protein to the cell.

- **`remove_internal_protein(self, protein: Protein) -> None`**
  Removes an internal protein from the cell.

---

### Chromosome Management
- **`add_chromosome(self, chromosome: Chromosome) -> None`**
  Adds a chromosome to the cell.

- **`remove_chromosome(self, chromosome_name: str) -> None`**
  Removes a chromosome from the cell by name.

---

### Cell Division
- **`mitosis(self) -> 'Cell'`**
  Simulates mitotic division, returning a daughter cell.

- **`meiosis(self) -> List['Cell']`**
  Simulates meiotic division, returning four haploid daughter cells.

- **`divide(self) -> Union['Cell', List['Cell'], None]`**
  General method to divide the cell, choosing between mitosis and meiosis.

- **`can_divide(self) -> bool`**
  Checks if the cell can still divide.

---

### Metabolism and Health
- **`metabolize(self) -> int`**
  Simulates the cell's metabolism, returning total ATP produced.

- **`repair(self, amount: float) -> None`**
  Repairs the cell, increasing its health and structural integrity.

- **`mutate(self) -> None`**
  Simulates a random mutation in the cell.

- **`calculate_structural_integrity(self) -> float`**
  Calculates the cell's structural integrity.

- **`update_structural_integrity(self) -> None`**
  Updates the cell's structural integrity based on current conditions.

---

### Chemical Properties
- **`adjust_ph(self, delta: float) -> None`**
  Adjusts the pH of the cell.

- **`adjust_osmolarity(self, delta: float) -> None`**
  Adjusts the osmolarity of the cell.

- **`adjust_ion_concentration(self, ion: str, delta: float) -> None`**
  Adjusts the concentration of a specific ion.

---

### Interaction and Signaling
- **`interact_with_protein(self, protein: Protein) -> None`**
  Simulates interaction between the cell and a protein.

- **`receive_signal(self, signal: str, intensity: float = 1.0) -> str`**
  Processes an external signal and returns the cell's response.

---

### Visualization and Serialization
- **`visualize_cell(self) -> None`**
  Creates a 2D visual representation of the cell.

- **`to_json(self) -> str`**
  Returns a JSON representation of the cell.

- **`from_json(cls, json_str: str) -> 'Cell'`**
  Creates a `Cell` object from a JSON string.

- **`to_dict(self) -> dict`**
  Returns a dictionary representation of the cell.

- **`from_dict(cls, cell_dict: dict) -> 'Cell'`**
  Creates a `Cell` object from a dictionary.

---

### Molecular Weight Calculation
- **`calculate_molecular_weight(self, custom_weights: Optional[Dict[str, float]] = None) -> float`**
  Calculates the total molecular weight of the cell.

- **`get_molecular_weight_breakdown(self, custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]`**
  Returns a breakdown of the molecular weight of cell components.

---

### Utility Methods
- **`describe(self) -> str`**
  Provides a detailed description of the cell.

- **`reset(self) -> None`**
  Resets the cell to its initial state.

- **`__str__(self) -> str`**
  Returns a string representation of the cell.

- **`__len__(self) -> int`**
  Returns the total number of proteins, chromosomes, and organelles.

- **`__getitem__(self, item)`**
  Returns a new `Cell` instance from the dictionary representation.

- **`__iter__(self)`**
  Iterates over the cell's proteins, chromosomes, and organelles.

---

## Example Usage

```python
# Create a cell
cell = Cell(name="Cell_0001", cell_type="epithelial")

# Add a mitochondrion
cell.add_mitochondrion(efficiency=1.2, health=95)

# Add a receptor
receptor = Protein(name="Receptor_1", sequence="ABCDEF")
cell.add_receptor(receptor)

# Simulate metabolism
cell.metabolize()

# Visualize the cell
cell.visualize_cell()

# Print cell description
print(cell.describe())
```

---

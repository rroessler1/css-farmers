# css-farmers

An Agent-Based Model (ABM) using Mesa to simulate farmers' decisions about building biogas plants.

## Overview

This project implements a spatial agent-based model where farmers decide whether to build biogas plants based on:
- Their farm size
- The size of neighboring farms
- Their personal willingness threshold

Farmers who build biogas plants receive regular payments (configurable).

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the simulation with default parameters:

```bash
python run.py
```

### Interactive Visualization

Run the interactive web-based visualization server:

```bash
solara run server.py
```

Then open your browser to http://localhost:8765 to see the model in action with:
- Real-time grid visualization (green circles = farmers with plants, brown = farmers without)
- Interactive parameter sliders
- Real-time charts tracking adoption and payments

### Running Tests

Run the unit tests:

```bash
python -m unittest test_model.py -v
```

## Model Components

### Agents

1. **Farmer**: Agricultural agents that make decisions about building biogas plants
   - Attributes:
     - `farm_size`: Size of the farm (affects decision-making)
     - `willingness`: Personal threshold for decision-making (0.0-1.0)
     - `has_biogas_plant`: Boolean indicating if farmer has built a plant
     - `money_received`: Total payments received from biogas plant

2. **BiogasPlant**: Facilities built by farmers
   - Attributes:
     - `owner`: Reference to the Farmer agent that owns this plant

### Decision Making

Farmers calculate a decision score based on:
- **Farm Size** (60% weight): Larger farms are more likely to build plants
- **Neighboring Farms** (40% weight): Farmers are influenced by the size of neighboring farms

If the decision score exceeds the farmer's willingness threshold, they build a biogas plant.

### Model Parameters

The model can be configured with the following parameters:

- `n_farmers` (default: 50): Number of farmer agents
- `width` (default: 10): Grid width
- `height` (default: 10): Grid height
- `min_farm_size` (default: 10): Minimum farm size
- `max_farm_size` (default: 100): Maximum farm size
- `min_willingness` (default: 0.3): Minimum willingness threshold
- `max_willingness` (default: 0.9): Maximum willingness threshold
- `biogas_payment` (default: 100.0): Money farmers receive per step with a plant

### Example Custom Configuration

```python
from model import FarmerBiogasModel

model = FarmerBiogasModel(
    n_farmers=100,
    width=20,
    height=20,
    min_farm_size=20,
    max_farm_size=150,
    min_willingness=0.4,
    max_willingness=0.8,
    biogas_payment=250.0
)

for i in range(100):
    model.step()
```

## Data Collection

The model tracks the following metrics:
- Total number of farmers
- Number of farmers with biogas plants
- Total number of biogas plants
- Total money distributed to farmers

Agent-level data includes:
- Farm size
- Willingness threshold
- Whether they have a plant
- Total money received

## Files

- `agents.py`: Agent class definitions (Farmer and BiogasPlant)
- `model.py`: Main model class (FarmerBiogasModel)
- `run.py`: Example script to run the simulation
- `server.py`: Interactive visualization server using Mesa's Solara interface
- `test_model.py`: Unit tests for the model
- `requirements.txt`: Python dependencies

## License

MIT License
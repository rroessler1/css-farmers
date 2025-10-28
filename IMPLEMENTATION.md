# Implementation Summary

## Overview
This repository contains a complete Agent-Based Model (ABM) implementation using Mesa 3.x that simulates farmers' decisions about building biogas plants.

## Requirements Met

### ✓ Two Agent Types
1. **Farmer agents**: Agricultural entities that make decisions about biogas plants
2. **BiogasPlant agents**: Facilities built and owned by farmers

### ✓ Decision-Making Logic
Farmers decide to build biogas plants based on:
- **Farm Size** (60% weight): Larger farms contribute more to the decision score
- **Neighboring Farms** (40% weight): Average size of neighboring farms influences decision
- **Personal Willingness**: Individual threshold that must be exceeded by the decision score

Formula: If `decision_score >= willingness_threshold`, farmer builds plant

### ✓ Configurable Payment System
- Farmers with biogas plants receive money each simulation step
- Payment amount is fully configurable via `biogas_payment` parameter
- Default: $100 per step
- Accumulated payments tracked for each farmer

### ✓ Spatial Relationships
- Grid-based model using Mesa's MultiGrid
- Farmers placed spatially on grid
- Neighboring farms influence decisions through spatial proximity

## Features

### Core Implementation (agents.py, model.py)
- Farmer agent with decision-making algorithm
- BiogasPlant agent linked to owner
- FarmerBiogasModel with configurable parameters
- Data collection for metrics tracking

### Command-Line Interface (run.py)
- Simple script to run simulations
- Progress reporting every 10 steps
- Final statistics summary
- Customizable simulation length

### Interactive Visualization (server.py)
- Web-based interface using Solara
- Real-time grid visualization
- Interactive parameter sliders
- Live charts tracking adoption and payments

### Testing (test_model.py)
- 8 comprehensive unit tests
- Tests for model initialization
- Tests for agent behavior
- Tests for payment system
- Tests for data collection

## Configuration Parameters

All parameters are configurable when creating a model:

```python
model = FarmerBiogasModel(
    n_farmers=50,          # Number of farmer agents
    width=10,              # Grid width
    height=10,             # Grid height
    min_farm_size=10,      # Minimum farm size
    max_farm_size=100,     # Maximum farm size
    min_willingness=0.3,   # Minimum willingness threshold
    max_willingness=0.9,   # Maximum willingness threshold
    biogas_payment=100.0   # Payment per step (CONFIGURABLE PAYMENT)
)
```

## Example Results

Typical simulation with 50 farmers over 100 steps:
- Adoption rate: ~16-28% of farmers build plants
- Payment distribution demonstrates economic impact
- Spatial patterns emerge based on farm sizes

## Quality Assurance

✓ All 8 unit tests pass
✓ Code review completed
✓ CodeQL security scan: 0 vulnerabilities
✓ Works with Mesa 3.3.0
✓ Compatible with Python 3.12

## Technical Details

- **Framework**: Mesa 3.3.0
- **Spatial Model**: MultiGrid with torus topology
- **Agent Activation**: Custom step method with safe iteration
- **Data Collection**: Model and agent-level reporters
- **Visualization**: Solara-based interactive interface

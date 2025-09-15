# Treemun: a growth and yield simulator for chilean plantation forest

[![PyPI version](https://badge.fury.io/py/treemun-sim.svg)](https://badge.fury.io/py/treemun-sim)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package that implements a discrete-time simulation framework for evaluating management policies in Pinus radiata and Eucalyptus globulus forest stands, with integrated optimization capabilities for forest management planning.

**Key Features:**
- Forest growth simulation for Pinus and Eucalyptus species
- Multiple configurable management policies
- Biomass calculation using allometric equations
- Random forest landscape generation (instance building)
- **Forest management optimization model**
- **Support for multiple optimization solvers**
- Data preparation for optimization algorithms
- Guaranteed reproducibility through seeds

## Installation

### Basic Installation
```bash
pip install treemun-sim
```

### Installation with Optimization Solvers
```bash
# With free CBC solver (recommended)
pip install treemun-sim[solvers]

# With commercial solvers (requires licenses)
pip install treemun-sim[solvers-extended]

# Complete installation with development tools
pip install treemun-sim[complete]
```

### Solver Requirements
- **CBC**: ✅ Included with `[solvers]` installation
- **CPLEX**: Requires IBM ILOG CPLEX license

## Basic Usage

### Forest Simulation
```python
import treemun_sim as tm

# Simulation with default parameters
forest, summary, final_biomass, collected_biomass = tm.simular_bosque()

print(f"Generated {len(forest)} stand-policy combinations")
print(f"Total optimization data points: {len(collected_biomass)}")
```

### Forest Management Optimization
```python
import treemun_sim as tm

# Generate forest data
horizon = 30
num_stands = 50

forest, summary, final_biomass, collected_biomass = tm.simular_bosque(
    horizonte=horizon,
    num_rodales=num_stands
)

# Create optimization model
model = tm.forest_management_optimization_model(
    bosque=forest,
    a_i_j_T=final_biomass,
    a_i_j_t=collected_biomass,
    horizon=horizon,
    pine_revenue=12,           # $/m³
    eucalyptus_revenue=10,     # $/m³
    min_ending_biomass=25000,  # m³
    discount_rate=0.08         # 8% annual
)

# Solve model
results = tm.solve_model(model, solver_name='cbc', gap=0.01)

# Extract solution
solution = tm.extract_results(model, results)

if solution:
    print(f"Optimal NPV: ${solution['objective_value']:,.2f}")
    print(f"Pine stands managed: {solution['total_pinus_stand_treated']}")
    print(f"Pine stands planning: {solution['pinus_stand_plan']}")
    print(f"Eucalyptus stands managed: {solution['total_eucalyptus_stand_treated']}")
    print(f"Eucalyptus stands planning: {solution['eucalyptus_stand_plan']}")
    print("Total biomass collected per period:", solution['total_harvest_per_period'])
```

## Advanced Usage

### Custom Simulation Parameters
```python
import treemun_sim as tm

# Custom simulation
forest, summary, final_biomass, collected_biomass = tm.simular_bosque(
    policies_pino=[(9, 18), (10, 20), (11, 22)],  # (thinning, harvest)
    policies_eucalyptus=[(9,), (10,), (11,)],     # (harvest,)
    horizonte=25,
    num_rodales=50,
    semilla=1234
)

# Results analysis
for i, df in enumerate(forest[:3]):  # First 3 stands
    print(f"Stand {i+1}:")
    print(f"  - Species: {df['Especie'].iloc[0]}")
    print(f"  - Policy: {df['politica'].iloc[0]}")
    print(f"  - Final biomass: {df['biomasa'].iloc[-1]:.2f} tons")
```

### Variable Revenue Optimization
```python
# Variable revenue over time
pine_revenues = [10, 11, 12, 13, 14]  # Increasing revenues for 5-year horizon
eucalyptus_revenues = [8, 9, 10, 11, 12]

model = tm.forest_management_optimization_model(
    bosque=forest,
    a_i_j_T=final_biomass,
    a_i_j_t=collected_biomass,
    horizon=5,
    pine_revenue=pine_revenues,        # Variable revenue
    eucalyptus_revenue=eucalyptus_revenues,
    min_ending_biomass=20000,
    discount_rate=0.06
)
```

## API Reference

### Simulation Function

#### `simular_bosque()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `policies_pino` | `List[Tuple[int, int]]` | 16 policies | Pine policies: `[(thinning_age, harvest_age), ...]` |
| `policies_eucalyptus` | `List[Tuple[int]]` | 4 policies | Eucalyptus policies: `[(harvest_age,), ...]` |
| `horizonte` | `int` | 30 | Time horizon in years |
| `num_rodales` | `int` | 100 | Number of stands to generate |
| `semilla` | `int` | 5555 | Seed for reproducibility |

### Optimization Functions

#### `forest_management_optimization_model()`

| Parameter | Type | Description |
|-----------|------|-------------|
| `bosque` | `List[pd.DataFrame]` | Forest simulation data |
| `a_i_j_T` | `Dict` | Final standing biomass by stand-policy |
| `a_i_j_t` | `Dict` | Harvestable biomass by period |
| `horizon` | `int` | Planning horizon in years |
| `pine_revenue` | `float` or `List[float]` | Pine biomass revenue ($/m³) |
| `eucalyptus_revenue` | `float` or `List[float]` | Eucalyptus biomass revenue ($/m³) |
| `min_ending_biomass` | `float` | Minimum final period biomass guaranteed |
| `discount_rate` | `float` | Annual discount rate for NPV |

#### `solve_model()`

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `ConcreteModel` | Pyomo optimization model |
| `solver_name` | `str` | Solver name ('cbc', 'cplex') |
| `gap` | `float` | Relative optimality gap (default: 0.01) |
| `executable_path` | `str` | Path to solver executable (optional) |
| `tee` | `bool` | Display solver output (default: True) |

#### `extract_results()`

Returns a dictionary with:
- `objective_value`: Optimal NPV for the planning
- `total_harvest_per_period`: Schedule for collected biomass 
- `pinus_stand_plan`: Policy assignments for pine stands
- `eucalyptus_stand_plan`: Policy assignments for eucalyptus stands
- `total_pinus_stand_treated`: Count of pine stands
- `total_eucalyptus_stand_treated`: Count of eucalyptus stands

## Output Data Structure

### Forest DataFrame
Each element in `forest` contains:
- `periodo`: Time period (1 to horizonte)
- `edad_rodal`: Stand age in each period
- `biomasa`: Total biomass in tons
- `bioOPT`: biomass collected in tons (considers only thinned and harvested biomass amounts)
- `condición`: Management status ("sin manejo" (no managed) / "con manejo" (managed)
- `kitral_class`: Classification according to Kitral's System (Chilean fuel model)
- `politica`: Applied policy identifier 

### Optimization Dictionaries
`collected_biomass` structure:
```python
{
    (period, species, policy, stand_id): biomass_value,
    ...
}
```

`final_biomass` structure:
```python
{
    (stand_id, policy): biomass_value,
    ...
}
```

## Supported Species

### Pinus
- **Policies**: Thinning + Harvest
- **Constraint**: Thinning age < harvest age 
- **Default policies**: 16 combinations (thinning ages: 9-12 years; harvest ages: 18-24 years)

### Eucalyptus
- **Policies**: Harvest only
- **Harvest ages**: Any year
- **Default policies**: 4 options (9-12 years)

## Use Cases

- **Forest research**: Analysis of different management strategies
- **Strategic planning**: Long-term forest management optimization
- **Investment analysis**: NPV maximization with financial constraints
- **Sustainability assessment**: Balancing economic and ecological objectives
- **Policy evaluation**: Comparing management alternatives
- **Education**: Teaching forest management and optimization concepts

## Solver Installation Guide

### Free Solvers
```bash
# CBC (recommended - included with treemun-sim[solvers])
pip install pulp

```

### Commercial Solvers
```bash
# CPLEX (requires IBM license)
pip install cplex

```

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Felipe Ulloa-Fierro**
- Email: felipe.ulloa@utalca.cl
- Institution: Universidad de Talca

## Citation

If you use Treemun in your research, you can cite it as:

```
Ulloa-Fierro, F. (2025). Treemun: A Growth and Yield Simulator for Chilean Plantation Forest. 
Python Package Version 1.1.0. https://pypi.org/project/treemun-sim/
```
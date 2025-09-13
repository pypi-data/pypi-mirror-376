# EvoLib – A Modular Framework for Evolutionary Computation

[![Docs Status](https://readthedocs.org/projects/evolib/badge/?version=latest)](https://evolib.readthedocs.io/en/latest/)
[![Code Quality & Tests](https://github.com/EvoLib/evo-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/EvoLib/evo-lib/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/evolib.svg)](https://pypi.org/project/evolib/)
[![Project Status: Beta](https://img.shields.io/badge/status-beta-blue.svg)](https://github.com/EvoLib/evo-lib)

<p align="center">
  <img src="https://raw.githubusercontent.com/EvoLib/evolib/main/assets/evolib_256.png" alt="EvoLib Logo" width="256"/>
</p>

EvoLib is a lightweight and transparent framework for evolutionary computation, focusing on simplicity, modularity, and clarity — aimed at experimentation, teaching, and small-scale research rather than industrial-scale applications.

---

## Key Features

- **Transparent design**: configuration via YAML, type-checked validation, and clear module boundaries.  
- **Modularity**: mutation, selection, crossover, and parameter representations can be freely combined.  
- **Educational value**: examples and a clean API make it practical for illustrating evolutionary concepts.  
- **Neuroevolution support**: structural mutations (adding/removing neurons and connections) and evolvable networks via EvoNet.  
- **Type-checked**: PEP8 compliant, and consistent code style.  


> **EvoLib is currently in beta. The core API and configuration format are stable, but some features are still under development.**

---

<p align="center">
  <img src="https://raw.githubusercontent.com/EvoLib/evo-lib/main/examples/05_advanced_topics/04_frames_vector_obstacles/04_vector_control_obstacles.gif" alt="Sample Plot" width="512"/>
</p>

---

## Directory Structure

```
evolib/
├── core/           # Individual, Population
├── config/         # Typed component configuration (Vector, EvoNet, etc.)
├── interfaces/     # Enums, types, helper protocols
├── initializers/   # Initializer registry and implementations
├── operators/      # Mutation, crossover, selection, etc.
├── registry/       # Strategy and operator registries
├── representation/ # ParaBase + Vector, EvoNet, Composite etc.
├── utils/          # Logging, plotting, math, config loader
└── examples/       # Educational examples and test runs

```

---

## Installation

```bash
pip install evolib
```

Requirements: Python 3.10+ and packages in `requirements.txt`.

---

## Example Usage

```python
from evolib import Pop

def my_fitness(indiv):
    # Custom fitness function (example: sum of vector)
    indiv.fitness = sum(indiv.para["main"].vector)

pop = Pop(config_path="config/my_experiment.yaml",
          fitness_function=my_fitness)

# Run the evolutionary process
pop.run()
```

For full examples, see 📁[`examples/`](https://github.com/EvoLib/evo-lib/tree/main/examples) – including adaptive mutation, controller evolution, and network approximation.

---

# Configuration Example (YAML)

```yaml
parent_pool_size: 20
offspring_pool_size: 60
max_generations: 100
num_elites: 2
max_indiv_age: 0

stopping:
  target_fitness: 0.01
  patience: 20
  min_delta: 0.0001
  minimize: true

evolution:
  strategy: mu_comma_lambda

modules:
  controller:
    type: vector
    dim: 8
    initializer: normal_vector
    bounds: [-1.0, 1.0]
    mutation:
      strategy: adaptive_individual
      probability: 1.0
      strength: 0.1

  brain:
    type: evonet
    dim: [4, 6, 2]
    activation: [linear, tanh, tanh]
    initializer: normal_evonet
    mutation:
      strategy: constant
      probability: 1.0
      strength: 0.05

      # Optional fine-grained control
      activations:
        probability: 0.01
        allowed: [tanh, relu, sigmoid]

      structural:
        add_neuron: 0.01
        add_connection: 0.05
        remove_connection: 0.02
        recurrent: local  # none | direct | local | all
        keep_connected: true

```

---

> ℹ️ Multiple parameter types (e.g. vector + evonet) can be combined in a single individual. Each component evolves independently, using its own configuration.

---

## Use Cases

EvoLib is developed for clarity, modularity, and exploration in evolutionary computation.  
It can be applied to:

- **Illustrating concepts**: simple, transparent examples for teaching and learning.  
- **Neuroevolution**: evolve weights and network structures using EvoNet.  
- **Multi-module evolution**: combine different parameter types (e.g. controller + brain).  
- **Strategy comparison**: benchmark and visualize mutation, selection, and crossover operators.  
- **Function optimization**: test behavior on benchmark functions (Sphere, Ackley, …).  
- **Showcases**: structural XOR, image approximation, and other demo tasks.  
- **Rapid prototyping**: experiment with new evolutionary ideas in a lightweight environment.  

---

## Roadmap

- [X] Adaptive Mutation (global, individual, per-parameter)
- [X] Flexible Crossover Strategies (BLX, intermediate, none)
- [X] Structured Neural Representations (EvoNet)
- [X] Composite Parameters (multi-module individuals)
- [X] Neuroevolution
- [X] Topological Evolution (neurons, edges)
- [ ] Co-Evolution & Speciation Support
- [ ] Advanced Visualization
- [ ] Game Environment Integration (pygame, PettingZoo - early prototypes)
- [ ] Ray Support for Parallel Evaluation (early prototypes)


---

## License

MIT License – see [MIT License](https://github.com/EvoLib/evo-lib/tree/main/LICENSE).

---
```{toctree}
:maxdepth: 1
:hidden:
:caption: Start here

getting_started
config_guide
config_parameter
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: API – Core

api_core_population
api_core_individual
```

```{toctree}
:maxdepth: 1
:hidden:
:caption: API – Representations

api_representation_vector
api_representation_netvector
api_representation_evonet
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: API – Operators

api_operators_strategy
api_operators_selection
api_operators_replacement
api_operators_reproduction
api_operators_mutation
api_operators_crossover
api_operators_evonet_structural_mutation
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: API – I/O & Utils

api_utils_loss_functions
api_utils_benchmarks
api_utils_plotting
api_utils_history_logger
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Public API

api_public_api
```

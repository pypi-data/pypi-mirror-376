# EvoLib – A Modular Framework for Evolutionary Computation

[![Docs Status](https://readthedocs.org/projects/evolib/badge/?version=latest)](https://evolib.readthedocs.io/en/latest/)
[![Code Quality & Tests](https://github.com/EvoLib/evo-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/EvoLib/evo-lib/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/evolib.svg)](https://pypi.org/project/evolib/)
[![Project Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/EvoLib/evo-lib)

<p align="center">
  <img src="https://raw.githubusercontent.com/EvoLib/evolib/main/assets/evolib_256.png" alt="EvoLib Logo" width="256"/>
</p>

**EvoLib** is a modular and extensible Python framework for designing, analyzing, and teaching evolutionary algorithms.
It supports classical strategies such as (μ, λ) and (μ + λ), with configurable mutation, selection, and crossover operators, as well as neuroevolution.

---

## Key Features

- **Configurable Evolution**: Define evolutionary strategies via simple YAML files.
- **Modular Design**: Easily swap mutation, selection, and crossover strategies.
- **Built-in Logging**: Fitness tracking and history recording out-of-the-box.
- **Educational Focus**: Includes didactic examples and an extensible code structure.
- **Neuroevolution**: Structured neural networks (`EvoNet`) and evolvable parameter vectors supported.
- **Type-Checked**: With [mypy](https://mypy-lang.org/) and PEP8 compliance.

> ⚠️ **This project is in alpha stage. APIs and configuration structure may change.**


---

<p align="center">
  <img src="https://raw.githubusercontent.com/EvoLib/evo-lib/main/examples/05_advanced_topics/04_frames_vector_obstacles/04_vector_control_obstacles.gif" alt="Sample Plott" width="512"/>
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

Requirements: Python 3.9+ and packages in `requirements.txt`.

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

## Supported Parameter Representations

| Type      | Structure                 | Description                                        |
|-----------|---------------------------|----------------------------------------------------|
| vector    | flat, net, tensor, blocks | Evolvable vectors or neural network encodings      |
| evonet    | —                         | Neural networks via EvoNet                         |

> ℹ️ Multiple parameter types (e.g. vector + evonet) can be combined in a single individual. Each component evolves independently, using its own configuration.

---

## Use Cases

EvoLib is designed for both research and education in evolutionary computation.
It supports a wide range of applications, including:

- **Function optimization**: Test and visualize search behavior on standard functions (e.g., Sphere, Ackley)
- **Hyperparameter tuning**: Use evolutionary strategies to optimize black-box functions.
- **Strategy comparison**: Test and evaluate different mutation, selection, and crossover methods.
- **Educational use**: Clear API and examples for teaching evolutionary computation concepts.
- **Neuroevolution**: Evolve neural networks with weights and structure.

---

## Roadmap

- [x] Adaptive Mutation (global, individual, per-parameter)
- [x] Flexible Crossover Strategies (BLX, intermediate, none)
- [x] Strategy Comparisons via Examples
- [X] Structured Neural Representations (EvoNet)
- [X] Composite Parameters (multi-module individuals)
- [X] Neuroevolution
- [X] Topological Evolution (add/remove neurons, edges)
- [ ] Co-Evolution & Speciation Support
- [ ] Advanced Visualization Tools
- [ ] Ray Support for Parallel Evaluation
- [ ] Game Environment Integration (pygame, PettingZoo)

---

## License

MIT License – see [MIT License](https://github.com/EvoLib/evo-lib/tree/main/LICENSE).

---

```{toctree}
:maxdepth: 2
:caption: API Modules

api_population
api_individual
api_mutation
api_selection
api_benchmarks
api_crossover
api_replacement
api_strategy
api_reproduction
api_plotting
api_loss_functions
api_config_loader
api_copy_indiv
api_history_logger
api_registry
api_math_utils
api_config_validator
api_enums
api_structs
api_types
api_numeric
api_utils
```

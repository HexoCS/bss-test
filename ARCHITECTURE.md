# Architecture Documentation

## System Overview

The refactored BSS system follows a clean, modular architecture that separates concerns while maintaining backward compatibility with the existing database schema.

## Architecture Layers

### 1. Core Layer (`src/core/`)

Contains the validated mathematical algorithms copied from the original codebase:

- **Metaheuristics** (`metaheuristics/`): GWO, PSO, SCA, WOA, HHO, CS
  - Implements nature-inspired optimization algorithms
  - No logic changes from original implementation
  
- **Machine Learning** (`machine_learning/`): Q-Learning, SARSA, BQSA, MAB
  - Adaptive discretization scheme selection
  - Reward and policy mechanisms
  
- **Problems** (`problems/`): SCP, RW
  - Problem definitions and constraints
  - Fitness evaluation and repair strategies
  
- **Discretization** (`discretization/`): Transfer functions and binarization
  - Continuous to binary transformation
  - Multiple transfer functions (S1-S4, V1-V4, X1-X4, Z1-Z4)
  
- **Metrics** (`metrics/`): Diversity calculations
  - Population diversity measurement
  - Exploration vs exploitation tracking

### 2. Database Layer (`src/database/`)

Manages all database operations:

- **DatabaseManager**: Singleton database connection manager
  - Queue operations (fetch, update status)
  - Results storage
  - Worker coordination
  - Atomic operations for distributed execution

### 3. Solver Layer (`src/solvers/`)

Orchestrates the optimization process:

- **SCPMLSolver**: SCP with ML-based discretization
- **SCPSolver**: SCP with fixed discretization
- **RWMLSolver**: RW with ML-based discretization
- **RWSolver**: RW with fixed discretization

Each solver:
- Initializes the problem
- Sets up the algorithm components
- Executes the optimization loop
- Stores results to database

### 4. Configuration Layer (`src/utils/`)

Manages experiment configurations:

- **ConfigManager**: 
  - Loads YAML configurations
  - Generates parameter combinations
  - Maintains database schema compatibility
  - Handles discretization scheme mappings

### 5. CLI Layer (`cli/`)

Command-line interfaces for users:

- **queue_manager.py**: Creates experiment queues
  - Reads YAML configuration
  - Generates all parameter combinations
  - Populates database with pending experiments
  
- **worker.py**: Executes experiments
  - Fetches pending experiments atomically
  - Selects appropriate solver
  - Executes optimization
  - Stores results

### 6. UI Layer (`ui/`)

Web-based monitoring dashboard:

- **dashboard.py**: Streamlit application
  - Real-time queue status
  - Experiment progress tracking
  - Results visualization
  - Worker monitoring

## Data Flow

### Producer Flow (Queue Creation)

```
YAML Config
    |
    v
ConfigManager (parse and expand)
    |
    v
Experiment Combinations
    |
    v
DatabaseManager (insert as 'pendiente')
    |
    v
Database Queue
```

### Consumer Flow (Worker Execution)

```
DatabaseManager.get_pending_experiment()
    |
    v
Update status to 'ejecutando' (atomic)
    |
    v
Solver.solve()
    |
    +-- Initialize Problem
    +-- Load Algorithms (MH + ML)
    +-- Execute Optimization Loop
    |       |
    |       +-- Apply Metaheuristic
    |       +-- Evaluate Fitness
    |       +-- ML Decision (if applicable)
    |       +-- Store Iteration Data
    |       |
    |       v
    +-- Store Final Results
    |
    v
Update status to 'terminado'
```

## Database Schema Compatibility

The refactored system maintains 100% compatibility with the original database schema:

### datos_ejecucion Table

- `id`: Experiment identifier
- `nombre_algoritmo`: Algorithm name (format: PROBLEM_MH_ML_DS_rwX_plY)
- `parametros`: JSON containing complete experiment configuration
- `estado`: Status (pendiente, ejecutando, terminado, error)
- `inicio`: Start timestamp
- `fin`: End timestamp

### datos_iteracion Table

- `id_ejecucion`: Foreign key to datos_ejecucion
- `numero_iteracion`: Iteration number
- `fitness_mejor`: Best fitness value
- `parametros_iteracion`: JSON with iteration metrics

### resultado_ejecucion Table

- `id_ejecucion`: Foreign key to datos_ejecucion
- `fitness`: Final best fitness
- `inicio`: Start time
- `fin`: End time
- `mejor_solucion`: JSON with Q-table or best solution

## Configuration Schema

YAML configuration maintains the same parameter structure:

```yaml
experiment:
  problem: SCP
  metaheuristics: [GWO, PSO]
  machine_learning: [QL, BQSA]
  parameters:
    runs: 20
    population: 40
    max_iterations: 1000
```

This generates JSON compatible with the original schema:

```json
{
  "MH": "GWO",
  "paramsMH": {"population": 40, "maxIter": 1000, ...},
  "ML": "QL",
  "paramsML": {"discretizationsScheme": [...], ...},
  "problemName": "SCP",
  "paramsProblem": {"instance_file": "mscp41.txt", ...}
}
```

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Dependency Injection**: Components receive dependencies rather than creating them
3. **Configuration over Code**: Behavior controlled by configuration files
4. **Database as Queue**: Enables distributed execution across multiple workers
5. **Atomic Operations**: Prevents race conditions in multi-worker scenarios
6. **Backward Compatibility**: Maintains existing database schema and data structures
7. **No Logic Changes**: Core algorithms preserved exactly as validated

## Extensibility

Adding new components:

### New Metaheuristic

1. Add algorithm file to `src/core/metaheuristics/`
2. Update solver's `_load_metaheuristic()` method
3. Add parameters to ConfigManager

### New Problem Type

1. Add problem definition to `src/core/problems/`
2. Create solver in `src/solvers/`
3. Update worker.py to recognize the problem

### New ML Algorithm

1. Add algorithm to `src/core/machine_learning/`
2. Update solver's `_load_ml_algorithm()` method
3. Add parameters to ConfigManager

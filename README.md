# BSS-Test: Refactored Metaheuristic Solver

A clean, modular implementation of metaheuristic algorithms for Set Covering Problem (SCP) and Retaining Wall (RW) optimization.

## Architecture Overview

This refactored version follows a clean architecture with clear separation of concerns:

- **Core Modules**: Problem definitions, metaheuristics, and machine learning components
- **Configuration**: Centralized configuration management
- **Database**: Queue management for distributed execution
- **CLI**: Command-line interfaces for workers and queue management
- **UI**: Streamlit dashboard for monitoring and control

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Edit `config/database.ini` with your PostgreSQL credentials.

### 3. Create Experiment Queue

```bash
python cli/queue_manager.py --config config/experiments/example.yaml
```

### 4. Run Workers

```bash
python cli/worker.py
```

### 5. Monitor Progress (Optional)

```bash
streamlit run ui/dashboard.py
```

## Project Structure

```
bss-test/
├── src/                    # Core application code
│   ├── core/              # Core algorithms (preserved logic)
│   │   ├── metaheuristics/
│   │   ├── machine_learning/
│   │   ├── problems/
│   │   └── discretization/
│   ├── database/          # Database and queue management
│   ├── utils/             # Helper utilities
│   └── metrics/           # Performance metrics
├── config/                # Configuration files
│   ├── experiments/       # Experiment configurations
│   └── database.ini       # Database credentials
├── cli/                   # Command-line interfaces
│   ├── queue_manager.py   # Create experiment queues
│   └── worker.py          # Execute queued experiments
├── ui/                    # Streamlit dashboard
│   └── dashboard.py
├── instances/             # Problem instances
│   ├── MSCP/
│   ├── SCP/
│   └── RW/
└── requirements.txt

```

## Workflow

### Producer (Queue Creation)

1. Define experiments in YAML configuration file
2. Run `queue_manager.py` to populate the database queue
3. Experiments are created with 'pendiente' (pending) status

### Consumer (Worker Execution)

1. Workers fetch pending experiments from the database
2. Execute the optimization algorithm
3. Store results and update status to 'completado' (completed)
4. Multiple workers can run in parallel across different machines

## Configuration

Experiments are defined using YAML files that maintain compatibility with the existing database schema. Example:

```yaml
experiment:
  problem: SCP
  instances:
    - mscp41
    - mscp42
  
  metaheuristics:
    - GWO
    - PSO
  
  machine_learning:
    - QL
    - BQSA
  
  parameters:
    runs: 20
    population: 40
    max_iterations: 1000
```

## Development Notes

- Core algorithms (metaheuristics and ML) are preserved without logic changes
- Database schema and JSON structure remain unchanged for compatibility
- All code follows PEP8 standards
- No emojis or decorative characters in code or documentation

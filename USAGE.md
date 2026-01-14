# User Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Creating Experiments](#creating-experiments)
3. [Running Workers](#running-workers)
4. [Monitoring Progress](#monitoring-progress)
5. [Configuration Reference](#configuration-reference)
6. [Common Workflows](#common-workflows)

## Quick Start

### 1. Install and Setup

Follow [INSTALL.md](INSTALL.md) to set up your environment.

### 2. Create Your First Experiment

```bash
python cli/queue_manager.py --config config/experiments/example.yaml
```

### 3. Run a Worker

```bash
python cli/worker.py
```

### 4. Monitor Progress

```bash
streamlit run ui/dashboard.py
```

Then open your browser to `http://localhost:8501`

## Creating Experiments

### Using Configuration Files

Experiments are defined using YAML files. This approach is cleaner and more maintainable than the original hardcoded configure files.

#### Basic Structure

```yaml
experiment:
  problem: SCP  # or RW
  instances:
    - mscp41
    - mscp42
  metaheuristics:
    - GWO
    - PSO
  machine_learning:
    - QL
  parameters:
    runs: 20
    population: 40
    max_iterations: 1000
```

#### Testing Configuration (Dry Run)

Before creating thousands of experiments, test your configuration:

```bash
python cli/queue_manager.py --config config/experiments/my_config.yaml --dry-run
```

This shows what will be created without touching the database.

### Parameter Combinations

The system automatically generates all combinations of:
- Instances
- Metaheuristics
- Machine Learning algorithms
- Discretization schemes
- Reward types
- Policy types
- Runs

Example: 3 instances x 2 MH x 2 ML x 20 runs = 240 experiments

### Available Algorithms

#### Metaheuristics
- GWO: Grey Wolf Optimizer
- PSO: Particle Swarm Optimization
- SCA: Sine Cosine Algorithm
- WOA: Whale Optimization Algorithm
- HHO: Harris Hawks Optimization
- CS: Cuckoo Search

#### Machine Learning
- QL: Q-Learning
- SA: SARSA
- BQSA: Backward Q-Learning with SARSA
- MAB: Multi-Armed Bandit
- BCL: Basic (no ML)
- MIR: Mirror (no ML)

## Running Workers

### Single Worker

Execute experiments until the queue is empty:

```bash
python cli/worker.py
```

### Limited Execution

Run a specific number of experiments:

```bash
python cli/worker.py --max-experiments 10
```

### Continuous Mode

Keep running and check for new experiments:

```bash
python cli/worker.py --continuous --check-interval 30
```

This is useful for long-running worker processes.

### Multiple Workers

Run multiple workers in parallel (different terminals or machines):

Terminal 1:
```bash
python cli/worker.py
```

Terminal 2:
```bash
python cli/worker.py
```

The database ensures each experiment is executed only once.

### Distributed Execution

Workers can run on different machines connected to the same database:

Machine 1:
```bash
python cli/worker.py --continuous
```

Machine 2:
```bash
python cli/worker.py --continuous
```

Machine 3:
```bash
python cli/worker.py --continuous
```

## Monitoring Progress

### Dashboard

The Streamlit dashboard provides real-time monitoring:

```bash
streamlit run ui/dashboard.py
```

Features:
- Queue status (pending, executing, completed, errors)
- Recent experiments
- Progress visualization
- Best results
- Fitness distribution

### Command Line

Check queue status programmatically:

```python
from src.database import DatabaseManager

db = DatabaseManager()
stats = db.get_queue_status()

print(f"Pending: {stats['pendiente']}")
print(f"Executing: {stats['ejecutando']}")
print(f"Completed: {stats['completado']}")
print(f"Total: {stats['total']}")
```

## Configuration Reference

### Complete Configuration Example

```yaml
experiment:
  problem: SCP
  
  instances:
    - mscp41
    - mscp42
    - mscp43
  
  metaheuristics:
    - GWO
    - PSO
    - SCA
  
  machine_learning:
    - QL
    - BQSA
  
  parameters:
    runs: 20
    population: 40
    max_iterations: 1000
    
    discretization_schemes:
      - 40a  # 40 transfer functions
      - 80a  # 80 transfer functions
    
    reward_types: [5, 6]  # Indices into reward list
    policy_types: [0, 4]  # Indices into policy list
    
    # ML parameters
    epsilon: 0.1
    states_q: 2
    W: 10
    visit_all_once: true
    ql_alpha: 0.1
    ql_gamma: 0.4
    ql_alpha_type: static
    beta_dis: 0.8
    cond_backward: 10
    
    # MH-specific parameters
    a_SCA: 2
    b_WOA: 1
    beta_HHO: 1.5
    pa_CS: 0.25
    alpha_CS: 1
    beta_CS: 1.5
    Vmax_PSO: 6
    wMax_PSO: 0.9
    wMin_PSO: 0.2
    c1_PSO: 2
    c2_PSO: 2
  
  problem_params:
    FO: min
    lb: -10
    ub: 10
    repair_type: 2
    instance_dir: MSCP/
```

### Reward Types

- 0: withPenalty1
- 1: withoutPenalty1
- 2: globalBest
- 3: rootAdaptation
- 4: escalatingMultiplicativeAdaptation
- 5: percentageImprovement
- 6: percentageImprovementAndDeterioration
- 7: percentageImprovementAndDeteriorationWithIter

### Policy Types

- 0: e-greedy
- 1: greedy
- 2: e-soft
- 3: softMax-rulette
- 4: softMax-rulette-elitist

### Discretization Schemes

- `40a`: 40 transfer function combinations (S1-S4, V1-V4 with 5 operators)
- `80a`: 80 transfer function combinations (adds X1-X4, Z1-Z4)
- `ver1-ver90`: Various predefined combinations

## Common Workflows

### Workflow 1: Small Test Run

Test configuration with minimal experiments:

```yaml
experiment:
  problem: SCP
  instances: [mscp41]
  metaheuristics: [GWO]
  machine_learning: [QL]
  parameters:
    runs: 3
    population: 20
    max_iterations: 100
    discretization_schemes: [40a]
    reward_types: [5]
    policy_types: [0]
```

```bash
# Create queue
python cli/queue_manager.py --config config/experiments/test.yaml

# Run
python cli/worker.py --max-experiments 3

# Monitor
streamlit run ui/dashboard.py
```

### Workflow 2: Large Production Run

Full experiment suite:

```yaml
experiment:
  problem: SCP
  instances:
    - mscp41
    - mscp42
    - mscp43
    # ... all instances
  metaheuristics: [GWO, PSO, SCA, WOA, HHO, CS]
  machine_learning: [QL, SA, BQSA, MAB]
  parameters:
    runs: 20
    population: 40
    max_iterations: 1000
    discretization_schemes: [40a, 80a]
    reward_types: [5, 6, 7]
    policy_types: [0, 1, 4]
```

```bash
# Create queue (thousands of experiments)
python cli/queue_manager.py --config config/experiments/production.yaml

# Start multiple workers
python cli/worker.py --continuous &
python cli/worker.py --continuous &
python cli/worker.py --continuous &
```

### Workflow 3: Incremental Experiments

Add new experiments to existing queue:

```bash
# Week 1: Initial batch
python cli/queue_manager.py --config config/experiments/batch1.yaml

# Week 2: Add more without affecting running experiments
python cli/queue_manager.py --config config/experiments/batch2.yaml

# Workers continue processing both batches
```

### Workflow 4: Error Recovery

If experiments fail:

```sql
-- Find failed experiments
SELECT id, nombre_algoritmo 
FROM datos_ejecucion 
WHERE estado = 'error';

-- Reset to pending for retry
UPDATE datos_ejecucion 
SET estado = 'pendiente', inicio = NULL 
WHERE estado = 'error';
```

Then restart workers to retry failed experiments.

## Tips and Best Practices

1. **Start Small**: Test with a few experiments before creating large queues
2. **Use Dry Run**: Always use `--dry-run` first to verify configuration
3. **Monitor Progress**: Keep the dashboard open during long runs
4. **Distributed Workers**: Leverage multiple machines for faster execution
5. **Backup Database**: Regularly backup your results database
6. **Save Configurations**: Keep all YAML files in version control
7. **Name Conventions**: Use descriptive names for configuration files
8. **Resource Planning**: Calculate total experiments before creating queue

## Troubleshooting

### Worker Stops Unexpectedly

Check the last log messages. If it's a database connection issue:

```bash
# Verify database connection
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print('OK')"
```

### Dashboard Shows No Data

Ensure:
1. Database is accessible
2. Experiments have been created
3. Workers have executed some experiments

### Experiments Stuck in 'ejecutando'

If a worker crashes, experiments may be stuck. Manual reset:

```sql
UPDATE datos_ejecucion 
SET estado = 'pendiente', inicio = NULL 
WHERE estado = 'ejecutando' 
AND inicio < NOW() - INTERVAL '2 hours';
```

### Import Errors

Ensure you're in the correct directory:

```bash
cd bss-test
python cli/worker.py  # Correct
```

Not:

```bash
cd bss-test/cli
python worker.py  # Wrong - import errors
```

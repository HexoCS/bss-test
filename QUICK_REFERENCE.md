# Quick Reference

## Common Commands

### Queue Management

```bash
# Create experiments from config
python cli/queue_manager.py --config config/experiments/example.yaml

# Preview without creating
python cli/queue_manager.py --config config/experiments/example.yaml --dry-run
```

### Worker Operations

```bash
# Run worker (stops when queue empty)
python cli/worker.py

# Run limited number of experiments
python cli/worker.py --max-experiments 10

# Continuous mode (keeps checking for new experiments)
python cli/worker.py --continuous

# Custom check interval
python cli/worker.py --continuous --check-interval 30
```

### Monitoring

```bash
# Launch dashboard
streamlit run ui/dashboard.py

# Check queue status (Python)
from src.database import DatabaseManager
db = DatabaseManager()
stats = db.get_queue_status()
```

## Configuration Quick Start

### Minimal Configuration

```yaml
experiment:
  problem: SCP
  instances: [mscp41]
  metaheuristics: [GWO]
  machine_learning: [QL]
  parameters:
    runs: 5
    population: 40
    max_iterations: 100
    discretization_schemes: [40a]
    reward_types: [5]
    policy_types: [0]
```

### Full Configuration Template

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
    discretization_schemes: [40a, 80a]
    reward_types: [5, 6]
    policy_types: [0, 4]
    
    # ML params (optional, these are defaults)
    epsilon: 0.1
    states_q: 2
    W: 10
    visit_all_once: true
    ql_alpha: 0.1
    ql_gamma: 0.4
    ql_alpha_type: static
    beta_dis: 0.8
    cond_backward: 10
  
  problem_params:
    FO: min
    lb: -10
    ub: 10
    repair_type: 2
    instance_dir: MSCP/
```

## Algorithm Reference

### Metaheuristics (MH)
- `GWO`: Grey Wolf Optimizer
- `PSO`: Particle Swarm Optimization
- `SCA`: Sine Cosine Algorithm
- `WOA`: Whale Optimization Algorithm
- `HHO`: Harris Hawks Optimization
- `CS`: Cuckoo Search

### Machine Learning (ML)
- `QL`: Q-Learning
- `SA`: SARSA
- `BQSA`: Backward Q-Learning with SARSA
- `MAB`: Multi-Armed Bandit
- `BCL`: Basic (no ML)
- `MIR`: Mirror (no ML)

### Discretization Schemes
- `40a`: S1-S4, V1-V4 with 5 operators (40 combinations)
- `80a`: S1-S4, V1-V4, X1-X4, Z1-Z4 with 5 operators (80 combinations)

### Reward Types (indices 0-7)
- `5`: percentageImprovement (commonly used)
- `6`: percentageImprovementAndDeterioration
- `7`: percentageImprovementAndDeteriorationWithIter

### Policy Types (indices 0-4)
- `0`: e-greedy (commonly used)
- `4`: softMax-rulette-elitist

## Database Queries

### Check Queue Status

```sql
-- Count by status
SELECT estado, COUNT(*) 
FROM datos_ejecucion 
GROUP BY estado;

-- Recent experiments
SELECT id, nombre_algoritmo, estado, inicio, fin
FROM datos_ejecucion
ORDER BY id DESC
LIMIT 10;

-- Failed experiments
SELECT id, nombre_algoritmo
FROM datos_ejecucion
WHERE estado = 'error';
```

### Reset Failed Experiments

```sql
-- Reset errors to pending
UPDATE datos_ejecucion
SET estado = 'pendiente', inicio = NULL
WHERE estado = 'error';

-- Reset stuck executions (> 2 hours)
UPDATE datos_ejecucion
SET estado = 'pendiente', inicio = NULL
WHERE estado = 'ejecutando'
AND inicio < NOW() - INTERVAL '2 hours';
```

### View Results

```sql
-- Best results
SELECT 
    re.id_ejecucion,
    de.nombre_algoritmo,
    re.fitness
FROM resultado_ejecucion re
JOIN datos_ejecucion de ON re.id_ejecucion = de.id
ORDER BY CAST(re.fitness AS FLOAT) ASC
LIMIT 10;

-- Execution statistics
SELECT 
    de.nombre_algoritmo,
    COUNT(*) as executions,
    AVG(EXTRACT(EPOCH FROM (de.fin - de.inicio))/3600) as avg_hours
FROM datos_ejecucion de
WHERE de.estado = 'terminado'
GROUP BY de.nombre_algoritmo;
```

## Troubleshooting

### Worker won't start
```bash
# Check database connection
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print('OK')"
```

### Import errors
```bash
# Ensure you're in bss-test directory
cd bss-test
pwd  # Should end with bss-test
```

### Dashboard won't load
```bash
# Check if streamlit is installed
pip install streamlit

# Check port availability
streamlit run ui/dashboard.py --server.port 8502
```

### Configuration errors
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/experiments/example.yaml'))"
```

## File Locations

- **Configs**: `config/experiments/*.yaml`
- **Database**: `config/database.ini`
- **Instances**: `instances/MSCP/`, `instances/SCP/`, `instances/RW/`
- **Logs**: Check terminal output
- **Results**: PostgreSQL database

## Typical Workflow

1. **Create Config**
   ```bash
   cp config/experiments/example.yaml config/experiments/my_experiment.yaml
   # Edit my_experiment.yaml
   ```

2. **Test Config**
   ```bash
   python cli/queue_manager.py --config config/experiments/my_experiment.yaml --dry-run
   ```

3. **Create Queue**
   ```bash
   python cli/queue_manager.py --config config/experiments/my_experiment.yaml
   ```

4. **Start Workers** (multiple terminals)
   ```bash
   python cli/worker.py --continuous
   ```

5. **Monitor**
   ```bash
   streamlit run ui/dashboard.py
   ```

## Directory Navigation

```bash
# Working directory should be bss-test
cd bss-test

# Activate virtual environment (if using)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# All commands run from bss-test root
python cli/worker.py
python cli/queue_manager.py --config config/experiments/example.yaml
streamlit run ui/dashboard.py
```

## Performance Tips

1. **Parallel Workers**: Run multiple workers for faster execution
2. **Batch Size**: Insert iterations every 50 iterations (already optimized)
3. **Continuous Mode**: Use for long-running workers
4. **Database**: Ensure PostgreSQL is tuned for concurrent access
5. **Monitoring**: Dashboard auto-refresh can be disabled for better performance

## Getting Help

- **Installation**: See [INSTALL.md](INSTALL.md)
- **Usage**: See [USAGE.md](USAGE.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Migration**: See [MIGRATION.md](MIGRATION.md)
- **Summary**: See [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)

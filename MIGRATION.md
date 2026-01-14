# Migration Guide

## Migrating from Original BSS to bss-test

This guide helps you transition from the original BSS codebase to the refactored bss-test version.

## What's Changed

### Structural Changes

#### Old Structure
```
BSS-main/
├── configure.py (monolithic script)
├── configure 2.py
├── configure 3.py
├── ...
├── main.py (worker loop)
├── Metaheuristics/
├── MachineLearning/
├── Problem/
└── Database/
```

#### New Structure
```
bss-test/
├── config/ (YAML configurations)
├── cli/ (queue_manager, worker)
├── ui/ (dashboard)
├── src/
│   ├── core/ (algorithms - unchanged logic)
│   ├── database/ (cleaned up)
│   ├── solvers/ (refactored execution)
│   └── utils/ (config management)
└── instances/
```

### Workflow Changes

#### Old Workflow
1. Edit `configure.py` to set parameters
2. Run `python configure.py` to populate database
3. Run `python main.py` on each worker machine
4. Monitor using database queries

#### New Workflow
1. Create YAML configuration file
2. Run `python cli/queue_manager.py --config your_config.yaml`
3. Run `python cli/worker.py` on each worker machine
4. Monitor using Streamlit dashboard

## Migration Steps

### Step 1: Understand Your Current Experiments

Review your existing `configure*.py` files to understand:
- Which instances you're using
- Which algorithms (MH + ML combinations)
- Parameter values
- Number of runs

### Step 2: Create Equivalent YAML Configuration

Convert your configure.py settings to YAML format.

#### Example Conversion

Old (configure.py):
```python
algorithmsMH = ["SCA", "WOA", "GWO"]
runs = 20
population = 40
maxIter = 1000
algorithmsML = ["SA", "BQSA"]
namesDS = ["80a", "40a"]
instances = ['mscp41', 'mscp42', 'mscp43']
numRewardTypes = [5]
numPolicyTypes = [0, 4]
```

New (config.yaml):
```yaml
experiment:
  problem: SCP
  instances:
    - mscp41
    - mscp42
    - mscp43
  metaheuristics:
    - SCA
    - WOA
    - GWO
  machine_learning:
    - SA
    - BQSA
  parameters:
    runs: 20
    population: 40
    max_iterations: 1000
    discretization_schemes:
      - 80a
      - 40a
    reward_types: [5]
    policy_types: [0, 4]
```

### Step 3: Test with Dry Run

Before creating actual experiments:

```bash
python cli/queue_manager.py --config config/experiments/migrated.yaml --dry-run
```

Verify:
- Total number of experiments matches expectations
- Algorithm names are correct
- Parameter combinations are as intended

### Step 4: Parallel Operation (Recommended)

You can run both systems simultaneously:

1. Keep old system for existing experiments
2. Use bss-test for new experiments
3. They share the same database

This allows gradual migration without disruption.

### Step 5: Update Worker Processes

Replace old `main.py` workers with new workers:

Old:
```bash
python main.py
```

New:
```bash
python cli/worker.py --continuous
```

The new worker is compatible with experiments created by both systems.

## Configuration Mapping

### Parameter Name Changes

| Old Name | New Name | Notes |
|----------|----------|-------|
| `maxIter` | `max_iterations` | More descriptive |
| `namesDS` | `discretization_schemes` | Clearer naming |
| `numRewardTypes` | `reward_types` | Simplified |
| `numPolicyTypes` | `policy_types` | Simplified |

### Algorithm Names

Algorithm names remain unchanged for database compatibility:
- Format: `PROBLEM_MH_ML_DS_rwX_plY`
- Example: `SCP_GWO_QL_40a_rw5_pl0`

## Database Compatibility

### Good News: 100% Compatible

The refactored system uses the exact same database schema:

- `datos_ejecucion`: No changes
- `datos_iteracion`: No changes
- `resultado_ejecucion`: No changes

This means:
- Existing data remains accessible
- Old and new systems can coexist
- No data migration required
- Results are comparable

### JSON Schema

The parameter JSON structure is preserved:

```json
{
  "MH": "GWO",
  "paramsMH": {...},
  "ML": "QL",
  "paramsML": {...},
  "problemName": "SCP",
  "paramsProblem": {...}
}
```

## Feature Comparison

| Feature | Old System | New System |
|---------|-----------|-----------|
| Configuration | Python scripts | YAML files |
| Queue Creation | Edit + Run script | CLI command |
| Worker | main.py | cli/worker.py |
| Monitoring | SQL queries | Streamlit dashboard |
| Multiple Workers | Manual coordination | Automatic via DB |
| Documentation | Minimal | Comprehensive |
| Code Organization | Scattered | Modular |
| Error Handling | Basic | Improved |
| Extensibility | Difficult | Easy |

## Common Migration Scenarios

### Scenario 1: Recreate Previous Experiment

If you want to repeat an old experiment:

1. Find the original `configure*.py` file
2. Extract parameters
3. Create YAML equivalent
4. Run with bss-test

### Scenario 2: Extend Previous Experiment

Add new instances or algorithms to existing study:

1. Copy original YAML
2. Add new instances/algorithms
3. Create queue
4. Workers process both old and new

### Scenario 3: Fresh Start

Start completely fresh with bss-test:

1. Archive old configure files
2. Design experiments in YAML
3. Use new workflow exclusively

## Advantages of bss-test

### For Researchers

- Easier experiment definition (YAML vs Python)
- Better visualization (dashboard)
- Cleaner results organization
- Reproducible configurations

### For Developers

- Modular codebase
- Clear separation of concerns
- Easier to extend
- Better documentation

### For Operations

- Simplified worker deployment
- Better monitoring
- Easier troubleshooting
- Distributed execution support

## Rollback Plan

If you need to revert to the old system:

1. Stop new workers
2. Original code still works with the database
3. No data loss
4. Can switch back anytime

Both systems can coexist indefinitely.

## FAQ

**Q: Do I need to migrate all at once?**

A: No. Both systems can run simultaneously. Migrate gradually.

**Q: Will my old results be accessible in bss-test?**

A: Yes. All results in the database are accessible via the new dashboard.

**Q: Can I still use my old configure files?**

A: Yes, but we recommend converting to YAML for better maintainability.

**Q: What if I find a bug in bss-test?**

A: You can immediately switch back to the old system without data loss.

**Q: Are the algorithms exactly the same?**

A: Yes. The core algorithm logic is unchanged. Only the organization is different.

**Q: Will experiment IDs conflict?**

A: No. The database auto-increments IDs regardless of which system created them.

## Getting Help

If you encounter issues during migration:

1. Check [USAGE.md](USAGE.md) for detailed instructions
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design details
3. Consult example configurations in `config/experiments/`
4. Compare your old configure.py with generated YAML

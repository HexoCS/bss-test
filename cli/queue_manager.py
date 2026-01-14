"""
Queue Manager CLI

Creates experiment queues from YAML configuration files.
Populates the database with pending experiments for workers to execute.

Usage:
    python queue_manager.py --config config/experiments/example.yaml
    python queue_manager.py --config config/experiments/example.yaml --dry-run
"""

import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import DatabaseManager
from src.utils.config_manager import ConfigManager


def main():
    parser = argparse.ArgumentParser(
        description='Generate and queue experiments from configuration file'
    )
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to YAML configuration file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without actually inserting to database'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    print(f"Loading configuration from: {args.config}")
    config = ConfigManager.load_yaml_config(args.config)
    
    # Generate experiments
    print("Generating experiment combinations...")
    experiments = ConfigManager.generate_experiments(config)
    
    print(f"Generated {len(experiments)} experiment configurations")
    
    if args.dry_run:
        print("\nDRY RUN - No database changes will be made\n")
        print("Sample experiment (first 3):")
        for i, exp in enumerate(experiments[:3]):
            print(f"\n--- Experiment {i+1} ---")
            print(f"Algorithm: {exp['nombre_algoritmo']}")
            print(f"MH: {exp['parametros']['MH']}")
            print(f"ML: {exp['parametros']['ML']}")
            print(f"Instance: {exp['parametros']['paramsProblem']['instance_name']}")
        print(f"\n... and {len(experiments) - 3} more")
        return
    
    # Insert to database
    db = DatabaseManager()
    
    print("\nInserting experiments to database queue...")
    success_count = 0
    
    for i, exp in enumerate(experiments, 1):
        exp_id = db.create_experiment(
            algorithm_name=exp['nombre_algoritmo'],
            parameters=exp['parametros'],
            status='pendiente'
        )
        
        if exp_id:
            success_count += 1
            if i % 100 == 0:
                print(f"  Inserted {i}/{len(experiments)} experiments...")
        else:
            print(f"  ERROR: Failed to insert experiment {i}")
    
    print(f"\nCompleted: {success_count}/{len(experiments)} experiments queued")
    
    # Show queue status
    stats = db.get_queue_status()
    print("\nCurrent queue status:")
    print(f"  Pending: {stats.get('pendiente', 0)}")
    print(f"  Executing: {stats.get('ejecutando', 0)}")
    print(f"  Completed: {stats.get('completado', 0)}")
    print(f"  Error: {stats.get('error', 0)}")
    print(f"  Total: {stats.get('total', 0)}")


if __name__ == '__main__':
    main()

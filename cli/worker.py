"""
Worker CLI

Executes pending experiments from the database queue.
Multiple workers can run in parallel across different machines.

Usage:
    python worker.py
    python worker.py --max-experiments 10
    python worker.py --continuous
"""

import argparse
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import DatabaseManager
from src.solvers import SCPMLSolver, SCPSolver, RWMLSolver, RWSolver


def main():
    parser = argparse.ArgumentParser(
        description='Execute pending experiments from the queue'
    )
    parser.add_argument(
        '--max-experiments',
        type=int,
        default=None,
        help='Maximum number of experiments to execute (default: unlimited)'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Keep running and check for new experiments periodically'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=60,
        help='Seconds to wait between checks in continuous mode (default: 60)'
    )
    
    args = parser.parse_args()
    
    db = DatabaseManager()
    experiments_completed = 0
    
    print("Worker started")
    print("=" * 60)
    
    # Initialize solvers
    scp_ml_solver = SCPMLSolver()
    scp_solver = SCPSolver()
    rw_ml_solver = RWMLSolver()
    rw_solver = RWSolver()
    
    while True:
        # Fetch next pending experiment
        exp_id, algorithm_name, params = db.get_pending_experiment()
        
        if exp_id == 0:
            if args.continuous:
                print(f"No pending experiments. Waiting {args.check_interval} seconds...")
                time.sleep(args.check_interval)
                continue
            else:
                print("No more pending experiments")
                break
        
        print(f"\nExperiment ID: {exp_id}")
        print(f"Algorithm: {algorithm_name}")
        print("-" * 60)
        
        # Extract parameters
        mh = params.get('MH')
        ml = params.get('ML')
        params_mh = params.get('paramsMH')
        params_ml = params.get('paramsML')
        problem_name = params.get('problemName')
        params_problem = params.get('paramsProblem')
        
        print(f"Problem: {problem_name}")
        print(f"MH: {mh}")
        print(f"ML: {ml}")
        print(f"Instance: {params_problem.get('instance_name', 'N/A')}")
        print(f"Run: {params_mh.get('run', 'N/A')}")
        
        # Select appropriate solver
        try:
            if problem_name == "SCP":
                if ml in ["QL", "SA", "BQSA", "MAB"]:
                    solver = scp_ml_solver
                else:
                    solver = scp_solver
            elif problem_name == "RW":
                if ml in ["QL", "SA", "BQSA", "MAB"]:
                    solver = rw_ml_solver
                else:
                    solver = rw_solver
            else:
                print(f"ERROR: Unknown problem type: {problem_name}")
                db.finish_experiment(exp_id, None, 'error')
                continue
            
            # Execute optimization
            success = solver.solve(
                exp_id, mh, params_mh, ml, params_ml,
                problem_name, params_problem
            )
            
            if success:
                experiments_completed += 1
                print(f"Experiment {exp_id} completed successfully")
            else:
                print(f"Experiment {exp_id} failed")
        
        except Exception as e:
            print(f"ERROR executing experiment {exp_id}: {e}")
            import traceback
            traceback.print_exc()
            db.finish_experiment(exp_id, None, 'error')
        
        # Check if we've hit the maximum
        if args.max_experiments and experiments_completed >= args.max_experiments:
            print(f"\nReached maximum experiments limit ({args.max_experiments})")
            break
        
        print("=" * 60)
    
    print(f"\nWorker finished. Completed {experiments_completed} experiments")


if __name__ == '__main__':
    main()

"""
Set Covering Problem Solver with Machine Learning

Implements metaheuristic optimization for SCP enhanced with ML-based
discretization scheme selection.
"""

import os
import numpy as np
import time
from datetime import datetime
import json

from ..database import DatabaseManager
from ..core.problems.util import read_instance as Instance
from ..core.problems import SCP
from ..core.metrics import Diversidad as dv


class SCPMLSolver:
    """
    Solver for Set Covering Problem with Machine Learning integration.
    
    This solver combines:
    - Metaheuristic algorithms (GWO, PSO, SCA, WOA, HHO, CS)
    - Machine Learning agents (Q-Learning, SARSA, BQSA, MAB)
    - Adaptive discretization scheme selection
    """
    
    def __init__(self):
        """Initialize solver with database connection."""
        self.db = DatabaseManager()
        self.workdir = os.path.abspath(os.getcwd())
        self.instance_dir = os.path.join(self.workdir, 'instances')
    
    def solve(self, experiment_id, mh_algorithm, params_mh, ml_algorithm, 
              params_ml, problem_name, params_problem):
        """
        Execute the optimization process for a single experiment.
        
        Args:
            experiment_id: Database ID of this experiment
            mh_algorithm: Name of metaheuristic (GWO, PSO, etc.)
            params_mh: Metaheuristic parameters dict
            ml_algorithm: Name of ML algorithm (QL, SA, BQSA, MAB)
            params_ml: ML parameters dict
            problem_name: Problem type (should be 'SCP')
            params_problem: Problem-specific parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load ML algorithm
            ml_agent = self._load_ml_algorithm(ml_algorithm)
            
            # Load metaheuristic
            metaheuristic = self._load_metaheuristic(mh_algorithm)
            
            # Initialize problem
            instance_file = params_problem['instance_file']
            instance_dir = params_problem['instance_dir']
            
            problem = SCP.SCP(self.instance_dir, instance_dir, instance_file)
            instance_path = problem.obtenerInstancia()
            
            if not os.path.exists(instance_path):
                print(f'Instance not found: {instance_path}')
                self.db.finish_experiment(
                    experiment_id,
                    datetime.now(),
                    'error'
                )
                return False
            
            # Read instance data
            instance = Instance.Read(instance_path)
            coverage_matrix = np.array(instance.get_r())
            cost_vector = np.array(instance.get_c())
            
            # Setup problem parameters
            dim = len(cost_vector)
            population = params_mh['population']
            max_iter = params_mh['maxIter']
            lb = params_problem["lb"]
            ub = params_problem["ub"]
            
            params_problem["costos"] = cost_vector
            params_problem["cobertura"] = coverage_matrix
            
            # Initialize population
            matrix_cont = np.random.uniform(low=lb, high=ub, size=(population, dim))
            matrix_bin = np.random.randint(low=0, high=2, size=(population, dim))
            fitness = np.zeros(population)
            solutions_ranking = np.zeros(population)
            
            # Initialize ML agent
            agent = ml_agent(params_ml, params_mh)
            action = agent.getAccion(0)
            ds_actions = params_ml['discretizationsScheme']
            
            params_problem["ds"] = ds_actions[action]
            
            # Initial fitness evaluation
            matrix_bin, fitness, solutions_ranking, num_repairs = problem.obtenerFitness(
                matrix_cont, matrix_bin, solutions_ranking, params_problem
            )
            
            params_problem['bestHistoricalIndividual'] = matrix_cont.copy()
            params_problem['fitnessHistoricalIndividual'] = fitness.copy()
            
            # Initial diversity calculation
            max_diversidades = np.zeros(7)
            diversidades, max_diversidades, porcentaje_explor, porcentaje_explot, new_states = \
                dv.ObtenerDiversidadYEstado(matrix_bin, max_diversidades)
            state = new_states[0]
            
            # Start optimization
            inicio = datetime.now()
            memory = []
            
            for iter in range(max_iter):
                process_time_start = time.process_time()
                wall_time_start = time.time()
                
                # Apply metaheuristic
                matrix_cont, params_problem = metaheuristic(
                    problem, params_problem, params_mh, matrix_cont,
                    matrix_bin, solutions_ranking, fitness, iter
                )
                
                # Evaluate fitness
                matrix_bin, fitness, solutions_ranking, num_repairs = \
                    problem.obtenerFitness(
                        matrix_cont, matrix_bin, solutions_ranking, params_problem
                    )
                
                # Preserve best solution
                if params_problem['FO'] == "min":
                    if fitness[solutions_ranking[0]] > params_problem['BestFitnessOld']:
                        fitness[solutions_ranking[0]] = params_problem['BestFitnessOld']
                        matrix_bin[solutions_ranking[0]] = params_problem['BestBinaryOld']
                    params_problem['bestHistoricalIndividual'][
                        params_problem['fitnessHistoricalIndividual'] > fitness
                    ] = matrix_cont[params_problem['fitnessHistoricalIndividual'] > fitness]
                else:
                    if fitness[solutions_ranking[0]] < params_problem['BestFitnessOld']:
                        fitness[solutions_ranking[0]] = params_problem['BestFitnessOld']
                        matrix_bin[solutions_ranking[0]] = params_problem['BestBinaryOld']
                    params_problem['bestHistoricalIndividual'][
                        params_problem['fitnessHistoricalIndividual'] < fitness
                    ] = matrix_cont[params_problem['fitnessHistoricalIndividual'] < fitness]
                
                # Calculate diversity
                diversidades, max_diversidades, porcentaje_explor, porcentaje_explot, new_states = \
                    dv.ObtenerDiversidadYEstado(matrix_bin, max_diversidades)
                
                best_fitness_str = str(np.min(fitness))
                
                # ML agent decision
                new_state = new_states[0]
                new_action = agent.getAccion(new_state)
                
                # Update Q-table
                agent.updateQtable(
                    np.min(fitness), action, new_action, state, new_state, iter
                )
                
                # Update for next iteration
                action = new_action
                state = new_state
                params_problem["ds"] = ds_actions[action]
                
                # Timing
                wall_time_end = np.round(time.time() - wall_time_start, 6)
                process_time_end = np.round(time.process_time() - process_time_start, 6)
                
                # Store iteration data
                data_iter = {
                    "id_ejecucion": experiment_id,
                    "numero_iteracion": iter,
                    "fitness_mejor": best_fitness_str,
                    "parametros_iteracion": json.dumps({
                        "fitness": best_fitness_str,
                        "clockTime": wall_time_end,
                        "processTime": process_time_end,
                        "DS": str(ds_actions[action]),
                        "Diversidades": str(diversidades),
                        "PorcentajeExplor": str(porcentaje_explor),
                        "numReparaciones": str(num_repairs)
                    })
                }
                
                memory.append(data_iter)
                
                # Periodic database insert
                if iter % 50 == 0 and iter != 0:
                    memory = self.db.insert_iteration_data(memory)
            
            # Insert remaining iteration data
            if len(memory) > 0:
                memory = self.db.insert_iteration_data(memory)
            
            # Store final results
            fin = datetime.now()
            qtable = agent.getQtable()
            
            data_result = {
                "id_ejecucion": experiment_id,
                "fitness": best_fitness_str,
                "inicio": inicio,
                "fin": fin,
                "mejor_solucion": json.dumps(qtable.tolist())
            }
            
            self.db.insert_best_solution([data_result])
            
            # Mark experiment as complete
            self.db.finish_experiment(experiment_id, datetime.now(), 'terminado')
            
            return True
            
        except Exception as e:
            print(f'Error executing experiment {experiment_id}: {e}')
            self.db.finish_experiment(experiment_id, datetime.now(), 'error')
            return False
    
    def _load_ml_algorithm(self, ml_algorithm):
        """Load ML algorithm class by name."""
        if ml_algorithm == "QL":
            from ..core.machine_learning.QLearning import Q_Learning
            return Q_Learning
        elif ml_algorithm == "SA":
            from ..core.machine_learning.SARSA import SARSA
            return SARSA
        elif ml_algorithm == "BQSA":
            from ..core.machine_learning.BQSA import BQSA
            return BQSA
        elif ml_algorithm == "MAB":
            from ..core.machine_learning.MAB import MAB
            return MAB
        else:
            raise ValueError(f"Unknown ML algorithm: {ml_algorithm}")
    
    def _load_metaheuristic(self, mh_algorithm):
        """Load metaheuristic function by name."""
        if mh_algorithm == "HHO":
            from ..core.metaheuristics.HHO import HHO
            return HHO
        elif mh_algorithm == "GWO":
            from ..core.metaheuristics.GWO import GWO
            return GWO
        elif mh_algorithm == "SCA":
            from ..core.metaheuristics.SCA import SCA
            return SCA
        elif mh_algorithm == "WOA":
            from ..core.metaheuristics.WOA import WOA
            return WOA
        elif mh_algorithm == "CS":
            from ..core.metaheuristics.CS import CS
            return CS
        elif mh_algorithm == "PSO":
            from ..core.metaheuristics.PSO import PSO
            return PSO
        else:
            raise ValueError(f"Unknown metaheuristic: {mh_algorithm}")

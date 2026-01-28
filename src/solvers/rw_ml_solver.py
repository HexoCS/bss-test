"""
Retaining Wall Solver with Machine Learning

Implements metaheuristic optimization for RW enhanced with ML-based
discretization scheme selection.
"""

import os
import numpy as np
import time
from datetime import datetime
import json

from ..database import DatabaseManager
from ..core.problems import RW
from ..core.metrics import Diversidad as dv


class RWMLSolver:
    """
    Solver for Retaining Wall Problem with Machine Learning integration.
    
    This solver combines:
    - Metaheuristic algorithms (GWO, PSO, SCA, WOA, HHO, CS)
    - Machine Learning agents (Q-Learning, SARSA, BQSA, MAB)
    - Adaptive discretization scheme selection
    """
    
    def __init__(self):
        """Initialize solver with database connection."""
        self.db = DatabaseManager()
        self.workdir = os.path.abspath(os.getcwd())
    
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
            problem_name: Problem type (should be 'RW')
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
            instance_name = params_problem['instance_name']
            beta_dis = params_ml.get('beta_dis', 0.8)
            
            problem = RW.RW(instance_name, beta_dis)
            
            # Setup problem parameters
            dim = 6  # RW has 6 decision variables
            population = params_mh['population']
            max_iter = params_mh['maxIter']
            
            params = {}
            params['FO'] = params_problem.get('FO', 'min')
            
            # Initialize population
            matrix_cont = np.random.uniform(low=-1.0, high=1.0, size=(population, dim))
            matrix_dis = problem.generarPoblacionInicial(population, dim)
            fitness = np.zeros(population)
            solutions_ranking = np.zeros(population)
            
            # Initialize ML agent
            agent = ml_agent(params_ml, params_mh)
            action = agent.getAccion(0)
            ds_actions_raw = params_ml['discretizationsScheme']
            
            # Convert SCP format ("V1,Standard") to RW format ("V1") by extracting TF only
            ds_actions = [ds.split(',')[0] if ',' in ds else ds for ds in ds_actions_raw]
            
            params['TF'] = ds_actions[action]
            
            # Initial fitness evaluation
            matrix_dis, fitness, solutions_ranking, best_costo, best_emision, \
                best_volumen, best_kilos = problem.obtenerFitness(
                    matrix_cont, matrix_dis, solutions_ranking, params
                )
            
            # Initialize historical best for PSO and other algorithms
            params['bestHistoricalIndividual'] = matrix_cont.copy()
            params['fitnessHistoricalIndividual'] = fitness.copy()
            
            # Initial diversity calculation
            max_diversidades = np.zeros(7)
            diversidades, max_diversidades, porcentaje_explor, porcentaje_explot, new_states = \
                dv.ObtenerDiversidadYEstado(matrix_dis, max_diversidades)
            state = new_states[0]
            
            # Start optimization
            inicio = datetime.now()
            memory = []
            
            for iter in range(max_iter):
                process_time_start = time.process_time()
                wall_time_start = time.time()
                
                # Apply metaheuristic
                matrix_cont, params = metaheuristic(
                    problem, params, params_mh, matrix_cont,
                    matrix_dis, solutions_ranking, fitness, iter
                )
                
                # Evaluate fitness
                matrix_dis, fitness, solutions_ranking, best_costo, best_emision, \
                    best_volumen, best_kilos = problem.obtenerFitness(
                        matrix_cont, matrix_dis, solutions_ranking, params
                    )
                
                # Preserve best solution and update historical best
                if params['FO'] == 'min':
                    if fitness[solutions_ranking[0]] > params.get('BestFitnessOld', float('inf')):
                        fitness[solutions_ranking[0]] = params['BestFitnessOld']
                        matrix_dis[solutions_ranking[0]] = params['BestBinaryOld']
                    # Update historical best where current fitness is better
                    params['bestHistoricalIndividual'][
                        params['fitnessHistoricalIndividual'] > fitness
                    ] = matrix_cont[params['fitnessHistoricalIndividual'] > fitness]
                    params['fitnessHistoricalIndividual'] = np.minimum(
                        params['fitnessHistoricalIndividual'], fitness
                    )
                else:
                    if fitness[solutions_ranking[0]] < params.get('BestFitnessOld', float('-inf')):
                        fitness[solutions_ranking[0]] = params['BestFitnessOld']
                        matrix_dis[solutions_ranking[0]] = params['BestBinaryOld']
                    # Update historical best where current fitness is better
                    params['bestHistoricalIndividual'][
                        params['fitnessHistoricalIndividual'] < fitness
                    ] = matrix_cont[params['fitnessHistoricalIndividual'] < fitness]
                    params['fitnessHistoricalIndividual'] = np.maximum(
                        params['fitnessHistoricalIndividual'], fitness
                    )
                
                # Calculate diversity
                diversidades, max_diversidades, porcentaje_explor, porcentaje_explot, new_states = \
                    dv.ObtenerDiversidadYEstado(matrix_dis, max_diversidades)
                
                best_fitness_str = str(np.min(fitness))
                
                # ML agent decision for next iteration
                new_state = new_states[0]
                new_action = agent.getAccion(new_state)
                
                # Update Q-table
                agent.updateQtable(np.min(fitness), action, new_action, state, new_state, iter)
                
                # Update for next iteration
                action = new_action
                state = new_state
                params['TF'] = ds_actions[action]
                
                # Calculate timing
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
                        "DS": str(action),
                        "Diversidades": str(diversidades),
                        "PorcentajeExplor": str(porcentaje_explor),
                        "BestCostoTotal": str(best_costo),
                        "BestEmisionTotal": str(best_emision),
                        "BestVolumenHormigon": str(best_volumen),
                        "BestKilosTotalesAcero": str(best_kilos),
                        "Best": str(matrix_dis[solutions_ranking[0]])
                    })
                }
                
                memory.append(data_iter)
                
                # Insert data every 100 iterations to avoid memory issues
                if iter % 100 == 0 and iter > 0:
                    self.db.insert_iteration_data(memory)
                    memory = []
            
            # Insert remaining iteration data
            if len(memory) > 0:
                self.db.insert_iteration_data(memory)
            
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
            import traceback
            traceback.print_exc()
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

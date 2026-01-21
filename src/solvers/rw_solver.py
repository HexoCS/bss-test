"""
Retaining Wall Solver (Non-ML)

Basic metaheuristic solver for RW without machine learning components.
"""

import os
import numpy as np
import time
from datetime import datetime
import json

from ..database import DatabaseManager
from ..core.problems import RW
from ..core.metrics import Diversidad as dv


class RWSolver:
    """
    Basic solver for Retaining Wall Problem.
    
    Uses fixed discretization schemes without ML adaptation.
    """
    
    def __init__(self):
        """Initialize solver with database connection."""
        self.db = DatabaseManager()
        self.workdir = os.path.abspath(os.getcwd())
    
    def solve(self, experiment_id, mh_algorithm, params_mh, ml_algorithm,
              params_ml, problem_name, params_problem):
        """
        Execute basic optimization without ML.
        
        Args:
            experiment_id: Database ID of this experiment
            mh_algorithm: Name of metaheuristic (GWO, PSO, etc.)
            params_mh: Metaheuristic parameters dict
            ml_algorithm: Name of fixed scheme (BCL, MIR)
            params_ml: ML parameters dict (contains discretization scheme)
            problem_name: Problem type (should be 'RW')
            params_problem: Problem-specific parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
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
            
            # Get discretization scheme (fixed for non-ML)
            ds_schemes = params_ml.get('discretizationsScheme', [])
            if ds_schemes:
                # For SCP format "V1,Standard", extract only TF part for RW
                ds_scheme = ds_schemes[0].split(',')[0] if ',' in ds_schemes[0] else ds_schemes[0]
            else:
                ds_scheme = 'V1'
            
            params = {}
            params['TF'] = ds_scheme
            params['FO'] = params_problem.get('FO', 'min')
            
            # Initialize population
            matrix_cont = np.random.uniform(low=-1.0, high=1.0, size=(population, dim))
            matrix_dis = problem.generarPoblacionInicial(population, dim)
            fitness = np.zeros(population)
            solutions_ranking = np.zeros(population)
            
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
            diversidades, max_diversidades, porcentaje_explor, porcentaje_explot, states = \
                dv.ObtenerDiversidadYEstado(matrix_dis, max_diversidades)
            
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
                diversidades, max_diversidades, porcentaje_explor, porcentaje_explot, states = \
                    dv.ObtenerDiversidadYEstado(matrix_dis, max_diversidades)
                
                best_fitness_str = str(np.min(fitness))
                
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
                        "DS": ds_scheme,
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
            
            data_result = {
                "id_ejecucion": experiment_id,
                "fitness": best_fitness_str,
                "inicio": inicio,
                "fin": fin
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

"""
Configuration Management

Handles experiment configuration generation while maintaining
compatibility with the existing database JSON schema.
"""

import yaml
import json
from typing import Dict, List, Any


class ConfigManager:
    """
    Manages experiment configurations.
    
    Responsibilities:
    - Load experiment definitions from YAML
    - Generate parameter combinations
    - Create database-compatible JSON structures
    """
    
    # Discretization scheme definitions
    DISCRETIZATION_SCHEMES = {
        "40a": [
            'S1,Standard', 'S1,Complement', 'S1,Elitist', 'S1,Static', 'S1,ElitistRoulette',
            'S2,Standard', 'S2,Complement', 'S2,Elitist', 'S2,Static', 'S2,ElitistRoulette',
            'S3,Standard', 'S3,Complement', 'S3,Elitist', 'S3,Static', 'S3,ElitistRoulette',
            'S4,Standard', 'S4,Complement', 'S4,Elitist', 'S4,Static', 'S4,ElitistRoulette',
            'V1,Standard', 'V1,Complement', 'V1,Static', 'V1,Elitist', 'V1,ElitistRoulette',
            'V2,Standard', 'V2,Complement', 'V2,Static', 'V2,Elitist', 'V2,ElitistRoulette',
            'V3,Standard', 'V3,Complement', 'V3,Static', 'V3,Elitist', 'V3,ElitistRoulette',
            'V4,Standard', 'V4,Complement', 'V4,Static', 'V4,Elitist', 'V4,ElitistRoulette'
        ],
        "80a": [
            'S1,Standard', 'S1,Complement', 'S1,Elitist', 'S1,Static', 'S1,ElitistRoulette',
            'S2,Standard', 'S2,Complement', 'S2,Elitist', 'S2,Static', 'S2,ElitistRoulette',
            'S3,Standard', 'S3,Complement', 'S3,Elitist', 'S3,Static', 'S3,ElitistRoulette',
            'S4,Standard', 'S4,Complement', 'S4,Elitist', 'S4,Static', 'S4,ElitistRoulette',
            'V1,Standard', 'V1,Complement', 'V1,Static', 'V1,Elitist', 'V1,ElitistRoulette',
            'V2,Standard', 'V2,Complement', 'V2,Static', 'V2,Elitist', 'V2,ElitistRoulette',
            'V3,Standard', 'V3,Complement', 'V3,Static', 'V3,Elitist', 'V3,ElitistRoulette',
            'V4,Standard', 'V4,Complement', 'V4,Static', 'V4,Elitist', 'V4,ElitistRoulette',
            'X1,Standard', 'X1,Complement', 'X1,Static', 'X1,Elitist', 'X1,ElitistRoulette',
            'X2,Standard', 'X2,Complement', 'X2,Static', 'X2,Elitist', 'X2,ElitistRoulette',
            'X3,Standard', 'X3,Complement', 'X3,Static', 'X3,Elitist', 'X3,ElitistRoulette',
            'X4,Standard', 'X4,Complement', 'X4,Static', 'X4,Elitist', 'X4,ElitistRoulette',
            'Z1,Standard', 'Z1,Complement', 'Z1,Static', 'Z1,Elitist', 'Z1,ElitistRoulette',
            'Z2,Standard', 'Z2,Complement', 'Z2,Static', 'Z2,Elitist', 'Z2,ElitistRoulette',
            'Z3,Standard', 'Z3,Complement', 'Z3,Static', 'Z3,Elitist', 'Z3,ElitistRoulette',
            'Z4,Standard', 'Z4,Complement', 'Z4,Static', 'Z4,Elitist', 'Z4,ElitistRoulette'
        ]
    }
    
    REWARD_TYPES = [
        "withPenalty1",
        "withoutPenalty1",
        "globalBest",
        "rootAdaptation",
        "escalatingMultiplicativeAdaptation",
        "percentageImprovement",
        "percentageImprovementAndDeterioration",
        "percentageImprovementAndDeteriorationWithIter"
    ]
    
    POLICY_TYPES = [
        "e-greedy",
        "greedy",
        "e-soft",
        "softMax-rulette",
        "softMax-rulette-elitist"
    ]
    
    @staticmethod
    def load_yaml_config(config_path: str) -> Dict:
        """Load experiment configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @classmethod
    def generate_experiments(cls, config: Dict) -> List[Dict]:
        """
        Generate all experiment combinations from config.
        
        Returns list of experiment dictionaries compatible with
        the database schema.
        """
        experiments = []
        
        exp_config = config['experiment']
        problem = exp_config['problem']
        instances = exp_config.get('instances', [])
        mh_algorithms = exp_config.get('metaheuristics', [])
        ml_algorithms = exp_config.get('machine_learning', [])
        
        params = exp_config['parameters']
        runs = params.get('runs', 1)
        population = params.get('population', 40)
        max_iter = params.get('max_iterations', 1000)
        
        ds_names = params.get('discretization_schemes', ['40a'])
        reward_indices = params.get('reward_types', [0])
        policy_indices = params.get('policy_types', [0])
        
        # Problem-specific params
        problem_params = exp_config.get('problem_params', {})
        fo = problem_params.get('FO', 'min')
        lb = problem_params.get('lb', -10)
        ub = problem_params.get('ub', 10)
        repair_type = problem_params.get('repair_type', 2)
        instance_dir = problem_params.get('instance_dir', 'MSCP/')
        
        # Generate all combinations
        for run in range(runs):
            for instance in instances:
                for mh in mh_algorithms:
                    for ml in ml_algorithms:
                        for ds_name in ds_names:
                            for reward_idx in reward_indices:
                                for policy_idx in policy_indices:
                                    exp = cls._create_experiment(
                                        problem=problem,
                                        instance=instance,
                                        mh=mh,
                                        ml=ml,
                                        ds_name=ds_name,
                                        reward_idx=reward_idx,
                                        policy_idx=policy_idx,
                                        run=run,
                                        population=population,
                                        max_iter=max_iter,
                                        fo=fo,
                                        lb=lb,
                                        ub=ub,
                                        repair_type=repair_type,
                                        instance_dir=instance_dir,
                                        params=params
                                    )
                                    experiments.append(exp)
        
        return experiments
    
    @classmethod
    def _create_experiment(cls, problem, instance, mh, ml, ds_name,
                          reward_idx, policy_idx, run, population, max_iter,
                          fo, lb, ub, repair_type, instance_dir, params):
        """
        Create a single experiment configuration.
        
        This maintains the exact JSON structure required by the database.
        """
        # Algorithm name
        algorithm_name = f"{problem}_{mh}_{ml}_{ds_name}_rw{reward_idx}_pl{policy_idx}"
        
        # Problem parameters
        params_problem = {
            'FO': fo,
            'instance_name': instance,
            'instance_file': f'{instance}.txt',
            'instance_dir': instance_dir,
            'repairType': repair_type,
            'lb': lb,
            'ub': ub
        }
        
        # MH parameters
        params_mh = cls._get_mh_params(mh, population, max_iter, run, params)
        
        # ML parameters
        params_ml = cls._get_ml_params(ml, ds_name, reward_idx, policy_idx, fo, params)
        
        # Database-compatible structure
        experiment = {
            'nombre_algoritmo': algorithm_name,
            'parametros': {
                'MH': mh,
                'paramsMH': params_mh,
                'ML': ml,
                'paramsML': params_ml,
                'problemName': problem,
                'paramsProblem': params_problem
            }
        }
        
        return experiment
    
    @classmethod
    def _get_mh_params(cls, mh, population, max_iter, run, params):
        """Get metaheuristic-specific parameters."""
        base_params = {
            'population': population,
            'maxIter': max_iter,
            'run': run
        }
        
        # Add algorithm-specific parameters
        if mh == "SCA":
            base_params['a_SCA'] = params.get('a_SCA', 2)
        elif mh == "WOA":
            base_params['b_WOA'] = params.get('b_WOA', 1)
        elif mh == "HHO":
            base_params['beta_HHO'] = params.get('beta_HHO', 1.5)
        elif mh == "CS":
            base_params.update({
                'pa_CS': params.get('pa_CS', 0.25),
                'alpha_CS': params.get('alpha_CS', 1),
                'beta_CS': params.get('beta_CS', 1.5)
            })
        elif mh == "PSO":
            base_params.update({
                'Vmax_PSO': params.get('Vmax_PSO', 6),
                'wMax_PSO': params.get('wMax_PSO', 0.9),
                'wMin_PSO': params.get('wMin_PSO', 0.2),
                'c1_PSO': params.get('c1_PSO', 2),
                'c2_PSO': params.get('c2_PSO', 2)
            })
        
        return base_params
    
    @classmethod
    def _get_ml_params(cls, ml, ds_name, reward_idx, policy_idx, fo, params):
        """Get ML-specific parameters."""
        if ml in ["BCL", "MIR"]:
            # For non-ML algorithms, provide a fixed discretization scheme
            return {
                'discretizationsScheme': cls.DISCRETIZATION_SCHEMES.get(ds_name, []),
                'FO': fo,
                'beta_dis': params.get('beta_dis', 0.8)
            }
        
        # Common ML parameters
        ml_params = {
            'discretizationsScheme': cls.DISCRETIZATION_SCHEMES.get(ds_name, []),
            'FO': fo,
            'policyType': cls.POLICY_TYPES[policy_idx],
            'rewardType': cls.REWARD_TYPES[reward_idx],
            'epsilon': params.get('epsilon', 0.1),
            'statesQ': params.get('states_q', 2),
            'W': params.get('W', 10),
            'visitarTodosAlmenosUnaVez': params.get('visit_all_once', True)
        }
        
        # QL/SARSA/BQSA specific
        if ml in ["QL", "SA", "BQSA"]:
            ml_params.update({
                'ql_alpha': params.get('ql_alpha', 0.1),
                'ql_gamma': params.get('ql_gamma', 0.4),
                'qlAlphaType': params.get('ql_alpha_type', 'static'),
                'beta_Dis': params.get('beta_dis', 0.8)
            })
        
        # BQSA specific
        if ml == "BQSA":
            ml_params['cond_backward'] = params.get('cond_backward', 10)
        
        return ml_params

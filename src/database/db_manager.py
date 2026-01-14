"""
Database Module

Handles all database operations for the metaheuristic solver.
Manages experiment queue, results storage, and distributed execution coordination.
"""

import configparser
import os
from datetime import datetime
import json
import sqlalchemy as db
from sqlalchemy.exc import SQLAlchemyError


class DatabaseManager:
    """
    Manages database connections and operations for the distributed solver.
    
    Responsibilities:
    - Database connection management
    - Experiment queue operations (fetch, update status)
    - Results storage (iterations, best solutions)
    - Worker coordination
    """
    
    def __init__(self, config_path=None):
        """
        Initialize database connection.
        
        Args:
            config_path: Path to database.ini file. If None, uses default location.
        """
        if config_path is None:
            # Get to project root: src/database -> src -> project_root
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config',
                'database.ini'
            )
        
        self.engine = self._create_engine(config_path)
        self.metadata = db.MetaData()
    
    def _create_engine(self, config_path):
        """
        Create SQLAlchemy engine from configuration file.
        
        Args:
            config_path: Path to database.ini
            
        Returns:
            SQLAlchemy engine instance
        """
        config = configparser.ConfigParser()
        
        # Read the file and check if it exists
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Database configuration file not found: {config_path}")
        
        config.read(config_path)
        
        # Verify the section exists
        if 'postgres' not in config:
            raise ValueError(f"Missing [postgres] section in {config_path}")
        
        host = config['postgres']['host']
        port = config['postgres']['port']
        user = config['postgres']['user']
        pwd = config['postgres']['pass']
        db_name = config['postgres']['db_name']
        
        connection_string = f'postgresql://{user}:{pwd}@{host}:{port}/{db_name}'
        return db.create_engine(connection_string)
    
    def get_pending_experiment(self):
        """
        Fetch the next pending experiment from the queue.
        
        This method atomically:
        1. Finds the oldest pending experiment
        2. Updates its status to 'ejecutando' (executing)
        3. Sets the start timestamp
        4. Returns the experiment details
        
        Returns:
            tuple: (experiment_id, algorithm_name, parameters_dict)
            If no pending experiments: (0, '', {})
        """
        try:
            connection = self.engine.connect()
            datos_ejecucion = db.Table(
                'datos_ejecucion',
                self.metadata,
                autoload=True,
                autoload_with=self.engine
            )
            
            # Atomic operation: select and update in one query
            sql = db.text("""
                UPDATE datos_ejecucion 
                SET estado = 'ejecutando', inicio = :inicio
                WHERE id = (
                    SELECT id 
                    FROM datos_ejecucion
                    WHERE estado = 'pendiente'
                    ORDER BY id ASC
                    LIMIT 1 
                    FOR UPDATE
                )
                RETURNING id, nombre_algoritmo, parametros;
            """)
            
            inicio = datetime.now()
            result = connection.execute(sql, **{"inicio": inicio}).fetchall()
            
            if result:
                row = result[0]
                experiment_id = row[datos_ejecucion.c.id]
                algorithm_name = row[datos_ejecucion.c.nombre_algoritmo]
                parameters = json.loads(row[datos_ejecucion.c.parametros])
                
                return experiment_id, algorithm_name, parameters
            else:
                return 0, '', {}
                
        except SQLAlchemyError as e:
            print(f"Database error fetching pending experiment: {e}")
            return 0, '', {}
    
    def finish_experiment(self, experiment_id, end_time, status):
        """
        Mark an experiment as finished.
        
        Args:
            experiment_id: ID of the experiment
            end_time: Timestamp when experiment finished
            status: Final status ('completado', 'error', etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            connection = self.engine.connect()
            datos_ejecucion = db.Table(
                'datos_ejecucion',
                self.metadata,
                autoload=True,
                autoload_with=self.engine
            )
            
            update_stmt = datos_ejecucion.update().where(
                datos_ejecucion.c.id == experiment_id
            )
            connection.execute(update_stmt, {'fin': end_time, 'estado': status})
            
            return True
            
        except SQLAlchemyError as e:
            print(f"Database error finishing experiment: {e}")
            return False
    
    def insert_iteration_data(self, iteration_data):
        """
        Insert iteration metrics into the database.
        
        Args:
            iteration_data: List of dictionaries containing iteration metrics
            
        Returns:
            list: Empty list on success, original list on failure
        """
        try:
            connection = self.engine.connect()
            datos_iteracion = db.Table(
                'datos_iteracion',
                self.metadata,
                autoload=True,
                autoload_with=self.engine
            )
            
            insert_stmt = datos_iteracion.insert().returning(datos_iteracion.c.id)
            connection.execute(insert_stmt, iteration_data)
            
            return []
            
        except SQLAlchemyError as e:
            print(f"Database error inserting iteration data: {e}")
            return iteration_data
    
    def insert_best_solution(self, solution_data):
        """
        Insert best solution data into the results table.
        
        Args:
            solution_data: List of dictionaries containing best solution metrics
            
        Returns:
            list: Empty list on success, original list on failure
        """
        try:
            connection = self.engine.connect()
            resultado_ejecucion = db.Table(
                'resultado_ejecucion',
                self.metadata,
                autoload=True,
                autoload_with=self.engine
            )
            
            insert_stmt = resultado_ejecucion.insert().returning(resultado_ejecucion.c.id)
            connection.execute(insert_stmt, solution_data)
            
            return []
            
        except SQLAlchemyError as e:
            print(f"Database error inserting best solution: {e}")
            return solution_data
    
    def create_experiment(self, algorithm_name, parameters, status='pendiente'):
        """
        Create a new experiment in the queue.
        
        Args:
            algorithm_name: Name of the algorithm configuration
            parameters: Dictionary of experiment parameters
            status: Initial status (default: 'pendiente')
            
        Returns:
            int: ID of created experiment, or None on failure
        """
        try:
            connection = self.engine.connect()
            datos_ejecucion = db.Table(
                'datos_ejecucion',
                self.metadata,
                autoload=True,
                autoload_with=self.engine
            )
            
            insert_stmt = datos_ejecucion.insert().returning(datos_ejecucion.c.id)
            
            data = {
                'nombre_algoritmo': algorithm_name,
                'parametros': json.dumps(parameters),
                'estado': status
            }
            
            result = connection.execute(insert_stmt, data)
            experiment_id = result.fetchone()[0]
            
            return experiment_id
            
        except SQLAlchemyError as e:
            print(f"Database error creating experiment: {e}")
            return None
    
    def get_queue_status(self):
        """
        Get statistics about the experiment queue.
        
        Returns:
            dict: Statistics including counts by status
        """
        try:
            connection = self.engine.connect()
            
            sql = db.text("""
                SELECT estado, COUNT(*) as count
                FROM datos_ejecucion
                GROUP BY estado;
            """)
            
            result = connection.execute(sql).fetchall()
            
            stats = {
                'pendiente': 0,
                'ejecutando': 0,
                'completado': 0,
                'error': 0
            }
            
            for row in result:
                status = row[0]
                count = row[1]
                if status in stats:
                    stats[status] = count
            
            stats['total'] = sum(stats.values())
            
            return stats
            
        except SQLAlchemyError as e:
            print(f"Database error getting queue status: {e}")
            return {}

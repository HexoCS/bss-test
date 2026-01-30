import configparser
import os
from datetime import datetime
import json
import sqlalchemy as db
from sqlalchemy import text  # IMPORTANTE: Para evitar el error "name 'text' is not defined"
from sqlalchemy.exc import SQLAlchemyError

class DatabaseManager:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config',
                'database.ini'
            )
        self.engine = self._create_engine(config_path)
        self.metadata = db.MetaData()

    def _create_engine(self, config_path):
        config = configparser.ConfigParser()
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
        config.read(config_path)
        if 'postgres' not in config:
            raise ValueError(f"Falta la sección [postgres] en {config_path}")
        
        c = config['postgres']
        conn_str = f"postgresql://{c['user']}:{c['pass']}@{c['host']}:{c['port']}/{c['db_name']}"
        return db.create_engine(conn_str)

    def get_queue_status(self):
        """Obtiene estadísticas de la cola de experimentos."""
        stats = {'pendiente': 0, 'ejecutando': 0, 'completado': 0, 'error': 0, 'total': 0}
        try:
            with self.engine.connect() as connection:
                sql = text("SELECT estado, COUNT(*) as count FROM datos_ejecucion GROUP BY estado;")
                result = connection.execute(sql).fetchall()
                for row in result:
                    status, count = row[0], row[1]
                    if status in stats:
                        stats[status] = count
                stats['total'] = sum(v for k, v in stats.items() if k != 'total')
            return stats
        except Exception as e:
            print(f"Error crítico en base de datos: {e}")
            return stats

    def get_pending_experiment(self):
        try:
            with self.engine.connect() as connection:
                # Se cargan las tablas dinámicamente si es necesario
                sql = text("""
                    UPDATE datos_ejecucion SET estado = 'ejecutando', inicio = :inicio
                    WHERE id = (SELECT id FROM datos_ejecucion WHERE estado = 'pendiente' 
                    ORDER BY id ASC LIMIT 1 FOR UPDATE)
                    RETURNING id, nombre_algoritmo, parametros;
                """)
                result = connection.execute(sql, {"inicio": datetime.now()}).fetchone()
                if result:
                    return result[0], result[1], json.loads(result[2])
                return 0, '', {}
        except Exception as e:
            print(f"Error al obtener experimento: {e}")
            return 0, '', {}
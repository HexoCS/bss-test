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

    def test_connection(self):
        """Prueba la conexión a la base de datos."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                if result:
                    url_safe = self.engine.url.render_as_string(hide_password=True)
                    print(f"✅ Conexión exitosa a: {url_safe}")
                    return True
        except Exception as e:
            url_safe = self.engine.url.render_as_string(hide_password=True)
            print(f"❌ Error de conexión a: {url_safe}")
            print(f"   Error: {type(e).__name__}: {str(e)}")
            return False

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
            with self.engine.begin() as connection:
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

    def create_experiment(self, algorithm_name, parameters, status='pendiente'):
        """Crea un nuevo experimento en la cola."""
        try:
            with self.engine.begin() as connection:
                # Convertir parámetros a JSON
                params_json = json.dumps(parameters) if isinstance(parameters, dict) else parameters
                
                sql = text("""
                    INSERT INTO datos_ejecucion (nombre_algoritmo, parametros, estado)
                    VALUES (:name, :params, :status)
                    RETURNING id;
                """)
                result = connection.execute(sql, {
                    "name": algorithm_name,
                    "params": params_json,
                    "status": status
                }).fetchone()
                
                return result[0] if result else None
        except Exception as e:
            import traceback
            error_type = type(e).__name__
            error_msg = str(e)
            
            print(f"\n❌ Error al crear experimento [{error_type}]:")
            print(f"   Mensaje: {error_msg}")
            
            # Mostrar conexión (sin password)
            url_safe = self.engine.url.render_as_string(hide_password=True)
            print(f"   Conexión: {url_safe}")
            
            if "could not translate host name" in error_msg.lower():
                print("   → Verifica que 'host' en database.ini sea correcto")
            elif "connection refused" in error_msg.lower():
                print("   → PostgreSQL no está corriendo o el puerto es incorrecto")
            elif "fe_sendauth" in error_msg.lower() or "password" in error_msg.lower():
                print("   → Credenciales incorrectas (usuario/contraseña)")
            elif "does not exist" in error_msg.lower():
                print("   → La base de datos no existe")
            
            print(f"\nTraceback completo:\n{traceback.format_exc()}")
            return None

    def insert_iteration_data(self, memory):
        """Inserta datos de iteración en lote en la tabla datos_iteracion."""
        if not memory:
            return []
        try:
            with self.engine.begin() as connection:
                sql = text("""
                    INSERT INTO datos_iteracion (id_ejecucion, numero_iteracion, fitness_mejor, parametros_iteracion)
                    VALUES (:id_ejecucion, :numero_iteracion, :fitness_mejor, :parametros_iteracion)
                """)
                connection.execute(sql, memory)
            return []
        except Exception as e:
            print(f"Error al insertar datos de iteración: {e}")
            return []

    def insert_best_solution(self, data_list):
        """Inserta el resultado final de un experimento en resultado_ejecucion."""
        if not data_list:
            return
        try:
            with self.engine.begin() as connection:
                for data in data_list:
                    if 'mejor_solucion' in data:
                        sql = text("""
                            INSERT INTO resultado_ejecucion (id_ejecucion, fitness, inicio, fin, mejor_solucion)
                            VALUES (:id_ejecucion, :fitness, :inicio, :fin, :mejor_solucion)
                        """)
                    else:
                        sql = text("""
                            INSERT INTO resultado_ejecucion (id_ejecucion, fitness, inicio, fin)
                            VALUES (:id_ejecucion, :fitness, :inicio, :fin)
                        """)
                    connection.execute(sql, data)
        except Exception as e:
            print(f"Error al insertar resultado: {e}")

    def finish_experiment(self, experiment_id, timestamp, status):
        """Actualiza el estado y timestamp de fin de un experimento."""
        try:
            with self.engine.begin() as connection:
                sql = text("""
                    UPDATE datos_ejecucion SET estado = :status, fin = :fin
                    WHERE id = :id
                """)
                connection.execute(sql, {"status": status, "fin": timestamp, "id": experiment_id})
        except Exception as e:
            print(f"Error al finalizar experimento {experiment_id}: {e}")
"""
Post-Processor CLI

Procesa experimentos terminados y normaliza los datos en tablas optimizadas
para consultas rapidas y generacion de graficos.

Fase 1: Procesa datos a nivel de experimento (rapido)
Fase 2: Procesa datos a nivel de iteracion (opcional, mas lento)

Uso:
    python post_processor.py --f-1
    python post_processor.py --f-1 --limite 1000
"""

import argparse
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import DatabaseManager
import sqlalchemy as db
from sqlalchemy.exc import SQLAlchemyError


def parsear_parametros(params_json):
    """
    Parsea el JSON de parametros y extrae campos relevantes.
    
    Args:
        params_json: String JSON con los parametros del experimento
        
    Returns:
        dict: Diccionario con campos normalizados
    """
    try:
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
        
        resultado = {
            'algoritmo_mh': None,
            'algoritmo_ml': None,
            'problema': None,
            'instancia': None,
            'poblacion': None,
            'iteraciones_totales': None,
            'discretization_scheme': None,
            'reward_type': None,
            'medida_diversidad': None
        }
        
        # Extraer metaheuristica (viene como 'MH')
        resultado['algoritmo_mh'] = params.get('MH')
        
        # Extraer ML (viene como 'ML')
        resultado['algoritmo_ml'] = params.get('ML')
        
        # Extraer problema (viene como 'problemName' a nivel raiz)
        resultado['problema'] = params.get('problemName')
        
        # Extraer parametros del problema
        if 'paramsProblem' in params:
            pp = params['paramsProblem']
            
            # Instancia viene como 'instance_name'
            resultado['instancia'] = pp.get('instance_name')
        
        # Parametros de ejecucion MH
        if 'paramsMH' in params:
            pmh = params['paramsMH']
            resultado['poblacion'] = pmh.get('population')
            resultado['iteraciones_totales'] = pmh.get('maxIter')
        
        # Parametros ML
        if 'paramsML' in params:
            pml = params['paramsML']
            
            # Discretization scheme (viene como array 'discretizationsScheme')
            ds = pml.get('discretizationsScheme')
            if isinstance(ds, list) and len(ds) > 0:
                # Guardar el primero como referencia o 'multiple' si hay varios
                resultado['discretization_scheme'] = f"multiple({len(ds)})"
            elif isinstance(ds, str):
                resultado['discretization_scheme'] = ds
            
            # Reward type (puede ser string como 'percentageImprovement')
            rt = pml.get('rewardType')
            if rt is not None:
                resultado['reward_type'] = str(rt)
            
            # Medida de diversidad (puede no existir en todos los experimentos)
            div_measure = pml.get('diversity_measure') or pml.get('medida_diversidad')
            if div_measure:
                resultado['medida_diversidad'] = str(div_measure)
            
            # Si no hay medida de diversidad explicita, pero hay discretizationsScheme,
            # podria estar implicito en el tipo de experimento
            # Por ahora dejamos como None si no existe
        
        return resultado
        
    except Exception as e:
        print(f"Error parseando parametros: {e}")
        return None


def procesar_fase_1(db_manager, limite=None):
    """
    Fase 1: Procesa experimentos terminados y crea registros normalizados.
    Incluye calculo de promedios de las 6 medidas de diversidad.
    
    Args:
        db_manager: Instancia de DatabaseManager
        limite: Numero maximo de experimentos a procesar (None = todos)
    """
    print("\n=== FASE 1: Procesando experimentos terminados ===")
    print("Calculando promedios de las 6 medidas de diversidad...\n")
    
    try:
        connection = db_manager.engine.connect()
        metadata = db.MetaData()
        
        datos_ejecucion = db.Table(
            'datos_ejecucion',
            metadata,
            autoload=True,
            autoload_with=db_manager.engine
        )
        
        resultado_ejecucion = db.Table(
            'resultado_ejecucion',
            metadata,
            autoload=True,
            autoload_with=db_manager.engine
        )
        
        datos_iteracion = db.Table(
            'datos_iteracion',
            metadata,
            autoload=True,
            autoload_with=db_manager.engine
        )
        
        resultados_normalizados = db.Table(
            'resultados_normalizados',
            metadata,
            autoload=True,
            autoload_with=db_manager.engine
        )
        
        # Obtener experimentos terminados que no han sido procesados
        query = db.text("""
            SELECT de.id, de.parametros, re.fitness, re.inicio, re.fin
            FROM datos_ejecucion de
            LEFT JOIN resultado_ejecucion re ON de.id = re.id_ejecucion
            WHERE de.estado = 'terminado' 
            AND NOT EXISTS (
                SELECT 1 FROM resultados_normalizados rn 
                WHERE rn.id_ejecucion = de.id
            )
            ORDER BY de.id ASC
        """)
        
        if limite:
            query = db.text(str(query) + f" LIMIT {limite}")
        
        experimentos = connection.execute(query).fetchall()
        
        total = len(experimentos)
        print(f"Encontrados {total} experimentos terminados para procesar\n")
        
        if total == 0:
            print("No hay experimentos nuevos para procesar.")
            return
        
        procesados = 0
        errores = 0
        
        for idx, exp in enumerate(experimentos, 1):
            try:
                exp_id = exp[0]
                parametros_json = exp[1]
                fitness_final = float(exp[2]) if exp[2] else None
                inicio = exp[3]
                fin = exp[4]
                
                # Calcular tiempo de ejecucion
                tiempo_ejecucion = None
                if inicio and fin:
                    tiempo_ejecucion = (fin - inicio).total_seconds()
                
                # Parsear parametros
                datos_parseados = parsear_parametros(parametros_json)
                
                if datos_parseados is None:
                    print(f"  [{idx}/{total}] ERROR: No se pudo parsear experimento {exp_id}")
                    errores += 1
                    continue
                
                # Calcular promedios de diversidades desde datos_iteracion
                diversidades_promedio = calcular_diversidades_promedio(connection, exp_id, datos_iteracion)
                
                # Insertar en resultados_normalizados
                insert_data = {
                    'id_ejecucion': exp_id,
                    'algoritmo_mh': datos_parseados['algoritmo_mh'],
                    'algoritmo_ml': datos_parseados['algoritmo_ml'],
                    'problema': datos_parseados['problema'],
                    'instancia': datos_parseados['instancia'],
                    'poblacion': datos_parseados['poblacion'],
                    'iteraciones_totales': datos_parseados['iteraciones_totales'],
                    'discretization_scheme': datos_parseados['discretization_scheme'],
                    'reward_type': datos_parseados['reward_type'],
                    'fitness_final': fitness_final,
                    'tiempo_ejecucion_segundos': tiempo_ejecucion,
                    'diversidad_0_promedio': diversidades_promedio[0],
                    'diversidad_1_promedio': diversidades_promedio[1],
                    'diversidad_2_promedio': diversidades_promedio[2],
                    'diversidad_3_promedio': diversidades_promedio[3],
                    'diversidad_4_promedio': diversidades_promedio[4],
                    'diversidad_5_promedio': diversidades_promedio[5]
                }
                
                insert_stmt = resultados_normalizados.insert()
                connection.execute(insert_stmt, insert_data)
                
                procesados += 1
                
                if idx % 100 == 0:
                    print(f"  Procesados {idx}/{total} experimentos...")
                    
            except Exception as e:
                print(f"  [{idx}/{total}] ERROR procesando experimento {exp[0]}: {e}")
                errores += 1
        
        print(f"\n=== Procesamiento completado ===")
        print(f"Total: {total}")
        print(f"Procesados exitosamente: {procesados}")
        print(f"Errores: {errores}")
        
        # Mostrar estadisticas
        stats_query = db.text("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT problema) as problemas,
                COUNT(DISTINCT instancia) as instancias,
                COUNT(DISTINCT algoritmo_mh) as algoritmos_mh,
                COUNT(DISTINCT algoritmo_ml) as algoritmos_ml,
                COUNT(diversidad_0_promedio) as con_diversidades
            FROM resultados_normalizados
        """)
        
        stats = connection.execute(stats_query).fetchone()
        
        print(f"\n=== Estadisticas de resultados_normalizados ===")
        print(f"Total de registros: {stats[0]}")
        print(f"Problemas unicos: {stats[1]}")
        print(f"Instancias unicas: {stats[2]}")
        print(f"Algoritmos MH unicos: {stats[3]}")
        print(f"Algoritmos ML unicos: {stats[4]}")
        print(f"Experimentos con diversidades: {stats[5]}")
        
    except SQLAlchemyError as e:
        print(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")


def calcular_diversidades_promedio(connection, exp_id, datos_iteracion_table):
    """
    Calcula el promedio de las 6 medidas de diversidad para un experimento.
    
    Args:
        connection: Conexion a la base de datos
        exp_id: ID del experimento
        datos_iteracion_table: Tabla de datos_iteracion
        
    Returns:
        list: Lista con 6 promedios (uno por cada medida de diversidad)
              Retorna [None]*6 si no hay datos de diversidad
    """
    try:
        # Obtener todas las iteraciones del experimento
        query = db.text("""
            SELECT parametros_iteracion
            FROM datos_iteracion
            WHERE id_ejecucion = :exp_id
            ORDER BY numero_iteracion ASC
        """)
        
        iteraciones = connection.execute(query, exp_id=exp_id).fetchall()
        
        if not iteraciones:
            return [None, None, None, None, None, None]
        
        # Arrays para acumular las 6 diversidades
        diversidades_acumuladas = [[] for _ in range(6)]
        
        for row in iteraciones:
            params_json = row[0]
            
            try:
                params = json.loads(params_json) if isinstance(params_json, str) else params_json
                
                # Parsear el campo Diversidades
                if 'Diversidades' in params:
                    div_str = params['Diversidades']
                    
                    # Convertir string "[3.30000e-01 5.26000e+00 ...]" a lista de floats
                    # Remover corchetes y dividir por espacios
                    div_str = div_str.strip('[]')
                    div_values = div_str.split()
                    
                    # Convertir a float y agregar a acumuladores
                    for i, val_str in enumerate(div_values):
                        if i < 6:  # Solo las primeras 6
                            try:
                                diversidades_acumuladas[i].append(float(val_str))
                            except ValueError:
                                pass
                                
            except Exception as e:
                # Si falla parsear una iteracion, continuar con las demas
                continue
        
        # Calcular promedios
        promedios = []
        for diversidad_list in diversidades_acumuladas:
            if diversidad_list:
                promedio = sum(diversidad_list) / len(diversidad_list)
                promedios.append(round(promedio, 4))
            else:
                promedios.append(None)
        
        return promedios
        
    except Exception as e:
        print(f"    Error calculando diversidades para experimento {exp_id}: {e}")
        return [None, None, None, None, None, None]


def main():
    parser = argparse.ArgumentParser(
        description='Post-procesamiento de experimentos terminados'
    )
    parser.add_argument(
        '--f-1',
        action='store_true',
        help='Ejecutar Fase 1: procesar datos a nivel experimento'
    )
    parser.add_argument(
        '--limite',
        type=int,
        default=None,
        help='Limitar el numero de experimentos a procesar (para pruebas)'
    )
    
    args = parser.parse_args()
    
    if not args.f_1:
        print("Debes especificar al menos una fase:")
        print("  --f-1    Procesar datos a nivel experimento")
        return
    
    print("="*60)
    print("POST-PROCESADOR DE EXPERIMENTOS")
    print("="*60)
    
    db = DatabaseManager()
    
    if args.f_1:
        procesar_fase_1(db, limite=args.limite)
    
    print("\n" + "="*60)
    print("Procesamiento finalizado")
    print("="*60)


if __name__ == '__main__':
    main()

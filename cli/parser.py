"""
Parser de Diversidades

Extrae las 6 medidas de diversidad de experimentos terminados,
muestreando cada N iteraciones para analisis y graficacion posterior.

El script espera a que todos los experimentos esten terminados y
luego parsea los datos de iteracion para extraer las diversidades.

Uso:
    python parser.py --intervalo 10
    python parser.py --intervalo 50 --experimento 28662
    python parser.py --intervalo 10 --limite 100
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


def verificar_todos_terminados(db_manager):
    """
    Verifica si todos los experimentos han terminado de ejecutarse.
    
    Args:
        db_manager: Instancia de DatabaseManager
        
    Returns:
        tuple: (bool, dict) - (True si todos terminados, estadisticas)
    """
    try:
        connection = db_manager.engine.connect()
        
        query = db.text("""
            SELECT estado, COUNT(*) as count
            FROM datos_ejecucion
            GROUP BY estado
        """)
        
        resultado = connection.execute(query).fetchall()
        
        stats = {}
        for row in resultado:
            stats[row[0]] = row[1]
        
        pendientes = stats.get('pendiente', 0)
        ejecutando = stats.get('ejecutando', 0)
        
        todos_terminados = (pendientes == 0 and ejecutando == 0)
        
        return todos_terminados, stats
        
    except SQLAlchemyError as e:
        print(f"Error verificando estado: {e}")
        return False, {}


def parsear_diversidades_experimento(connection, exp_id, intervalo=1):
    """
    Parsea las diversidades de un experimento especifico, muestreando cada N iteraciones.
    
    Args:
        connection: Conexion a la base de datos
        exp_id: ID del experimento
        intervalo: Cada cuantas iteraciones muestrear (default: 1 = todas)
        
    Returns:
        dict: Diccionario con estructura:
            {
                'diversidades': [[d0_vals], [d1_vals], ..., [d5_vals]],
                'iteraciones': [num_iter1, num_iter2, ...],
                'metadata': {...}
            }
            Retorna None si no hay datos
    """
    try:
        # Obtener metadatos del experimento
        query_meta = db.text("""
            SELECT de.parametros, re.fitness
            FROM datos_ejecucion de
            LEFT JOIN resultado_ejecucion re ON de.id = re.id_ejecucion
            WHERE de.id = :exp_id
        """)
        
        meta_result = connection.execute(query_meta, exp_id=exp_id).fetchone()
        
        if not meta_result:
            return None
        
        params_json = meta_result[0]
        fitness_final = float(meta_result[1]) if meta_result[1] else None
        
        # Parsear metadata basica
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
        
        metadata = {
            'algoritmo_mh': params.get('MH'),
            'algoritmo_ml': params.get('ML'),
            'problema': params.get('problemName'),
            'instancia': params.get('paramsProblem', {}).get('instance_name'),
            'poblacion': params.get('paramsMH', {}).get('population'),
            'max_iteraciones': params.get('paramsMH', {}).get('maxIter'),
            'fitness_final': fitness_final
        }
        
        # Obtener iteraciones del experimento
        query_iter = db.text("""
            SELECT numero_iteracion, parametros_iteracion
            FROM datos_iteracion
            WHERE id_ejecucion = :exp_id
            ORDER BY numero_iteracion ASC
        """)
        
        iteraciones = connection.execute(query_iter, exp_id=exp_id).fetchall()
        
        if not iteraciones:
            return None
        
        # Inicializar listas para las 6 diversidades
        diversidades = [[] for _ in range(6)]
        iteraciones_muestreadas = []
        
        # Procesar cada iteracion (muestrear segun intervalo)
        for row in iteraciones:
            num_iter = row[0]
            params_iter_json = row[1]
            
            # Muestrear solo las iteraciones que correspondan
            if num_iter % intervalo != 0 and num_iter != 1:
                continue
            
            try:
                params_iter = json.loads(params_iter_json) if isinstance(params_iter_json, str) else params_iter_json
                
                # Parsear el campo Diversidades
                if 'Diversidades' in params_iter:
                    div_str = params_iter['Diversidades']
                    
                    # Convertir string "[3.30000e-01 5.26000e+00 ...]" a lista de floats
                    div_str = div_str.strip('[]')
                    div_values = div_str.split()
                    
                    # Agregar cada diversidad a su lista correspondiente
                    for i, val_str in enumerate(div_values):
                        if i < 6:
                            try:
                                diversidades[i].append(float(val_str))
                            except ValueError:
                                diversidades[i].append(None)
                    
                    iteraciones_muestreadas.append(num_iter)
                    
            except Exception as e:
                # Si falla parsear una iteracion, continuar
                continue
        
        # Verificar que tengamos datos
        if not iteraciones_muestreadas:
            return None
        
        resultado = {
            'diversidades': diversidades,
            'iteraciones': iteraciones_muestreadas,
            'metadata': metadata
        }
        
        return resultado
        
    except Exception as e:
        print(f"    Error parseando experimento {exp_id}: {e}")
        return None


def parsear_todos_experimentos(db_manager, intervalo=1, limite=None, exp_especifico=None):
    """
    Parsea diversidades de todos los experimentos terminados.
    
    Args:
        db_manager: Instancia de DatabaseManager
        intervalo: Cada cuantas iteraciones muestrear
        limite: Numero maximo de experimentos a procesar (None = todos)
        exp_especifico: ID de experimento especifico a procesar (None = todos)
        
    Returns:
        dict: Diccionario con estructura {exp_id: datos_experimento}
    """
    print(f"\n=== PARSER DE DIVERSIDADES ===")
    print(f"Intervalo de muestreo: cada {intervalo} iteraciones\n")
    
    try:
        connection = db_manager.engine.connect()
        
        # Obtener lista de experimentos terminados
        if exp_especifico:
            query = db.text("""
                SELECT id
                FROM datos_ejecucion
                WHERE id = :exp_id AND estado = 'terminado'
            """)
            experimentos = connection.execute(query, exp_id=exp_especifico).fetchall()
        else:
            query = db.text("""
                SELECT id
                FROM datos_ejecucion
                WHERE estado = 'terminado'
                ORDER BY id ASC
            """)
            
            if limite:
                query = db.text(str(query) + f" LIMIT {limite}")
            
            experimentos = connection.execute(query).fetchall()
        
        total = len(experimentos)
        print(f"Encontrados {total} experimentos terminados para parsear\n")
        
        if total == 0:
            print("No hay experimentos terminados.")
            return {}
        
        # Parsear cada experimento
        resultados = {}
        procesados = 0
        errores = 0
        
        for idx, row in enumerate(experimentos, 1):
            exp_id = row[0]
            
            try:
                datos = parsear_diversidades_experimento(connection, exp_id, intervalo)
                
                if datos is not None:
                    resultados[exp_id] = datos
                    procesados += 1
                    
                    if idx % 100 == 0:
                        print(f"  Procesados {idx}/{total} experimentos...")
                else:
                    errores += 1
                    
            except Exception as e:
                print(f"  [{idx}/{total}] ERROR en experimento {exp_id}: {e}")
                errores += 1
        
        print(f"\n=== Parseo completado ===")
        print(f"Total: {total}")
        print(f"Parseados exitosamente: {procesados}")
        print(f"Errores: {errores}")
        
        # Estadisticas rapidas
        if resultados:
            tamaños_muestra = [len(datos['iteraciones']) for datos in resultados.values()]
            promedio_puntos = sum(tamaños_muestra) / len(tamaños_muestra)
            print(f"\nPromedio de puntos muestreados por experimento: {promedio_puntos:.1f}")
            print(f"Total de puntos de datos: {sum(tamaños_muestra)}")
        
        return resultados
        
    except SQLAlchemyError as e:
        print(f"Error de base de datos: {e}")
        return {}
    except Exception as e:
        print(f"Error inesperado: {e}")
        return {}


def guardar_muestra(resultados, nombre_archivo='diversidades_muestreadas.json'):
    """
    Guarda una muestra de los resultados en un archivo JSON para inspeccion.
    
    Args:
        resultados: Diccionario con resultados parseados
        nombre_archivo: Nombre del archivo de salida
    """
    if not resultados:
        print("No hay datos para guardar muestra")
        return
    
    # Tomar primer experimento como muestra
    primer_exp_id = list(resultados.keys())[0]
    muestra = {
        'experimento_id': primer_exp_id,
        'datos': resultados[primer_exp_id]
    }
    
    try:
        with open(nombre_archivo, 'w') as f:
            json.dump(muestra, f, indent=2)
        print(f"\nMuestra guardada en: {nombre_archivo}")
    except Exception as e:
        print(f"Error guardando muestra: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Parser de diversidades de experimentos terminados'
    )
    parser.add_argument(
        '--intervalo',
        type=int,
        default=10,
        help='Intervalo de muestreo (cada N iteraciones, default: 10)'
    )
    parser.add_argument(
        '--limite',
        type=int,
        default=None,
        help='Limitar numero de experimentos a procesar (para pruebas)'
    )
    parser.add_argument(
        '--experimento',
        type=int,
        default=None,
        help='ID de experimento especifico a procesar'
    )
    parser.add_argument(
        '--verificar',
        action='store_true',
        help='Solo verificar si todos los experimentos han terminado'
    )
    parser.add_argument(
        '--guardar-muestra',
        action='store_true',
        help='Guardar una muestra de los resultados en JSON'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("PARSER DE DIVERSIDADES")
    print("="*60)
    
    db = DatabaseManager()
    
    # Verificar estado de experimentos
    todos_terminados, stats = verificar_todos_terminados(db)
    
    print("\n=== Estado de experimentos ===")
    print(f"Pendientes: {stats.get('pendiente', 0)}")
    print(f"Ejecutando: {stats.get('ejecutando', 0)}")
    print(f"Terminados: {stats.get('terminado', 0)}")
    print(f"Errores: {stats.get('error', 0)}")
    
    if args.verificar:
        if todos_terminados:
            print("\nTodos los experimentos han terminado. Listo para parsear.")
        else:
            print("\nAun hay experimentos pendientes o en ejecucion.")
        return
    
    if not todos_terminados and not args.experimento:
        print("\nADVERTENCIA: Hay experimentos pendientes o ejecutando.")
        respuesta = input("Continuar de todas formas? (s/n): ")
        if respuesta.lower() != 's':
            print("Parseo cancelado.")
            return
    
    # Parsear experimentos
    resultados = parsear_todos_experimentos(
        db, 
        intervalo=args.intervalo,
        limite=args.limite,
        exp_especifico=args.experimento
    )
    
    if args.guardar_muestra and resultados:
        guardar_muestra(resultados)
    
    print("\n" + "="*60)
    print("PARSEO FINALIZADO")
    print("="*60)
    print("\nLos datos estan listos para ser utilizados por scripts de graficacion.")
    print(f"Total de experimentos parseados: {len(resultados)}")
    
    # Retornar resultados para uso programatico
    return resultados


if __name__ == '__main__':
    resultados = main()

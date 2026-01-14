#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 23:00:31 2019

@author: mauri
"""

# import readOrProblems as rOP
from . import solution as sl
from . import heuristic as he
import random
import numpy as np

class ReparaStrategy:

    def __init__(self, matrix, pesos, row, cols):
        
        """
    Inicializa la estrategia de reparacion para soluciones del problema SCP.
    
    Args:
        matrix (numpy.ndarray): Matriz de cobertura del problema.
        pesos (numpy.ndarray): Vector de costos de cada columna.
        row (int): Numero de filas (restricciones) del problema.
        cols (int): Numero de columnas (variables) del problema.
    """
        
        
        matrix = np.array(matrix)
        self.rows = row
        self.cols = cols
        self.pesos = np.array(pesos)
        self.matrix = matrix
        self.rHeuristic = he.getRowHeuristics(matrix)
        self.dictCol = he.getColumnRow(matrix)
        self.dictcHeuristics = {}
        self.cHeuristic = []
        self.lSolution = []
        self.dict = he.getRowColumn(matrix)

    def repara_one(self,solution,repair):
        
        """
    Aplica una estrategia de reparacion especifica a una solucion infactible.
    
    Selecciona y ejecuta el metodo de reparacion segun el parametro 'repair'.
    Las estrategias disponibles son reparacion simple (greedy local) o
    reparacion compleja (construccion completa de solucion).

    Args:
        solution (list): Lista binaria representando la solucion a reparar.
        repair (int): Identificador de la estrategia de reparacion.
                     - 1: Reparacion simple (reparaSimple).
                     - 2: Reparacion compleja (reparaComplejo).

    Returns:
        tuple: Tupla con 2 elementos:
               - solucion_reparada (list): Lista binaria con la solucion factible.
               - numero_reparaciones (int): Cantidad de modificaciones realizadas.
    """
        if repair == 1:
            return self.reparaSimple(solution)
        elif repair == 2:
            return self.reparaComplejo(solution)
        
        
        
    def reparaComplejo(self, solution):
        
        """
    Repara una solucion mediante construccion completa usando heuristicas avanzadas.
    
    Extrae las columnas activas de la solucion inicial y reconstruye una solucion
    factible utilizando el algoritmo de generacion de solucion con heuristicas
    de filas y columnas, diccionarios de cobertura y estrategias de seleccion.

    Args:
        solution (list): Lista binaria representando la solucion inicial a reparar.

    Returns:
        tuple: Tupla con 2 elementos (solucion_reparada, numero_reparaciones).
               - solucion_reparada (list): Lista binaria con la solucion factible completa.
               - numero_reparaciones (int): Cantidad de operaciones de reparacion realizadas.
    """
        
        
        lSolution = [i for i in range(len(solution)) if solution[i] == 1]
        lSolution, numReparaciones = sl.generaSolucion(lSolution, self.matrix, self.pesos, self.rHeuristic,
                                                       self.dictcHeuristics, self.dict, self.cHeuristic, self.dictCol)
        sol = np.zeros(self.cols, dtype=np.float64)
        sol[lSolution] = 1
        return sol.tolist(), numReparaciones

    def reparaSimple(self, solution):
        
        """
    Repara una solucion mediante seleccion greedy de columnas para filas descubiertas.
    
    Itera aleatoriamente sobre las filas del problema. Si una fila no esta cubierta,
    selecciona la columna de menor costo que la cubra y la agrega a la solucion.
    Este metodo es mas rapido pero puede generar soluciones de mayor costo.

    Args:
        solution (list): Lista binaria representando la solucion a reparar.

    Returns:
        tuple: Tupla con 2 elementos (solucion_reparada, numero_reparaciones).
               - solucion_reparada (list): Lista binaria con la solucion factible.
               - numero_reparaciones (int): Numero de columnas agregadas durante la reparacion.
    """
        
        
        numRep = 0
        indices = list(range(self.rows))
        random.shuffle(indices)
        for i in indices:
            if np.sum(self.matrix[i] * solution) < 1:
                idxRestriccion = np.argwhere((self.matrix[i]) > 0)
                idxMenorPeso = idxRestriccion[np.argmin(self.pesos[idxRestriccion])]
                solution[idxMenorPeso[0]] = 1
                numRep += 1
        return solution, numRep

    def cumple(self, solucion):
        
        """
    Verifica si una solucion es factible.
    
    Comprueba que todas las filas (restricciones) esten cubiertas por al menos
    una columna activa en la solucion.

    Args:
        solucion (list): Lista binaria representando la solucion a verificar.

    Returns:
        int: 1 si la solucion es factible (todas las filas cubiertas), 0 si es infactible.
    """
        
        
        for i in range(self.rows):
            if np.sum(self.matrix[i] * solucion) < 1: return 0
        return 1
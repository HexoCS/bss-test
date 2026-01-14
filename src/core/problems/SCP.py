import numpy as np
import os

#Gracias Mauricio Y Lemus!
from .repair import ReparaStrategy as repara
from ..discretization import DiscretizationScheme as DS

#action : esquema de discretizacion DS
class SCP:
    def __init__(self,workdirInstance, instance_dir, instance_file):
        """Inicializa una instancia del Set Covering Problem.

        Args:
            workdirInstance (str): Directorio de trabajo base donde se encuentran las instancias.
            instance_dir (str): Subdirectorio que contiene la instancia especifica
            instance_file (str): Nombre del archivo de la instancia.
        """
        self.workdirInstance = workdirInstance
        self.instance_dir = instance_dir
        self.instance_file = instance_file
        
    def obtenerInstancia(self):
        """Obtiene la ruta completa de la instancia del problema.    

        Returns:
            str: Ruta completa del archivo de la instancia.
        """
        return os.path.join(self.workdirInstance, self.instance_dir, self.instance_file)

    def obtenerFitness(self,poblacion,matrix,solutionsRanking,paramsProblem):
        
        """Calcula el fitness de toda la poblacion aplicando discretizacion y reparacion.
        Aplica discretizacion, repara aquellas que no cumplen con restricciones de cobertura y calcula costo total de cada solucion.

        Args:
            poblacion (numpy.ndarray): Matriz donde cada fila representa una solucion continua.
            matrix (numpy.ndarray): Matriz de soluciones discretizadas.
            solutionsRanking (numpy.ndarray): Ranking de soluciones basado en su fitness.
            paramsProblem (dict): Diccionario con parámetros del problema:
                             - "costos" (numpy.ndarray): Vector de costos de cada conjunto.
                             - "cobertura" (numpy.ndarray): Matriz de cobertura del problema.
                             - "ds" (str): Esquema de discretizacion en formato "TF,BO".
                             - "repairType" (str): Estrategia de reparacion.
        Returns:
            tuple: Una tupla con 4 elementos:
               - matrix (numpy.ndarray): Matriz de soluciones discretizadas y reparadas.
               - fitness (numpy.ndarray): Vector con el fitness de cada solucion.
               - solutionsRanking (numpy.ndarray): Indices ordenados de menor a mayor fitness.
               - numReparaciones (int): Numero total de reparaciones realizadas en la poblacion.
        """
        
        
                
        costos = paramsProblem["costos"]
        cobertura = paramsProblem["cobertura"]
        ds = paramsProblem["ds"]
        repairType = paramsProblem["repairType"]

        ds = ds.split(",")
        ds = DS.DiscretizationScheme(poblacion,matrix,solutionsRanking,ds[0],ds[1])
        matrix = ds.binariza()

        repair = repara.ReparaStrategy(cobertura,costos,cobertura.shape[0],cobertura.shape[1])
        matrizSinReparar = matrix
        for solucion in range(matrix.shape[0]):
            if repair.cumple(matrix[solucion]) == 0:
                matrix[solucion] = repair.repara_one(matrix[solucion],repairType)[0]
        matrizReparada = matrix
        numReparaciones = np.sum(np.abs(matrizReparada - matrizSinReparar))

        #Calculamos Fitness
        fitness = np.sum(np.multiply(matrix,costos),axis =1)
        solutionsRanking = np.argsort(fitness) # rankings de los mejores fitness

        return matrix,fitness,solutionsRanking,numReparaciones



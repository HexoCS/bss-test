import numpy as np
import math

#action : esquema de discretizacion DS
def MomentoDeInercia(Poblacion):
  """
  Calcula el Momento de Inercia de una poblacion
  Args:
    Poblacion (np.array): Matriz de población donde cada fila es un individuo y cada columna una dimensión.
  Returns:
    float: Valor del Momento de Inercia de la población.
  """

  Diversidad = 0
  N = Poblacion.shape[0]
  D = Poblacion.shape[1]
  promedio = np.mean(Poblacion, axis=0)
  MatrizDiversidad = np.power((Poblacion - promedio),2)

  Diversidad = np.sum(MatrizDiversidad)

  return Diversidad

def Hamming(Poblacion):
  """
  Calcula la diversidad de Hamming de una poblacion. 
  Args:
    Poblacion (np.array): Matriz de población donde cada fila es un individuo y cada columna una dimensión.
  Returns:      
    float: Valor de la diversidad de Hamming de la población.
  """

  Diversidad = 0
  frecuencias0 = []
  frecuencias1 = []
  
  for d in range(len(Poblacion[0])):
    frecuencia0 = 0
    frecuencia1 = 0
    
    for p in range(len(Poblacion)):
      if Poblacion[p][d] == 0:
        frecuencia0 = frecuencia0 + 1
      else:
        frecuencia1 = frecuencia1 + 1
    
    frecuencias0.append(frecuencia0)
    frecuencias1.append(frecuencia1)

  sumatoria = 0
  for d in range(len(Poblacion[0])):
    n = len(Poblacion)
    sumatoria = sumatoria + (frecuencias0[d]/n) * (1 - (frecuencias0[d]/n))
    sumatoria = sumatoria + (frecuencias1[d]/n) * (1 - (frecuencias1[d]/n))

  Diversidad = ((len(Poblacion)**2) / (2 * len(Poblacion[0]))) * sumatoria

  return Diversidad

def Entropica(Poblacion):
  """
  Calcula la diversidad entropica de una poblacion.
  Args:
      Poblacion (np.array): Matriz de población donde cada fila es un individuo y cada columna una dimensión.

  Returns:      
      float: Valor de la diversidad entropica de la población.
  """
  Diversidad = 0
  frecuencias0 = []
  frecuencias1 = []
  
  for d in range(len(Poblacion[0])):
    frecuencia0 = 0
    frecuencia1 = 0
    
    for p in range(len(Poblacion)):
      if Poblacion[p][d] == 0:
        frecuencia0 = frecuencia0 + 1
      else:
        frecuencia1 = frecuencia1 + 1
    
    frecuencias0.append(frecuencia0)
    frecuencias1.append(frecuencia1)

  sumatoria = 0
  for d in range(len(Poblacion[0])):
    n = len(Poblacion)
    if frecuencias0[d] != 0 and frecuencias1[d] != 0:
      sumatoria = sumatoria + (frecuencias0[d]/n) * (math.log(frecuencias0[d]/n))
      sumatoria = sumatoria + (frecuencias1[d]/n) * (math.log(frecuencias1[d]/n))

  Diversidad = (-1 / (len(Poblacion[0]))) * sumatoria

  return Diversidad


def LeungGaoXu(Poblacion):
  """
  Calcula la métrica de diversidad Leung-Gao-Xu (LGX) para una población.
  Esta métrica evalúa la uniformidad de las soluciones a lo largo del frente 
  de Pareto (o las soluciones ordenadas). Una mayor diversidad indica una mejor distribución de soluciones.
  Args:
      Poblacion (np.array): Matriz de población donde cada fila es un individuo y cada columna una dimensión.
  Returns:
      float: Valor de la diversidad de Leung Gao Xu de la población.
  """
  Diversidad = 0
  frecuencias0 = []
  frecuencias1 = []
  n = len(Poblacion)
  for d in range(len(Poblacion[0])):
    frecuencia0 = 0
    frecuencia1 = 0
    
    for p in range(len(Poblacion)):
      if Poblacion[p][d] == 0:
        frecuencia0 = frecuencia0 + 1
      else:
        frecuencia1 = frecuencia1 + 1
    
    frecuencias0.append(frecuencia0/n)
    frecuencias1.append(frecuencia1/n)

  sumatoria = 0
  for d in range(len(Poblacion[0])):
    
    sumatoria = sumatoria + g(frecuencias0[d]) * g(1- frecuencias0[d])

  Diversidad =  sumatoria

  return Diversidad

def g(frecuencia):

  if frecuencia == 0 or frecuencia == 1:
    g = frecuencia
  else:
    g = 1

  return g

def Dimensional(Poblacion):
  """
  Calcula la media de diferencias absolutas entre la mediana de cada individuo y cada dimensión
  Args:
      Poblacion (np.array): Matriz de población donde cada fila es un individuo y cada columna una dimensión.
  Returns:
      float: Valor de la diversidad dimensional de la población.
  """

  Diversidad = 0
  MatrizDiversidad = np.zeros((len(Poblacion)))
  Pob = np.array(Poblacion)
  Promedio = np.median(Poblacion, axis=1)

  for d in range(len(Poblacion[0])):
    Divj = 0
    MatrizDiversidad = abs(Promedio  - Pob[:,d])
    Diversidad = Diversidad + MatrizDiversidad.sum()/len(Poblacion[0])
        
  Diversidad = Diversidad / len(Poblacion)

  return Diversidad

def PesosDeInercia(Poblacion):
  """
  Calcula la diversidad de Pesos de Inercia de una poblacion
  Args:
      Poblacion (np.array): Matriz de población donde cada fila es un individuo y cada columna una dimensión.
  Returns:
      float: Valor de la diversidad de Pesos de Inercia de la población.
  """

  Pob = Poblacion
  N = Pob.shape[0]
  D = Pob.shape[1]
  promedio = np.mean(Poblacion, axis=0)
  
  MatrizDiversidad = np.divide((np.sqrt(np.sum((np.power((Pob - promedio),2)), axis=1))),N)
  Diversidad = np.sum(MatrizDiversidad)

  return Diversidad

def DimensionalHussain(Poblacion):
  """
  Suma normalizada de diferencias absolutas entre medias y población, dividida por N y D
  Args:
      Poblacion (np.array): Matriz de población donde cada fila es un individuo y cada columna una dimensión.
      
  Returns:
      float: Valor de la diversidad dimensional de Hussain de la población.
  """

  Pob = np.array(Poblacion)
  N = Pob.shape[0]
  D = Pob.shape[1]
  Medias = np.mean(Poblacion, axis=0)
  
  MatrizDiversidad = np.divide(np.divide(np.abs(Medias - Pob),N),D)
    
  Diversidad = np.sum(MatrizDiversidad)

  return Diversidad

def ObtenerDiversidadYEstado(Poblacion,maxDiversidades):
  """
    Calcula las diversidades de una población, actualiza máximos históricos 
    y determina el estado de exploración/explotación.

    Args:
        Poblacion (np.array): Matriz de población donde cada fila es un individuo 
                              y cada columna una dimensión.
        maxDiversidades (list): Lista con los valores máximos históricos de cada diversidad.

    Returns:
        tuple: Una tupla con las métricas de diversidad y estado en el siguiente orden:
              1. diversidades (np.array): Valores de las 6 diversidades calculadas.
              2. maxDiversidades (np.array): Máximos históricos de cada diversidad.
              3. PorcentajeExplor (np.array): Porcentaje de exploración.
              4. PorcentajeExplot (np.array): Porcentaje de explotación.
              5. state (list): Estado de la exploración (1=Exploración, 0=Explotación).
  """
  #Calculamos las diversidades
  diversidades = []
  diversidades.append(DimensionalHussain(Poblacion)) #0
  diversidades.append(PesosDeInercia(Poblacion)) #1
  diversidades.append(LeungGaoXu(Poblacion)) #2
  diversidades.append(Entropica(Poblacion)) #3
  diversidades.append(Hamming(Poblacion)) #4
  diversidades.append(MomentoDeInercia(Poblacion)) #5

  #Actualizar maxDiversidades y calculamos PorcentajeExplor PorcentajeExplot
  PorcentajeExplor = []
  PorcentajeExplot = []
  state = []
  for i in range(len(diversidades)):
    # Actualizar máximo si es necesario
    if diversidades[i] > maxDiversidades[i]:
      maxDiversidades[i] = diversidades[i]
    
    # Calcular porcentajes siempre (no solo cuando actualiza el máximo)
    if maxDiversidades[i] > 0:
      PorcentajeExplor.append((diversidades[i]/maxDiversidades[i])*100)
      PorcentajeExplot.append((abs(diversidades[i]-maxDiversidades[i])/maxDiversidades[i])*100)
      
      #Determinar estado
      if PorcentajeExplor[i] >= PorcentajeExplot[i]:
          state.append(1) # Exploración
      else:
          state.append(0) # Explotación
    else:
      # Caso cuando maxDiversidades[i] es 0
      PorcentajeExplor.append(0.0)
      PorcentajeExplot.append(0.0)
      state.append(1) # Asumir exploración por defecto
    #return diversidades, maxDiversidades, PorcentajeExplor, PorcentajeExplot, state
  return np.around(diversidades,2), np.around(maxDiversidades,2), np.around(PorcentajeExplor,2), np.around(PorcentajeExplot,2), state
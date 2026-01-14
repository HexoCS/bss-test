__author__ = 'INVESTIGACION'
import numpy as np
from copy import deepcopy
import math

def getHeuristic(matrix, pesos):
    """
    Calcula la heuristica Cj/Pj para cada columna del problema SCP.
    
    Pi se obtiene por el numero de filas que cubre la columna. La heuristica
    ordena las columnas de menor a mayor costo relativo de cobertura.

    Args:
        matrix (numpy.ndarray): Matriz de cobertura del problema.
        pesos (numpy.ndarray): Vector de costos/pesos de cada columna.

    Returns:
        numpy.ndarray: Matriz de 2 columnas ordenada por heuristica ascendente.
                      - Columna 0: Indice de la columna.
                      - Columna 1: Valor heuristico (costo/cobertura).
    """
    lHeuristic = np.zeros((len(pesos),2)) # Dos columnas. La primera para indicar la columna la segunda para la Heuristica
    for i in range(0,len(pesos)):
        lHeuristic[i,0] = int(i)
        #print i,sum(matrix[:,i]), pesos[i], float(pesos[i]/sum(matrix[:,i]))
        lHeuristic[i,1] = float(pesos[i]/sum(matrix[:,i]))

        #lHeuristic[lHeuristic[:,1].argsort()]
    return lHeuristic[lHeuristic[:,1].argsort()]

def getRowHeuristics(matrix):
    """
    Calcula la importancia para cada fila del problema.
    Para cada fila, calcula 1/Cubrimiento. Mientras menos cubrimiento tenga
    una fila, mas importante es cubrirla.
    Args:
        matrix (numpy.ndarray): Matriz de cobertura del problema.

    Returns:
        numpy.ndarray: Matriz de 2 columnas ordenada por heuristica ascendente.
                      - Columna 0: Indice de la fila.
                      - Columna 1: Valor heuristico (1/suma_cobertura).
    """
    row, col = matrix.shape
    rHeuristic = np.zeros((row,2)) # Dos columnas. La primera para indicar la columna la segunda para la Heuristica
    for i in range(0,row):
        rHeuristic[i,0] = int(i)
        #print (i,sum(matrix[:,i]), pesos[i], float(pesos[i]/sum(matrix[:,i])))
        rHeuristic[i,1] = 1/sum(matrix[i,:])
    return rHeuristic[rHeuristic[:,1].argsort()]

def getRowColumn(matrix):
    """
    Genera un diccionario que mapea cada fila con las columnas que la cubren.

    Args:
        matrix (numpy.ndarray): Matriz de cobertura del problema (filas x columnas).

    Returns:
        dict: Diccionario donde cada llave es un índice de fila y su valor
              es una lista con los índices de las columnas que cubren esa fila.
    """
    nrow, ncol = matrix.shape
    dict = {}
    for i in range(0,nrow):
        list = []
        for j in range(0,ncol):
            if matrix[i,j]==1:
                list.append(j)
        dict[i] = deepcopy(list)
    return dict

def getColumnRow(matrix):
    """
    Genera un diccionario que mapea cada columna con las filas que cubre.

    Args:
        matrix (numpy.ndarray): Matriz de cobertura del problema (filas x columnas).

    Returns:
        dict: Diccionario donde cada llave es un índice de columna y su valor es una lista con los índices de las filas que cubre esa columna.
    """
    nrow, ncol = matrix.shape
    dictCol = {}
    for j in range(0,ncol):
        list = []
        for i in range(0,nrow):
            if matrix[i,j]==1:
                list.append(i)
        dictCol[j] = deepcopy(list)
    return dictCol

def getProposedRows(uRows,rHeuristic,lparam):
    """
        Selecciona las filas más importantes de entre las filas no cubiertas.
        
        Utiliza la heurística de filas (1/cobertura) para proponer las lparam filas más críticas que requieren ser cubiertas.

        Args:
            uRows (list): Lista de índices de filas no cubiertas (Uncovered Rows).
            rHeuristic (numpy.ndarray): Matriz de heurísticas de filas ordenada ascendentemente.
            Cada fila contiene [índice_fila, 1/suma_cobertura].
            lparam (int): Número de filas propuestas a retornar.

        Returns:
            list: Lista con los índices de las filas propuestas (máximo lparam elementos).
        """
    pRows = []
    contador = 1
    if len(uRows) < lparam:
        pRows = uRows
    else:
        while len(pRows) < lparam:
            if  rHeuristic[len(rHeuristic)-contador,0] in uRows:
                pRows.append(rHeuristic[len(rHeuristic)-contador,0])
            contador = contador + 1
            if contador > len(rHeuristic):
                break
    return pRows

def getProposedColumns(uColumns, cHeuristic,lparam):
    """
    Selecciona las mejores columnas de entre las columnas no utilizadas.
    
    Utiliza la heurística de columnas Cj/Pj donde Cj es el costo de la columna y Pj es el número de filas que cubre. Para proponer las lparam mejores columnas según su relación costo/cobertura. Las columnas
    con menor relación costo/cobertura tienen mayor prioridad.

    Args:
        uColumns (list): Lista de índices de columnas no utilizadas.
        cHeuristic (numpy.ndarray): Matriz de heurísticas de columnas ordenada ascendentemente.
        Cada fila contiene [índice_columna, costo/cobertura].
        lparam (int): Número de columnas propuestas a retornar.

    Returns:
        list: Lista con los índices de las columnas propuestas (máximo lparam elementos).
    """
    pColumns = []
    contador = 0
    #print 'Cuantas columnas propuestas', len(uColumns)

    while len(pColumns) < lparam:
        #print uColumns
        if  cHeuristic[contador,0] in uColumns:
            pColumns.append(cHeuristic[contador,0])
        if contador == len(cHeuristic)-1:
            break
        contador = contador + 1
    return pColumns

def getProposedColumnsNew(uColumns, dictcHeuristics ,lparam):
    """
    Selecciona las mejores columnas usando un diccionario de heurísticas.
    
    Versión mejorada que utiliza un diccionario para acceder directamente
    a los valores heurísticos de cada columna.

    Args:
        uColumns (list): Lista de índices de columnas no utilizadas.
        dictcHeuristics (dict): Diccionario con valores heurísticos por columna.
        lparam (int): Número de columnas propuestas a retornar.

    Returns:
        numpy.ndarray: Array con los índices de las columnas propuestas ordenadas por su valor heurístico (máximo lparam elementos).
    """
    pColumns = []
    tColumns = np.zeros((len(uColumns),2))
    contador = 0
    #print 'Cuantas columnas propuestas', len(uColumns)

    for i in range(0,len(uColumns)):
        tColumns[i,0] = uColumns[i]
        tColumns[i,1] = dictcHeuristics[uColumns[i]]


    return  tColumns[tColumns[:,1].argsort()][0:lparam,0]

def getProposedColumnsDict(uColumns,dictcHeuristics,lparam):
    """
    Selecciona las mejores columnas usando diccionario y retorna una lista.
    

    Args:
        uColumns (list): Lista de índices de columnas no utilizadas.
        dictcHeuristics (dict): Diccionario con valores heurísticos por columna.
        lparam (int): Número de columnas propuestas a retornar.

    Returns:
        list: Lista con los índices de las columnas propuestas (máximo lparam elementos).
    """
    pColumns = []
    tColumns = np.zeros((len(uColumns),2))
    for i in range(0,len(uColumns)):
        tColumns[i,0] = uColumns[i]
        tColumns[i,1] = dictcHeuristics[uColumns[i]]
    tColumns = tColumns[tColumns[:,1].argsort()]
    largo = min(lparam, len(tColumns[:,0]))
    for i in range(0,largo):
        pColumns.append(tColumns[i,0])
    return pColumns

def getColumnsDict(cHeuristic):
    """
    Convierte la matriz de heurísticas de columnas en un diccionario.

    Args:
        cHeuristic (numpy.ndarray): Matriz de heurísticas con índices y valores.

    Returns:
        dict: Diccionario donde las llaves son índices de columnas y los valores
        son sus respectivos valores heurísticos.
    """
    dictcHeuristics = {}
    for i in range(0,len(cHeuristic)):
        dictcHeuristics[cHeuristic[i,0]] = cHeuristic[i,1]
    return dictcHeuristics

def diff(A,B):
    """
    Calcula la diferencia entre dos conjuntos (A - B).

    Args:
        A (list): Conjunto A.
        B (list): Conjunto B.

    Returns:
        list: Lista con los elementos que están en A pero no en B.
    """
    C = set(A) -set(B)
    return list(C)

def Calcula_Measure_j(Option, Pesos,j, K_j):
    """
    Calcula la medida heurística para una columna j según la opción seleccionada.
    
    Implementa diferentes métricas de evaluación:
    - Option = 0: Costo directo
    - Option = 1: Costo normalizado por cobertura
    - Option = 2: Costo normalizado por logaritmo de cobertura

    Args:
        Option (int): Identifica la medida a calcular (0, 1 o 2).
        Pesos (numpy.ndarray): Vector de costos de las columnas.
        j (int): Índice de la columna a evaluar.
        K_j (int): Número de filas cubiertas por la columna j.

    Returns:
        float: Valor de la medida heurística calculada para la columna j.
    """
    if Option==0:
        Measure = Pesos[j]

    elif Option==1:
        Measure = Pesos[j]/K_j

    elif Option==2:
        Measure =  (Pesos[j]/math.log(K_j,2))

    return Measure

def SeleccionaColumna(Matrix,S,cHeuristic):
    """
    Selecciona la mejor columna del complemento de S.
    
    Busca en la matriz de heurísticas ordenada la primera columna que no
    esté en la solución actual S.

    Args:
        Matrix (numpy.ndarray): Matriz de cobertura del problema.
        S (list): Lista de índices de columnas en la solución actual.
        cHeuristic (numpy.ndarray): Matriz de heurísticas de columnas ordenada.

    Returns:
        int: Índice de la columna seleccionada.
    """


    row, col = Matrix.shape
    columnTot = range(0,col)
    columnComplement = diff(columnTot,S)
    estado = 0
    i = 0
    while estado == 0:
        if cHeuristic[i,0] in columnComplement:
            column = cHeuristic[i,0]
            estado = 1
        i = i + 1
    return column

def SeleccionaColumna1(S,cHeuristic):
    """
    Selecciona la mejor columna del complemento de S.
    
    Versión simplificada que no requiere la matriz completa.

    Args:
        S (list): Lista de índices de columnas en la solución actual.
        cHeuristic (numpy.ndarray): Matriz de heurísticas de columnas ordenada.

    Returns:
        int: Índice de la columna seleccionada.
    """
    estado = 0
    i = 0
    while estado == 0:
        if cHeuristic[i,0] not in S:
            column = cHeuristic[i,0]
            estado = 1
        i = i + 1
    return column

def SeleccionaColumna6(Pesos, Matrix, R,S):
    """
    Selecciona una columna usando heurística avanzada + aleatorización.
    
    Calcula la medida heurística para columnas que cubren filas no cubiertas (R)
    y no están en la solución (S). Puede seleccionar aleatoriamente entre las
    mejores opciones para diversificación.

    Args:
        Pesos (numpy.ndarray): Vector de costos de las columnas.
        Matrix (numpy.ndarray): Matriz de cobertura del problema.
        R (list): Lista de índices de filas no cubiertas.
        S (list): Lista de índices de columnas en la solución actual.

    Returns:
        int: Índice de la columna seleccionada.
    """


    NumberCalculus = 2

    T = 1 # start choice
    Option1 = np.random.randint(0,9)
    #Option = np.random.randint(2)
    Option = 1
    #Choice = np.random.randint(0,T)
    rows, cols = Matrix.shape
    compl = range(0,cols)
    columnComplement = list(set(compl)-set(S))
    Matrix_F = Matrix[R,:]

    Matrix_F = Matrix_F[:,columnComplement]

    rowF, colF = Matrix_F.shape
    #print rowF, colF
    ColumnWeight = np.zeros((colF,NumberCalculus))
    Cont = 0

    for i in range(0,colF):

        ColumnWeight[Cont,0] = columnComplement[i]
        K_i = np.sum(Matrix_F[:,i])
        if K_i > 0:
            ColumnWeight[Cont,1] = Calcula_Measure_j(Option,Pesos,columnComplement[i],K_i)
        else:
            ColumnWeight[Cont,1] = Pesos[columnComplement[i]]*100
        Cont = Cont + 1
    ColumnWeight = ColumnWeight[ColumnWeight[:,1].argsort()]

    # We need to get the S complement
    if Option1 == 0:
        #print tam, Option1, len(ColumnWeight)
        tam = min(len(ColumnWeight),10)
        #print 'El largo', len(ColumnWeight)
        if tam == 1:
            column = int(ColumnWeight[0,0])
        else:
            column = int(ColumnWeight[np.random.randint(1,tam),0])
    else:
        column = int(ColumnWeight[0,0])
        #print 'La columna', column
    return column

def SeleccionaColumnaNueva(Pesos, Matrix, pRows,pColumns):
    """
    Selecciona la mejor columna de un subconjunto propuesto para cubrir filas específicas.
    
    Evalúa solo las columnas propuestas (pColumns) para cubrir las filas
    propuestas (pRows). Incluye aleatorización para diversificación.

    Args:
        Pesos (numpy.ndarray): Vector de costos de las columnas.
        Matrix (numpy.ndarray): Matriz de cobertura del problema.
        pRows (list): Lista de índices de filas propuestas a cubrir.
        pColumns (list): Lista de índices de columnas candidatas.

    Returns:
        int: Índice de la columna seleccionada.
    """


    NumberCalculus = 2

    T = 1 # start choice

    Option = np.random.randint(2)
    #Choice = np.random.randint(0,T)

    row, col = Matrix.shape
    #print 'El largo de las columnas antes', len(pColumns)
    columnComplement = list(set(pColumns).intersection(range(0,col)))
    #print 'El largo de las columnas ', len(columnComplement), pColumns
    Matrix_F = Matrix[pRows,:]

    Matrix_F = Matrix_F[:,columnComplement]
    rowF, colF = Matrix_F.shape


    ColumnWeight = np.zeros((colF,NumberCalculus))

    Cont = 0

    for i in range(0,colF):

        ColumnWeight[Cont,0] = columnComplement[i]
        K_i = np.sum(Matrix_F[:,i])
        if K_i > 0:
            ColumnWeight[Cont,1] = Calcula_Measure_j(Option,Pesos,columnComplement[i],K_i)
        else:
            ColumnWeight[Cont,1] = Pesos[columnComplement[i]]*100
        Cont = Cont + 1
    ColumnWeight = ColumnWeight[ColumnWeight[:,1].argsort()]

    # We need to get the S complement

    #tam = min(len(ColumnWeight)-1,9)

    Option1 = np.random.randint(0,5)
    if Option1 == 0:
        #print tam, Option1, len(ColumnWeight)
        tam = min(len(ColumnWeight),10)
        #print 'El largo', len(ColumnWeight)
        #print tam
        if tam == 1:
            column = int(ColumnWeight[0,0])
        else:
            column = int(ColumnWeight[np.random.randint(1,tam),0])
    else:
        #print len(ColumnWeight), len(pRows), len(columnComplement)
        column = int(ColumnWeight[0,0])
    #print 'El calculo', column
    return column

def heuristByCols(pesos,uRows,pCols,dictCols):
    """
    Selecciona columna evaluando cobertura sobre filas no cubiertas.
    
    Calcula la heurística costo/cobertura considerando solo las filas no cubiertas
    que cada columna propuesta puede cubrir. Incluye selección aleatoria entre
    las mejores opciones.

    Args:
        pesos (numpy.ndarray): Vector de costos de las columnas.
        uRows (list): Lista de índices de filas no cubiertas (Uncovered Rows).
        pCols (list): Lista de índices de columnas propuestas.
        dictCols (dict): Diccionario que mapea columnas a las filas que cubren.

    Returns:
        int: Índice de la columna seleccionada.
    """
    ColumnWeight = np.zeros((len(pCols),2))
    #print('pcols',len(pCols))
    for i in range(0,len(pCols)):
        lRows = dictCols[pCols[i]]
        ColumnWeight[i,0] = pCols[i]
        ColumnWeight[i,1] = float(pesos[pCols[i]])/len(list(set(lRows).intersection(set(uRows))))
    ColumnWeight = ColumnWeight[ColumnWeight[:,1].argsort()]
    Option1 = np.random.randint(0,5)
    if Option1 == 0:
        #print tam, Option1, len(ColumnWeight)
        tam = min(len(ColumnWeight),10)
        #print 'El largo', len(ColumnWeight)
        #print tam
        if tam == 1:
            #print('El valor del elemento',ColumnWeight[0,0])
            column = int(ColumnWeight[0,0])
        else:
            #print('El valor del elemento',ColumnWeight[0,0])
            column = int(ColumnWeight[np.random.randint(1,tam),0])
    else:
        #print len(ColumnWeight), len(pRows), len(columnComplement)
        #print('El valor del elemento',ColumnWeight[0,0])
        column = int(ColumnWeight[0,0])
    #print 'El calculo', column
    return column
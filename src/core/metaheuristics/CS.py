import numpy as np
import math

#Cuckoo Search (CS) algorithm
#DOI: 10.1109/NABIC.2009.5393690

def CS(Problem, paramsProblem, paramsMH, matrixCont, matrixDis, solutionsRanking, fitness, iter):
    
    # guardamos en memoria la mejor solution anterior, para mantenerla
    paramsProblem['bestRowAuxOld'] = solutionsRanking[0]
    paramsProblem['BestOld'] = matrixCont[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestBinaryOld'] = matrixDis[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestFitnessOld'] = np.min(fitness)

    lb = paramsProblem["lb"]
    ub = paramsProblem["ub"]

    pa_CS = paramsMH['pa_CS']
    alpha_CS = paramsMH['alpha_CS']
    beta_CS = paramsMH['beta_CS']

    #Movimiento de CS
    sigma = (
        math.gamma(1 + beta_CS)
        * math.sin(math.pi * beta_CS / 2)
        / (math.gamma((1 + beta_CS) / 2) * beta_CS * 2 ** ((beta_CS - 1) / 2))
    ) ** (1 / beta_CS)
    # s = matrixDis #Binario
    s = matrixCont #Continuo
    u = np.random.uniform(size=s.shape) * sigma
    v = np.random.uniform(size=s.shape)
    levy = u / (np.abs(v) ** (1 / beta_CS))

    # step_levy = step * (s - paramsProblem['BestBinaryOld']) #Binario
    step_levy = levy * (s - paramsProblem['BestOld']) #Continuo
    matrixCont = matrixCont + alpha_CS * step_levy #Continuo

    #Evaluar fitness de nidos teporales
    matrixDis,fitness,solutionsRanking,numReparaciones = Problem.obtenerFitness(matrixCont,matrixDis,solutionsRanking,paramsProblem)
    
    #Ordenar y eliminar nidos encontrados
    descarte = int(len(solutionsRanking) * pa_CS)
    matrixCont[solutionsRanking[-descarte:]] = np.random.uniform(low=lb, high=ub, size=(len(solutionsRanking[-descarte:]),matrixDis.shape[1]))

    return matrixCont, paramsProblem
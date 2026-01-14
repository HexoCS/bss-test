import numpy as np
import math

#Particle Swarm Optimization (PSO)
#DOI: 10.1109/ICNN.1995.488968

def PSO(Problem, paramsProblem, paramsMH, matrixCont, matrixDis, solutionsRanking, fitness, iter):
    
    # guardamos en memoria la mejor solution anterior, para mantenerla
    paramsProblem['bestRowAuxOld'] = solutionsRanking[0]
    paramsProblem['BestOld'] = matrixCont[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestBinaryOld'] = matrixDis[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestFitnessOld'] = np.min(fitness)

    maxIter = paramsMH['maxIter']

    Vmax_PSO = paramsMH['Vmax_PSO']
    wMax_PSO = paramsMH['wMax_PSO']
    wMin_PSO = paramsMH['wMin_PSO']
    c1_PSO = paramsMH['c1_PSO']
    c2_PSO = paramsMH['c2_PSO']

    vel = np.zeros(matrixDis.shape)
    pBest = paramsProblem['bestHistoricalIndividual']
    gBest = paramsProblem['BestOld']

    #Movimiento de PSO
    w = wMax_PSO - iter * ((wMax_PSO - wMin_PSO) / maxIter)
    r1 = np.random.uniform(low=0.0,high=1.0, size=matrixCont.shape)
    r2 = np.random.uniform(low=0.0,high=1.0, size=matrixCont.shape)
    vel = (w * vel) + (c1_PSO * r1 * (pBest - matrixCont)) + (c2_PSO * r2 * (gBest - matrixCont))
    vel[vel > Vmax_PSO] = Vmax_PSO
    vel[vel < -Vmax_PSO] = -Vmax_PSO
    matrixCont = matrixCont + vel   

    return matrixCont, paramsProblem
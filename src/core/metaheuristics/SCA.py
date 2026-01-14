import numpy as np

#Sine Cosine Algorithm (SCA)
#DOI: 10.1016/j.knosys.2015.12.022

def SCA(Problem, paramsProblem, paramsMH, matrixCont, matrixDis, solutionsRanking, fitness, iter):

    # guardamos en memoria la mejor solution anterior, para mantenerla
    paramsProblem['bestRowAuxOld'] = solutionsRanking[0]
    paramsProblem['BestOld'] = matrixCont[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestBinaryOld'] = matrixDis[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestFitnessOld'] = np.min(fitness)

    maxIter = paramsMH['maxIter']
    a_SCA = paramsMH['a_SCA']

    #Movimiento de SCA
    r1 = a_SCA - iter * (a_SCA/maxIter)
    r4 = np.random.uniform(low=0.0,high=1.0, size=matrixCont.shape[0])
    r2 = (2*np.pi) * np.random.uniform(low=0.0,high=1.0, size=matrixCont.shape)
    r3 = np.random.uniform(low=0.0,high=2.0, size=matrixCont.shape)
    matrixCont[r4<0.5] = matrixCont[r4<0.5] + np.multiply(r1,np.multiply(np.sin(r2[r4<0.5]),np.abs(np.multiply(r3[r4<0.5],paramsProblem['BestOld'])-matrixCont[r4<0.5])))
    matrixCont[r4>=0.5] = matrixCont[r4>=0.5] + np.multiply(r1,np.multiply(np.cos(r2[r4>=0.5]),np.abs(np.multiply(r3[r4>=0.5],paramsProblem['BestOld'])-matrixCont[r4>=0.5])))

    return matrixCont, paramsProblem
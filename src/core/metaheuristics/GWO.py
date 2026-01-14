import numpy as np

#Grey wolf optimization
#DOI: 10.1016/j.advengsoft.2013.12.007

def GWO(Problem, paramsProblem, paramsMH, matrixCont, matrixDis, solutionsRanking, fitness, iter):
    
    # guardamos en memoria la mejor solution anterior, para mantenerla
    paramsProblem['bestRowAuxOld'] = solutionsRanking[0]
    paramsProblem['BestOld'] = matrixCont[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestBinaryOld'] = matrixDis[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestFitnessOld'] = np.min(fitness)

    maxIter = paramsMH['maxIter']
    pob = paramsMH['population']
    dim = matrixDis.shape[1]
    # linear parameter 2->0
    a = 2 - iter * (2/maxIter)

    A1 = 2 * a * np.random.uniform(0,1,size=(pob,dim)) - a; 
    A2 = 2 * a * np.random.uniform(0,1,size=(pob,dim)) - a; 
    A3 = 2 * a * np.random.uniform(0,1,size=(pob,dim)) - a; 

    C1 = 2 *  np.random.uniform(0,1,size=(pob,dim))
    C2 = 2 *  np.random.uniform(0,1,size=(pob,dim))
    C3 = 2 *  np.random.uniform(0,1,size=(pob,dim))

    # eq. 3.6
    Xalfa  = matrixCont[solutionsRanking[0]]
    Xbeta  = matrixCont[solutionsRanking[1]]
    Xdelta = matrixCont[solutionsRanking[2]]

    # eq. 3.5
    Dalfa = np.abs(np.multiply(C1,Xalfa)-matrixCont)
    Dbeta = np.abs(np.multiply(C2,Xbeta)-matrixCont)
    Ddelta = np.abs(np.multiply(C3,Xdelta)-matrixCont)

    # Eq. 3.7
    X1 = Xalfa - np.multiply(A1,Dalfa)
    X2 = Xbeta - np.multiply(A2,Dbeta)
    X3 = Xdelta - np.multiply(A3,Ddelta)

    X = np.divide((X1+X2+X3),3)
    matrixCont = X

    return matrixCont, paramsProblem
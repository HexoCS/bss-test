import numpy as np

#Whale Optimization Algorithm (WOA)
#DOI: 10.1016/j.advengsoft.2016.01.008

def WOA(Problem, paramsProblem, paramsMH, matrixCont, matrixDis, solutionsRanking, fitness, iter):

    # guardamos en memoria la mejor solution anterior, para mantenerla
    paramsProblem['bestRowAuxOld'] = solutionsRanking[0]
    paramsProblem['BestOld'] = matrixCont[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestBinaryOld'] = matrixDis[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestFitnessOld'] = np.min(fitness)

    maxIter = paramsMH['maxIter']
    b_WOA = paramsMH['b_WOA']
    pob = paramsMH['population']
    dim = matrixDis.shape[1]

    #movimiento de WOA
    a = 2 - ((2*iter)/maxIter)
    A = np.random.uniform(low=-a,high=a,size=(pob,dim)) #vector rand de tam (pob,dim)
    Aabs = np.abs(A[0]) # Vector de A absoluto en tam pob
    C = np.random.uniform(low=0,high=2,size=(pob,dim)) #vector rand de tam (pob,dim)
    l = np.random.uniform(low=-1,high=1,size=(pob,dim)) #vector rand de tam (pob,dim)
    p = np.random.uniform(low=0,high=1,size=pob) #vector rand de tam pob ***

    #ecu 2.1 Pero el movimiento esta en 2.2
    indexCond2_2 = np.intersect1d(np.argwhere(p<0.5),np.argwhere(Aabs<1)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 2.2
    if indexCond2_2.shape[0] != 0:
        matrixCont[indexCond2_2] = paramsProblem['BestOld'] - np.multiply(A[indexCond2_2],np.abs(np.multiply(C[indexCond2_2],paramsProblem['BestOld'])-matrixCont[indexCond2_2]))

    #ecu 2.8
    indexCond2_8 = np.intersect1d(np.argwhere(p<0.5),np.argwhere(Aabs>=1)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 2.1
    if indexCond2_8.shape[0] != 0:
        Xrand = matrixCont[np.random.randint(low=0, high=pob, size=indexCond2_8.shape[0])] #Me entrega un conjunto de soluciones rand de tam indexCond2_2.shape[0] (osea los que cumplen la cond11)

        matrixCont[indexCond2_8] = Xrand - np.multiply(A[indexCond2_8],np.abs(np.multiply(C[indexCond2_8],Xrand)-matrixCont[indexCond2_8]))

    #ecu 2.5
    indexCond2_5 = np.intersect1d(np.argwhere(p>=0.5),np.argwhere(p>=0.5)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 2.1
    if indexCond2_5.shape[0] != 0:
        matrixCont[indexCond2_5] = np.multiply(np.multiply(np.abs(paramsProblem['BestOld'] - matrixCont[indexCond2_5]),np.exp(b_WOA*l[indexCond2_5])),np.cos(2*np.pi*l[indexCond2_5])) + paramsProblem['BestOld']
    
    return matrixCont, paramsProblem

import numpy as np
import math

#Harris Hawks Optimization (HHO) 
#DOI: 10.1016/j.future.2019.02.028

def HHO(Problem, paramsProblem, paramsMH, matrixCont, matrixDis, solutionsRanking, fitness, iter):
    
    paramsProblem['bestRowAuxOld'] = solutionsRanking[0]
    paramsProblem['BestOld'] = matrixCont[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestBinaryOld'] = matrixDis[paramsProblem['bestRowAuxOld']]
    paramsProblem['BestFitnessOld'] = np.min(fitness)

    LB = paramsProblem["lb"]
    UB = paramsProblem["ub"]
    maxIter = paramsMH['maxIter']
    pob = paramsMH['population']
    beta_HHO = paramsMH['beta_HHO']
    sigma = (
        math.gamma(1 + beta_HHO)
        * math.sin(math.pi * beta_HHO / 2)
        / (math.gamma((1 + beta_HHO) / 2) * beta_HHO * 2 ** ((beta_HHO - 1) / 2))
    ) ** (1 / beta_HHO)

    E0 = np.random.uniform(low=-1.0,high=1.0,size=pob) #vector de tam Pob
    E = 2 * E0 * (1-(iter/maxIter)) #vector de tam Pob
    Eabs = np.abs(E)
    
    q = np.random.uniform(low=0.0,high=1.0,size=pob) #vector de tam Pob
    r = np.random.uniform(low=0.0,high=1.0,size=pob) #vector de tam Pob
    
    Xm = np.mean(matrixCont,axis=0)

    #ecu 1.1
    indexCond1_1 = np.intersect1d(np.argwhere(Eabs>=1),np.argwhere(q>=0.5)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 1.1
    if indexCond1_1.shape[0] != 0:
        Xrand = matrixCont[np.random.randint(low=0, high=pob, size=indexCond1_1.shape[0])] #Me entrega un conjunto de soluciones rand de tam indexCond1_1.shape[0] (osea los que cumplen la cond11)
        matrixCont[indexCond1_1] = Xrand - np.multiply(np.random.uniform(low= 0.0, high=1.0, size=indexCond1_1.shape[0]), np.abs(Xrand- (2* np.multiply(np.random.uniform(low= 0.0, high=1.0, size = indexCond1_1.shape[0]),matrixCont[indexCond1_1].T).T)).T).T #Aplico la ecu 1.1 solamente a las que cumplen las condiciones np.argwhere(Eabs>=1),np.argwhere(q>=0.5)
    
    #ecu 1.2
    indexCond1_2 = np.intersect1d(np.argwhere(Eabs>=1),np.argwhere(q<0.5)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 1.2 
    if indexCond1_2.shape[0] != 0:
        array_Xm = np.zeros(matrixCont[indexCond1_2].shape)
        array_Xm = array_Xm + Xm
        matrixCont[indexCond1_2] = ((paramsProblem['BestOld'] - array_Xm).T - np.multiply( np.random.uniform(low= 0.0, high=1.0, size = indexCond1_2.shape[0]), (LB + np.random.uniform(low= 0.0, high=1.0, size = indexCond1_2.shape[0]) * (UB-LB)) )).T

    #ecu 4
    indexCond4 = np.intersect1d(np.argwhere(Eabs>=0.5),np.argwhere(r>=0.5)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 4
    if indexCond4.shape[0] != 0:
        array_Xm = np.zeros(matrixCont[indexCond4].shape)
        array_Xm = array_Xm + Xm
        matrixCont[indexCond4] = ((array_Xm - matrixCont[indexCond4]) - np.multiply( E[indexCond4], np.abs(np.multiply( 2*(1-np.random.uniform(low= 0.0, high=1.0, size=indexCond4.shape[0])), array_Xm.T ).T - matrixCont[indexCond4]).T).T)

    #ecu 10
    indexCond10 = np.intersect1d(np.argwhere(Eabs>=0.5),np.argwhere(r<0.5))#Nos entrega los index de las soluciones a las que debemos aplicar la ecu 10 
    if indexCond10.shape[0] != 0:
        y10 = matrixCont

        #ecu 7
        Array_y10 = np.zeros(matrixCont[indexCond10].shape)
        Array_y10 = Array_y10 + y10[paramsProblem['bestRowAuxOld']]
        y10[indexCond10] = Array_y10- np.multiply( E[indexCond10], np.abs( np.multiply( 2*(1-np.random.uniform(low= 0.0, high=1.0, size=indexCond10.shape[0])), Array_y10.T ).T- Array_y10 ).T ).T  
        
        #ecu 8
        z10 = y10
        S = np.random.uniform(low= 0.0, high=1.0, size=(y10[indexCond10].shape))
        LF = np.divide((0.01 * np.random.uniform(low= 0.0, high=1.0, size=(y10[indexCond10].shape)) * sigma),np.power(np.abs(np.random.uniform(low= 0.0, high=1.0, size=(y10[indexCond10].shape))),(1/beta_HHO)))
        z10[indexCond10] = y10[indexCond10] + np.multiply(LF,S)

        #evaluar fitness de ecu 7 y 8
        Fy10 = solutionsRanking
        Fy10[indexCond10] = Problem.obtenerFitness(y10[indexCond10],matrixDis[indexCond10],solutionsRanking[indexCond10],paramsProblem)[1]
        
        Fz10 = solutionsRanking
        Fz10[indexCond10] = Problem.obtenerFitness(z10[indexCond10],matrixDis[indexCond10],solutionsRanking[indexCond10],paramsProblem)[1]
        
        #ecu 10.1
        indexCond101 = np.intersect1d(indexCond10, np.argwhere(Fy10 < solutionsRanking)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 10.1
        if indexCond101.shape[0] != 0:
            matrixCont[indexCond101] = y10[indexCond101]

        #ecu 10.2
        indexCond102 = np.intersect1d(indexCond10, np.argwhere(Fz10 < solutionsRanking)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 10.2
        if indexCond102.shape[0] != 0:
            matrixCont[indexCond102] = z10[indexCond102]

        # ecu 6
        indexCond6 = np.intersect1d(np.argwhere(Eabs<0.5),np.argwhere(r>=0.5)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 6
        if indexCond6.shape[0] != 0:
            matrixCont[indexCond6] = paramsProblem['BestOld'] - np.multiply(E[indexCond6], np.abs(paramsProblem['BestOld'] - matrixCont[indexCond6] ).T ).T

        #ecu 11
        indexCond11 = np.intersect1d(np.argwhere(Eabs<0.5),np.argwhere(r<0.5))#Nos entrega los index de las soluciones a las que debemos aplicar la ecu 11
        if indexCond11.shape[0] != 0:
            #ecu 12
            y11 = matrixCont
            array_Xm = np.zeros(matrixCont[indexCond11].shape)
            array_Xm = array_Xm + Xm
            y11[indexCond11] = y11[paramsProblem['bestRowAuxOld']]-  np.multiply(E[indexCond11],  np.abs(  np.multiply(  2*(1-np.random.uniform(low= 0.0, high=1.0, size=matrixCont[indexCond11].shape)),  y11[paramsProblem['bestRowAuxOld']]  )- array_Xm ).T ).T

            #ecu 13
            z11 = y11
            S = np.random.uniform(low= 0.0, high=1.0, size=(y11.shape))
            LF = np.divide((0.01 * np.random.uniform(low= 0.0, high=1.0, size=(y11.shape)) * sigma),np.power(np.abs(np.random.uniform(low= 0.0, high=1.0, size=(y11.shape))),(1/beta_HHO)))
            z11[indexCond11] = y11[indexCond11] + np.multiply(S[indexCond11],LF[[indexCond11]])

            #evaluar fitness de ecu 12 y 13
            if solutionsRanking is None: solutionsRanking = np.ones(pob)*999999
            Fy11 = solutionsRanking
            
            Fy11[indexCond11] = Problem.obtenerFitness(y11[indexCond11],matrixDis[indexCond11],solutionsRanking[indexCond11],paramsProblem)[1]
            
            Fz11 = solutionsRanking
            Fz11[indexCond11] = Problem.obtenerFitness(z11[indexCond11],matrixDis[indexCond11],solutionsRanking[indexCond11],paramsProblem)[1]
            
            #ecu 11.1
            indexCond111 = np.intersect1d(indexCond11, np.argwhere(Fy11 < solutionsRanking)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 11.1
            if indexCond111.shape[0] != 0:
                matrixCont[indexCond111] = y11[indexCond111]

            #ecu 11.2
            indexCond112 = np.intersect1d(indexCond11, np.argwhere(Fz11 < solutionsRanking)) #Nos entrega los index de las soluciones a las que debemos aplicar la ecu 11.2
            if indexCond112.shape[0] != 0:
                matrixCont[indexCond112] = z11[indexCond112]

    return matrixCont, paramsProblem
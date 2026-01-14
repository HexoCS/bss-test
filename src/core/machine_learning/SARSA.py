#  Author: Diego Tapia R.
#  E-mail: root.chile@gmail.com - diego.tapia.r@mail.pucv.cl
import numpy as np
import math
class SARSA():

    # Initialize alpha, gamma, states, actions, rewards, and Q-values
    def __init__(self, paramsML, paramsMH):

        self.state = 0
        self.statesQ = paramsML['statesQ'] # Configure
        self.actions = paramsML['discretizationsScheme']
        self.visitarTodosAlmenosUnaVez = paramsML['visitarTodosAlmenosUnaVez']
        self.listaBlanca = np.zeros(len(self.actions))
        self.rewardType = paramsML['rewardType']
        self.iterMax = paramsMH["maxIter"]
        self.MinMax = paramsML['FO']
        self.policy = paramsML['policyType']
        self.iter = 0 
        self.epsilon = paramsML['epsilon'] 
        self.W = paramsML['W']        
        
        #Propios de SARSA
        self.gamma = paramsML['ql_gamma'] 
        self.qlAlphaType = paramsML['qlAlphaType'] 
        self.qlAlpha = paramsML['ql_alpha'] 

        if self.MinMax == "min":
            self.bestMetric = 999999999 #Esto en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
        else:
            self.bestMetric = -999999999
        self.Qvalues = np.zeros(shape=(self.statesQ,len(self.actions))) #state,actions
        self.visitas = np.zeros(shape=(self.statesQ,len(self.actions))) #state,actions

    def getReward(self,metric):
        
        if self.MinMax == "min":
            if self.rewardType == "withPenalty1": 
                if self.bestMetric > metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return 1
                return -1

            elif self.rewardType == "withoutPenalty1":
                if self.bestMetric > metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return 1
                return 0

            elif self.rewardType == "globalBest":
                if self.bestMetric > metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return self.W/self.bestMetric
                return 0

            elif self.rewardType == "rootAdaptation":
                if self.bestMetric > metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return math.sqrt(metric)
                return 0

            elif self.rewardType == "escalatingMultiplicativeAdaptation":
                if self.bestMetric > metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return self.W*self.bestMetric
                return 0
            #recompansas nuevas
            elif self.rewardType == "percentageImprovement": 
                if self.iter == 0:
                    #Usaremos valor "pequeño", hasta conseguir forma de pablo
                    return 0.01*metric
                else:
                    if self.bestMetric > metric: #Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo, debe usar paramsML['FO'] para hacer un if.
                        old_fit = self.bestMetric
                        self.bestMetric = metric
                        return float(np.true_divide(np.array(old_fit - metric), np.array(old_fit), out=np.zeros(1), where=old_fit!=0) * 100)
                    else:
                        return 0
            elif self.rewardType == "percentageImprovementAndDeterioration": 
                if self.iter == 0:
                    #Usaremos valor "pequeño", hasta conseguir forma de pablo
                    return 0.01*metric
                else:
                    if self.bestMetric > metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                        old_fit = self.bestMetric
                        self.bestMetric = metric
                        # return (old_fit - metric)/old_fit * 100
                        return float(np.true_divide(np.array(old_fit - metric), np.array(old_fit), out=np.zeros(1), where=old_fit!=0) * 100)
                    else:
                        # return (metric - self.bestMetric)/self.bestMetric * 100
                        return float(np.true_divide(np.array(metric - self.bestMetric), np.array(self.bestMetric), out=np.zeros(1), where=self.bestMetric!=0) * 100)

            elif self.rewardType == "percentageImprovementAndDeteriorationWithIter": 
                if self.iter == 0:
                    #Usaremos valor "pequeño", hasta conseguir forma de pablo
                    return 0.01*metric
                else:
                    if self.bestMetric > metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                        old_fit = self.bestMetric
                        self.bestMetric = metric
                        # porcentajeMejoramiento = (old_fit - metric)/old_fit * 100
                        porcentajeMejoramiento = float(np.true_divide(np.array(old_fit - metric), np.array(old_fit), out=np.zeros(1), where=old_fit!=0) * 100)
                        # r = (1 + 3*porcentajeMejoramiento)/self.iter
                        r = float(np.true_divide(np.array(1 + 3*porcentajeMejoramiento), np.array(self.iter), out=np.zeros(1), where=self.iter!=0) * 100)
                        return r
                    else:
                        return 0

            elif self.rewardType == "percentageImprovementAndDeteriorationWithIter": 
                if self.iter == 0:
                    #Usaremos valor "pequeño", hasta conseguir forma de pablo
                    return 0.01*metric
                else:
                    if self.bestMetric > metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                        old_fit = self.bestMetric
                        self.bestMetric = metric
                        # porcentajeMejoramiento = (old_fit - metric)/old_fit * 100
                        porcentajeMejoramiento = float(np.true_divide(np.array(old_fit - metric), np.array(old_fit), out=np.zeros(1), where=old_fit!=0) * 100)
                        # r = (1 + 3*porcentajeMejoramiento)/self.ite
                        r = float(np.true_divide(np.array(1 + 3*porcentajeMejoramiento), np.array(self.iter), out=np.zeros(1), where=self.iter!=0) * 100)
                        return r
                    else:
                        # porcentajeEmpeoramiento = (metric - self.bestMetric)/self.bestMetric * 100
                        porcentajeEmpeoramiento = float(np.true_divide(np.array(metric - self.bestMetric), np.array(self.bestMetric), out=np.zeros(1), where=self.bestMetric!=0) * 100)
                        # r = (1 + 3*porcentajeEmpeoramiento)/self.iter
                        r = float(np.true_divide(np.array(1 + 3*porcentajeEmpeoramiento), np.array(self.iter), out=np.zeros(1), where=self.iter!=0) * 100)
                        return r

        if self.MinMax == "max": 
            if self.rewardType == "withPenalty1": 
                if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return 1
                return -1

            elif self.rewardType == "withoutPenalty1":
                if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return 1
                return 0

            elif self.rewardType == "globalBest":
                if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return self.W/self.bestMetric
                return 0

            elif self.rewardType == "rootAdaptation":
                if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return math.sqrt(metric)
                return 0

            elif self.rewardType == "escalatingMultiplicativeAdaptation":
                if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                    self.bestMetric = metric
                    return self.W*self.bestMetric
                return 0

            elif self.rewardType == "percentageImprovement": 
                if self.iter == 0:
                    #Usaremos valor "pequeño", hasta conseguir forma de pablo
                    return 0.01*metric
                else:
                    if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                        old_fit = self.bestMetric
                        self.bestMetric = metric
                        # return (metric - old_fit)/old_fit * 100
                        return float(np.true_divide(np.array(metric - old_fit), np.array(old_fit), out=np.zeros(1), where=old_fit!=0) * 100)
                    else:
                        return 0
            elif self.rewardType == "percentageImprovementAndDeterioration": 
                if self.iter == 0:
                    #Usaremos valor "pequeño", hasta conseguir forma de pablo
                    return 0.01*metric
                else:
                    if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                        old_fit = self.bestMetric
                        self.bestMetric = metric
                        # return (metric - old_fit)/old_fit * 100
                        return float(np.true_divide(np.array(metric - old_fit), np.array(old_fit), out=np.zeros(1), where=old_fit!=0) * 100)
                    else:
                        # return (self.bestMetric - metric)/self.bestMetric * 100
                        return float(np.true_divide(np.array(self.bestMetric - metric), np.array(self.bestMetric), out=np.zeros(1), where=self.bestMetric!=0) * 100)
                    

            elif self.rewardType == "percentageImprovementAndDeteriorationWithIter": 
                if self.iter == 0:
                    #Usaremos valor "pequeño", hasta conseguir forma de pablo
                    return 0.01*metric
                else:
                    if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                        old_fit = self.bestMetric
                        self.bestMetric = metric
                        # porcentajeMejoramiento = (metric - old_fit)/old_fit * 100
                        porcentajeMejoramiento = float(np.true_divide(np.array(metric - old_fit), np.array(old_fit), out=np.zeros(1), where=old_fit!=0) * 100)
                        # r = (1 + 3*porcentajeMejoramiento)/self.iter
                        r = float(np.true_divide(np.array(1 + 3*porcentajeMejoramiento), np.array(self.iter), out=np.zeros(1), where=self.iter!=0) * 100)
                        return r
                    else:
                        return 0

            elif self.rewardType == "percentageImprovementAndDeteriorationWithIter": 
                if self.iter == 0:
                    #Usaremos valor "pequeño", hasta conseguir forma de pablo
                    return 0.01*metric
                else:
                    if self.bestMetric < metric:#Esta condición en el framework debe ser consultada según el problema, ya que puede min o max la función objetivo
                        old_fit = self.bestMetric
                        self.bestMetric = metric
                        # porcentajeMejoramiento = (metric - old_fit)/old_fit * 100
                        porcentajeMejoramiento = float(np.true_divide(np.array(metric - old_fit), np.array(old_fit), out=np.zeros(1), where=old_fit!=0) * 100)
                        # r = (1 + 3*porcentajeMejoramiento)/self.iter
                        r = float(np.true_divide(np.array(1 + 3*porcentajeMejoramiento), np.array(self.iter), out=np.zeros(1), where=self.iter!=0) * 100)
                        return r
                    else:
                        # porcentajeEmpeoramiento = (self.bestMetric - metric)/self.bestMetric * 100
                        porcentajeEmpeoramiento = float(np.true_divide(np.array(self.bestMetric - metric), np.array(self.bestMetric), out=np.zeros(1), where=self.bestMetric!=0) * 100)
                        # r = (1 + 3*porcentajeEmpeoramiento)/self.iter
                        r = float(np.true_divide(np.array(1 + 3*porcentajeEmpeoramiento), np.array(self.iter), out=np.zeros(1), where=self.iter!=0) * 100)
                        return r
                    
    def getAccion(self,state):
        if self.visitarTodosAlmenosUnaVez == True:
            self.state = 1
            if np.sum(self.listaBlanca) <= len(self.actions):
                indices = np.where(self.listaBlanca == 0)
                indexElegida = np.random.choice(np.array(indices)[0])
                self.listaBlanca[indexElegida] = 1
                # if len(indices) == 1:
                if len(indices[0]) == 1:
                    self.visitarTodosAlmenosUnaVez = False
                return indexElegida
        else:
            self.state = state
            # e-greedy
            if self.policy == "e-greedy":
                probabilidad = np.random.uniform(low=0.0, high=1.0) #numero aleatorio [0,1]
                if probabilidad <= self.epsilon: #seleccion aleatorio
                    accionRandom = np.random.randint(low=0, high=self.Qvalues.shape[1])
                    return accionRandom #seleccion aleatoria de una accion     
                else: #selecion de Q_Value mayor      
                    maximo = np.amax(self.Qvalues[self.state]) # retorna el elemento mayor por fila    
                    indices = np.where(self.Qvalues[self.state,:] == maximo)[0]  #retorna los indices donde se ubica el maximo en la fila estado  
                    return np.random.choice(indices) # funciona tanto cuando hay varios iguales como cuando hay solo uno
            # greedy
            elif self.policy == "greedy":
                return np.argmax(self.Qvalues[self.state])

            # e-soft 
            elif self.policy == "e-soft":
                probabilidad = np.random.uniform(low=0.0, high=1.0) #numero aleatorio [0,1]
                if probabilidad > self.epsilon: #seleccion aleatorio
                    return np.random.randint(low=0, high=self.Qvalues.shape[0]) #seleccion aleatoria de una accion     
                else: #selecion de Q_Value mayor        
                    maximo = np.amax(self.Qvalues,axis=1) # retorna el elemento mayor por fila        
                    indices = np.where(self.Qvalues[self.state,:] == maximo[self.state])[0]  #retorna los indices donde se ubica el maximo en la fila estado        
                    return np.random.choice(indices) # funciona tanto cuando hay varios iguales como cuando hay solo uno 

            # softMax seleccion ruleta
            elif self.policy == "softMax-rulette":
                #*** Falta generar una normalización de las probabilidades que sumen 1, para realizar el choice
                QtablePositiva = (self.Qvalues[self.state]+np.abs(np.min(self.Qvalues[self.state])))/np.max(self.Qvalues[self.state]+np.abs(np.min(self.Qvalues[self.state])))
                Qtable_normalizada = QtablePositiva/np.sum(QtablePositiva) #La suma de las prob deben ser 1
                seleccionado = np.random.choice(self.Qvalues[self.state],p=Qtable_normalizada)
                indices = np.where(self.Qvalues[self.state,:] == seleccionado)[0]
                return np.random.choice(indices)
        
            # softmax seleccion ruleta elitista (25% mejores acciones)
            elif self.policy == "softMax-rulette-elitist":
                ordenInvertido = np.multiply(self.Qvalues[self.state],-1)
                sort = np.argsort(ordenInvertido) # argumentos ordenados
                cant_mejores = int(sort.shape[0]*0.25) # obtenemos el 25% de los mejores argumentos
                rulette_elitist = sort[0:cant_mejores] # tiene el 25% de los mejores argumentos
                return np.random.choice(rulette_elitist)

    def actualizar_Visitas(self,action): # ACTUALIZACION DE LAS VISITAS
        self.visitas[self.state,action] = self.visitas[self.state,action] + 1
       
    def getAlpha(self,state,action,iter):

        if self.qlAlphaType == "static": 
            #alpha estatico 
            return  self.qlAlpha

        elif self.qlAlphaType == "iteration":
            return 1 - (0.9*(iter/self.iterMax))
            
        elif self.qlAlphaType == "visits":
            return (1/(1 + self.visitas[state,action]))

    def updateQtable(self,metric,action,newAction,state,newState,iter):

        if self.visitarTodosAlmenosUnaVez == False:
            self.state = state
            
        self.iter = iter
        Reward = self.getReward(metric)
        alpha = self.getAlpha(state,action,self.iter)

        # Qnuevo = ( (1 - alpha) * self.Qvalues[state][action]) + alpha * (Reward + (self.gamma  * self.Qvalues[state][action]))
        Qnuevo = self.Qvalues[state][action] +  alpha * (Reward + (self.gamma  * self.Qvalues[newState][newAction]) - self.Qvalues[state][action])
        self.actualizar_Visitas(action) #Actuzación de visitas

        self.Qvalues[state][action] = Qnuevo

    def getQtable(self):
        return self.Qvalues

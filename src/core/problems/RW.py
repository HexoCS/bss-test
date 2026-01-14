import numpy as np
import os
import time
from ..discretization import DiscretizationScheme as DS

class RW:
    def __init__(self,instance,betaDis):
        
        """
        Inicializa una instancia del problema de muros de contencion.
        Configura parametros, dominios de variables, constantes del problema y datos de materiales necearios.
        
        Args:
            instance (str): Identificador de la instancia del problema (ej: "RW300").
            betaDis (float): Parametro beta utilizado en discretizacion.
        
        Returns:
            None
        """
        
        

        #Leer la instancia a resolver,pendiente,por ahora damos datos en "duro".
        # parametrosIntancia = leerinstancia(instance)
        #La altura libre será el parámetro que definirá cada instancia
        self.alturaLibre = int(instance[2:])/100

        #parámetro de la discretización
        self.betaDis = betaDis
        
        self.domResistCaractHormCompresion = np.linspace(25,40,4)
        self.domFluenciaAcero = np.array([2.8,4.2])
        # self.domEspesorCoronamiento = np.linspace(self.alturaLibre*0.05,self.alturaLibre*0.1,10)
        self.domEspesorCoronamiento = np.linspace(0.15,0.65,51) 
        # self.domBaseMuro = np.linspace(self.alturaLibre*0.1,self.alturaLibre*0.2,10)
        self.domBaseMuro = np.linspace(0.3,1.2,91) 
        # self.domEspesorZapata = np.linspace(self.alturaLibre*0.15,self.alturaLibre*0.25,10)
        self.domEspesorZapata = np.linspace(0.45,1.5,106)
        self.domDensidadTerreno = np.linspace(1.6,2.1,6)



        #####################################################
        #Constantes del problema de Muros de Contención
        #####################################################
        self.Ce = 0.24 #Coeficiente estatico del suelo,adimensional.
        self.Cs = 0.14 #Coeficiente sismico del suelo,adimensional.
        self.densidadHormigon = 2.5 #T/m3
        self.recubrimientoMuro = 0.025 #m
        self.yf = 1.4 #adimensional,coef. de mayoración
        self.phiReduccion = 0.83 #adimensional,factor de reducción adimensional,revisar en la ACI318.
        self.ResistCaracHormCompresion = 3000#t/m2
        self.b = 1 #ancho del muro en m
        self.B = 0.85 #reducción a la resistencia caract. del hormigón.
        self.coefRozamientoU = 0.55 #Depende tipo de suelo
        self.recubrimientoZapata = 0.05 #m
        self.lambdaHormigon = 1
        self.factorReduccionCorte = 0.75
        #Preguntar a Ossandón por está variable y por el "coronamientoMenosRecubrimiento = 0.375" que no se usa
        self.empotramiento = 0.2 #m


        self.combinacionesAceroNumpy = np.array([[6,1,0.28],[6,2,0.57],[6,3,0.85],[6,4,1.13],[6,5,1.41],[6,6,1.7],[6,7,1.98],[6,8,2.26],[6,9,2.54],[6,10,2.83],[6,11,3.11],[6,12,3.39],
                                    [8,1,0.50],[8,2,1.01],[8,3,1.51],[8,4,2.01],[8,5,2.51],[8,6,3.02],[8,7,3.52],[8,8,4.02],[8,9,4.52],[8,9,4.52],[8,10,5.03],[8,11,5.53],[8,12,6.03],
                                    [10,1,0.79],[10,2,1.57],[10,3,2.36],[10,4,3.14],[10,5,3.93],[10,6,4.71],[10,7,5.50],[10,8,6.28],[10,9,7.07],[10,10,7.85],[10,11,8.64],[10,12,9.42],
                                    [12,1,1.13],[12,2,2.26],[12,3,3.39],[12,4,4.52],[12,5,5.65],[12,6,6.79],[12,7,7.92],[12,8,9.05],[12,9,10.18],[12,10,11.31],[12,11,12.44],[12,12,13.57],
                                    [14,1,1.54],[14,2,3.08],[14,3,4.62],[14,4,6.16],[14,5,7.70],[14,6,9.24],[14,7,10.78],[14,8,12.32],[14,9,13.85],[14,10,15.39],[14,11,16.93],[14,12,18.47],
                                    [16,1,2.01],[16,2,4.02],[16,3,6.03],[16,4,8.04],[16,5,10.05],[16,6,12.06],[16,7,14.07],[16,8,16.08],[16,9,18.10],[16,10,20.11],[16,11,22.12],[16,12,24.13],
                                    [18,1,2.54],[18,2,5.09],[18,3,7.63],[18,4,10.18],[18,5,12.72],[18,6,15.27],[18,7,17.81],[18,8,20.36],[18,9,22.90],[18,10,25.45],[18,11,27.99],[18,12,30.54],
                                    [20,1,3.14],[20,2,6.28],[20,3,9.42],[20,4,12.57],[20,5,15.71],[20,6,18.85],[20,7,21.99],[20,8,25.13],[20,9,28.27],[20,10,31.42],[20,11,34.56],[20,12,37.70],
                                    [22,1,3.80],[22,2,7.60],[22,3,11.40],[22,4,15.21],[22,5,19.01],[22,6,22.81],[22,7,26.61],[22,8,30.41],[22,9,34.21],[22,10,38.01],[22,11,41.81],[22,12,45.62],
                                    [25,1,4.91],[25,2,9.82],[25,3,14.73],[25,4,19.63],[25,5,24.54],[25,6,29.45],[25,7,34.36],[25,8,39.27],[25,9,44.18],[25,10,49.09],[25,11,54.0],[25,12,58.9],
                                    [28,1,6.16],[28,2,12.32],[28,3,18.47],[28,4,24.63],[28,5,30.79],[28,6,36.95],[28,7,43.1],[28,8,49.26],[28,9,55.42],[28,10,61.58],[28,11,67.73],[28,12,73.89],
                                    [32,1,8.04],[32,2,16.08],[32,3,24.13],[32,4,32.17],[32,5,40.21],[32,6,48.25],[32,7,56.3],[32,8,64.34],[32,9,72.38],[32,10,80.42],[32,11,88.47],[32,12,96.51],
                                    [38,1,11.34],[38,2,22.68],[38,3,34.02],[38,4,45.36],[38,5,56.71],[38,6,68.05],[38,7,79.39],[38,8,90.73],[38,9,102.1],[38,10,113.40],[38,11,124.80],[38,12,136.10]])

        self.KilosAcero = np.array([[6,0.222],
                            [8,0.395],
                            [10,0.617],
                            [12,0.888],
                            [14,1.208],
                            [16,1.578],
                            [18,1.998],
                            [20,2.466],
                            [22,2.984],
                            [25,3.853],
                            [28,4.834],
                            [32,6.313],
                            [38,8.903],])

        self.precioHormigon = np.array([[25 ,63555.73],
                            [30 ,69228.54],
                            [35 ,77218.84],
                            [40 ,81081.35]])

        self.precioAcero = np.array([[4.2,636.5],
                            [2.8,572.28]])
        
        self.emisionesHormigon = np.array([[25,224.34],
                            [30,224.94],
                            [35,265.28],
                            [40,265.28]])

        self.emisionesAcero = np.array([[4.2,3.02],
                                        [2.8,2.82]])

    def fitness(self,solution):
        """Evalua una solucion calculando su costo, emisiones y factibilidad

        Args:
            solution (numpy.ndarray):  Array con 6 elementos [ResistCaractHormCompresion, fluenciaAcero, espesorCoronamiento, baseMuro, espesorZapata, densidadTerreno].

        Returns:
            tuple: Tupla con 5 elementos:
               - costoTotal (float): Costo total de la solucion en clp.
               - emisionTotal (float): Emisiones totales de co2 en kg.
               - volumenHormigon (float): Volumen total de hormigon en m3.
               - kilosTotalesAcero (float): Peso total de acero en kg.
               - factibilidad (int): 1 si cumple todas las restricciones, 99999 si es infactible.
                
        """



        ResistCaractHormCompresion = solution[0]
        fluenciaAcero = solution[1]
        espesorCoronamiento = solution[2]
        baseMuro = solution[3]
        espesorZapata = solution[4]
        densidadTerreno = solution[5]
        
        trasdosGS = (0.8*self.alturaLibre)
        distMuroIntradosGS = (2*self.alturaLibre)*0.1
        
        volumenHormigon = ((trasdosGS+distMuroIntradosGS+baseMuro)*espesorZapata)+((self.alturaLibre+self.empotramiento)*espesorCoronamiento)+((baseMuro-espesorCoronamiento)*(self.alturaLibre+self.empotramiento)*0.5)
        
        empujeActivo = self.Ce*densidadTerreno*(self.alturaLibre+self.empotramiento+espesorZapata)
        empujeSismico = self.Cs*densidadTerreno*(self.alturaLibre+self.empotramiento+espesorZapata) 
        empujeActivoA = self.Ce*densidadTerreno*(self.alturaLibre+self.empotramiento)
        empujeSismicoAInferior = self.Cs*densidadTerreno*espesorZapata
        empujeSismicoA = empujeSismico-empujeSismicoAInferior 

        MomentoSolicitante = (empujeSismicoAInferior*(self.alturaLibre+self.empotramiento)*0.5*(self.alturaLibre+self.empotramiento))+(0.5*empujeSismicoA*(self.alturaLibre+self.empotramiento)*2/3*(self.alturaLibre+self.empotramiento))+(0.5*empujeActivoA*(self.alturaLibre+self.empotramiento)*1/3*(self.alturaLibre+self.empotramiento))

        N1 = (espesorCoronamiento*(self.alturaLibre+self.empotramiento)*self.densidadHormigon)
        N2 = (0.5*(self.alturaLibre+self.empotramiento)*(baseMuro-espesorCoronamiento)*self.densidadHormigon)
        Nt = N1 + N2 

        distanciad1 = (0.5*espesorCoronamiento)+(baseMuro-espesorCoronamiento)-self.recubrimientoMuro
        distanciad2 = (2/3)*(baseMuro-espesorCoronamiento)-self.recubrimientoMuro

        momentoMa = (MomentoSolicitante+(N1*distanciad1)+(N2*distanciad2))
        momentoDiseno = momentoMa * self.yf

        cargaAxial = Nt * self.yf

        u = (momentoDiseno/(self.phiReduccion*self.B*ResistCaractHormCompresion*100*self.b*(baseMuro-self.recubrimientoMuro)*(baseMuro-self.recubrimientoMuro)))
        v = (cargaAxial/(self.phiReduccion*self.B*ResistCaractHormCompresion*100*(baseMuro-self.recubrimientoMuro)*self.b))
        w = 1-((1-2*u)**0.5)-v
        
        aceroEstribos = (self.B*w*ResistCaractHormCompresion*self.b*(baseMuro-self.recubrimientoMuro))/fluenciaAcero

        cargaSueloNs = trasdosGS*(self.alturaLibre+self.empotramiento)*densidadTerreno
        cargaInteraccionNm = (baseMuro-espesorCoronamiento)*((densidadTerreno+self.densidadHormigon)/2)*1*(self.empotramiento+self.alturaLibre)

        cargaDescargaN1 = espesorCoronamiento*(self.alturaLibre+self.empotramiento)*1*self.densidadHormigon
        cargaFundacionNf = (trasdosGS+distMuroIntradosGS+baseMuro)*1*espesorZapata*self.densidadHormigon

        cargaTotalMuro = cargaDescargaN1+cargaFundacionNf+cargaInteraccionNm+cargaSueloNs

        Xs = abs((trasdosGS+baseMuro+distMuroIntradosGS)*0.5-(trasdosGS*0.5))
        Xm = abs((trasdosGS+baseMuro+distMuroIntradosGS)*0.5-(trasdosGS+((1/3)*(baseMuro-espesorCoronamiento))))
        X1 = abs((trasdosGS+baseMuro+distMuroIntradosGS)*0.5-(trasdosGS+(baseMuro-espesorCoronamiento)+0.5*espesorCoronamiento))

        momentoSolicitanteVolcamiento = empujeSismico*((self.alturaLibre+self.empotramiento+espesorZapata)*0.5)*((self.alturaLibre+self.empotramiento+espesorZapata)*(2/3))+empujeActivo*(0.5*(self.alturaLibre+self.empotramiento+espesorZapata))*((self.alturaLibre+self.empotramiento+espesorZapata)/3)

        momentoAplicadoSuelo = momentoSolicitanteVolcamiento-(cargaSueloNs*Xs)+(cargaInteraccionNm*Xm)+(cargaDescargaN1*X1)
        excentricidad = momentoAplicadoSuelo/cargaTotalMuro
        seccionApoyada = 3*(((baseMuro+distMuroIntradosGS+trasdosGS)/2)-excentricidad)

        #Esta verificación no se está utilizando, consultar
        verificacionDisenoEsfuerzo = 2*cargaTotalMuro/seccionApoyada

        momentoResistente = cargaSueloNs*(baseMuro+distMuroIntradosGS+(trasdosGS*0.5))+cargaInteraccionNm*(espesorCoronamiento+distMuroIntradosGS+((baseMuro-espesorCoronamiento)*0.5))+cargaDescargaN1*(distMuroIntradosGS+espesorCoronamiento*0.5)+cargaFundacionNf*((baseMuro+distMuroIntradosGS+trasdosGS)*0.5)
        fuerzasSolicitantesDeslizamiento = 0.5*empujeActivo*(self.alturaLibre+self.empotramiento+espesorZapata)+0.5*empujeSismico*(self.alturaLibre+self.empotramiento+espesorZapata)
        #Esta ecuación tenia "alturaLibre" en vez "self.alturaLibre" y "espesorZapata" en vez de "espesorZapata"
        fuerzasSolicitantesEstaticasDeslizamiento = 0.5*empujeActivo*(self.alturaLibre+self.empotramiento+espesorZapata)

        fuerzaResistenteDeslizamiento = self.coefRozamientoU*(cargaDescargaN1+cargaFundacionNf+cargaInteraccionNm+cargaSueloNs)

        factorSeguridadSismicoVolcamiento = momentoResistente/momentoSolicitanteVolcamiento #Correcto, debe ser mayor a 1.15*FSSD
        factorSeguridadSismicoDeslizamiento = fuerzaResistenteDeslizamiento/fuerzasSolicitantesDeslizamiento #correcto, debe ser mayor a 1.1
        if factorSeguridadSismicoDeslizamiento >= 1.1:
            FSSD = 1
            factorSeguridadSismicoDeslizamiento = 1
        else:
            FSSD = 0
            factorSeguridadSismicoDeslizamiento = 0
            print("*************************************No cumple factor Seguridad Sismico Deslizamiento")
        if factorSeguridadSismicoVolcamiento >= 1.15*FSSD:
            factorSeguridadSismicoVolcamiento =1
        else:
            factorSeguridadSismicoVolcamiento = 0
            print("*************************************No cumple factor Seguridad Sismico Volcamiento")

        momentoSolicitanteEstaticoVolcamiento = empujeActivo*(0.5*(self.alturaLibre+self.empotramiento+espesorZapata))*((self.alturaLibre+self.empotramiento+espesorZapata)/3)
        
        factorSeguridadEstaticoVolcamiento = momentoResistente/momentoSolicitanteEstaticoVolcamiento #Correcto, debe ser mayor a 1,5 y cercano a su valor para optimizar
        if factorSeguridadEstaticoVolcamiento >= 1.5:
            factorSeguridadEstaticoVolcamiento =  1
        else:
            factorSeguridadEstaticoVolcamiento = 0
            print("*************************************No cumple factor Seguridad Estatico Volcamiento")

        factorSeguridadEstaticoDeslizamiento = fuerzaResistenteDeslizamiento/fuerzasSolicitantesEstaticasDeslizamiento #correcto, mayor a 1.5
        if factorSeguridadEstaticoDeslizamiento >= 1.5:
            factorSeguridadEstaticoDeslizamiento = 1
        else:
            factorSeguridadEstaticoDeslizamiento = 0
            print("*************************************No cumple factor Seguridad Estatico Deslizamiento")

        porcentajeApoyo = (seccionApoyada/((baseMuro+distMuroIntradosGS+trasdosGS))) #Correcto, debe ser mayor al 80%
        if porcentajeApoyo > 0.8:
            porcentajeApoyo = 1
        else:
            porcentajeApoyo = 0
            print("*************************************No cumple Restricción al Corte")

        factibilidad = 1
        if factorSeguridadSismicoDeslizamiento == 0 or factorSeguridadSismicoVolcamiento == 0 or factorSeguridadEstaticoVolcamiento == 0 or factorSeguridadEstaticoDeslizamiento == 0 or porcentajeApoyo == 0:
            factibilidad = 99999

        ecuacionNavierMaximo = (cargaTotalMuro/(baseMuro+distMuroIntradosGS+trasdosGS))+(momentoAplicadoSuelo/((baseMuro+distMuroIntradosGS+trasdosGS)*(baseMuro+distMuroIntradosGS+trasdosGS))/6)
        ecuacionNavierMinimo = (cargaTotalMuro/(baseMuro+distMuroIntradosGS+trasdosGS))-(momentoAplicadoSuelo/((baseMuro+distMuroIntradosGS+trasdosGS)*(baseMuro+distMuroIntradosGS+trasdosGS))/6)

        if ecuacionNavierMinimo > 0:
            tensionSuelo = (ecuacionNavierMinimo*trasdosGS)+ (trasdosGS*((trasdosGS*(ecuacionNavierMaximo-ecuacionNavierMinimo))/(baseMuro+distMuroIntradosGS+trasdosGS)))*0.5 
        else:
            tensionSuelo = (seccionApoyada-(distMuroIntradosGS+baseMuro))*(((ecuacionNavierMaximo)*(seccionApoyada-(distMuroIntradosGS+baseMuro)))/(distMuroIntradosGS+baseMuro+trasdosGS))*0.5

        empujeRellenoTrasdos = densidadTerreno*(self.alturaLibre+self.empotramiento)
        empujeFundacionTrasdos = self.densidadHormigon*trasdosGS

        if ecuacionNavierMinimo > 0:
            armaduraMomentoDiseno = 1.4*(((empujeFundacionTrasdos+empujeRellenoTrasdos)*trasdosGS*0.5*trasdosGS)-
                                        ((ecuacionNavierMinimo*trasdosGS)*0.5*trasdosGS)-
                                        ((trasdosGS*((trasdosGS*(ecuacionNavierMaximo-ecuacionNavierMinimo))/(baseMuro+distMuroIntradosGS+trasdosGS))
                                        *0.5)*1/3*trasdosGS))
        else:
            armaduraMomentoDiseno = 1.4*(((empujeFundacionTrasdos+empujeRellenoTrasdos)*trasdosGS*0.5*trasdosGS)-0.5*tensionSuelo*(seccionApoyada-(baseMuro+distMuroIntradosGS))*0.3333*(seccionApoyada-(baseMuro+distMuroIntradosGS)))
        
        uZapata = (armaduraMomentoDiseno/(self.phiReduccion*self.B*ResistCaractHormCompresion*100*self.b*(espesorZapata-self.recubrimientoZapata)*(espesorZapata-self.recubrimientoZapata)))
        vZapata = (cargaAxial/(self.phiReduccion*self.B*ResistCaractHormCompresion*100*(espesorZapata-self.recubrimientoZapata)*self.b))
        wZapata = 1-((1-(2*uZapata))**0.5)-vZapata

        #Preguntar a Ossandón por ResistCaractHormCompresion, en algunas ecuciones está *100, entiendo que es por las unidades, pero hay que confirmar si están bien las unidades
        #En esta ecuación iba "w" donde va "wZapata"
        aceroPrincipalZapata = (self.B*wZapata*ResistCaractHormCompresion*self.b*(espesorZapata-self.recubrimientoZapata))/fluenciaAcero

        #subir cuantiaMinimaTransversalZapata
        cuantiaMinimaTransversalZapata = 0.0018*(trasdosGS+distMuroIntradosGS+baseMuro)*100*espesorZapata*100
        #subir cuantiaminimalongitudinal zapata
        cuantiaMinimaLongitudinalZapata = 0.0018*100*espesorZapata*100

        #pesoMuro y pesoMuroDiseno podria ir fuera de este for
        pesoMuro = (espesorCoronamiento*(self.alturaLibre+self.empotramiento)+(baseMuro-espesorCoronamiento)*(self.alturaLibre+self.empotramiento)*0.5)*self.densidadHormigon
        pesoMuroDiseno = 1.4*pesoMuro
                            
        #subir esfuerzoMuroDiseno
        esfuerzoMuroDiseno = pesoMuroDiseno/(trasdosGS+distMuroIntradosGS+baseMuro)

        if trasdosGS > distMuroIntradosGS:
            momentoDisenoTransversalZapata = (trasdosGS-baseMuro)*0.5*(trasdosGS-baseMuro)*0.25*esfuerzoMuroDiseno
        else:
            momentoDisenoTransversalZapata = (distMuroIntradosGS-baseMuro)*0.5*(distMuroIntradosGS-baseMuro)*0.25*esfuerzoMuroDiseno
                            
        momentoDisenoLongitudinalZapata = pesoMuroDiseno*0.5

        tensionDisenoAcero = momentoDisenoTransversalZapata/(0.9*(espesorZapata-self.recubrimientoZapata))
        tensionDisenoAceroLongitudinal = momentoDisenoLongitudinalZapata/(0.9*(espesorZapata-self.recubrimientoZapata))

        areaAceroTransversalZapata = tensionDisenoAcero/(0.9*fluenciaAcero)
        areaAceroLongitudinalZapata = tensionDisenoAceroLongitudinal/(0.9*fluenciaAcero)

        if cuantiaMinimaTransversalZapata > areaAceroTransversalZapata:
            areaAceroDisenoTransversal = cuantiaMinimaTransversalZapata
        else:
            areaAceroDisenoTransversal = areaAceroTransversalZapata
        if cuantiaMinimaLongitudinalZapata > areaAceroLongitudinalZapata:
            areaAceroDisenoLongitudinal = cuantiaMinimaLongitudinalZapata
        else:
            areaAceroDisenoLongitudinal = areaAceroLongitudinalZapata

        AceroTransversalMasCercano = self.combinacionesAceroNumpy[np.where(np.abs(np.float16(self.combinacionesAceroNumpy[:,2]) - areaAceroDisenoTransversal) == np.min(np.abs(np.float16(self.combinacionesAceroNumpy[:,2]) - areaAceroDisenoTransversal)))]
        AceroLongitudinalMasCercano = self.combinacionesAceroNumpy[np.where(np.abs(np.float16(self.combinacionesAceroNumpy[:,2]) - areaAceroDisenoLongitudinal) == np.min(np.abs(np.float16(self.combinacionesAceroNumpy[:,2]) - areaAceroDisenoLongitudinal)))]
        
        if aceroEstribos == 0:
            maximo_barrasAceroEstribos = 0
            phi_maximo_barrasAceroEstribos = None
        else:
            Resultado = self.combinacionesAceroNumpy[np.where(np.abs(np.float16(self.combinacionesAceroNumpy[:,2]) - aceroEstribos) == np.min(np.abs(np.float16(self.combinacionesAceroNumpy[:,2]) - aceroEstribos)))]
            index = np.argmax(Resultado[:,2])
            maximo_barrasAceroEstribos = Resultado[index][1]
            phi_maximo_barrasAceroEstribos = Resultado[index][0]

        if aceroPrincipalZapata == 0:
            maximo_barrasAceroPrincipalZapata = 0
            phi_maximo_barrasAceroPrincipalZapata = None
        else:
            Resultado = self.combinacionesAceroNumpy[np.where(np.abs(np.float16(self.combinacionesAceroNumpy[:,2]) - aceroPrincipalZapata) == np.min(np.abs(np.float16(self.combinacionesAceroNumpy[:,2]) - aceroPrincipalZapata)))]
            index = np.argmax(Resultado[:,2])
            maximo_barrasAceroPrincipalZapata = Resultado[index][1]
            phi_maximo_barrasAceroPrincipalZapata = Resultado[index][0]

        for valor in AceroTransversalMasCercano:
            if valor[1] > -9999999:
                maximo_barrasAceroTransversalZapata = valor[1]
                diametro_maximoTransversal = valor[0]

        for valor in AceroLongitudinalMasCercano:
            if valor[1] > -9999999:
                maximo_barrasAceroLongitudinalZapata = valor[1]
                diametro_maximoLongitudinal = valor[0]

        metrosEstribo = 0.05*(self.alturaLibre+self.empotramiento)+(espesorCoronamiento-2*self.recubrimientoMuro)+(((self.alturaLibre+self.empotramiento) - self.recubrimientoMuro)**2 + (baseMuro - espesorCoronamiento)**2)**0.5 + (espesorZapata - self.recubrimientoZapata) + (baseMuro - self.recubrimientoMuro)
        metrosAceroPrincipalZapata = 0.1*(espesorZapata)+(distMuroIntradosGS+baseMuro+trasdosGS-(2*self.recubrimientoZapata))

        kilosAceroEstribo = maximo_barrasAceroEstribos*(metrosEstribo) * self.KilosAcero[:,1][np.argwhere(self.KilosAcero[:,0] == phi_maximo_barrasAceroEstribos)[0]]
        kilosAceroPrincipalZapata = maximo_barrasAceroPrincipalZapata*(metrosAceroPrincipalZapata) * self.KilosAcero[:,1][np.argwhere(self.KilosAcero[:,0] == phi_maximo_barrasAceroPrincipalZapata)[0]]   
        kilosAceroTransversalZapata = maximo_barrasAceroTransversalZapata *(1-self.recubrimientoZapata) * self.KilosAcero[:,1][np.argwhere(self.KilosAcero[:,0] == diametro_maximoTransversal)]
        kilosAceroLongitudinalZapata = maximo_barrasAceroLongitudinalZapata *(trasdosGS+distMuroIntradosGS+baseMuro-(2*self.recubrimientoZapata)) * self.KilosAcero[:,1][np.argwhere(self.KilosAcero[:,0] == diametro_maximoLongitudinal)]
        
        kilosTotalesAcero = float(kilosAceroPrincipalZapata+kilosAceroEstribo+kilosAceroTransversalZapata+kilosAceroLongitudinalZapata)

        emisionUnitarioHormigon = float(self.emisionesHormigon[np.argwhere(self.emisionesHormigon[:,0].astype(int) == ResistCaractHormCompresion.astype(int)),1]) #ok
        precioUnitarioHormigon = float(self.precioHormigon[np.argwhere(self.precioHormigon[:, 0] == ResistCaractHormCompresion.astype(int)),1]) #ok

        emisionUnitarioAcero = float(self.emisionesAcero[np.argwhere(self.emisionesAcero[:,0] == fluenciaAcero),1]) #ok
        precioUnitarioAcero = float(self.precioAcero[np.argwhere(self.precioAcero[:,0] == fluenciaAcero),1]) #ok

        emisionTotal = float((emisionUnitarioHormigon*volumenHormigon)+(emisionUnitarioAcero*kilosTotalesAcero))
        costoTotal = float((precioUnitarioHormigon*volumenHormigon)+(precioUnitarioAcero*kilosTotalesAcero))

        return round(costoTotal,3), round(emisionTotal,3), round(volumenHormigon,3), round(kilosTotalesAcero,3), factibilidad

    def obtenerFitness(self,poblacion,matrix,solutionsRanking,params):
        """
        Calcula el fitness de toda la población aplicando discretización.
        
        Aplica la función de transferencia, discretiza las soluciones y evalua cada una
        calculando su fitness según la funcion objetivo especificada.
        

        Args:
            poblacion (numpy.ndarray): Matriz donde cada fila representa una solucion.
            matrix (numpy.ndarray): Matriz de soluciones discretizadas.
            solutionsRanking (numpy.ndarray): Ranking de soluciones basado en su fitness.
            params (dict): Diccionario con parámetros adicionales de funcion de transferencia (TF) y funcion objetivo (FO).

        Returns:
            tuple: Tupla con 7 elementos:
                - matrix (numpy.ndarray): Matriz de soluciones discretizadas actualizada.
                - fitness (numpy.ndarray): Array con valores de fitness de cada solucion.
                - solutionsRanking (numpy.ndarray): Indices ordenados de menor a mayor fitness.
                - BestCostoTotal (float): Costo de la mejor solucion.
                - BestEmisionTotal (float): Emisiones de la mejor solucion.
                - BestVolumenHormigon (float): Volumen de hormigon de la mejor solucion.
                - BestKilosTotalesAcero (float): Kilos de acero de la mejor solucion.
        """
        
        
        
        
        TF = params["TF"]
        FO = params["FO"]
        
        ds = DS.DiscretizationScheme(poblacion,matrix,solutionsRanking,TF,binarizationOperator = None)
        matrixProbT = ds.appliedTransferFunction()
        matrix = self.discretization(matrix,matrixProbT,solutionsRanking[0])

        costoTotal = np.zeros(poblacion.shape[0])
        emisionTotal = np.zeros(poblacion.shape[0])
        volumenHormigon = np.zeros(poblacion.shape[0])
        kilosTotalesAcero = np.zeros(poblacion.shape[0])
        factibilidad = np.zeros(poblacion.shape[0])

        for i in range(matrix.shape[0]):
            solution = matrix[i]
            costoTotal[i], emisionTotal[i], volumenHormigon[i], kilosTotalesAcero[i], factibilidad[i] = self.fitness(solution)

        # Por definir
        if FO == "C": #costoTotal
            fitness = np.multiply(costoTotal,factibilidad)
        if FO == "E": #emisionTotal
            fitness = np.multiply(emisionTotal,factibilidad)
        if FO == "C+E": #costoTotal + emisionTotal
            fitness = np.multiply((costoTotal +emisionTotal),factibilidad)

        solutionsRanking = np.argsort(fitness)
        
        BestCostoTotal = costoTotal[solutionsRanking[0]]
        BestEmisionTotal = emisionTotal[solutionsRanking[0]]
        BestVolumenHormigon = volumenHormigon[solutionsRanking[0]]
        BestKilosTotalesAcero = kilosTotalesAcero[solutionsRanking[0]]

        return matrix,fitness,solutionsRanking,BestCostoTotal,BestEmisionTotal,BestVolumenHormigon,BestKilosTotalesAcero

    def getAlturaLibre(self):
        """Obtiene la altura libre del muro de contencion

        Returns:
            float: Altura libre del muro en metros. 
        """
        return self.alturaLibre

    def discretization(self,matrix,matrixProbT,BestSolutionsRanking):
        """Aplica discretizacion a la matriz de soluciones.
        
        Utiliza probabilidades de transferencia y el parametro beta para decidir si mantener el valor de la mejor solucion o generar uno nuevo aleatorio.

        Args:
            matrix (numpy.ndarray): Array de soluciones discretizadas actual.
            matrixProbT (numpy.ndarray): Matriz de probabilidades de transferencia.
            BestSolutionsRanking (int): Indice de la mejor solucion en el ranking.

        Returns:
            numpy.ndarray: Matriz de soluciones discretizadas actualizada.
        """
        r1 = np.random.uniform(low=0.0, high=1.0)
        r2 = np.random.uniform(low=0.0, high=1.0)
        for i in range(matrix.shape[0]):
            if i !=int(BestSolutionsRanking):
                continue
            else:
                for j in range(matrix.shape[1]):
                    if matrixProbT[i,j] > r1:
                        if self.betaDis > r2:
                            matrix[i,j] = matrix[int(BestSolutionsRanking),j]
                        else:
                            matrix[i,j] = self.obtenerDimensionRandom(j)

        return matrix
                    
    def generarPoblacionInicial(self,pob,dim):
        """Genera una poblacion inicial aleatoria de soluciones factibles.
        
        Crea soluciones aleatorias seleccionando valores de los dominios discretos para cada variable de decision.

        Args:
            pob (int): Tamaño de la poblacion.
            dim (int): Numero de dimensiones del problema (6 en este caso).

        Returns:
            numpy.ndarray: Matriz de tamaño pob x dim con la poblacion inicial aletoria.
        """
        matrix = np.zeros((pob,dim))
        for i in range(matrix.shape[0]):
            matrix[i,0] = self.domResistCaractHormCompresion[np.random.randint(low=0,high=self.domResistCaractHormCompresion.shape[0])]
            matrix[i,1] = self.domFluenciaAcero[np.random.randint(low=0,high=self.domFluenciaAcero.shape[0])]
            matrix[i,2] = self.domEspesorCoronamiento[np.random.randint(low=0,high=self.domEspesorCoronamiento.shape[0])]
            matrix[i,3] = self.domBaseMuro[np.random.randint(low=0,high=self.domBaseMuro.shape[0])]
            matrix[i,4] = self.domEspesorZapata[np.random.randint(low=0,high=self.domEspesorZapata.shape[0])]
            matrix[i,5] = self.domDensidadTerreno[np.random.randint(low=0,high=self.domDensidadTerreno.shape[0])]

        return matrix
    
    def obtenerDimensionRandom(self,j):
        """Obtiene un valor aleatorio del dominio de la dimension j

        Args:
            j (int): Indice de la dimension ( 0: ResistCaractHormCompresion, 1: FluenciaAcero, 2: EspesorCoronamiento, 3: BaseMuro, 4: EspesorZapata, 5: DensidadTerreno).

        Returns:
            float: Valor aleatorio del dominio de la dimension j.
        """
        if j == 0:
            randDim = self.domResistCaractHormCompresion[np.random.randint(low=0,high=self.domResistCaractHormCompresion.shape[0])]
        if j == 1:
            randDim = self.domFluenciaAcero[np.random.randint(low=0,high=self.domFluenciaAcero.shape[0])]
        if j == 2:
            randDim = self.domEspesorCoronamiento[np.random.randint(low=0,high=self.domEspesorCoronamiento.shape[0])]
        if j == 3:
            randDim = self.domBaseMuro[np.random.randint(low=0,high=self.domBaseMuro.shape[0])]
        if j == 4:
            randDim = self.domEspesorZapata[np.random.randint(low=0,high=self.domEspesorZapata.shape[0])]
        if j == 5:
            randDim = self.domDensidadTerreno[np.random.randint(low=0,high=self.domDensidadTerreno.shape[0])]
        
        return randDim



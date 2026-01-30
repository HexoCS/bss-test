-- Tabla para almacenar resultados parseados y normalizados
-- Facilita consultas rapidas sin necesidad de parsear JSON repetidamente

CREATE TABLE IF NOT EXISTS resultados_normalizados (
    id SERIAL PRIMARY KEY,
    id_ejecucion INTEGER NOT NULL REFERENCES datos_ejecucion(id) ON DELETE CASCADE,
    
    -- Informacion del algoritmo (parseado de 'parametros' JSON)
    algoritmo_mh VARCHAR(50),
    algoritmo_ml VARCHAR(50),
    problema VARCHAR(20),
    instancia VARCHAR(100),
    
    -- Parametros de configuracion
    poblacion INTEGER,
    iteraciones_totales INTEGER,
    discretization_scheme VARCHAR(20),
    reward_type VARCHAR(100),
    
    -- Metricas de resultado (de resultado_ejecucion)
    fitness_final NUMERIC,
    tiempo_ejecucion_segundos NUMERIC,
    
    -- Promedios de las 6 medidas de diversidad calculadas durante ejecucion
    -- Parseadas desde datos_iteracion.parametros_iteracion.Diversidades
    diversidad_0_promedio NUMERIC,  -- DimensionalHussain
    diversidad_1_promedio NUMERIC,  -- PesosDeInercia
    diversidad_2_promedio NUMERIC,  -- LeungGaoXu
    diversidad_3_promedio NUMERIC,  -- Entropica
    diversidad_4_promedio NUMERIC,  -- Hamming
    diversidad_5_promedio NUMERIC,  -- MomentoDeInercia
    
    -- Metadata
    fecha_procesamiento TIMESTAMP DEFAULT NOW(),
    
    -- Constraint para evitar duplicados
    UNIQUE(id_ejecucion)
);

-- Indices para consultas rapidas
CREATE INDEX IF NOT EXISTS idx_resultados_algoritmo_mh ON resultados_normalizados(algoritmo_mh);
CREATE INDEX IF NOT EXISTS idx_resultados_algoritmo_ml ON resultados_normalizados(algoritmo_ml);
CREATE INDEX IF NOT EXISTS idx_resultados_problema ON resultados_normalizados(problema);
CREATE INDEX IF NOT EXISTS idx_resultados_instancia ON resultados_normalizados(instancia);
CREATE INDEX IF NOT EXISTS idx_resultados_fitness ON resultados_normalizados(fitness_final);

-- Indices para las 6 medidas de diversidad
CREATE INDEX IF NOT EXISTS idx_diversidad_0 ON resultados_normalizados(diversidad_0_promedio);
CREATE INDEX IF NOT EXISTS idx_diversidad_1 ON resultados_normalizados(diversidad_1_promedio);
CREATE INDEX IF NOT EXISTS idx_diversidad_2 ON resultados_normalizados(diversidad_2_promedio);
CREATE INDEX IF NOT EXISTS idx_diversidad_3 ON resultados_normalizados(diversidad_3_promedio);
CREATE INDEX IF NOT EXISTS idx_diversidad_4 ON resultados_normalizados(diversidad_4_promedio);
CREATE INDEX IF NOT EXISTS idx_diversidad_5 ON resultados_normalizados(diversidad_5_promedio);

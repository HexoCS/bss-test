import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
import time
import warnings
from sqlalchemy import text

#REVISAR ITERACIÓN DE INTERACCIONES CON LA BASE DE DATOS, REVISAR DELIMITADORES DE VECTOR SOLUCION

# Evita avisos innecesarios de Pandas con SQLAlchemy
warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy connectable.*')

# Asegurar que el sistema encuentre la carpeta 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database import DatabaseManager

st.set_page_config(page_title="Metaheuristic Solver Dashboard", layout="wide")

@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

def get_queue_stats():
    try:
        return db.get_queue_status()
    except Exception as e:
        st.error(f"Error al conectar con la DB: {e}")
        return {}

st.title("Metaheuristic Solver Dashboard")

# Métricas Principales
stats = get_queue_stats()
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total", stats.get('total', 0))
c2.metric("Pendientes", stats.get('pendiente', 0))
c3.metric("Ejecutando", stats.get('ejecutando', 0))
c4.metric("Completados", stats.get('completado', 0))
c5.metric("Errores", stats.get('error', 0))


st.header("Recent Experiments")
try:
    query = "SELECT id, nombre_algoritmo, estado, inicio, fin FROM datos_ejecucion ORDER BY id DESC LIMIT 50"

    df = pd.read_sql(text(query), db.engine)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay experimentos registrados.")
except Exception as e:
    st.error(f"Error cargando experimentos: {e}")

# Resultados Recientes
st.header("Recent Results")
try:
    query_res = """
        SELECT re.id_ejecucion, de.nombre_algoritmo, re.fitness
        FROM resultado_ejecucion re
        JOIN datos_ejecucion de ON re.id_ejecucion = de.id
        ORDER BY re.id DESC LIMIT 20
    """
    df_res = pd.read_sql(text(query_res), db.engine)
    if not df_res.empty:
        st.dataframe(df_res, use_container_width=True, hide_index=True)
    else:
        st.info("No hay resultados disponibles.")
except Exception as e:
    st.error(f"Error cargando resultados: {e}")
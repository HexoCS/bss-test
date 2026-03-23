import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
from cli.post_processor import obtener_diversidades_por_iteracion

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


# Análisis de Diversidades por Iteracion
st.header("Diversity Analysis per Iteration")

try:
    # Obtener lista de experimentos terminados
    query_exp = "SELECT id, nombre_algoritmo FROM datos_ejecucion WHERE estado = 'terminado' ORDER BY id DESC LIMIT 100"
    df_exp = pd.read_sql(text(query_exp), db.engine)
    
    if not df_exp.empty:
        # Selector de experimento
        exp_options = df_exp.apply(lambda x: f"ID: {x['id']} - {x['nombre_algoritmo']}", axis=1)
        selected_exp = st.selectbox(
            "Select an experiment to analyze:",
            options=range(len(df_exp)),
            format_func=lambda i: exp_options.iloc[i]
        )
        
        exp_id = df_exp.iloc[selected_exp]['id']
        
        if st.button("Load Diversity Data", key=f"load_div_{exp_id}"):
            with st.spinner("Loading diversity data..."):
                try:
                    div_data = obtener_diversidades_por_iteracion(db, exp_id)
                    
                    if div_data['exito']:
                        st.success(f"Loaded {len(div_data['iteraciones'])} iterations")
                        
                        # Crear dataframe con los datos de diversidad
                        df_diversidades = pd.DataFrame({
                            'Iteration': div_data['iteraciones'],
                            'Diversity 0': div_data['diversidad_0'],
                            'Diversity 1': div_data['diversidad_1'],
                            'Diversity 2': div_data['diversidad_2'],
                            'Diversity 3': div_data['diversidad_3'],
                            'Diversity 4': div_data['diversidad_4'],
                            'Diversity 5': div_data['diversidad_5'],
                        })
                        
                        # Tabs para diferentes vistas
                        tab1, tab2, tab3 = st.tabs(["Combined Plot", "Individual Plots", "Data Table"])
                        
                        with tab1:
                            # Gráfico combinado
                            fig_combined = go.Figure()
                            
                            for i in range(6):
                                fig_combined.add_trace(go.Scatter(
                                    x=df_diversidades['Iteration'],
                                    y=df_diversidades[f'Diversity {i}'],
                                    mode='lines+markers',
                                    name=f'Diversity {i}',
                                    hovertemplate='<b>Diversity ' + str(i) + '</b><br>Iteration: %{x}<br>Value: %{y:.6f}<extra></extra>'
                                ))
                            
                            fig_combined.update_layout(
                                title=f"All Diversity Measures - Experiment {exp_id}",
                                xaxis_title="Iteration",
                                yaxis_title="Diversity Value",
                                hovermode='x unified',
                                height=500,
                                template="plotly_white"
                            )
                            st.plotly_chart(fig_combined, use_container_width=True)
                        
                        with tab2:
                            # Gráficos individuales en una grilla 2x3
                            cols = st.columns(2)
                            
                            for i in range(6):
                                col = cols[i % 2]
                                
                                fig_individual = go.Figure()
                                fig_individual.add_trace(go.Scatter(
                                    x=df_diversidades['Iteration'],
                                    y=df_diversidades[f'Diversity {i}'],
                                    mode='lines+markers',
                                    line=dict(color=px.colors.qualitative.Plotly[i]),
                                    fill='tozeroy',
                                    hovertemplate='Iteration: %{x}<br>Value: %{y:.6f}<extra></extra>'
                                ))
                                
                                fig_individual.update_layout(
                                    title=f"Diversity {i}",
                                    xaxis_title="Iteration",
                                    yaxis_title="Value",
                                    height=400,
                                    template="plotly_white"
                                )
                                
                                col.plotly_chart(fig_individual, use_container_width=True)
                        
                        with tab3:
                            # Tabla de datos
                            st.dataframe(df_diversidades, use_container_width=True, hide_index=True)
                            
                            # Estadísticas
                            st.subheader("Statistics")
                            stats_cols = st.columns(6)
                            
                            for i in range(6):
                                with stats_cols[i]:
                                    div_values = df_diversidades[f'Diversity {i}'].dropna()
                                    if len(div_values) > 0:
                                        st.metric(
                                            f"Div {i}",
                                            f"{div_values.mean():.6f}",
                                            f"Min: {div_values.min():.6f} | Max: {div_values.max():.6f}"
                                        )
                    else:
                        st.warning(f"No diversity data available for experiment {exp_id}")
                        
                except Exception as e:
                    st.error(f"Error loading diversity data: {e}")
    else:
        st.info("No completed experiments available for analysis.")
        
except Exception as e:
    st.error(f"Error loading experiments: {e}")
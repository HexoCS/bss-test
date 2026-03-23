import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

#REVISAR ITERACIÓN DE INTERACCIONES CON LA BASE DE DATOS, REVISAR DELIMITADORES DE VECTOR SOLUCION

# Asegurar que el sistema encuentre la carpeta 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database import DatabaseManager
from sqlalchemy import text


def query_to_df(engine, sql, params=None):
    """Ejecuta una query y devuelve un DataFrame, compatible con cualquier versión."""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        rows = result.fetchall()
        columns = list(result.keys())
    return pd.DataFrame(rows, columns=columns)



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




# Fitness Over Time
st.header("Fitness Over Time")

# Cargar todos los experimentos para selector
try:
    df_exp = query_to_df(db.engine, "SELECT id, nombre_algoritmo FROM datos_ejecucion ORDER BY id DESC LIMIT 100")
    
    if not df_exp.empty:
        # Columnas para controles
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Selector de experimento
            exp_options = df_exp.apply(lambda x: f"ID {x['id']}: {x['nombre_algoritmo']}", axis=1)
            selected_exp_idx = st.selectbox(
                "Elige un experimento",
                options=range(len(df_exp)),
                format_func=lambda i: exp_options.iloc[i],
                key="fitness_exp_select"
            )
            selected_exp_id = df_exp.iloc[selected_exp_idx]['id']
        
        with col2:
            # Tipo de gráfico
            plot_type = st.selectbox(
                "Tipo de gráfico",
                ["Líneas + Marcadores", "Solo Líneas", "Solo Marcadores", "Área"],
                key="fitness_plot_type"
            )
        
        with col3:
            # Métrica a mostrar
            metric_type = st.selectbox(
                "Métrica",
                ["fitness_mejor", "fitness_promedio", "fitness_mejor_iteracion"],
                key="fitness_metric"
            )
        
        # Cargar datos de iteraciones
        try:
            df_iterations = query_to_df(
                db.engine,
                "SELECT numero_iteracion, fitness_mejor, fitness_promedio, fitness_mejor_iteracion "
                "FROM datos_iteracion WHERE id_ejecucion = :exp_id ORDER BY numero_iteracion ASC",
                {"exp_id": int(selected_exp_id)}
            )
            
            if not df_iterations.empty:
                # Crear gráfico
                fig = go.Figure()
                
                if plot_type == "Líneas + Marcadores":
                    fig.add_trace(go.Scatter(
                        x=df_iterations['numero_iteracion'],
                        y=df_iterations[metric_type],
                        mode='lines+markers',
                        name=metric_type,
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=6)
                    ))
                elif plot_type == "Solo Líneas":
                    fig.add_trace(go.Scatter(
                        x=df_iterations['numero_iteracion'],
                        y=df_iterations[metric_type],
                        mode='lines',
                        name=metric_type,
                        line=dict(color='#1f77b4', width=2)
                    ))
                elif plot_type == "Solo Marcadores":
                    fig.add_trace(go.Scatter(
                        x=df_iterations['numero_iteracion'],
                        y=df_iterations[metric_type],
                        mode='markers',
                        name=metric_type,
                        marker=dict(size=8, color='#1f77b4')
                    ))
                elif plot_type == "Área":
                    fig.add_trace(go.Scatter(
                        x=df_iterations['numero_iteracion'],
                        y=df_iterations[metric_type],
                        mode='lines',
                        name=metric_type,
                        fill='tozeroy',
                        line=dict(color='#1f77b4', width=2)
                    ))
                
                fig.update_layout(
                    title=f"Fitness Over Time - Experimento {selected_exp_id}",
                    xaxis_title="Iteración",
                    yaxis_title=metric_type,
                    hovermode='x unified',
                    height=500,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Estadísticas
                st.subheader("Estadísticas")
                stat_cols = st.columns(4)
                stat_cols[0].metric("Mejor", f"{df_iterations[metric_type].min():.2f}")
                stat_cols[1].metric("Peor", f"{df_iterations[metric_type].max():.2f}")
                stat_cols[2].metric("Promedio", f"{df_iterations[metric_type].mean():.2f}")
                stat_cols[3].metric("Total Iteraciones", f"{len(df_iterations)}")
            else:
                st.warning(f"No hay datos de iteraciones para el experimento {selected_exp_id}")
        except Exception as e:
            st.error(f"Error cargando datos: {e}")
    else:
        st.info("No hay experimentos disponibles")
except Exception as e:
    st.error(f"Error cargando experimentos: {e}")
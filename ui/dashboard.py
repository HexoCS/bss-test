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


# Visualización Personalizada de Experimentos
st.header("Custom Experiment Visualization")

try:
    # Cargar todos los experimentos
    query_all_exp = "SELECT id, nombre_algoritmo, estado, inicio, fin FROM datos_ejecucion ORDER BY id DESC LIMIT 200"
    df_all_exp = pd.read_sql(text(query_all_exp), db.engine)
    
    if not df_all_exp.empty:
        # Columnas para controles
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Selector de experimento
            exp_options = df_all_exp.apply(lambda x: f"ID: {x['id']} - {x['nombre_algoritmo']} ({x['estado']})", axis=1)
            selected_exp_idx = st.selectbox(
                "Select Experiment",
                options=range(len(df_all_exp)),
                format_func=lambda i: exp_options.iloc[i],
                key="custom_exp_select"
            )
            selected_exp_id = df_all_exp.iloc[selected_exp_idx]['id']
        
        with col2:
            # Tipo de dato a graficar
            graph_type = st.selectbox(
                "Graph Type",
                ["Fitness Over Time", "Diversity Measures", "Comparison", "Fitness Distribution"],
                key="custom_graph_select"
            )
        
        with col3:
            # Tipo de gráfico
            plot_style = st.selectbox(
                "Plot Style",
                ["Lines + Markers", "Lines Only", "Bars", "Scatter", "Area"],
                key="custom_plot_select"
            )
        
        with col4:
            # Botón para graficar
            generate_plot = st.button("Generate Graph", key="custom_gen_btn", use_container_width=True)
        
        # Generar gráfico basado en la selección
        if generate_plot:
            with st.spinner("Loading data..."):
                try:
                    if graph_type == "Fitness Over Time":
                        # Obtener datos de fitness histórico
                        query_fitness = f"""
                            SELECT iteracion, fitness
                            FROM resultado_ejecucion
                            WHERE id_ejecucion = {selected_exp_id}
                            ORDER BY iteracion ASC
                        """
                        df_fitness = pd.read_sql(text(query_fitness), db.engine)
                        
                        if not df_fitness.empty:
                            fig = go.Figure()
                            
                            if plot_style == "Lines + Markers":
                                fig.add_trace(go.Scatter(x=df_fitness['iteracion'], y=df_fitness['fitness'],
                                                        mode='lines+markers', name='Fitness', 
                                                        line=dict(color='#1f77b4', width=2)))
                            elif plot_style == "Lines Only":
                                fig.add_trace(go.Scatter(x=df_fitness['iteracion'], y=df_fitness['fitness'],
                                                        mode='lines', name='Fitness',
                                                        line=dict(color='#1f77b4', width=2)))
                            elif plot_style == "Scatter":
                                fig.add_trace(go.Scatter(x=df_fitness['iteracion'], y=df_fitness['fitness'],
                                                        mode='markers', name='Fitness',
                                                        marker=dict(size=6, color='#1f77b4')))
                            elif plot_style == "Area":
                                fig.add_trace(go.Scatter(x=df_fitness['iteracion'], y=df_fitness['fitness'],
                                                        mode='lines', name='Fitness', fill='tozeroy',
                                                        line=dict(color='#1f77b4', width=2)))
                            elif plot_style == "Bars":
                                fig.add_trace(go.Bar(x=df_fitness['iteracion'], y=df_fitness['fitness'],
                                                    name='Fitness', marker=dict(color='#1f77b4')))
                            
                            fig.update_layout(
                                title=f"Fitness Over Time - Experiment {selected_exp_id}",
                                xaxis_title="Iteration",
                                yaxis_title="Fitness Value",
                                hovermode='x unified',
                                height=500,
                                template="plotly_white"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Mostrar estadísticas
                            st.subheader("Statistics")
                            stat_cols = st.columns(4)
                            stat_cols[0].metric("Best Fitness", f"{df_fitness['fitness'].min():.6f}")
                            stat_cols[1].metric("Worst Fitness", f"{df_fitness['fitness'].max():.6f}")
                            stat_cols[2].metric("Average Fitness", f"{df_fitness['fitness'].mean():.6f}")
                            stat_cols[3].metric("Total Iterations", f"{len(df_fitness)}")
                        else:
                            st.warning(f"No fitness data available for experiment {selected_exp_id}")
                    
                    elif graph_type == "Diversity Measures":
                        # Obtener diversidades
                        div_data = obtener_diversidades_por_iteracion(db, selected_exp_id)
                        
                        if div_data['exito']:
                            df_div = pd.DataFrame({
                                'Iteration': div_data['iteraciones'],
                                'Diversity 0': div_data['diversidad_0'],
                                'Diversity 1': div_data['diversidad_1'],
                                'Diversity 2': div_data['diversidad_2'],
                                'Diversity 3': div_data['diversidad_3'],
                                'Diversity 4': div_data['diversidad_4'],
                                'Diversity 5': div_data['diversidad_5'],
                            })
                            
                            fig = go.Figure()
                            colors = px.colors.qualitative.Plotly
                            
                            for i in range(6):
                                if plot_style == "Lines + Markers":
                                    fig.add_trace(go.Scatter(x=df_div['Iteration'], y=df_div[f'Diversity {i}'],
                                                            mode='lines+markers', name=f'Diversity {i}',
                                                            line=dict(color=colors[i])))
                                elif plot_style == "Lines Only":
                                    fig.add_trace(go.Scatter(x=df_div['Iteration'], y=df_div[f'Diversity {i}'],
                                                            mode='lines', name=f'Diversity {i}',
                                                            line=dict(color=colors[i])))
                                elif plot_style == "Scatter":
                                    fig.add_trace(go.Scatter(x=df_div['Iteration'], y=df_div[f'Diversity {i}'],
                                                            mode='markers', name=f'Diversity {i}',
                                                            marker=dict(color=colors[i])))
                                elif plot_style == "Area":
                                    fig.add_trace(go.Scatter(x=df_div['Iteration'], y=df_div[f'Diversity {i}'],
                                                            mode='lines', name=f'Diversity {i}', 
                                                            stackgroup='one', fill='tonexty',
                                                            line=dict(color=colors[i])))
                            
                            fig.update_layout(
                                title=f"All Diversity Measures - Experiment {selected_exp_id}",
                                xaxis_title="Iteration",
                                yaxis_title="Diversity Value",
                                hovermode='x unified',
                                height=500,
                                template="plotly_white"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning(f"No diversity data available for experiment {selected_exp_id}")
                    
                    elif graph_type == "Comparison":
                        # Comparar múltiples experimentos
                        st.info("Select multiple experiments to compare their fitness evolution")
                        
                        selected_exp_ids = st.multiselect(
                            "Experiments to Compare",
                            options=df_all_exp['id'].tolist(),
                            default=[selected_exp_id],
                            key="comparison_select"
                        )
                        
                        if selected_exp_ids and st.button("Compare", key="comparison_btn"):
                            fig = go.Figure()
                            
                            for exp_id in selected_exp_ids:
                                query_fit = f"""
                                    SELECT iteracion, fitness
                                    FROM resultado_ejecucion
                                    WHERE id_ejecucion = {exp_id}
                                    ORDER BY iteracion ASC
                                """
                                df_fit = pd.read_sql(text(query_fit), db.engine)
                                
                                if not df_fit.empty:
                                    exp_name = df_all_exp[df_all_exp['id'] == exp_id]['nombre_algoritmo'].values[0]
                                    
                                    if plot_style == "Lines + Markers":
                                        fig.add_trace(go.Scatter(x=df_fit['iteracion'], y=df_fit['fitness'],
                                                                mode='lines+markers', name=f"Exp {exp_id} ({exp_name})"))
                                    elif plot_style in ["Lines Only", "Area"]:
                                        fig.add_trace(go.Scatter(x=df_fit['iteracion'], y=df_fit['fitness'],
                                                                mode='lines', name=f"Exp {exp_id} ({exp_name})",
                                                                fill='tozeroy' if plot_style == "Area" else None))
                                    elif plot_style == "Scatter":
                                        fig.add_trace(go.Scatter(x=df_fit['iteracion'], y=df_fit['fitness'],
                                                                mode='markers', name=f"Exp {exp_id} ({exp_name})"))
                            
                            fig.update_layout(
                                title="Experiments Comparison",
                                xaxis_title="Iteration",
                                yaxis_title="Fitness Value",
                                hovermode='x unified',
                                height=500,
                                template="plotly_white"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    elif graph_type == "Fitness Distribution":
                        # Distribución de fitness
                        query_dist = f"""
                            SELECT fitness
                            FROM resultado_ejecucion
                            WHERE id_ejecucion = {selected_exp_id}
                        """
                        df_dist = pd.read_sql(text(query_dist), db.engine)
                        
                        if not df_dist.empty:
                            fig = go.Figure()
                            
                            if plot_style == "Bars":
                                fig.add_trace(go.Histogram(x=df_dist['fitness'], nbinsx=30,
                                                          name='Fitness Distribution',
                                                          marker=dict(color='#1f77b4')))
                            else:
                                fig.add_trace(go.Box(y=df_dist['fitness'], name='Fitness Distribution',
                                                    marker=dict(color='#1f77b4')))
                            
                            fig.update_layout(
                                title=f"Fitness Distribution - Experiment {selected_exp_id}",
                                xaxis_title="Fitness Value" if plot_style == "Bars" else "",
                                yaxis_title="Count" if plot_style == "Bars" else "Fitness Value",
                                height=500,
                                template="plotly_white"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning(f"No data available for experiment {selected_exp_id}")
                
                except Exception as e:
                    st.error(f"Error generating graph: {e}")
    else:
        st.info("No experiments available.")
        
except Exception as e:
    st.error(f"Error loading experiments: {e}")



"""
Streamlit Dashboard for Metaheuristic Solver

Provides real-time monitoring and management of experiment queues.

Features:
- Queue status overview
- Experiment progress tracking
- Worker monitoring
- Results visualization

Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime
import time
import warnings

# Suppress pandas SQLAlchemy warnings
warnings.filterwarnings('ignore', message='pandas only supports SQLAlchemy connectable')

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import DatabaseManager


# Page configuration
st.set_page_config(
    page_title="Metaheuristic Solver Dashboard",
    page_icon="chart_with_upwards_trend",
    layout="wide"
)

# Initialize database connection
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()


def get_queue_stats():
    """Fetch current queue statistics."""
    return db.get_queue_status()


def format_duration(start, end):
    """Calculate and format duration."""
    if start is None or end is None:
        return "N/A"
    duration = end - start
    hours = duration.total_seconds() / 3600
    return f"{hours:.2f}h"


# Dashboard header
st.title("Metaheuristic Solver Dashboard")
st.markdown("Real-time monitoring of experiment queues and results")

# Refresh control
col1, col2 = st.columns([3, 1])
with col2:
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    if st.button("Refresh Now"):
        st.rerun()

if auto_refresh:
    time.sleep(30)
    st.rerun()

# Queue Status Overview
st.header("Queue Status")

stats = get_queue_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total", stats.get('total', 0))

with col2:
    st.metric("Pending", stats.get('pendiente', 0), 
              delta=None, delta_color="off")

with col3:
    st.metric("Executing", stats.get('ejecutando', 0),
              delta=None, delta_color="normal")

with col4:
    st.metric("Completed", stats.get('completado', 0),
              delta=None, delta_color="normal")

with col5:
    st.metric("Errors", stats.get('error', 0),
              delta=None, delta_color="inverse")

# Progress visualization
if stats.get('total', 0) > 0:
    completed_pct = (stats.get('completado', 0) / stats['total']) * 100
    st.progress(completed_pct / 100)
    st.caption(f"Overall Progress: {completed_pct:.1f}%")

# Detailed experiment view
st.header("Recent Experiments")

try:
    # Query recent experiments
    query = """
        SELECT 
            id,
            nombre_algoritmo,
            estado,
            inicio,
            fin
        FROM datos_ejecucion
        ORDER BY id DESC
        LIMIT 100
    """
    
    with db.engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    if not df.empty:
        # Add duration column
        df['Duration'] = df.apply(
            lambda row: format_duration(row['inicio'], row['fin'])
            if pd.notna(row['inicio']) and pd.notna(row['fin'])
            else "In Progress" if row['estado'] == 'ejecutando'
            else "Not Started",
            axis=1
        )
        
        # Display table
        st.dataframe(
            df[['id', 'nombre_algoritmo', 'estado', 'inicio', 'fin', 'Duration']],
            use_container_width=True,
            hide_index=True
        )
        
        # Status distribution chart
        st.subheader("Status Distribution")
        status_counts = df['estado'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Experiment Status Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No experiments found in the queue")

except Exception as e:
    st.error(f"Error loading experiment data: {e}")

# Recent results
st.header("Recent Results")

try:
    query = """
        SELECT 
            re.id_ejecucion,
            de.nombre_algoritmo,
            re.fitness,
            re.inicio,
            re.fin
        FROM resultado_ejecucion re
        JOIN datos_ejecucion de ON re.id_ejecucion = de.id
        ORDER BY re.id DESC
        LIMIT 50
    """
    
    with db.engine.connect() as conn:
        df_results = pd.read_sql(query, conn)
    
    if not df_results.empty:
        # Convert fitness to numeric
        df_results['fitness'] = pd.to_numeric(df_results['fitness'], errors='coerce')
        
        # Display best results
        st.subheader("Best Results (Top 10 by Fitness)")
        best_results = df_results.nsmallest(10, 'fitness')
        st.dataframe(
            best_results[['id_ejecucion', 'nombre_algoritmo', 'fitness']],
            use_container_width=True,
            hide_index=True
        )
        
        # Fitness distribution
        st.subheader("Fitness Distribution")
        fig_fitness = px.histogram(
            df_results,
            x='fitness',
            nbins=30,
            title="Distribution of Final Fitness Values"
        )
        st.plotly_chart(fig_fitness, use_container_width=True)
        
    else:
        st.info("No results available yet")

except Exception as e:
    st.error(f"Error loading results: {e}")

# Footer
st.markdown("---")
st.caption("BSS Metaheuristic Solver - Refactored Architecture")

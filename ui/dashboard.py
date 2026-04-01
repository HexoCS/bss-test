import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import sys
import os
import json
import yaml



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





tab_fitness, tab_summary, tab_queue = st.tabs([
    "Fitness Over Time",
    "Summary Table",
    "Queue Experiments",
])

with tab_fitness:
    # Fitness Over Time
    st.header("Fitness Over Time")

    DIVERSITY_NAMES = [
        "DimensionalHussain",
        "PesosDeInercia",
        "LeungGaoXu",
        "Entropica",
        "Hamming",
        "MomentoDeInercia",
    ]

    def safe_float(value, default=0.0):
        """Convierte a float de forma segura, manejando arrays como strings."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            # Si es un string tipo '[100. 100. 96.15 ...]', extraer el primer valor
            s = str(value).strip("[]")
            parts = s.split()
            if parts:
                try:
                    return float(parts[0])
                except (ValueError, TypeError):
                    return default
            return default

    def parse_iteration_data(df_raw):
        """Parsea los datos de iteración extrayendo métricas del JSON parametros_iteracion."""
        records = []
        for _, row in df_raw.iterrows():
            rec = {
                "numero_iteracion": row["numero_iteracion"],
                "fitness_mejor": safe_float(row["fitness_mejor"]),
            }
            params_raw = row.get("parametros_iteracion")
            if params_raw:
                params = json.loads(params_raw) if isinstance(params_raw, str) else params_raw
                rec["fitness_iteracion"] = safe_float(params.get("fitness", 0))
                rec["PorcentajeExplor"] = safe_float(params.get("PorcentajeExplor", 0))
                # Parsear diversidades
                div_str = params.get("Diversidades", "")
                if div_str:
                    div_str = str(div_str).strip("[]")
                    div_values = div_str.split()
                    for i, val in enumerate(div_values):
                        if i < 6:
                            try:
                                rec[DIVERSITY_NAMES[i]] = float(val)
                            except ValueError:
                                rec[DIVERSITY_NAMES[i]] = 0.0
            records.append(rec)

        df = pd.DataFrame(records)

        # Calcular fórmulas XPL% y XPT% para cada diversidad
        # XPL% = (Div / Div_max) * 100
        # XPT% = (|Div - Div_max| / Div_max) * 100
        for div_name in DIVERSITY_NAMES:
            if div_name in df.columns:
                div_max = df[div_name].max()
                if div_max > 0:
                    df[f"XPL_{div_name}"] = (df[div_name] / div_max) * 100
                    df[f"XPT_{div_name}"] = (abs(df[div_name] - div_max) / div_max) * 100
                else:
                    df[f"XPL_{div_name}"] = 0.0
                    df[f"XPT_{div_name}"] = 0.0

        return df

    # Cargar todos los experimentos para selector
    try:
        df_exp = query_to_df(db.engine, "SELECT id, nombre_algoritmo FROM datos_ejecucion ORDER BY id DESC")

        if not df_exp.empty:
            # Columnas para controles principales
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
                # Construir lista de métricas con diversidades y sus ratios
                xpl_metrics = [f"XPL_{div}" for div in DIVERSITY_NAMES]

                all_metrics = (
                    [
                        "fitness_mejor",
                        "fitness_iteracion",
                        "PorcentajeExplor",
                        "---DIVERSITY ANALYSIS (XPL% + XPT%)---",
                    ] + 
                    xpl_metrics
                )
                metric_type = st.selectbox(
                    "Métrica",
                    all_metrics,
                    key="fitness_metric"
                )

            # Cargar datos de iteraciones (solo columnas que existen)
            try:
                df_raw = query_to_df(
                    db.engine,
                    "SELECT numero_iteracion, fitness_mejor, parametros_iteracion "
                    "FROM datos_iteracion WHERE id_ejecucion = :exp_id ORDER BY numero_iteracion ASC",
                    {"exp_id": int(selected_exp_id)}
                )

                if not df_raw.empty:
                    df_iterations = parse_iteration_data(df_raw)

                    # Ignorar separadores en metric_type
                    if metric_type.startswith("---"):
                        st.info("Selecciona una métrica válida (no un separador)")
                    elif metric_type not in df_iterations.columns:
                        st.warning(f"La métrica '{metric_type}' no está disponible para este experimento.")
                    else:
                        # ─ CREAR COLUMNAS: GRÁFICO + OPCIONES ─
                        col_graph, col_options = st.columns([2.5, 1])
                        
                        # COLUMNA DE OPCIONES (DERECHA)
                        with col_options:
                            st.subheader("Estilo")
                            
                            with st.expander("Tamaño", expanded=False):
                                fig_width = st.slider("Ancho (in)", 4.0, 14.0, 7.0, 0.5, key="fig_width")
                                fig_height = st.slider("Alto (in)", 3.0, 10.0, 4.5, 0.5, key="fig_height")
                                dpi = st.selectbox("DPI", [100, 150, 200, 300], index=1, key="plot_dpi")
                            
                            with st.expander("Líneas", expanded=False):
                                line_width = st.slider("Grosor", 0.5, 3.5, 1.5, 0.1, key="line_width")
                                marker_size = st.slider("Marcador", 2.0, 8.0, 3.5, 0.5, key="marker_size")
                                marker_style = st.selectbox(
                                    "Estilo",
                                    ["o", "s", "^", "D", "*", "x", "+", "v"],
                                    format_func=lambda x: {"o": "Círculo", "s": "Cuadrado", "^": "Triángulo", 
                                                            "D": "Diamante", "*": "Estrella", "x": "Equis", "+": "Más", "v": "Triángulo invertido"}[x],
                                    key="marker_style"
                                )
                                alpha_line = st.slider("Transp. línea", 0.3, 1.0, 1.0, 0.05, key="alpha_line")
                                alpha_fill = st.slider("Transp. área", 0.05, 0.5, 0.15, 0.05, key="alpha_fill")
                            
                            with st.expander("Colores", expanded=False):
                                color_palette = st.selectbox(
                                    "Paleta",
                                    ["Azul/Naranja", "Rojo/Verde", "Púrpura/Amarillo", "Personalizado"],
                                    key="color_palette"
                                )
                                
                                if color_palette == "Personalizado":
                                    color1_custom = st.color_picker("Color1", "#1f77b4", key="color1_custom")
                                    color2_custom = st.color_picker("Color2", "#ff7f0e", key="color2_custom")
                                    color_single = st.color_picker("Color único", "#000000", key="color_single")
                                else:
                                    color1_custom = None
                                    color2_custom = None
                                    color_single = None
                            
                            with st.expander("Grid", expanded=False):
                                show_grid = st.checkbox("Mostrar", value=True, key="show_grid")
                                grid_linewidth = st.slider("Grosor", 0.1, 1.0, 0.4, 0.05, key="grid_linewidth")
                                grid_alpha = st.slider("Transp.", 0.1, 0.5, 0.3, 0.05, key="grid_alpha")
                                grid_style = st.selectbox("Estilo", ["-", "--", "-.", ":"], 
                                                    format_func=lambda x: {"-": "Sólido", "--": "Punt.", "-.": "Guión", ":": "Puntos"}[x],
                                                    key="grid_style")
                            
                            with st.expander("Leyenda", expanded=False):
                                legend_pos = st.selectbox(
                                    "Posición",
                                    ["best", "upper left", "upper right", "center left", "center", 
                                     "center right", "lower left", "lower right"],
                                    index=0, key="legend_pos"
                                )
                                legend_fontsize = st.slider("Tamaño", 8, 16, 11, 1, key="legend_fontsize")
                                legend_frameon = st.checkbox("Marco", value=True, key="legend_frameon")
                            
                            with st.expander("Fuentes", expanded=False):
                                font_family = st.selectbox("Familia", ["serif", "sans-serif", "monospace"], index=0, key="font_family")
                                font_size = st.slider("Tañ general", 8, 16, 12, 1, key="font_size")
                                label_size = st.slider("Tañ ejes", 10, 18, 13, 1, key="label_size")
                                tick_size = st.slider("Tañ marcas", 8, 14, 10, 1, key="tick_size")
                            
                            with st.expander("Ejes", expanded=False):
                                xlabel_custom = st.text_input("Etiqueta X", value="Iteration", key="xlabel_custom")
                                ylabel_custom = st.text_input("Etiqueta Y", value="", key="ylabel_custom", placeholder="Automática si vacío")
                                x_rotation = st.slider("Ángulo X", -90, 90, 0, 5, key="x_rotation")
                                y_rotation = st.slider("Ángulo Y", -90, 90, 0, 5, key="y_rotation")
                            
                            with st.expander("Título", expanded=False):
                                show_title = st.checkbox("Mostrar", value=True, key="show_title")
                                title_custom = st.text_input("Personalizado", value="", key="title_custom", placeholder="Dejar vacío para automático")
                            
                            with st.expander("Rango Y", expanded=False):
                                auto_ylim = st.checkbox("Automático", value=True, key="auto_ylim")
                                if not auto_ylim:
                                    ylim_min = st.number_input("Mín", value=None, key="ylim_min")
                                    ylim_max = st.number_input("Máx", value=None, key="ylim_max")
                                else:
                                    ylim_min = None
                                    ylim_max = None
                        
                        # COLUMNA DE GRÁFICO (IZQUIERDA)
                        with col_graph:
                            # Construir diccionario de etiquetas dinámicamente
                            METRIC_LABELS = {
                                "fitness_mejor": "Best Fitness",
                                "fitness_iteracion": "Iteration Fitness",
                                "PorcentajeExplor": "Exploration Rate",
                            }

                            # Agregar etiquetas para XPL% y XPT%
                            for i, div_name in enumerate(DIVERSITY_NAMES):
                                xpl_key = f"XPL_{div_name}"
                                xpt_key = f"XPT_{div_name}"
                                METRIC_LABELS[xpl_key] = f"XPL% - {div_name} (Exploration %)"
                                METRIC_LABELS[xpt_key] = f"XPT% - {div_name} (Exploitation %)"

                            y_label = METRIC_LABELS.get(metric_type, metric_type)

                            # Determinar colores según paleta seleccionada
                            if color_palette == "Personalizado":
                                color_line1 = color1_custom
                                color_line2 = color2_custom
                                color_single_line = color_single
                            elif color_palette == "Rojo/Verde":
                                color_line1 = "#d62728"
                                color_line2 = "#2ca02c"
                                color_single_line = "#d62728"
                            elif color_palette == "Púrpura/Amarillo":
                                color_line1 = "#9467bd"
                                color_line2 = "#ff9800"
                                color_single_line = "#9467bd"
                            else:  # Azul/Naranja (defecto)
                                color_line1 = "#1f77b4"
                                color_line2 = "#ff7f0e"
                                color_single_line = "#000000"

                            # --- Actualizar matplotlib según opciones ---
                            plt.rcParams.update({
                                'font.family': 'serif' if font_family == 'serif' else font_family,
                                'font.serif': ['Times New Roman'],
                                'font.size': font_size,
                                'axes.linewidth': 1.2,
                                'xtick.direction': 'in',
                                'ytick.direction': 'in',
                                'xtick.major.width': 1.0,
                                'ytick.major.width': 1.0,
                                'xtick.major.size': 5,
                                'ytick.major.size': 5,
                                'xtick.labelsize': tick_size,
                                'ytick.labelsize': tick_size,
                            })

                            fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

                            x = df_iterations['numero_iteracion']

                            # Detectar si es XPL% o XPT% para graficar ambas juntas
                            is_xpl_metric = "XPL_" in metric_type
                            is_xpt_metric = "XPT_" in metric_type

                            if is_xpl_metric or is_xpt_metric:
                                # Extraer el nombre de la diversidad
                                if is_xpl_metric:
                                    div_name = metric_type.replace("XPL_", "")
                                else:
                                    div_name = metric_type.replace("XPT_", "")

                                xpl_col = f"XPL_{div_name}"
                                xpt_col = f"XPT_{div_name}"

                                y_xpl = df_iterations[xpl_col]
                                y_xpt = df_iterations[xpt_col]

                                # Graficar ambas líneas
                                if plot_type == "Líneas + Marcadores":
                                    ax.plot(x, y_xpl, color=color_line1, linewidth=line_width, alpha=alpha_line,
                                            marker=marker_style, markersize=marker_size, markerfacecolor=color_line1,
                                            label='Exploration (XPL%)')
                                    ax.plot(x, y_xpt, color=color_line2, linewidth=line_width, alpha=alpha_line,
                                            marker=marker_style, markersize=marker_size, markerfacecolor=color_line2,
                                            label='Exploitation (XPT%)')
                                elif plot_type == "Solo Líneas":
                                    ax.plot(x, y_xpl, color=color_line1, linewidth=line_width, alpha=alpha_line, label='Exploration (XPL%)')
                                    ax.plot(x, y_xpt, color=color_line2, linewidth=line_width, alpha=alpha_line, label='Exploitation (XPT%)')
                                elif plot_type == "Solo Marcadores":
                                    ax.plot(x, y_xpl, color=color_line1, linewidth=0,
                                            marker=marker_style, markersize=marker_size+1, markerfacecolor=color_line1,
                                            label='Exploration (XPL%)', alpha=alpha_line)
                                    ax.plot(x, y_xpt, color=color_line2, linewidth=0,
                                            marker=marker_style, markersize=marker_size+1, markerfacecolor=color_line2,
                                            label='Exploitation (XPT%)', alpha=alpha_line)
                                elif plot_type == "Área":
                                    ax.fill_between(x, y_xpl, alpha=alpha_fill, color=color_line1, label='Exploration (XPL%)')
                                    ax.plot(x, y_xpl, color=color_line1, linewidth=line_width, alpha=alpha_line)
                                    ax.fill_between(x, y_xpt, alpha=alpha_fill, color=color_line2, label='Exploitation (XPT%)')
                                    ax.plot(x, y_xpt, color=color_line2, linewidth=line_width, alpha=alpha_line)

                                # Establecer etiqueta Y personalizada o por defecto
                                y_axis_label = ylabel_custom if ylabel_custom.strip() else 'Rate (%)'
                                ax.set_ylabel(y_axis_label, fontsize=label_size)
                                ax.legend(loc=legend_pos, frameon=legend_frameon, fontsize=legend_fontsize)
                            else:
                                # Gráfico singular para otras métricas
                                y = df_iterations[metric_type]

                                if plot_type == "Líneas + Marcadores":
                                    ax.plot(x, y, color=color_single_line, linewidth=line_width, alpha=alpha_line,
                                            marker=marker_style, markersize=marker_size, markerfacecolor=color_single_line)
                                elif plot_type == "Solo Líneas":
                                    ax.plot(x, y, color=color_single_line, linewidth=line_width, alpha=alpha_line)
                                elif plot_type == "Solo Marcadores":
                                    ax.plot(x, y, color=color_single_line, linewidth=0,
                                            marker=marker_style, markersize=marker_size+1, markerfacecolor=color_single_line, alpha=alpha_line)
                                elif plot_type == "Área":
                                    ax.fill_between(x, y, alpha=alpha_fill, color=color_single_line)
                                    ax.plot(x, y, color=color_single_line, linewidth=line_width, alpha=alpha_line)

                                # Establecer etiqueta Y personalizada o por defecto
                                y_axis_label = ylabel_custom if ylabel_custom.strip() else y_label
                                ax.set_ylabel(y_axis_label, fontsize=label_size)

                            # Establecer etiqueta X y ángulos de rotación
                            ax.set_xlabel(xlabel_custom, fontsize=label_size)
                            ax.tick_params(axis='x', rotation=x_rotation)
                            ax.tick_params(axis='y', rotation=y_rotation)
                            
                            # Aplicar rango Y si se especifica
                            if not auto_ylim and ylim_min is not None and ylim_max is not None:
                                ax.set_ylim(ylim_min, ylim_max)
                            
                            # Mostrar/ocultar grid
                            if show_grid:
                                ax.grid(True, linewidth=grid_linewidth, alpha=grid_alpha, linestyle=grid_style)
                            else:
                                ax.grid(False)
                            
                            ax.tick_params(axis='both', which='both', direction='in', top=True, right=True)
                            
                            # Título
                            if show_title:
                                if title_custom.strip():
                                    title = title_custom
                                else:
                                    title = f"{y_label} - Experimento {selected_exp_id}"
                                fig.suptitle(title, fontsize=label_size + 2, fontweight='bold')
                            
                            fig.tight_layout()

                            st.pyplot(fig)
                            
                            # Opciones de exportación
                            st.subheader("Descargar")
                            exp1, exp2, exp3, exp4 = st.columns(4)
                            
                            # PDF
                            pdf_buffer = io.BytesIO()
                            fig.savefig(pdf_buffer, format='pdf', bbox_inches='tight', dpi=dpi)
                            pdf_buffer.seek(0)
                            with exp1:
                                st.download_button(
                                    label="PDF",
                                    data=pdf_buffer,
                                    file_name=f"exp{selected_exp_id}_{metric_type}.pdf",
                                    mime="application/pdf",
                                    key="download_pdf"
                                )
                            
                            # PNG
                            png_buffer = io.BytesIO()
                            fig.savefig(png_buffer, format='png', bbox_inches='tight', dpi=dpi)
                            png_buffer.seek(0)
                            with exp2:
                                st.download_button(
                                    label="PNG",
                                    data=png_buffer,
                                    file_name=f"exp{selected_exp_id}_{metric_type}.png",
                                    mime="image/png",
                                    key="download_png"
                                )
                            
                            # SVG
                            svg_buffer = io.BytesIO()
                            fig.savefig(svg_buffer, format='svg', bbox_inches='tight')
                            svg_buffer.seek(0)
                            with exp3:
                                st.download_button(
                                    label="SVG",
                                    data=svg_buffer,
                                    file_name=f"exp{selected_exp_id}_{metric_type}.svg",
                                    mime="image/svg+xml",
                                    key="download_svg"
                                )
                            
                            # EPS
                            eps_buffer = io.BytesIO()
                            fig.savefig(eps_buffer, format='eps', bbox_inches='tight', dpi=dpi)
                            eps_buffer.seek(0)
                            with exp4:
                                st.download_button(
                                    label="EPS",
                                    data=eps_buffer,
                                    file_name=f"exp{selected_exp_id}_{metric_type}.eps",
                                    mime="application/postscript",
                                    key="download_eps"
                                )
                            
                            plt.close(fig)

                            # Estadísticas
                            st.divider()
                            st.subheader("Estadísticas")
                            
                            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

                            # Si es XPL% o XPT%, mostrar ambas
                            if "XPL_" in metric_type or "XPT_" in metric_type:
                                if "XPL_" in metric_type:
                                    div_name = metric_type.replace("XPL_", "")
                                else:
                                    div_name = metric_type.replace("XPT_", "")

                                xpl_col = f"XPL_{div_name}"
                                xpt_col = f"XPT_{div_name}"

                                col_xpl = pd.to_numeric(df_iterations[xpl_col], errors='coerce')
                                col_xpt = pd.to_numeric(df_iterations[xpt_col], errors='coerce')

                                with stat_col1:
                                    st.metric("XPL% Mín", f"{col_xpl.min():.2f}")
                                with stat_col2:
                                    st.metric("XPL% Máx", f"{col_xpl.max():.2f}")
                                with stat_col3:
                                    st.metric("XPL% Prom", f"{col_xpl.mean():.2f}")
                                with stat_col4:
                                    st.metric("Iteraciones", f"{len(df_iterations)}")

                                st.divider()
                                
                                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                                with stat_col1:
                                    st.metric("XPT% Mín", f"{col_xpt.min():.2f}")
                                with stat_col2:
                                    st.metric("XPT% Máx", f"{col_xpt.max():.2f}")
                                with stat_col3:
                                    st.metric("XPT% Prom", f"{col_xpt.mean():.2f}")
                                with stat_col4:
                                    st.metric("Desv.Est. XPL", f"{col_xpl.std():.4f}")
                            else:
                                col_values = pd.to_numeric(df_iterations[metric_type], errors='coerce')
                                with stat_col1:
                                    st.metric("Mejor (mín)", f"{col_values.min():.4f}")
                                with stat_col2:
                                    st.metric("Peor (máx)", f"{col_values.max():.4f}")
                                with stat_col3:
                                    st.metric("Promedio", f"{col_values.mean():.4f}")
                                with stat_col4:
                                    st.metric("Desv.Est.", f"{col_values.std():.4f}")
                else:
                    st.warning(f"No hay datos de iteraciones para el experimento {selected_exp_id}")
            except Exception as e:
                st.error(f"Error cargando datos: {e}")
        else:
            st.info("No hay experimentos disponibles")
    except Exception as e:
        st.error(f"Error cargando experimentos: {e}")


with tab_summary:
    # ═══════════════════════════════════════════════════════════════════════════════
    #  TABLA RESUMEN COMPARATIVA
    # ═══════════════════════════════════════════════════════════════════════════════
    st.header("Summary Table")

    try:
        df_all = query_to_df(db.engine, """
            SELECT de.id, de.nombre_algoritmo, de.parametros,
                   re.fitness, re.inicio, re.fin
            FROM datos_ejecucion de
            LEFT JOIN resultado_ejecucion re ON de.id = re.id_ejecucion
            WHERE de.estado = 'terminado'
            ORDER BY de.id DESC
        """)

        if not df_all.empty:
            # Parsear parámetros JSON para extraer campos clave
            def extract_params(row):
                try:
                    p = json.loads(row['parametros']) if isinstance(row['parametros'], str) else row['parametros']
                    return pd.Series({
                        'Problem': p.get('problemName', ''),
                        'MH': p.get('MH', ''),
                        'ML': p.get('ML', 'None'),
                        'Instance': p.get('paramsProblem', {}).get('instance_name', ''),
                        'Population': p.get('paramsMH', {}).get('population', ''),
                        'MaxIter': p.get('paramsMH', {}).get('maxIter', ''),
                        'DS': p.get('paramsML', {}).get('discretizationsScheme', ''),
                    })
                except Exception:
                    return pd.Series({
                        'Problem': '', 'MH': '', 'ML': '', 'Instance': '',
                        'Population': '', 'MaxIter': '', 'DS': '',
                    })

            df_params = df_all.apply(extract_params, axis=1)
            df_table = pd.concat([df_all[['id', 'nombre_algoritmo']], df_params, df_all[['fitness', 'inicio', 'fin']]], axis=1)
            df_table['fitness'] = pd.to_numeric(df_table['fitness'], errors='coerce')

            # Calcular tiempo de ejecución
            df_table['inicio'] = pd.to_datetime(df_table['inicio'], errors='coerce')
            df_table['fin'] = pd.to_datetime(df_table['fin'], errors='coerce')
            df_table['Time (s)'] = (df_table['fin'] - df_table['inicio']).dt.total_seconds()

            # Filtros
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                problems = sorted(df_table['Problem'].dropna().unique())
                sel_problem = st.multiselect("Problem", problems, default=problems, key="summary_problem")
            with col_f2:
                mhs = sorted(df_table['MH'].dropna().unique())
                sel_mh = st.multiselect("Metaheuristic", mhs, default=mhs, key="summary_mh")
            with col_f3:
                mls = sorted(df_table['ML'].dropna().unique())
                sel_ml = st.multiselect("ML Strategy", mls, default=mls, key="summary_ml")

            mask = (
                df_table['Problem'].isin(sel_problem) &
                df_table['MH'].isin(sel_mh) &
                df_table['ML'].isin(sel_ml)
            )
            df_filtered = df_table[mask]

            if not df_filtered.empty:
                # Agrupar por combinación (Problem, MH, ML, Instance) y calcular estadísticas
                group_cols = ['Problem', 'MH', 'ML', 'Instance']
                summary = df_filtered.groupby(group_cols).agg(
                    Runs=('fitness', 'count'),
                    Best=('fitness', 'min'),
                    Worst=('fitness', 'max'),
                    Mean=('fitness', 'mean'),
                    Std=('fitness', 'std'),
                    **{'Mean Time (s)': ('Time (s)', 'mean')},
                ).reset_index()
                summary['Std'] = summary['Std'].fillna(0)

                # Formatear
                for c in ['Best', 'Worst', 'Mean', 'Std', 'Mean Time (s)']:
                    summary[c] = summary[c].map(lambda v: f"{v:.4f}")

                st.dataframe(summary, use_container_width=True, hide_index=True)

                # Descargar CSV
                csv_buffer = summary.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar CSV",
                    data=csv_buffer,
                    file_name="summary_table.csv",
                    mime="text/csv",
                )
            else:
                st.info("No hay datos con los filtros seleccionados.")
        else:
            st.info("No hay experimentos terminados.")
    except Exception as e:
        st.error(f"Error cargando tabla resumen: {e}")


with tab_queue:
    # ═══════════════════════════════════════════════════════════════════════════════
    #  SUBIR EXPERIMENTOS A LA BASE DE DATOS
    # ═══════════════════════════════════════════════════════════════════════════════
    st.header("Queue Experiments")

    from src.utils.config_manager import ConfigManager

    _MH_OPTIONS  = ["GWO", "PSO", "SCA", "WOA", "HHO", "CS", "GA", "DE"]
    _ML_OPTIONS  = ["QL", "SA", "BQSA", "MAB", "BCL", "MIR"]
    _DS_OPTIONS  = ["40a", "80a"] + [f"ver{i}" for i in range(1, 91)]
    _REWARD_LABELS = [
        "0: withPenalty1", "1: withoutPenalty1", "2: globalBest",
        "3: rootAdaptation", "4: escalatingMultiplicativeAdaptation",
        "5: percentageImprovement", "6: percentageImprovementAndDeterioration",
        "7: percentageImprovementAndDeteriorationWithIter",
    ]
    _POLICY_LABELS = [
        "0: e-greedy", "1: greedy", "2: e-soft",
        "3: softMax-rulette", "4: softMax-rulette-elitist",
    ]

    tab_yaml, tab_form = st.tabs(["Subir YAML", "Configurar manualmente"])

    # ── TAB 1: YAML ──────────────────────────────────────────────────────────────
    with tab_yaml:
        st.markdown("Sube un archivo `.yaml` con la configuración del experimento (mismo formato que `config/experiments/`).")
        uploaded_file = st.file_uploader("Archivo YAML", type=["yaml", "yml"], key="yaml_uploader")

        if uploaded_file is not None:
            try:
                config_yaml = yaml.safe_load(uploaded_file.read())
                experiments_yaml = ConfigManager.generate_experiments(config_yaml)
                st.success(f"YAML válido — se generarán **{len(experiments_yaml)} experimentos**.")

                with st.expander("Vista previa (primeros 10)"):
                    preview_rows = []
                    for e in experiments_yaml[:10]:
                        p = e['parametros']
                        preview_rows.append({
                            "Nombre": e['nombre_algoritmo'],
                            "MH": p.get('MH', ''),
                            "ML": p.get('ML', ''),
                            "Instancia": p.get('paramsProblem', {}).get('instance_name', ''),
                            "Iters": p.get('paramsMH', {}).get('maxIter', ''),
                            "Pob": p.get('paramsMH', {}).get('population', ''),
                        })
                    st.dataframe(pd.DataFrame(preview_rows), hide_index=True, use_container_width=True)

                if st.button("Encolar en base de datos", key="enqueue_yaml", type="primary"):
                    progress = st.progress(0, text="Insertando experimentos...")
                    inserted, failed = 0, 0
                    for i, exp in enumerate(experiments_yaml):
                        eid = db.create_experiment(
                            algorithm_name=exp['nombre_algoritmo'],
                            parameters=exp['parametros'],
                            status='pendiente'
                        )
                        if eid:
                            inserted += 1
                        else:
                            failed += 1
                        progress.progress((i + 1) / len(experiments_yaml),
                                          text=f"Insertando {i+1}/{len(experiments_yaml)}...")
                    progress.empty()
                    if failed == 0:
                        st.success(f"{inserted} experimentos encolados correctamente.")
                    else:
                        st.warning(f"{inserted} insertados, {failed} fallaron.")
            except Exception as e:
                st.error(f"Error procesando el YAML: {e}")

    # ── TAB 2: FORMULARIO ────────────────────────────────────────────────────────
    with tab_form:
        with st.form("form_queue"):
            st.subheader("Problema")
            fc1, fc2 = st.columns(2)
            with fc1:
                f_problem = st.selectbox("Tipo de problema", ["SCP", "RW", "MSCP"], key="f_problem")
                f_fo      = st.selectbox("Dirección optimización (FO)", ["min", "max"], key="f_fo")
                f_repair  = st.selectbox("repairType", [1, 2], key="f_repair")
            with fc2:
                f_instance_dir = st.text_input("instance_dir", value="MSCP/", key="f_idir")
                f_lb = st.number_input("lb", value=-10, key="f_lb")
                f_ub = st.number_input("ub", value=10,  key="f_ub")

            f_instances = st.text_area(
                "Instancias (una por línea)",
                value="mscp41\nmscp42\nmscp43",
                key="f_instances",
                height=100,
            )

            st.subheader("Algoritmos")
            fa1, fa2 = st.columns(2)
            with fa1:
                f_mhs = st.multiselect("Metaheurísticas", _MH_OPTIONS, default=["GWO"], key="f_mhs")
            with fa2:
                f_mls = st.multiselect("ML / Estrategia", _ML_OPTIONS, default=["QL"], key="f_mls")

            st.subheader("Parámetros de ejecución")
            fp1, fp2, fp3 = st.columns(3)
            with fp1:
                f_runs    = st.number_input("Runs",       min_value=1,  value=5,    step=1,  key="f_runs")
                f_pop     = st.number_input("Population", min_value=1,  value=40,   step=1,  key="f_pop")
                f_maxiter = st.number_input("Max Iters",  min_value=1,  value=1000, step=10, key="f_maxiter")
            with fp2:
                f_ds     = st.multiselect("Discretization schemes", _DS_OPTIONS, default=["40a"], key="f_ds")
                f_rwtypes = st.multiselect("Reward types",  _REWARD_LABELS, default=[_REWARD_LABELS[5]], key="f_rw")
            with fp3:
                f_pltypes = st.multiselect("Policy types",  _POLICY_LABELS, default=[_POLICY_LABELS[0]], key="f_pl")
                f_epsilon  = st.number_input("epsilon",  value=0.1, step=0.01, key="f_eps")
                f_statesq  = st.number_input("states_q", value=2,   step=1,   key="f_sq")
                f_W        = st.number_input("W",        value=10,  step=1,   key="f_W")

            submitted = st.form_submit_button("Previsualizar experimentos", type="primary")

        if submitted:
            instances_list = [i.strip() for i in f_instances.splitlines() if i.strip()]
            reward_indices = [_REWARD_LABELS.index(r) for r in f_rwtypes]
            policy_indices = [_POLICY_LABELS.index(p) for p in f_pltypes]

            if not instances_list:
                st.error("Agrega al menos una instancia.")
            elif not f_mhs:
                st.error("Selecciona al menos una metaheurística.")
            elif not f_mls:
                st.error("Selecciona al menos una estrategia ML.")
            elif not f_ds:
                st.error("Selecciona al menos un esquema de discretización.")
            elif not reward_indices:
                st.error("Selecciona al menos un reward type.")
            elif not policy_indices:
                st.error("Selecciona al menos un policy type.")
            else:
                form_config = {
                    'experiment': {
                        'problem': f_problem,
                        'instances': instances_list,
                        'metaheuristics': f_mhs,
                        'machine_learning': f_mls,
                        'parameters': {
                            'runs': int(f_runs),
                            'population': int(f_pop),
                            'max_iterations': int(f_maxiter),
                            'discretization_schemes': f_ds,
                            'reward_types': reward_indices,
                            'policy_types': policy_indices,
                            'epsilon': float(f_epsilon),
                            'states_q': int(f_statesq),
                            'W': int(f_W),
                        },
                        'problem_params': {
                            'FO': f_fo,
                            'lb': int(f_lb),
                            'ub': int(f_ub),
                            'repair_type': int(f_repair),
                            'instance_dir': f_instance_dir,
                        },
                    }
                }
                st.session_state['form_experiments'] = ConfigManager.generate_experiments(form_config)

        if 'form_experiments' in st.session_state and st.session_state['form_experiments']:
            exps = st.session_state['form_experiments']
            st.success(f"Se generarán **{len(exps)} experimentos**.")

            with st.expander("Vista previa (primeros 10)"):
                preview_rows = []
                for e in exps[:10]:
                    p = e['parametros']
                    preview_rows.append({
                        "Nombre": e['nombre_algoritmo'],
                        "MH": p.get('MH', ''),
                        "ML": p.get('ML', ''),
                        "Instancia": p.get('paramsProblem', {}).get('instance_name', ''),
                        "Iters": p.get('paramsMH', {}).get('maxIter', ''),
                        "Pob": p.get('paramsMH', {}).get('population', ''),
                    })
                st.dataframe(pd.DataFrame(preview_rows), hide_index=True, use_container_width=True)

            if st.button("Encolar en base de datos", key="enqueue_form", type="primary"):
                progress = st.progress(0, text="Insertando experimentos...")
                inserted, failed = 0, 0
                for i, exp in enumerate(exps):
                    eid = db.create_experiment(
                        algorithm_name=exp['nombre_algoritmo'],
                        parameters=exp['parametros'],
                        status='pendiente'
                    )
                    if eid:
                        inserted += 1
                    else:
                        failed += 1
                    progress.progress((i + 1) / len(exps),
                                      text=f"Insertando {i+1}/{len(exps)}...")
                progress.empty()
                st.session_state.pop('form_experiments', None)
                if failed == 0:
                    st.success(f"{inserted} experimentos encolados correctamente.")
                else:
                    st.warning(f"{inserted} insertados, {failed} fallaron.")
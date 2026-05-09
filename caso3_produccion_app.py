import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE LA PÁGINA
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title='Producción Dashboard',
    page_icon='🏭',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { color: #1b2631; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════
@st.cache_data
def cargar_datos():
    ruta = os.path.join(os.path.dirname(__file__), 'caso3_produccion_dataset.csv')
    df = pd.read_csv(ruta)
    df['fecha_produccion'] = pd.to_datetime(df['fecha_produccion'])
    return df

df = cargar_datos()

# ═══════════════════════════════════════════════════════════════
# SIDEBAR — FILTROS
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1b2631/ffffff?text=ProducciónCo", width=200)
    st.markdown("---")
    st.header("🔧 Filtros")

    linea_sel = st.multiselect(
        "Línea de Producción",
        options=sorted(df['linea_produccion'].unique()),
        default=list(df['linea_produccion'].unique())
    )

    turno_sel = st.multiselect(
        "Turno",
        options=sorted(df['turno'].unique()),
        default=list(df['turno'].unique())
    )

    maquina_sel = st.multiselect(
        "Máquina",
        options=sorted(df['maquina'].unique()),
        default=list(df['maquina'].unique())
    )

    producto_sel = st.multiselect(
        "Producto",
        options=sorted(df['producto'].unique()),
        default=list(df['producto'].unique())
    )

    st.markdown("---")
    st.caption("📅 Datos: Año 2024 | 160 órdenes de producción")

# ═══════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ═══════════════════════════════════════════════════════════════
df_f = df.copy()
if linea_sel:
    df_f = df_f[df_f['linea_produccion'].isin(linea_sel)]
if turno_sel:
    df_f = df_f[df_f['turno'].isin(turno_sel)]
if maquina_sel:
    df_f = df_f[df_f['maquina'].isin(maquina_sel)]
if producto_sel:
    df_f = df_f[df_f['producto'].isin(producto_sel)]

# ═══════════════════════════════════════════════════════════════
# TÍTULO PRINCIPAL
# ═══════════════════════════════════════════════════════════════
st.title("🏭 ProducciónCo — Dashboard de Control de Planta")
st.markdown("**Panel de eficiencia operacional, calidad y costos de producción · 2024**")
st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# KPIs
# Cada métrica resume un aspecto clave de la operación:
# - Eficiencia: qué tan cerca estamos de la producción planificada
# - Defectos: porcentaje de unidades que no pasan calidad
# - Unidades: volumen total producido en el período filtrado
# - Paro: minutos totales perdidos por paradas de máquina
# - Costo: inversión total de producción en COP
# ═══════════════════════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5)

eficiencia_prom   = df_f['eficiencia_pct'].mean() if len(df_f) > 0 else 0
defectos_prom     = df_f['tasa_defectos_pct'].mean() if len(df_f) > 0 else 0
total_producidas  = df_f['unidades_producidas'].sum() if len(df_f) > 0 else 0
total_paro        = df_f['tiempo_paro_min'].sum() if len(df_f) > 0 else 0
costo_total       = df_f['costo_produccion_cop'].sum() if len(df_f) > 0 else 0

k1.metric("⚙️ Eficiencia Promedio",   f"{eficiencia_prom:.1f}%",
          delta=f"{eficiencia_prom - 80:.1f}% vs meta 80%")
k2.metric("❌ Tasa de Defectos",      f"{defectos_prom:.2f}%",
          delta=f"{defectos_prom - 3:.2f}% vs meta 3%", delta_color="inverse")
k3.metric("📦 Unidades Producidas",   f"{total_producidas:,}")
k4.metric("⏸️ Tiempo de Paro Total",  f"{total_paro:,.0f} min")
k5.metric("💰 Costo Total",           f"${costo_total:,.0f}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# FILA 1 — Eficiencia por línea + Causas de paro
#
# Izquierda: barras horizontales con eficiencia promedio por línea.
#   Permite identificar rápidamente cuál línea está rindiendo menos.
#
# Derecha: pie con distribución de causas de paro.
#   Muestra qué problemas generan más tiempo perdido.
# ═══════════════════════════════════════════════════════════════
col_izq, col_der = st.columns([1.5, 1])

with col_izq:
    efic_linea = (
        df_f.groupby('linea_produccion')
            .agg(eficiencia_promedio=('eficiencia_pct', 'mean'))
            .round(2)
            .reset_index()
            .sort_values('eficiencia_promedio', ascending=True)
    )
    fig1 = px.bar(
        efic_linea,
        x='eficiencia_promedio',
        y='linea_produccion',
        orientation='h',
        title='⚙️ Eficiencia Promedio por Línea de Producción',
        labels={'eficiencia_promedio': 'Eficiencia (%)', 'linea_produccion': ''},
        color='eficiencia_promedio',
        color_continuous_scale='Teal',
        text_auto='.1f'
    )
    fig1.update_layout(height=320, margin=dict(t=40, b=20), showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col_der:
    causas = df_f['causa_paro'].value_counts().reset_index()
    causas.columns = ['causa_paro', 'count']
    fig2 = px.pie(
        causas,
        names='causa_paro',
        values='count',
        title='⏸️ Distribución de Causas de Paro',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig2.update_layout(height=320, margin=dict(t=40, b=20))
    st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# FILA 2 — Evolución mensual + Scatter paro vs defectos
#
# Izquierda: línea de tiempo de unidades producidas por mes.
#   Detecta tendencias, caídas estacionales o picos de producción.
#
# Derecha: scatter tiempo de paro vs tasa de defectos.
#   Hipótesis: más paro → más defectos. El scatter lo confirma o refuta.
#   El color por turno permite ver si algún turno concentra los problemas.
# ═══════════════════════════════════════════════════════════════
col_izq2, col_der2 = st.columns([1, 1.5])

with col_izq2:
    prod_mes = (
        df_f.groupby(df_f['fecha_produccion'].dt.to_period('M'))['unidades_producidas']
            .sum()
            .reset_index()
    )
    prod_mes['fecha_produccion'] = prod_mes['fecha_produccion'].astype(str)
    fig3 = px.line(
        prod_mes,
        x='fecha_produccion',
        y='unidades_producidas',
        markers=True,
        title='📅 Evolución Mensual de Unidades Producidas',
        labels={'fecha_produccion': 'Mes', 'unidades_producidas': 'Unidades'},
        color_discrete_sequence=['#1a6b4a']
    )
    fig3.update_traces(line_width=3, marker_size=8)
    fig3.update_layout(height=320, margin=dict(t=40, b=20))
    st.plotly_chart(fig3, use_container_width=True)

with col_der2:
    fig4 = px.scatter(
        df_f,
        x='tiempo_paro_min',
        y='tasa_defectos_pct',
        color='turno',
        size='unidades_producidas',
        hover_data=['maquina', 'producto', 'operador'],
        title='🔍 Tiempo de Paro vs Tasa de Defectos (por Turno)',
        labels={
            'tiempo_paro_min': 'Tiempo de Paro (min)',
            'tasa_defectos_pct': 'Tasa de Defectos (%)',
            'turno': 'Turno'
        }
    )
    fig4.update_layout(height=320, margin=dict(t=40, b=20))
    st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# FILA 3 — Heatmap: tasa de defectos por máquina y turno
#
# Combina dos dimensiones clave: la máquina y el turno.
# Permite detectar combinaciones críticas, por ejemplo:
# "Torno-01 en turno noche tiene el doble de defectos que el resto".
# ═══════════════════════════════════════════════════════════════
st.markdown("### 🌡️ Mapa de Calor — Tasa de Defectos por Máquina y Turno")
pivot = df_f.pivot_table(
    values='tasa_defectos_pct',
    index='maquina',
    columns='turno',
    aggfunc='mean'
).round(2)

fig5 = px.imshow(
    pivot,
    color_continuous_scale='RdYlGn_r',
    text_auto=True,
    title='Tasa de Defectos Promedio (%) — Rojo = Mayor defectividad'
)
fig5.update_layout(height=300, margin=dict(t=40, b=20))
st.plotly_chart(fig5, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TABLA DE DATOS FILTRADOS
# ═══════════════════════════════════════════════════════════════
with st.expander("📋 Ver datos filtrados"):
    cols_show = [
        'id_orden', 'fecha_produccion', 'linea_produccion', 'producto',
        'turno', 'operador', 'maquina', 'unidades_planificadas',
        'unidades_producidas', 'unidades_defectuosas', 'tiempo_paro_min',
        'causa_paro', 'costo_produccion_cop', 'eficiencia_pct', 'tasa_defectos_pct'
    ]
    st.dataframe(
        df_f[cols_show].sort_values('fecha_produccion', ascending=False),
        use_container_width=True
    )
    st.download_button("⬇️ Descargar CSV", df_f.to_csv(index=False), "produccion_filtrado.csv")

st.caption("🔧 Desarrollado con Streamlit + Plotly | Clase de Visualización de Datos")
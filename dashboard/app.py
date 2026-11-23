import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import aplicar_estilo, cargar_datos, cargar_resumen, encabezado, kpis, pie, seccion

aplicar_estilo()
df = cargar_datos()
resumen = cargar_resumen()

encabezado(
    "🎮 Segmentación de videojuegos con K-Means",
    "Exploración de ventas y agrupamientos del mercado global entre 1980 y 2020",
    "PROYECTO INTEGRADOR · MINERÍA DE DATOS",
)

st.markdown(
    """
    Este dashboard analiza **16,598 videojuegos** y aplica **K-Means** sobre variables estandarizadas para descubrir
    perfiles comerciales similares. Los resultados se presentan en dos secciones complementarias.
    """
)

seccion("Navegación")
col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("#### 📊 Página 1 · Análisis general")
        st.write("Indicadores generales, evolución temporal, ventas por región y estadísticas descriptivas.")
with col2:
    with st.container(border=True):
        st.markdown("#### 🧩 Página 2 · Segmentación K-Means")
        st.write("Clústeres, centroides, comparaciones, perfiles, hallazgos y recomendaciones.")

seccion("Resumen del modelo")
kpis([
    {"label": "Clústeres", "value": resumen["k_seleccionado"], "hint": "seleccionados por silueta", "color": "#2563eb"},
    {"label": "Juegos procesados", "value": f"{resumen['registros_procesados']:,}", "hint": "tras limpieza", "color": "#10b981"},
    {"label": "Variables", "value": len(resumen["variables_agrupamiento"]), "hint": "estandarizadas", "color": "#f59e0b"},
])

pie("Fuente: Video Game Sales · VGChartz / Kaggle · Procesado con Python, Pandas y Scikit-learn")

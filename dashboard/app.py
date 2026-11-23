import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import aplicar_estilo, cargar_datos, cargar_resumen

aplicar_estilo()
df = cargar_datos()
resumen = cargar_resumen()

st.title("🎮 Segmentación de videojuegos mediante K-Means")
st.subheader("Exploración de ventas y agrupamientos del mercado global")

st.markdown(
    """
    Este dashboard presenta el análisis de **16,598 videojuegos** publicados entre 1980 y 2020.
    El objetivo es identificar patrones de venta por región y agrupar títulos con comportamientos
    similares usando el algoritmo **K-Means** sobre variables estandarizadas.

    ### Navegación
    - **Página 1 · Análisis general:** indicadores, distribución del dataset y estadísticas.
    - **Página 2 · Segmentación K-Means:** clústeres, centroides, comparaciones y recomendaciones.

    Utilice el menú lateral para cambiar de página y los **tres filtros interactivos**
    (género, plataforma y rango de años) para explorar los datos.
    """
)

col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**K seleccionado:** {resumen['k_seleccionado']}")
with col2:
    st.info(f"**Juegos procesados:** {resumen['registros_procesados']:,}")
with col3:
    st.info(f"**Variables de agrupamiento:** {len(resumen['variables_agrupamiento'])}")

st.caption(f"Fuente: Video Game Sales (VGChartz / Kaggle), incluido en data/raw/vgsales.csv")

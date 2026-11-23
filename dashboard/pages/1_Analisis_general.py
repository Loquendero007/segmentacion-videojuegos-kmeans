import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import BASE, aplicar_estilo, configurar_grafico, cargar_datos, cargar_resumen, filtros_comunes, grafico_barras

aplicar_estilo()
df = cargar_datos()
resumen = cargar_resumen()
filtro = filtros_comunes(df)

st.title("📊 Página 1 · Análisis general")
st.caption("Los indicadores y gráficas se recalculan con los filtros del panel lateral.")

if filtro.empty:
    st.warning("No hay registros con la combinación de filtros seleccionada.")
    st.stop()

ventas_totales = filtro["Ventas_Globales_Millones"].sum()
ventas_promedio = filtro["Ventas_Globales_Millones"].mean()
genero_top = filtro["Genero"].mode().iat[0]
anio_promedio = filtro["Anio"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Juegos analizados", f"{len(filtro):,}")
k2.metric("Ventas globales", f"{ventas_totales:,.0f} M", help="Millones de copias")
k3.metric("Ventas promedio", f"{ventas_promedio:.2f} M")
k4.metric("Año promedio", f"{anio_promedio:.1f}", delta=genero_top, delta_color="off", help=f"Género más frecuente: {genero_top}")

st.markdown("### Evolución y composición del mercado")

lanzamientos = filtro.groupby("Anio").size().rename("Juegos").reset_index()
linea = alt.Chart(lanzamientos).mark_line(point=True, color="#2563eb").encode(
    x=alt.X("Anio:O", title="Año", axis=alt.Axis(labelAngle=-45, labelFontSize=9)),
    y=alt.Y("Juegos:Q", title="Cantidad de juegos"),
    tooltip=[alt.Tooltip("Anio:O", title="Año"), alt.Tooltip("Juegos:Q", title="Juegos", format=",")],
).properties(title="Lanzamientos por año")
st.altair_chart(configurar_grafico(linea, 290), width="stretch")

regiones = filtro[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum().rename("Ventas (M)").reset_index()
regiones.columns = ["Region", "Ventas (M)"]
regiones["Region"] = regiones["Region"].map({"NA_Sales": "Norteamérica", "EU_Sales": "Europa", "JP_Sales": "Japón", "Other_Sales": "Resto del mundo"})

generos = filtro["Genero"].value_counts().head(10).rename("Juegos").reset_index()
generos.columns = ["Genero", "Juegos"]

colA, colB = st.columns(2)
with colA:
    st.altair_chart(grafico_barras(regiones, "Region", "Ventas (M)", titulo="Ventas acumuladas por región"), width="stretch")
with colB:
    st.altair_chart(grafico_barras(generos, "Genero", "Juegos", titulo="Top 10 de géneros"), width="stretch")

st.markdown("### Estadísticas descriptivas de variables numéricas")
columnas = ["Ventas_Globales_Millones", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Cuota_NA", "Cuota_EU", "Cuota_JP", "Log_Ventas_Globales", "Anio"]
stats = filtro[columnas].describe().T.round(3).rename_axis("Variable").reset_index()
st.dataframe(stats, width="stretch", hide_index=True)

with st.expander("Ver gráfica exploratoria exportada (Matplotlib / Seaborn)"):
    ruta = BASE / resumen["figuras"]["ventas"]
    st.image(str(ruta), caption="Distribución de ventas globales en escala logarítmica")

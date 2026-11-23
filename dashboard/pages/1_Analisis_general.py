import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import (
    BASE,
    aplicar_estilo,
    cargar_datos,
    cargar_resumen,
    configurar_grafico,
    encabezado,
    filtros_comunes,
    grafico_barras,
    kpis,
    pie,
    seccion,
)

aplicar_estilo()
df = cargar_datos()
resumen = cargar_resumen()
filtro = filtros_comunes(df)

encabezado(
    "📊 Análisis general del mercado",
    "Indicadores y visualizaciones que se actualizan con los filtros del panel lateral",
    "PÁGINA 1 DE 2",
)

if filtro.empty:
    st.warning("No hay registros con la combinación de filtros seleccionada.")
    st.stop()

ventas_totales = filtro["Ventas_Globales_Millones"].sum()
ventas_promedio = filtro["Ventas_Globales_Millones"].mean()
genero_top = filtro["Genero"].mode().iat[0]
anio_promedio = filtro["Anio"].mean()

kpis([
    {"label": "Juegos analizados", "value": f"{len(filtro):,}", "hint": "registros visibles", "color": "#2563eb"},
    {"label": "Ventas globales", "value": f"{ventas_totales:,.0f} M", "hint": "millones de copias", "color": "#10b981"},
    {"label": "Ventas promedio", "value": f"{ventas_promedio:.2f} M", "hint": "por título", "color": "#f59e0b"},
    {"label": "Año promedio", "value": f"{anio_promedio:.1f}", "hint": f"género líder: {genero_top}", "color": "#8b5cf6"},
])

seccion("Evolución temporal")
lanzamientos = filtro.groupby("Anio").size().rename("Juegos").reset_index()
linea = alt.Chart(lanzamientos).mark_area(
    line={"color": "#2563eb"}, color=alt.Gradient(gradient="linear", stops=[
        alt.GradientStop(color="rgba(37,99,235,0.45)", offset=0),
        alt.GradientStop(color="rgba(37,99,235,0.02)", offset=1),
    ], x1=0, x2=0, y1=0, y2=1)
).encode(
    x=alt.X("Anio:O", title="Año", axis=alt.Axis(labelAngle=-45, labelFontSize=9)),
    y=alt.Y("Juegos:Q", title="Cantidad de juegos"),
    tooltip=[alt.Tooltip("Anio:O", title="Año"), alt.Tooltip("Juegos:Q", title="Juegos", format=",")],
).properties(title="Lanzamientos por año")
with st.container(border=True):
    st.altair_chart(configurar_grafico(linea, 300), width="stretch")

seccion("Composición del mercado")
regiones = filtro[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum().rename("Ventas (M)").reset_index()
regiones.columns = ["Region", "Ventas (M)"]
regiones["Region"] = regiones["Region"].map({"NA_Sales": "Norteamérica", "EU_Sales": "Europa", "JP_Sales": "Japón", "Other_Sales": "Resto del mundo"})
generos = filtro["Genero"].value_counts().head(10).rename("Juegos").reset_index()
generos.columns = ["Genero", "Juegos"]

colA, colB = st.columns(2)
with colA:
    with st.container(border=True):
        st.altair_chart(grafico_barras(regiones, "Region", "Ventas (M)", titulo="Ventas acumuladas por región"), width="stretch")
with colB:
    with st.container(border=True):
        st.altair_chart(grafico_barras(generos, "Genero", "Juegos", titulo="Top 10 de géneros"), width="stretch")

seccion("Estadísticas descriptivas")
columnas = ["Ventas_Globales_Millones", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Cuota_NA", "Cuota_EU", "Cuota_JP", "Log_Ventas_Globales", "Anio"]
stats = filtro[columnas].describe().T.round(3).rename_axis("Variable").reset_index()
with st.container(border=True):
    st.dataframe(stats, width="stretch", hide_index=True)

with st.expander("Ver gráfica exploratoria exportada (Matplotlib / Seaborn)"):
    st.image(str(BASE / resumen["figuras"]["ventas"]), caption="Distribución de ventas globales en escala logarítmica")

pie("Los filtros afectan todos los indicadores y visualizaciones de esta página")

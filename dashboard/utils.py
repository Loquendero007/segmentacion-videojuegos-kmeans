from pathlib import Path
import json

import altair as alt
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parents[1]
DATOS = BASE / "data" / "processed" / "videojuegos_clusterizados.csv"
RESUMEN = BASE / "outputs" / "resumen.json"


@st.cache_data(show_spinner=False)
def cargar_datos():
    df = pd.read_csv(DATOS)
    df["Anio"] = df["Anio"].astype(int)
    df["Cluster"] = df["Cluster"].astype(int)
    return df


@st.cache_data(show_spinner=False)
def cargar_resumen():
    with open(RESUMEN, encoding="utf-8") as f:
        return json.load(f)


def aplicar_estilo():
    st.set_page_config(page_title="Segmentación de Videojuegos", page_icon="🎮", layout="wide")
    st.markdown(
        """
        <style>
            .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
            .stMetric {background-color: #f1f5f9; border-radius: 12px; padding: 12px;}
            div[data-testid="stSidebar"] {background-color: #0f172a; color: white;}
            div[data-testid="stSidebar"] h2, div[data-testid="stSidebar"] h3 {color: #38bdf8;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def filtros_comunes(df):
    st.sidebar.header("Filtros interactivos")
    generos = sorted(df["Genero"].dropna().unique().tolist())
    plataformas = sorted(df["Plataforma"].dropna().unique().tolist())
    anio_min, anio_max = int(df["Anio"].min()), int(df["Anio"].max())

    sel_generos = st.sidebar.multiselect("1. Género", generos, default=generos)
    sel_plataformas = st.sidebar.multiselect("2. Plataforma", plataformas, default=plataformas)
    rango = st.sidebar.slider("3. Rango de años", anio_min, anio_max, (anio_min, anio_max))

    filtrado = df[
        df["Genero"].isin(sel_generos)
        & df["Plataforma"].isin(sel_plataformas)
        & df["Anio"].between(rango[0], rango[1])
    ]
    st.sidebar.caption(f"Registros visibles: {len(filtrado):,} de {len(df):,}")
    return filtrado


def configurar_grafico(chart, altura=320):
    return chart.properties(height=altura).configure_view(stroke=None).configure_axis(labelFontSize=11, titleFontSize=12)


def grafico_barras(df, x, y, color=None, titulo="", altura=320, orden=None):
    kwargs = {}
    if color:
        kwargs["color"] = alt.Color(f"{color}:N", scale=alt.Scale(scheme="tableau10"), title=color)
    base = alt.Chart(df).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X(f"{x}:N", sort=orden, title=x, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{y}:Q", title=y),
        tooltip=[alt.Tooltip(f"{x}:N", title=x), alt.Tooltip(f"{y}:Q", title=y, format=",.2f")],
        **kwargs,
    )
    return configurar_grafico(base.properties(title=titulo), altura)


def grafico_dispersion(df, x, y, color, size=None, titulo="", altura=430):
    codigo = {
        "x": alt.X(f"{x}:Q", title=x, scale=alt.Scale(zero=False)),
        "y": alt.Y(f"{y}:Q", title=y, scale=alt.Scale(zero=False)),
        "color": alt.Color(f"{color}:N", scale=alt.Scale(scheme="tableau10"), title="Grupo"),
        "tooltip": [
            alt.Tooltip("Nombre:N", title="Juego"),
            alt.Tooltip("Plataforma:N", title="Plataforma"),
            alt.Tooltip(f"{x}:Q", title=x, format=".0f"),
            alt.Tooltip(f"{y}:Q", title=y, format=".2f"),
            alt.Tooltip("Ventas_Globales_Millones:Q", title="Ventas (M)", format=".2f"),
        ],
    }
    if size:
        codigo["size"] = alt.Size(f"{size}:Q", title=size, scale=alt.Scale(range=[20, 220]))
    return configurar_grafico(alt.Chart(df).mark_circle(opacity=0.65).encode(**codigo).properties(title=titulo), altura)

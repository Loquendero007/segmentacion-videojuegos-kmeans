from pathlib import Path
import json

import altair as alt
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parents[1]
DATOS = BASE / "data" / "processed" / "videojuegos_clusterizados.csv"
RESUMEN = BASE / "outputs" / "resumen.json"
COLORES = ["#60a5fa", "#fbbf24", "#34d399", "#a78bfa", "#f87171", "#22d3ee"]


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
    st.set_page_config(page_title="Segmentación de Videojuegos", page_icon="🎮", layout="wide", initial_sidebar_state="expanded")
    st.markdown(
        """
        <style>
            .stApp {background: linear-gradient(180deg, #070b16 0%, #0f172a 55%, #111827 100%); color: #f1f5f9;}
            .block-container {padding-top: 1.1rem; padding-bottom: 2.5rem; max-width: 1500px; color: #e5e7eb;}
            .stMarkdown, .stMarkdown p, .stMarkdown li, .stText, [data-testid="stCaptionContainer"] p {
                color: #e2e8f0 !important;
            }
            [data-testid="stSidebar"] {background: linear-gradient(180deg, #020617 0%, #0f172a 100%); border-right: 1px solid #1e293b;}
            [data-testid="stSidebar"] * {color: #e2e8f0 !important;}
            [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {color: #7dd3fc !important;}
            [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {color: #e2e8f0 !important;}
            [data-baseweb="select"] > div, [data-baseweb="input"] > div {
                background-color: #1e293b !important; color: #f8fafc !important; border-color: #475569 !important;
            }
            .hero {
                background: linear-gradient(120deg, #1e3a8a 0%, #4338ca 55%, #0f766e 100%);
                padding: 26px 30px; border-radius: 20px; color: white; margin: 6px 0 24px;
                box-shadow: 0 12px 34px rgba(0, 0, 0, 0.45); position: relative; overflow: hidden;
            }
            .hero:after {
                content: ""; position: absolute; right: -40px; top: -60px; width: 220px; height: 220px;
                border-radius: 50%; background: rgba(255,255,255,0.10);
            }
            .hero h1 {margin: 0; font-size: 31px; letter-spacing: -0.02em; position: relative; z-index: 1; color: #ffffff;}
            .hero p {margin: 9px 0 0; font-size: 15px; opacity: 0.94; position: relative; z-index: 1; color: #ffffff;}
            .hero .badge {
                display: inline-block; margin-top: 14px; padding: 5px 12px; border-radius: 999px;
                background: rgba(255,255,255,0.20); font-size: 12px; letter-spacing: 0.06em;
                position: relative; z-index: 1; color: #ffffff;
            }
            .kpi {
                background: rgba(30, 41, 59, 0.88); border: 1px solid #334155; border-radius: 16px;
                padding: 17px 18px; border-left: 5px solid var(--accent); box-shadow: 0 8px 22px rgba(0,0,0,0.35);
                transition: transform 0.15s ease;
            }
            .kpi:hover {transform: translateY(-3px);}
            .kpi .label {font-size: 11px; text-transform: uppercase; letter-spacing: 0.10em; color: #94a3b8; font-weight: 700;}
            .kpi .value {font-size: 27px; font-weight: 800; color: #f8fafc; margin: 6px 0 2px; line-height: 1.1;}
            .kpi .hint {font-size: 11px; color: #94a3b8;}
            .seccion {display: flex; align-items: center; gap: 11px; margin: 26px 0 12px;}
            .seccion:before {content: ""; width: 7px; height: 25px; border-radius: 5px; background: linear-gradient(#60a5fa, #34d399);}
            .seccion h3 {margin: 0; font-size: 19px; color: #f1f5f9; font-weight: 700;}
            [data-testid="stContainer"] {
                background-color: rgba(30, 41, 59, 0.72) !important; border: 1px solid #334155 !important;
                border-radius: 16px !important; box-shadow: 0 6px 18px rgba(0,0,0,0.28); color: #e2e8f0;
            }
            [data-testid="stExpander"] {background-color: rgba(30,41,59,0.72) !important; border: 1px solid #334155 !important; border-radius: 12px !important;}
            [data-testid="stExpander"] summary, [data-testid="stExpander"] p, [data-testid="stExpander"] div {color: #e2e8f0 !important;}
            [data-testid="stDataFrame"] {background-color: rgba(15,23,42,0.6) !important; border-radius: 12px;}
            [data-testid="stDataFrame"] * {color: #e2e8f0 !important;}
            [data-testid="stImage"] p, [data-testid="stImage"] span {color: #cbd5e1 !important;}
            hr {border-color: #334155 !important;}
            .nota {font-size: 12px; color: #94a3b8; margin-top: 8px;}
            .footer {margin-top: 34px; padding-top: 12px; border-top: 1px solid #334155; font-size: 11px; color: #94a3b8;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def encabezado(titulo, subtitulo, badge=""):
    st.markdown(
        f'<div class="hero"><h1>{titulo}</h1><p>{subtitulo}</p>'
        + (f'<span class="badge">{badge}</span>' if badge else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def seccion(texto):
    st.markdown(f'<div class="seccion"><h3>{texto}</h3></div>', unsafe_allow_html=True)


def kpis(items):
    columnas = st.columns(len(items))
    for col, item in zip(columnas, items):
        with col:
            st.markdown(
                f'<div class="kpi" style="--accent:{item.get("color", "#60a5fa")}">'
                f'<div class="label">{item["label"]}</div>'
                f'<div class="value">{item["value"]}</div>'
                f'<div class="hint">{item.get("hint", "")}</div></div>',
                unsafe_allow_html=True,
            )


def pie(texto):
    st.markdown(f'<div class="footer">{texto}</div>', unsafe_allow_html=True)


def filtros_comunes(df):
    st.sidebar.markdown("## 🎛️ Filtros interactivos")
    generos = sorted(df["Genero"].dropna().unique().tolist())
    plataformas = sorted(df["Plataforma"].dropna().unique().tolist())
    anio_min, anio_max = int(df["Anio"].min()), int(df["Anio"].max())

    sel_generos = st.sidebar.multiselect("Género", generos, default=generos)
    sel_plataformas = st.sidebar.multiselect("Plataforma", plataformas, default=plataformas)
    rango = st.sidebar.slider("Rango de años", anio_min, anio_max, (anio_min, anio_max))

    filtrado = df[
        df["Genero"].isin(sel_generos)
        & df["Plataforma"].isin(sel_plataformas)
        & df["Anio"].between(rango[0], rango[1])
    ]
    st.sidebar.markdown(
        f'<div style="background:rgba(96,165,250,0.14);border:1px solid #334155;padding:10px 12px;'
        f'border-radius:10px;margin-top:10px;color:#e2e8f0;"><b>{len(filtrado):,}</b> de {len(df):,} juegos visibles</div>',
        unsafe_allow_html=True,
    )
    return filtrado


def configurar_grafico(chart, altura=320):
    return (
        chart.properties(height=altura)
        .configure_view(stroke=None, fill="rgba(0,0,0,0)")
        .configure_axis(gridColor="rgba(148,163,184,0.22)", grid=True, labelColor="#cbd5e1", titleColor="#e2e8f0",
                        labelFontSize=11, titleFontSize=12, domainColor="#475569", tickColor="#475569")
        .configure_legend(labelColor="#e2e8f0", titleColor="#e2e8f0", labelFontSize=11)
        .configure_title(color="#f8fafc", fontSize=14, anchor="start", offset=12)
    )


def escala_color(dominio=None):
    return alt.Scale(domain=dominio or [], range=COLORES[:len(dominio or COLORES)])


def grafico_barras(df, x, y, color=None, titulo="", altura=320, orden=None, dominio=None):
    kwargs = {}
    if color:
        kwargs["color"] = alt.Color(f"{color}:N", scale=escala_color(dominio or sorted(df[color].unique())), title=color)
    base = alt.Chart(df).mark_bar(cornerRadiusEnd=5).encode(
        x=alt.X(f"{x}:N", sort=orden, title=x, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{y}:Q", title=y),
        tooltip=[alt.Tooltip(f"{x}:N", title=x), alt.Tooltip(f"{y}:Q", title=y, format=",.2f")],
        **kwargs,
    )
    return configurar_grafico(base.properties(title=titulo), altura)


def grafico_dispersion(df, x, y, color, size=None, titulo="", altura=430, dominio=None):
    codigo = {
        "x": alt.X(f"{x}:Q", title=x, scale=alt.Scale(zero=False)),
        "y": alt.Y(f"{y}:Q", title=y, scale=alt.Scale(zero=False)),
        "color": alt.Color(f"{color}:N", scale=escala_color(dominio or sorted(df[color].unique())), title="Grupo"),
        "tooltip": [
            alt.Tooltip("Nombre:N", title="Juego"),
            alt.Tooltip("Plataforma:N", title="Plataforma"),
            alt.Tooltip(f"{x}:Q", title=x, format=".0f"),
            alt.Tooltip(f"{y}:Q", title=y, format=".2f"),
            alt.Tooltip("Ventas_Globales_Millones:Q", title="Ventas (M)", format=".2f"),
        ],
    }
    if size:
        codigo["size"] = alt.Size(f"{size}:Q", title=size, scale=alt.Scale(range=[25, 240]))
    return configurar_grafico(alt.Chart(df).mark_circle(opacity=0.72).encode(**codigo).properties(title=titulo), altura)

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import (
    BASE,
    COLORES,
    aplicar_estilo,
    cargar_datos,
    cargar_resumen,
    configurar_grafico,
    encabezado,
    filtros_comunes,
    grafico_barras,
    grafico_dispersion,
    kpis,
    pie,
    seccion,
)

aplicar_estilo()
df = cargar_datos()
resumen = cargar_resumen()
filtro = filtros_comunes(df)
perfil_df = pd.DataFrame(resumen["perfil"])
silueta_k = [m["silueta"] for m in resumen["metricas"] if m["k"] == resumen["k_seleccionado"]][0]
dominio = perfil_df.sort_values("Cluster")["Nombre_Grupo"].tolist()

encabezado(
    "🧩 Segmentación mediante K-Means",
    f"Modelo final: K={resumen['k_seleccionado']} · semilla {resumen['semilla']} · "
    + ", ".join(resumen["variables_agrupamiento"]),
    "PÁGINA 2 DE 2",
)

kpis([
    {"label": "Clústeres", "value": resumen["k_seleccionado"], "hint": "grupos detectados", "color": "#2563eb"},
    {"label": "Silueta promedio", "value": f"{silueta_k:.3f}", "hint": "calidad del agrupamiento", "color": "#10b981"},
    {"label": "Juegos segmentados", "value": f"{len(df):,}", "hint": "dataset procesado", "color": "#f59e0b"},
    {"label": "Varianza PCA 2D", "value": f"{sum(resumen['pca_varianza']):.1%}", "hint": "información visualizada", "color": "#8b5cf6"},
])

st.sidebar.markdown("## 🧩 Filtro de segmento")
seleccion = st.sidebar.multiselect("Grupo (K-Means)", dominio, default=dominio)
filtro = filtro[filtro["Nombre_Grupo"].isin(seleccion)]

seccion("Distribución de registros por clúster")
conteo = perfil_df[["Nombre_Grupo", "Cluster", "Registros"]].sort_values("Cluster")
barra = grafico_barras(conteo, "Nombre_Grupo", "Registros", color="Nombre_Grupo", titulo="", altura=300, orden=dominio, dominio=dominio)
with st.container(border=True):
    st.altair_chart(barra, width="stretch")

seccion("Visualización de los agrupamientos")
if filtro.empty:
    st.warning("Ajuste los filtros para visualizar los agrupamientos.")
else:
    dispersion = grafico_dispersion(
        filtro, "Anio", "Log_Ventas_Globales", "Nombre_Grupo", "Cuota_JP",
        "Año de lanzamiento vs. ventas (el tamaño representa la cuota en Japón)",
        altura=450, dominio=dominio,
    )
    with st.container(border=True):
        st.altair_chart(dispersion, width="stretch")
    st.markdown('<div class="nota">Cada punto es un videojuego; las burbujas grandes vendieron proporcionalmente más en Japón.</div>', unsafe_allow_html=True)

seccion("Comparación de características entre grupos")
colA, colB = st.columns(2)
with colA:
    with st.container(border=True):
        if filtro.empty:
            st.info("Sin datos para comparar.")
        else:
            caja = alt.Chart(filtro).mark_boxplot(extent="min-max").encode(
                x=alt.X("Nombre_Grupo:N", sort=dominio, title="Grupo", axis=alt.Axis(labelAngle=-30)),
                y=alt.Y("Ventas_Globales_Millones:Q", title="Ventas globales (M)", scale=alt.Scale(type="sqrt")),
                color=alt.Color("Nombre_Grupo:N", scale=alt.Scale(domain=dominio, range=COLORES), legend=None),
                tooltip=[alt.Tooltip("Nombre_Grupo:N", title="Grupo"), alt.Tooltip("Ventas_Globales_Millones:Q", title="Ventas (M)", format=".2f")],
            ).properties(title="Distribución de ventas por grupo", height=330)
            st.altair_chart(configurar_grafico(caja), width="stretch")
with colB:
    with st.container(border=True):
        regiones = perfil_df.melt(
            id_vars="Nombre_Grupo",
            value_vars=["Cuota_NA", "Cuota_EU", "Cuota_JP"],
            var_name="Region",
            value_name="Cuota",
        )
        regiones["Region"] = regiones["Region"].map({"Cuota_NA": "Norteamérica", "Cuota_EU": "Europa", "Cuota_JP": "Japón"})
        barras = alt.Chart(regiones).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X("Nombre_Grupo:N", sort=dominio, title="Grupo", axis=alt.Axis(labelAngle=-30)),
            xOffset="Region:N",
            y=alt.Y("Cuota:Q", title="Cuota promedio", axis=alt.Axis(format="%")),
            color=alt.Color("Region:N", title="Región", scale=alt.Scale(range=["#2563eb", "#10b981", "#f59e0b"])),
            tooltip=[alt.Tooltip("Nombre_Grupo:N", title="Grupo"), alt.Tooltip("Region:N", title="Región"), alt.Tooltip("Cuota:Q", title="Cuota", format=".1%")],
        ).properties(title="Preferencia regional por grupo", height=330)
        st.altair_chart(configurar_grafico(barras), width="stretch")

seccion("Estadísticas descriptivas por clúster")
columnas = ["Cluster", "Nombre_Grupo", "Registros", "Ventas_Globales_Millones", "Cuota_NA", "Cuota_EU", "Cuota_JP", "Anio", "Genero_mas_frecuente", "Plataforma_mas_frecuente"]
tabla = perfil_df[columnas].rename(columns={
    "Ventas_Globales_Millones": "Ventas prom. (M)", "Cuota_NA": "Cuota NA", "Cuota_EU": "Cuota EU",
    "Cuota_JP": "Cuota JP", "Anio": "Año prom.", "Registros": "Juegos",
    "Genero_mas_frecuente": "Género típico", "Plataforma_mas_frecuente": "Plataforma típica",
})
with st.container(border=True):
    st.dataframe(tabla, width="stretch", hide_index=True)

seccion("Descripción de los grupos identificados")
for _, fila in perfil_df.iterrows():
    with st.expander(f"**{fila['Nombre_Grupo']}** · clúster {int(fila['Cluster'])} · {int(fila['Registros']):,} juegos"):
        st.write(
            f"Ventas promedio de **{fila['Ventas_Globales_Millones']:.2f} M** de copias. "
            f"Distribución regional: Norteamérica {fila['Cuota_NA']:.1%}, Europa {fila['Cuota_EU']:.1%} y Japón {fila['Cuota_JP']:.1%}. "
            f"Año promedio de lanzamiento: **{fila['Anio']:.1f}**. "
            f"Género típico: {fila['Genero_mas_frecuente']}; plataforma típica: {fila['Plataforma_mas_frecuente']}."
        )

ventas_grupo = df.groupby("Nombre_Grupo")["Ventas_Globales_Millones"].sum()
participacion = (ventas_grupo / ventas_grupo.sum() * 100).sort_values(ascending=False)
blockbuster = [g for g in participacion.index if "Blockbusters" in g][0]
japones = [g for g in participacion.index if "japonés" in g][0]
europeo = [g for g in participacion.index if "Europa" in g][0]
n_blk = int(perfil_df.loc[perfil_df["Nombre_Grupo"] == blockbuster, "Registros"].iat[0])

seccion("Hallazgos y recomendaciones")
col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("#### 🔍 Hallazgos")
        st.write(f"**1.** {blockbuster}: {n_blk / len(df):.1%} de los juegos concentra el {participacion[blockbuster]:.1%} de las ventas.")
        st.write(f"**2.** {japones}: el 96% de sus ventas se concentra en Japón, con volúmenes bajos por título.")
        st.write(f"**3.** {europeo}: lanzamientos más recientes (2010.6 en promedio) frente a 2004.5 del grupo de blockbusters.")
with col2:
    with st.container(border=True):
        st.markdown("#### 💡 Recomendaciones")
        st.write("**1.** Diseñar propuestas con atractivo NA + EU y lanzamiento multiplataforma.")
        st.write("**2.** Mantener catálogo localizado para Japón (ROL y portátiles) con alta fidelidad regional.")
        st.write("**3.** Reforzar distribución PC/digital en Europa, donde aparecen los títulos más recientes.")

with st.expander("Ver proyección PCA del modelo (Matplotlib / Seaborn)"):
    st.image(str(BASE / resumen["figuras"]["pca"]), caption="Agrupamientos K-Means proyectados en dos componentes principales")

pie("Limitaciones: ventas estimadas, datos hasta 2020, sin críticas/precios y sensibilidad de K-Means a escala y semilla")

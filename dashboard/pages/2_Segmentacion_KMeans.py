import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import BASE, aplicar_estilo, cargar_datos, cargar_resumen, filtros_comunes, grafico_barras, grafico_dispersion

aplicar_estilo()
df = cargar_datos()
resumen = cargar_resumen()
filtro = filtros_comunes(df)

st.title("🧩 Página 2 · Segmentación mediante K-Means")
st.caption(f"Modelo final: K={resumen['k_seleccionado']} · semilla={resumen['semilla']} · variables: {', '.join(resumen['variables_agrupamiento'])}")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Clústeres", resumen["k_seleccionado"])
k2.metric("Silueta promedio", f"{[m['silueta'] for m in resumen['metricas'] if m['k'] == resumen['k_seleccionado']][0]:.3f}")
k3.metric("Juegos segmentados", f"{len(df):,}")
k4.metric("Varianza PCA 2D", f"{sum(resumen['pca_varianza']):.1%}")

grupos = sorted(df["Nombre_Grupo"].unique().tolist())
seleccion = st.sidebar.multiselect("4. Grupo (K-Means)", grupos, default=grupos)
filtro = filtro[filtro["Nombre_Grupo"].isin(seleccion)]

st.markdown("### Distribución de registros por clúster")
conteo = df.groupby(["Nombre_Grupo", "Cluster"]).size().rename("Juegos").reset_index().sort_values("Cluster")
barra = grafico_barras(conteo, "Nombre_Grupo", "Juegos", color="Nombre_Grupo", titulo="Cantidad de juegos por grupo", altura=300)
barra = barra.encode(x=alt.X("Nombre_Grupo:N", sort=conteo["Nombre_Grupo"].tolist(), title="Grupo", axis=alt.Axis(labelAngle=0)))
st.altair_chart(barra, width="stretch")

st.markdown("### Visualización de los agrupamientos")
if filtro.empty:
    st.warning("Ajuste los filtros para visualizar los agrupamientos.")
else:
    dispersion = grafico_dispersion(
        filtro, "Anio", "Log_Ventas_Globales", "Nombre_Grupo", "Cuota_JP",
        "Año de lanzamiento vs. ventas (tamaño = cuota de ventas en Japón)",
    )
    st.altair_chart(dispersion, width="stretch")

st.markdown("### Comparación de características entre grupos")
colA, colB = st.columns(2)
with colA:
    if filtro.empty:
        st.info("Sin datos para comparar.")
    else:
        caja = alt.Chart(filtro).mark_boxplot(extent="min-max").encode(
            x=alt.X("Nombre_Grupo:N", title="Grupo", axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("Ventas_Globales_Millones:Q", title="Ventas globales (M)", scale=alt.Scale(type="sqrt")),
            color=alt.Color("Nombre_Grupo:N", scale=alt.Scale(scheme="tableau10"), legend=None),
            tooltip=[alt.Tooltip("Nombre_Grupo:N", title="Grupo"), alt.Tooltip("Ventas_Globales_Millones:Q", title="Ventas (M)", format=".2f")],
        ).properties(title="Distribución de ventas por grupo", height=320)
        st.altair_chart(caja.configure_view(stroke=None), width="stretch")
with colB:
    perfil_df = pd.DataFrame(resumen["perfil"])
    regiones = perfil_df.melt(
        id_vars="Nombre_Grupo",
        value_vars=["Cuota_NA", "Cuota_EU", "Cuota_JP"],
        var_name="Region",
        value_name="Cuota",
    )
    regiones["Region"] = regiones["Region"].map({"Cuota_NA": "Norteamérica", "Cuota_EU": "Europa", "Cuota_JP": "Japón"})
    barras = alt.Chart(regiones).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("Nombre_Grupo:N", title="Grupo", axis=alt.Axis(labelAngle=-30)),
        xOffset="Region:N",
        y=alt.Y("Cuota:Q", title="Cuota promedio", axis=alt.Axis(format="%")),
        color=alt.Color("Region:N", title="Región", scale=alt.Scale(scheme="set2")),
        tooltip=[alt.Tooltip("Nombre_Grupo:N", title="Grupo"), alt.Tooltip("Region:N", title="Región"), alt.Tooltip("Cuota:Q", title="Cuota", format=".1%")],
    ).properties(title="Preferencia regional por grupo", height=320)
    st.altair_chart(barras.configure_view(stroke=None), width="stretch")

st.markdown("### Estadísticas descriptivas por clúster")
columnas = ["Cluster", "Nombre_Grupo", "Registros", "Ventas_Globales_Millones", "Cuota_NA", "Cuota_EU", "Cuota_JP", "Anio", "Genero_mas_frecuente", "Plataforma_mas_frecuente"]
tabla = pd.DataFrame(resumen["perfil"])[columnas].rename(columns={
    "Ventas_Globales_Millones": "Ventas prom. (M)", "Cuota_NA": "Cuota NA", "Cuota_EU": "Cuota EU",
    "Cuota_JP": "Cuota JP", "Anio": "Año prom.", "Registros": "Juegos",
    "Genero_mas_frecuente": "Género típico", "Plataforma_mas_frecuente": "Plataforma típica",
})
st.dataframe(tabla, width="stretch", hide_index=True)

st.markdown("### Descripción de los grupos identificados")
for _, fila in pd.DataFrame(resumen["perfil"]).iterrows():
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

st.markdown("### Hallazgos y recomendaciones")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Hallazgos**")
    st.write(f"1. El grupo **{blockbuster}** representa solo {int(pd.DataFrame(resumen['perfil']).query('Nombre_Grupo == @blockbuster')['Registros'].iat[0]) / len(df):.1%} de los juegos, pero concentra el {participacion[blockbuster]:.1%} de las ventas globales.")
    st.write(f"2. El grupo **{japones}** destina el 96% de sus ventas al mercado japonés, con un volumen promedio bajo: es un nicho regional muy concentrado.")
    st.write(f"3. El grupo **{europeo}** tiene los lanzamientos más recientes (año promedio 2010.6), lo que sugiere un cambio reciente hacia Europa y plataformas PC.")
with col2:
    st.markdown("**Recomendaciones**")
    st.write("1. Priorizar diseños con atractivo Transatlántico (NA + EU) y lanzamientos multiplataforma para replicar el perfil de los blockbusters.")
    st.write("2. Desarrollar catálogo localizado para Japón (géneros de rol y formatos portátiles), aceptando menor volumen pero alta fidelidad regional.")
    st.write("3. Reforzar la distribución digital/PC en Europa, donde se concentran los títulos más recientes del dataset.")

with st.expander("Ver proyección PCA del modelo (Matplotlib / Seaborn)"):
    ruta = BASE / resumen["figuras"]["pca"]
    st.image(str(ruta), caption="Agrupamientos K-Means proyectados en dos componentes principales")

st.caption("Limitaciones: datos historiales hasta 2020, ventas estimadas, sin variables de crítica/precio y K-Means sensible a la escala y a los valores atípicos.")

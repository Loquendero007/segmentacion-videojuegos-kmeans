from pathlib import Path
import json

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw" / "vgsales.csv"
PROCESSED = BASE / "data" / "processed" / "videojuegos_clusterizados.csv"
FIG = BASE / "outputs" / "figures"
TAB = BASE / "outputs" / "tablas"
MOD = BASE / "outputs" / "modelos"
FEATURES = ["Log_Ventas_Globales", "Cuota_NA", "Cuota_EU", "Cuota_JP", "Anio"]
FEATURES_SIMPLES = ["Log_Ventas_Globales", "Cuota_JP", "Anio"]
SEED = 42

for carpeta in (FIG, TAB, MOD, PROCESSED.parent):
    carpeta.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", palette="viridis")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["axes.titlesize"] = 14


def guardar_tabla(df, nombre):
    df.to_csv(TAB / nombre, index=False, encoding="utf-8-sig")


def guardar_figura(nombre):
    ruta = FIG / nombre
    plt.tight_layout()
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    return str(ruta.relative_to(BASE)).replace("\\", "/")


def cargar_datos():
    df = pd.read_csv(RAW)
    for col in df.columns:
        if str(df[col].dtype) in ("object", "str", "string"):
            df[col] = df[col].astype(str).str.strip().replace({"nan": np.nan, "N/A": np.nan, "Unknown": "Desconocido"})
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    return df


def explorar(df):
    guardar_tabla(df.head(10), "01_primeros_10_registros.csv")
    estructura = pd.DataFrame({
        "columna": df.columns,
        "tipo": df.dtypes.astype(str).values,
        "no_nulos": df.notna().sum().values,
        "nulos": df.isna().sum().values,
        "unicos": df.nunique().values,
    })
    guardar_tabla(estructura, "02_estructura_dataset.csv")
    guardar_tabla(df.describe(include="all").T.rename_axis("columna").reset_index(), "03_estadisticas_descriptivas.csv")
    nulos = df.isna().sum().rename_axis("columna").reset_index(name="nulos")
    nulos["porcentaje"] = (nulos["nulos"] / len(df) * 100).round(2)
    guardar_tabla(nulos, "04_valores_nulos.csv")
    guardar_tabla(pd.DataFrame({"registros_duplicados_completos": [int(df.duplicated().sum())],
                                "duplicados_nombre_plataforma_anio": [int(df.duplicated(subset=["Name", "Platform", "Year"]).sum())]}),
                  "05_duplicados.csv")

    figuras = {}
    fig, ax = plt.subplots()
    top = df["Genre"].value_counts().head(10)
    sns.barplot(x=top.values, y=top.index, ax=ax, hue=top.index, legend=False)
    ax.set(title="Géneros más frecuentes", xlabel="Cantidad de juegos", ylabel="Género")
    figuras["generos"] = guardar_figura("01_generos_frecuentes.png")

    fig, ax = plt.subplots()
    anios = df["Year"].dropna().astype(int).value_counts().sort_index()
    ax.plot(anios.index, anios.values, marker="o", markersize=3, linewidth=1)
    ax.set(title="Lanzamientos por año", xlabel="Año", ylabel="Cantidad de juegos")
    figuras["anios"] = guardar_figura("02_lanzamientos_por_anio.png")

    fig, ax = plt.subplots()
    sns.histplot(np.log1p(df["Global_Sales"].dropna()), bins=40, kde=True, ax=ax)
    ax.set(title="Distribución de ventas globales (escala log)", xlabel="log(1 + ventas globales, millones)", ylabel="Juegos")
    figuras["ventas"] = guardar_figura("03_ventas_globales_log.png")

    fig, ax = plt.subplots()
    sns.boxplot(x="Platform", y="Global_Sales", data=df[df["Platform"].isin(df["Platform"].value_counts().head(10).index)], ax=ax)
    ax.set(title="Ventas globales por plataforma (top 10)", xlabel="Plataforma", ylabel="Millones de copias")
    ax.tick_params(axis="x", rotation=45)
    figuras["plataformas"] = guardar_figura("04_ventas_por_plataforma.png")

    fig, ax = plt.subplots()
    regiones = df[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum()
    sns.barplot(x=regiones.values, y=regiones.index, ax=ax, hue=regiones.index, legend=False)
    ax.set(title="Ventas totales por región", xlabel="Millones de copias", ylabel="Región")
    figuras["regiones"] = guardar_figura("05_ventas_por_region.png")
    return figuras


def limpiar_y_preparar(df):
    pasos = []
    pasos.append(("Registros iniciales", len(df)))

    antes = len(df)
    df = df.drop_duplicates()
    pasos.append(("Eliminación de filas idénticas", antes - len(df)))

    antes = len(df)
    df = df.sort_values("Global_Sales", ascending=False).drop_duplicates(subset=["Name", "Platform", "Year"], keep="first")
    pasos.append(("Eliminación de juegos repetidos (Nombre-Plataforma-Año)", antes - len(df)))

    nulos_anio = int(df["Year"].isna().sum())
    mediana_anio = int(round(df["Year"].median()))
    df["Year"] = df["Year"].fillna(mediana_anio).astype(int)
    pasos.append((f"Imputación de año faltante con la mediana ({mediana_anio})", nulos_anio))

    nulos_editor = int(df["Publisher"].isna().sum())
    df["Publisher"] = df["Publisher"].fillna("Desconocido")
    pasos.append(("Imputación de editorial faltante como 'Desconocido'", nulos_editor))

    df["Nombre"] = df["Name"]
    df["Genero"] = df["Genre"]
    df["Editorial"] = df["Publisher"]
    df["Plataforma"] = df["Platform"]
    df["Anio"] = df["Year"]

    total = df[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].sum(axis=1).replace(0, np.nan)
    df["Cuota_NA"] = (df["NA_Sales"] / total).fillna(0)
    df["Cuota_EU"] = (df["EU_Sales"] / total).fillna(0)
    df["Cuota_JP"] = (df["JP_Sales"] / total).fillna(0)
    df["Cuota_Otros"] = (df["Other_Sales"] / total).fillna(0)
    df["Log_Ventas_Globales"] = np.log1p(df["Global_Sales"])
    df["Ventas_Globales_Millones"] = df["Global_Sales"]
    pasos.append(("Ingeniería de variables (cuotas regionales y log de ventas)", len(df)))

    q1, q3 = df["Global_Sales"].quantile([0.01, 0.99])
    atipicos = int(((df["Global_Sales"] < q1) | (df["Global_Sales"] > q3)).sum())
    pasos.append((f"Valores atípicos en ventas detectados (límites 1%-99%: {q1:.2f}-{q3:.2f}M); se conservan y se atenúan con log", atipicos))

    pasos_df = pd.DataFrame(pasos, columns=["paso", "registros_afectados"])
    guardar_tabla(pasos_df, "06_limpieza_preparacion.csv")
    return df, pasos_df


def evaluar_modelos(X, X_simple, k_range=range(2, 7)):
    filas = []
    curvas = {"k": list(k_range), "inercia": [], "silueta": [], "calinski": [], "davies": []}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=SEED, n_init=25)
        etiquetas = km.fit_predict(X)
        filas.append({
            "k": k,
            "inercia": round(km.inertia_, 2),
            "silueta": round(silhouette_score(X, etiquetas), 4),
            "calinski_harabasz": round(calinski_harabasz_score(X, etiquetas), 2),
            "davies_bouldin": round(davies_bouldin_score(X, etiquetas), 4),
            "configuracion": "5 variables estandarizadas",
        })
        curvas["inercia"].append(round(km.inertia_, 2))
        curvas["silueta"].append(round(silhouette_score(X, etiquetas), 4))
        curvas["calinski"].append(round(calinski_harabasz_score(X, etiquetas), 2))
        curvas["davies"].append(round(davies_bouldin_score(X, etiquetas), 4))

    metricas = pd.DataFrame(filas)
    guardar_tabla(metricas, "07_evaluacion_k.csv")

    k_mejor = int(metricas.loc[metricas["silueta"].idxmax(), "k"])
    km_final = KMeans(n_clusters=k_mejor, random_state=SEED, n_init=25)
    etiquetas = km_final.fit_predict(X)
    km_simple = KMeans(n_clusters=k_mejor, random_state=SEED, n_init=25)
    etiquetas_simple = km_simple.fit_predict(X_simple)
    comparacion = pd.DataFrame([
        {
            "configuracion": "A: 5 variables (seleccionada)",
            "variables": ", ".join(FEATURES),
            "silueta": round(silhouette_score(X, etiquetas), 4),
            "calinski_harabasz": round(calinski_harabasz_score(X, etiquetas), 2),
            "davies_bouldin": round(davies_bouldin_score(X, etiquetas), 4),
            "inercia": round(km_final.inertia_, 2),
        },
        {
            "configuracion": "B: 3 variables (comparación)",
            "variables": ", ".join(FEATURES_SIMPLES),
            "silueta": round(silhouette_score(X_simple, etiquetas_simple), 4),
            "calinski_harabasz": round(calinski_harabasz_score(X_simple, etiquetas_simple), 2),
            "davies_bouldin": round(davies_bouldin_score(X_simple, etiquetas_simple), 4),
            "inercia": round(km_simple.inertia_, 2),
        },
    ])
    guardar_tabla(comparacion, "08_comparacion_configuraciones.csv")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].plot(curvas["k"], curvas["inercia"], marker="o")
    axes[0].axvline(k_mejor, color="crimson", linestyle="--", label=f"K seleccionado = {k_mejor}")
    axes[0].set(title="Método del codo", xlabel="K", ylabel="Inercia")
    axes[0].legend()
    axes[1].plot(curvas["k"], curvas["silueta"], marker="o", color="darkgreen")
    axes[1].axvline(k_mejor, color="crimson", linestyle="--", label=f"K seleccionado = {k_mejor}")
    axes[1].set(title="Coeficiente de silueta", xlabel="K", ylabel="Silueta promedio")
    axes[1].legend()
    curvas_fig = guardar_figura("06_seleccion_k.png")

    return km_final, etiquetas, metricas, comparacion, curvas_fig


def nombrar_grupos(perfil, base):
    nombres = {}
    for cluster, fila in perfil.iterrows():
        if fila["Cuota_JP"] > base["Cuota_JP"] * 1.35:
            nombre = "Fenómeno japonés"
        elif fila["Ventas_Globales_Millones"] > base["Ventas_Globales_Millones"] * 1.8:
            nombre = "Blockbusters globales"
        elif fila["Anio"] < 2000:
            nombre = "Clásicos retro"
        elif fila["Cuota_NA"] > base["Cuota_NA"] * 1.12:
            nombre = "Favoritos de Norteamérica"
        elif fila["Cuota_EU"] > base["Cuota_EU"] * 1.12:
            nombre = "Favoritos de Europa"
        elif fila["Ventas_Globales_Millones"] < base["Ventas_Globales_Millones"] * 0.65:
            nombre = "Catálogo de nicho"
        else:
            nombre = "Éxito regional equilibrado"
        nombres[int(cluster)] = nombre
    return nombres


def main():
    df = cargar_datos()
    figuras = explorar(df)
    limpio, pasos = limpiar_y_preparar(df)

    scaler = StandardScaler()
    X = scaler.fit_transform(limpio[FEATURES])
    scaler_simple = StandardScaler()
    X_simple = scaler_simple.fit_transform(limpio[FEATURES_SIMPLES])

    modelo, etiquetas, metricas, comparacion, curvas_fig = evaluar_modelos(X, X_simple)
    limpio["Cluster"] = etiquetas

    base = limpio[["Ventas_Globales_Millones", "Cuota_NA", "Cuota_EU", "Cuota_JP", "Anio"]].mean()
    perfil = limpio.groupby("Cluster").agg(
        Registros=("Cluster", "size"),
        Ventas_Globales_Millones=("Ventas_Globales_Millones", "mean"),
        Cuota_NA=("Cuota_NA", "mean"),
        Cuota_EU=("Cuota_EU", "mean"),
        Cuota_JP=("Cuota_JP", "mean"),
        Anio=("Anio", "mean"),
        Genero_mas_frecuente=("Genero", lambda s: s.mode().iat[0]),
        Plataforma_mas_frecuente=("Plataforma", lambda s: s.mode().iat[0]),
    ).round(3)
    nombres = nombrar_grupos(perfil, base)
    perfil["Nombre_Grupo"] = [nombres[int(c)] for c in perfil.index]
    perfil = perfil.reset_index()
    guardar_tabla(perfil, "09_perfil_clusters.csv")

    limpio["Nombre_Grupo"] = limpio["Cluster"].map(nombres)
    columnas_salida = [
        "Rank", "Nombre", "Plataforma", "Anio", "Genero", "Editorial",
        "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Ventas_Globales_Millones",
        "Cuota_NA", "Cuota_EU", "Cuota_JP", "Cuota_Otros",
        "Log_Ventas_Globales", "Cluster", "Nombre_Grupo",
    ]
    limpio[columnas_salida].to_csv(PROCESSED, index=False, encoding="utf-8-sig")

    centroides_original = pd.DataFrame(
        scaler.inverse_transform(modelo.cluster_centers_), columns=FEATURES
    )
    centroides_original.insert(0, "Cluster", range(len(centroides_original)))
    centroides_original["Nombre_Grupo"] = [nombres[i] for i in centroides_original["Cluster"]]
    guardar_tabla(centroides_original.round(4), "10_centroides.csv")
    guardar_tabla(pd.DataFrame(modelo.cluster_centers_, columns=FEATURES).round(4).assign(Cluster=range(len(centroides_original))), "11_centroides_estandarizados.csv")

    fig, ax = plt.subplots(figsize=(11, 7))
    pca = PCA(n_components=2, random_state=SEED)
    coords = pca.fit_transform(X)
    puntos = pd.DataFrame({"PC1": coords[:, 0], "PC2": coords[:, 1], "Cluster": etiquetas,
                           "Nombre": limpio["Nombre_Grupo"].values})
    sns.scatterplot(data=puntos, x="PC1", y="PC2", hue="Nombre", style="Cluster", s=28, alpha=0.65, ax=ax)
    centros_pc = pca.transform(modelo.cluster_centers_)
    ax.scatter(centros_pc[:, 0], centros_pc[:, 1], marker="X", s=260, c="black", edgecolor="white", linewidth=1.5, label="Centroides")
    ax.set(title="Segmentación de videojuegos K-Means (proyección PCA)", xlabel=f"PC1 ({pca.explained_variance_ratio_[0]:.1%} varianza)", ylabel=f"PC2 ({pca.explained_variance_ratio_[1]:.1%} varianza)")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    pca_fig = guardar_figura("07_clusters_pca.png")

    fig, ax = plt.subplots(figsize=(11, 7))
    sns.scatterplot(data=limpio, x="Anio", y="Log_Ventas_Globales", hue="Nombre_Grupo", size="Cuota_JP", sizes=(15, 130), alpha=0.7, ax=ax)
    ax.set(title="Agrupamientos: año de lanzamiento vs. ventas globales", xlabel="Año de lanzamiento", ylabel="log(1 + ventas globales)")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    dispersion_fig = guardar_figura("08_clusters_anio_ventas.png")

    fig, ax = plt.subplots(figsize=(11, 6))
    orden = limpio["Cluster"].value_counts().sort_index()
    sns.barplot(x=orden.index.astype(str), y=orden.values, ax=ax, hue=orden.index.astype(str), legend=False)
    for i, v in enumerate(orden.values):
        ax.text(i, v + 60, str(v), ha="center", fontsize=9)
    ax.set(title="Distribución de juegos por clúster", xlabel="Clúster", ylabel="Cantidad de juegos")
    distribucion_fig = guardar_figura("09_distribucion_clusters.png")

    fig, ax = plt.subplots(figsize=(12, 6))
    perfil_plot = perfil.set_index("Nombre_Grupo")[["Ventas_Globales_Millones", "Cuota_NA", "Cuota_EU", "Cuota_JP"]]
    perfil_plot = perfil_plot / perfil_plot.max()
    perfil_plot.T.plot(kind="bar", ax=ax)
    ax.set(title="Perfil relativo de los grupos (normalizado por el máximo)", xlabel="Variable", ylabel="Valor relativo")
    ax.legend(title="Grupo", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    ax.tick_params(axis="x", rotation=0)
    perfil_fig = guardar_figura("10_perfil_relativo.png")

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    for ax, col in zip(axes.ravel(), FEATURES):
        sns.boxplot(data=limpio, x="Nombre_Grupo", y=col, ax=ax)
        ax.set(title=col, xlabel="", ylabel=col)
        ax.tick_params(axis="x", rotation=30, labelsize=8)
    box_fig = guardar_figura("11_comparacion_variables.png")

    figuras.update({"seleccion_k": curvas_fig, "pca": pca_fig, "dispersion": dispersion_fig,
                    "distribucion": distribucion_fig, "perfil": perfil_fig, "boxplots": box_fig})

    joblib.dump(modelo, MOD / "kmeans_final.joblib")
    joblib.dump(scaler, MOD / "scaler_final.joblib")

    resumen = {
        "registros_originales": int(len(df)),
        "registros_procesados": int(len(limpio)),
        "variables_originales": int(df.shape[1]),
        "variables_agrupamiento": FEATURES,
        "variables_comparacion": FEATURES_SIMPLES,
        "k_seleccionado": int(modelo.n_clusters),
        "semilla": SEED,
        "pca_varianza": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        "metricas": metricas.to_dict(orient="records"),
        "comparacion": comparacion.to_dict(orient="records"),
        "perfil": perfil.to_dict(orient="records"),
        "centroides": centroides_original.round(4).to_dict(orient="records"),
        "figuras": figuras,
        "medias_generales": {k: round(float(v), 4) for k, v in base.items()},
        "nombres_grupos": nombres,
        "nulos_originales": {k: int(v) for k, v in df.isna().sum().items() if v > 0},
        "duplicados_eliminados": int(pasos.iloc[1]["registros_afectados"] + pasos.iloc[2]["registros_afectados"]),
    }
    with open(BASE / "outputs" / "resumen.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    print(f"Registros procesados: {len(limpio)}")
    print(metricas.to_string(index=False))
    print(comparacion.to_string(index=False))
    print(perfil.to_string(index=False))
    print(f"Grupos: {nombres}")


if __name__ == "__main__":
    main()

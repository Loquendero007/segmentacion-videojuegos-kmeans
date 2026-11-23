import json
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE = Path(__file__).resolve().parents[1]
SALIDA = BASE / "docs" / "documentacion_proyecto.pdf"
TAB = BASE / "outputs" / "tablas"
FIG = BASE / "outputs" / "figures"

with open(BASE / "outputs" / "resumen.json", encoding="utf-8") as f:
    R = json.load(f)

perfil = pd.DataFrame(R["perfil"])
metricas = pd.DataFrame(R["metricas"])
comparacion = pd.DataFrame(R["comparacion"])
centroides = pd.DataFrame(R["centroides"])
limpieza = pd.read_csv(TAB / "06_limpieza_preparacion.csv")
estructura = pd.read_csv(TAB / "02_estructura_dataset.csv")

styles = getSampleStyleSheet()
titulo = ParagraphStyle("titulo", parent=styles["Title"], fontSize=23, leading=28, textColor=colors.HexColor("#1e3a8a"))
subtitulo = ParagraphStyle("subtitulo", parent=styles["Normal"], fontSize=13, leading=17, alignment=TA_CENTER, textColor=colors.HexColor("#475569"))
h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=15, leading=19, textColor=colors.HexColor("#1e3a8a"), spaceBefore=14, spaceAfter=7)
h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#0f766e"), spaceBefore=9, spaceAfter=5)
cuerpo = ParagraphStyle("cuerpo", parent=styles["BodyText"], fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=6)
nota = ParagraphStyle("nota", parent=cuerpo, fontSize=8.5, leading=11, textColor=colors.HexColor("#475569"))
celda = ParagraphStyle("celda", parent=styles["BodyText"], fontSize=7.6, leading=9.5, spaceAfter=0)
celda_head = ParagraphStyle("celda_head", parent=celda, textColor=colors.white, fontName="Helvetica-Bold")


def P(texto, estilo=cuerpo):
    return Paragraph(escape(str(texto)), estilo)


def tabla(df, anchos=None, max_filas=None, formato=None):
    datos = df if max_filas is None else df.head(max_filas)
    encabezados = [Paragraph(escape(str(c)), celda_head) for c in datos.columns]
    filas = []
    for _, fila in datos.iterrows():
        fila_txt = []
        for valor in fila:
            if isinstance(valor, float):
                valor = f"{valor:,.3f}".rstrip("0").rstrip(".")
            fila_txt.append(Paragraph(escape(str(valor)), celda))
        filas.append(fila_txt)
    t = Table([encabezados] + filas, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def figura(nombre, ancho=6.3, pie=""):
    ruta = FIG / nombre
    with Image.open(ruta) as img:
        w, h = img.size
    alto = ancho * h / w
    elementos = [RLImage(str(ruta), width=ancho * inch, height=alto * inch), Spacer(1, 4)]
    if pie:
        elementos.append(P(pie, nota))
    return KeepTogether(elementos)


def numero_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "Proyecto integrador · Segmentación de videojuegos con K-Means")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Página {doc.page}")
    canvas.restoreState()


elementos = []
elementos += [Spacer(1, 1.1 * inch), P("1. Portada", subtitulo), Spacer(1, 0.35 * inch), P("Proyecto Integrador de Minería de Datos", subtitulo), Spacer(1, 0.25 * inch)]
elementos += [P("Segmentación del mercado de videojuegos mediante K-Means y dashboard interactivo", titulo)]
elementos += [Spacer(1, 0.3 * inch), P("Temática: análisis de ventas y preferencias regionales de videojuegos", subtitulo), Spacer(1, 0.7 * inch)]
portada = [
    ["Nombre del proyecto", "Segmentación del mercado de videojuegos mediante K-Means"],
    ["Integrantes", "Proyecto individual (completar con el nombre del autor)"],
    ["Grupo", "Completar con el número de grupo"],
    ["Fecha", "23 de noviembre de 2026"],
]
elementos += [tabla(pd.DataFrame(portada, columns=["Campo", "Dato"]), anchos=[1.7 * inch, 4.7 * inch])]
elementos += [Spacer(1, 0.5 * inch), P("Documento elaborado con Python, Pandas, Scikit-learn, Matplotlib, Seaborn y Streamlit.", nota)]
elementos.append(PageBreak())

elementos.append(P("2. Introducción y planteamiento del problema", h1))
elementos.append(P(
    "La industria de los videojuegos genera grandes volúmenes de información sobre ventas por título, plataforma, género, "
    "editorial y región. Sin embargo, la simple observación de esos datos no permite distinguir qué títulos comparten "
    "comportamientos comerciales similares ni dónde se concentran sus ventas. Este proyecto aborda la necesidad de "
    "comprender la estructura del mercado a partir de datos históricos de ventas globales."))
elementos.append(P(
    "El problema se plantea como la dificultad para identificar patrones de comportamiento comercial en un catálogo de "
    f"{R['registros_originales']:,} videojuegos: algunos títulos son éxitos masivos y equilibrados entre regiones, otros "
    "venden casi exclusivamente en Japón y otros dependen de Norteamérica o Europa. La fragmentación del mercado dificulta "
    "la toma de decisiones de editoriales, distribuidores y analistas. La agrupación no supervisada permite descubrir esos "
    "perfiles sin usar etiquetas previas y traducirlos en segmentos accionables."))
elementos.append(P(
    "La importancia del proyecto radica en que transforma datos descriptivos en información útil para decidir dónde "
    "publicar, qué géneros priorizar y qué mercados requieren estrategias localizadas. Mediante K-Means se espera identificar "
    "agrupamientos por nivel de ventas, distribución regional (NA, EU, JP) y antigüedad del lanzamiento; posteriormente se "
    "interpretan sus centroides y se presentan en un dashboard interactivo de dos páginas."))

elementos.append(P("3. Objetivos", h1))
elementos.append(P("Objetivo general", h2))
elementos.append(P("Aplicar el algoritmo K-Means para segmentar videojuegos según su desempeño comercial y preferencia regional, e interpretar los resultados mediante un dashboard interactivo que apoye la toma de decisiones."))
elementos.append(P("Objetivos específicos", h2))
for objetivo in [
    "Explorar y caracterizar el dataset de ventas de videojuegos mediante estadísticas descriptivas y visualizaciones.",
    "Limpiar, transformar y escalar las variables relevantes para garantizar la calidad del agrupamiento.",
    "Evaluar distintos valores de K y seleccionar la configuración más adecuada con métricas internas.",
    "Interpretar los centroides y nombrar los grupos según sus características comerciales.",
    "Construir un dashboard interactivo con indicadores, filtros y visualizaciones de los segmentos.",
]:
    elementos.append(P("• " + objetivo))

elementos.append(P("4. Descripción del dataset", h1))
elementos.append(P(
    "Se utilizó el dataset público <i>Video Game Sales</i> (Gregory Smith, Kaggle), una recopilación de ventas de juegos con "
    "más de 100,000 copias obtenida de VGChartz. Está disponible en Zenodo (DOI 10.5281/zenodo.5898311) y en un espejo "
    "público de GitHub; la copia utilizada se incluye en <b>data/raw/vgsales.csv</b>. El archivo original contiene "
    f"{R['registros_originales']:,} registros y {R['variables_originales']} variables, con años entre 1980 y 2020. "
    f"Tras la limpieza quedaron {R['registros_procesados']:,} registros."))
variables = pd.DataFrame([
    ["Rank", "Numerica", "Posición en el ranking global de ventas"],
    ["Name", "Texto", "Nombre del videojuego"],
    ["Platform", "Categorica", "Plataforma de lanzamiento (PS2, Wii, DS, PC, ...)"],
    ["Year", "Numerica", "Año de lanzamiento; 271 valores ausentes"],
    ["Genre", "Categorica", "Género del juego (Action, Sports, Role-Playing, ...)"],
    ["Publisher", "Categorica", "Editorial; 58 valores 'Unknown' estandarizados"],
    ["NA_Sales / EU_Sales / JP_Sales / Other_Sales", "Numerica", "Ventas por región en millones de copias"],
    ["Global_Sales", "Numerica", "Ventas mundiales totales en millones de copias"],
], columns=["Variable", "Tipo", "Descripción"])
elementos.append(tabla(variables, anchos=[1.75 * inch, 0.85 * inch, 3.8 * inch]))
elementos.append(Spacer(1, 6))
elementos.append(P("Variables derivadas para el agrupamiento:", h2))
derivadas = pd.DataFrame([
    ["Log_Ventas_Globales", "log(1 + Global_Sales): atenúa la asimetría extrema de las ventas"],
    ["Cuota_NA / Cuota_EU / Cuota_JP", "Proporción de ventas de cada región respecto al total regional del juego"],
    ["Anio", "Año de lanzamiento imputado y convertido a entero"],
], columns=["Variable", "Definición"])
elementos.append(tabla(derivadas, anchos=[1.85 * inch, 4.55 * inch]))
elementos.append(P(
    "Estas cinco variables se seleccionaron porque, en conjunto, describen las dos dimensiones que se quieren separar: "
    "el tamaño comercial del título y su orientación geográfica. El logaritmo de ventas evita que unos pocos éxitos "
    "masivos dominen la distancia; las tres cuotas regionales capturan el perfil de mercado sin depender del volumen "
    "absoluto; y el año incorpora la evolución temporal del catálogo. Género, plataforma y editorial se dejaron fuera "
    "del entrenamiento por ser categóricas de alta cardinalidad, y se usaron únicamente para interpretar los grupos.", nota))

elementos.append(P("5. Desarrollo del proyecto", h1))
elementos.append(P("5.1 Limpieza y preparación", h2))
elementos.append(P(
    "Se normalizaron los textos (espacios y valores 'N/A'/'Unknown'), se convirtió Year a numérico y se imputaron los 271 "
    "años ausentes con la mediana (2007). Se eliminaron registros idénticos y juegos repetidos por combinación "
    "Nombre-Plataforma-Año, conservando la versión con mayores ventas. Las editoriales desconocidas se etiquetaron como "
    "'Desconocido'. Las ventas presentan valores atípicos extremos (máximo 82.74 M); en lugar de eliminarlos se aplicó "
    "logaritmo natural, una transformación que conserva la información y reduce su influencia. Finalmente se calcularon "
    "las cuotas regionales y se aplicó StandardScaler a las cinco variables de entrenamiento, dejando media 0 y desviación 1."))
elementos.append(tabla(limpieza, anchos=[4.9 * inch, 1.5 * inch]))
elementos.append(Spacer(1, 6))
elementos.append(P("5.2 Implementación de K-Means", h2))
elementos.append(P(
    "Se empleó <b>KMeans</b> de Scikit-learn con semilla 42 y n_init=25. Se evaluaron los valores K = 2, 3, 4, 5 y 6 con "
    "inercia, coeficiente de silueta, índice de Calinski-Harabasz e índice de Davies-Bouldin. Se seleccionó K = "
    f"{R['k_seleccionado']} por presentar la mayor silueta ({metricas['silueta'].max():.4f}). El modelo final se ajustó con "
    "fit_predict() para asignar un grupo a cada juego."))
elementos.append(tabla(metricas, anchos=[0.45 * inch, 1.05 * inch, 0.9 * inch, 1.35 * inch, 1.25 * inch, 1.4 * inch]))
elementos.append(Spacer(1, 6))
elementos.append(P("Comparación de dos configuraciones:", h2))
elementos.append(tabla(comparacion[["configuracion", "silueta", "calinski_harabasz", "davies_bouldin", "inercia"]],
                       anchos=[2.2 * inch, 0.9 * inch, 1.3 * inch, 1.2 * inch, 0.8 * inch]))
elementos.append(P(
    "La configuración B (3 variables) obtiene una silueta ligeramente superior porque separa con más nitidez los ejes de "
    "ventas, Japón y año, pero ignora la distinción entre Norteamérica y Europa. La configuración A (5 variables) tiene una "
    "silueta algo menor y mayor inercia por la dimensión adicional, aunque produce segmentos más interpretables y accionables; "
    "por esa razón se eligió para el análisis final.", nota))

elementos.append(PageBreak())
elementos.append(P("6. Resultados y análisis", h1))
elementos.append(P(
    f"El modelo final generó {R['k_seleccionado']} grupos con una silueta promedio de {metricas['silueta'].max():.3f} y un "
    f"índice de Davies-Bouldin de {float(metricas.loc[metricas['k'] == R['k_seleccionado'], 'davies_bouldin'].iat[0]):.3f}. "
    "La evolución de las métricas y la selección de K se muestran a continuación."))
elementos.append(figura("06_seleccion_k.png", pie="Figura 1. Inercia y silueta según el número de clústeres; la línea roja marca K=4."))
elementos.append(P("6.1 Centroides", h2))
elementos.append(tabla(centroides, anchos=[0.55 * inch, 1.85 * inch, 1.05 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.65 * inch]))
elementos.append(P(
    "Los centroides se expresan en unidades originales (inversión del escalamiento). El grupo 0 combina ventas altas con "
    "cuotas equilibradas; el grupo 1 casi no vende fuera de Japón; el grupo 2 depende fuertemente de Norteamérica y el grupo 3 "
    "de Europa, además de ser el más reciente.", nota))

elementos.append(P("6.2 Perfil y estadísticas por grupo", h2))
perfil_tabla = perfil[["Cluster", "Nombre_Grupo", "Registros", "Ventas_Globales_Millones", "Cuota_NA", "Cuota_EU", "Cuota_JP", "Anio"]]
elementos.append(tabla(perfil_tabla, anchos=[0.55 * inch, 1.65 * inch, 0.75 * inch, 0.9 * inch, 0.65 * inch, 0.6 * inch, 0.6 * inch, 0.65 * inch]))
elementos.append(Spacer(1, 8))
elementos.append(figura("09_distribucion_clusters.png", pie="Figura 2. Distribución de juegos por clúster."))
elementos.append(figura("07_clusters_pca.png", pie="Figura 3. Proyección PCA de los agrupamientos y sus centroides."))
elementos.append(figura("10_perfil_relativo.png", pie="Figura 4. Perfil relativo de los grupos por ventas y cuotas regionales."))

elementos.append(P("6.3 Interpretación de los agrupamientos", h2))
for _, f in perfil.iterrows():
    elementos.append(P(
        f"{f['Nombre_Grupo']} (clúster {int(f['Cluster'])}): {int(f['Registros']):,} juegos; "
        f"ventas promedio {f['Ventas_Globales_Millones']:.2f} M; cuotas NA {f['Cuota_NA']:.1%}, EU {f['Cuota_EU']:.1%}, "
        f"JP {f['Cuota_JP']:.1%}; año promedio {f['Anio']:.1f}; género típico {f['Genero_mas_frecuente']}."))

elementos.append(P("6.4 Hallazgos relevantes", h2))
datos = pd.read_csv(BASE / "data" / "processed" / "videojuegos_clusterizados.csv")
participacion = datos.groupby("Nombre_Grupo")["Ventas_Globales_Millones"].sum()
participacion = (participacion / participacion.sum() * 100).sort_values(ascending=False)
blk = [g for g in participacion.index if "Blockbusters" in g][0]
jap = [g for g in participacion.index if "japonés" in g][0]
eur = [g for g in participacion.index if "Europa" in g][0]
n_blk = int(perfil.loc[perfil["Nombre_Grupo"] == blk, "Registros"].iat[0])
for hallazgo in [
    f"El grupo {blk} concentra el {participacion[blk]:.1%} de las ventas totales con solo {n_blk / len(datos):.1%} de los títulos.",
    f"El grupo {jap} dirige el 96% de sus ventas a Japón, con un promedio bajo: es un nicho regional muy concentrado.",
    f"El grupo {eur} tiene los lanzamientos más recientes (2010.6 en promedio), frente a 2004.5 del grupo de blockbusters.",
    "Norteamérica sigue siendo el destino dominante para la mayor parte del catálogo (más de la mitad de los juegos).",
]:
    elementos.append(P("• " + hallazgo))

elementos.append(PageBreak())
elementos.append(P("7. Dashboard", h1))
elementos.append(P(
    "Se desarrolló un dashboard en Streamlit con dos páginas. Todas las visualizaciones se generan a partir del dataset "
    "procesado y de los resultados exportados por el pipeline de Python. El panel lateral incluye filtros funcionales de "
    "género, plataforma y rango de años, más un filtro de grupo en la página de segmentación."))
elementos.append(P("Página 1 · Análisis general", h2))
elementos.append(P(
    "Incluye cuatro KPI (juegos analizados, ventas globales, ventas promedio y año promedio), evolución anual de lanzamientos, "
    "ventas por región, top 10 de géneros y una tabla de estadísticas descriptivas que se actualiza con los filtros."))
elementos.append(figura("dashboard_pagina1.png", pie="Figura 5. Captura de la página de análisis general."))
elementos.append(P("Página 2 · Segmentación mediante K-Means", h2))
elementos.append(P(
    "Presenta cuatro KPI del modelo, distribución de registros por clúster, gráfico de dispersión año vs. ventas (el tamaño "
    "representa la cuota japonesa), diagramas de caja de ventas y barras de preferencia regional, tabla de estadísticas por "
    "grupo, descripciones desplegables, hallazgos, recomendaciones y la proyección PCA."))
elementos.append(figura("dashboard_pagina2.png", pie="Figura 6. Captura de la página de segmentación."))
elementos.append(P("Página de inicio", h2))
elementos.append(figura("dashboard_home.png", pie="Figura 7. Captura de la portada del dashboard."))

elementos.append(P("8. Conclusiones y recomendaciones", h1))
elementos.append(P("Conclusiones", h2))
elementos.append(P(
    "K-Means permitió separar el catálogo en cuatro perfiles comerciales bien diferenciados. El agrupamiento confirma que el "
    "éxito global es minoritario pero concentra la mayor parte de las ventas, mientras que el resto del catálogo se reparte "
    "entre mercados regionales muy específicos. El escalamiento y la transformación logarítmica fueron determinantes para evitar "
    "que unos pocos títulos dominaran la distancia euclidiana."))
elementos.append(P("Recomendaciones", h2))
for recomendacion in [
    "Priorizar propuestas con atractivo en Norteamérica y Europa y lanzamientos multiplataforma para acercarse al perfil de blockbusters.",
    "Mantener una línea de contenido localizado para Japón, especialmente de Rol y portátiles, aceptando volúmenes menores pero alta concentración regional.",
    "Fortalecer la distribución en PC y canales digitales en Europa, donde aparecen los títulos más recientes.",
    "Utilizar el dashboard con los filtros de género, plataforma y año para revisar cada segmento antes de decidir inversiones.",
]:
    elementos.append(P("• " + recomendacion))
elementos.append(P("Limitaciones", h2))
elementos.append(P(
    "El dataset finaliza en 2020 y no incluye ventas digitales, precios, críticas ni campañas de marketing. Las cifras de "
    "VGChartz son estimaciones. La imputación del año puede introducir ruido y K-Means asume clústeres esféricos, por lo que "
    "los resultados dependen de la escala, la semilla y las variables seleccionadas; las etiquetas de los grupos son una "
    "interpretación de los centroides, no una verdad absoluta."))

doc = SimpleDocTemplate(
    str(SALIDA), pagesize=letter,
    rightMargin=0.75 * inch, leftMargin=0.75 * inch,
    topMargin=0.75 * inch, bottomMargin=0.7 * inch,
    title="Segmentación de videojuegos con K-Means",
    author="Proyecto integrador",
)
doc.build(elementos, onFirstPage=numero_pagina, onLaterPages=numero_pagina)
print(f"PDF generado: {SALIDA}")

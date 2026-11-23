import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

BASE = Path(__file__).resolve().parents[1]
SALIDA = BASE / "docs" / "documentacion_proyecto.docx"
TAB = BASE / "outputs" / "tablas"
FIG = BASE / "outputs" / "figures"

with open(BASE / "outputs" / "resumen.json", encoding="utf-8") as f:
    R = json.load(f)

perfil = pd.DataFrame(R["perfil"])
metricas = pd.DataFrame(R["metricas"])
comparacion = pd.DataFrame(R["comparacion"])
centroides = pd.DataFrame(R["centroides"])
limpieza = pd.read_csv(TAB / "06_limpieza_preparacion.csv")
datos = pd.read_csv(BASE / "data" / "processed" / "videojuegos_clusterizados.csv")

doc = Document()
seccion = doc.sections[0]
seccion.left_margin = Inches(0.9)
seccion.right_margin = Inches(0.9)
seccion.top_margin = Inches(0.8)
seccion.bottom_margin = Inches(0.8)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.15

for nombre, color, size in [("Heading 1", RGBColor(30, 58, 138), 16), ("Heading 2", RGBColor(15, 118, 110), 12)]:
    estilo = doc.styles[nombre]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(size)
    estilo.font.color.rgb = color
    estilo.font.bold = True

pie = seccion.footer.paragraphs[0]
pie.text = "Proyecto integrador · Segmentación de videojuegos con K-Means · Página "
pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
pie.runs[0].font.size = Pt(8)
pie.runs[0].font.color.rgb = RGBColor(100, 116, 139)
campo = OxmlElement("w:fldSimple")
campo.set(qn("w:instr"), "PAGE")
pie._p.append(campo)


def parrafo(texto, estilo=None, centrado=False, cursiva=False):
    p = doc.add_paragraph(style=estilo)
    run = p.add_run(texto)
    run.italic = cursiva
    if centrado:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def lista(textos):
    for texto in textos:
        doc.add_paragraph(texto, style="List Bullet")


def sombrear(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def tabla_df(df, anchos=None):
    t = doc.add_table(rows=1, cols=len(df.columns))
    t.style = "Table Grid"
    for i, col in enumerate(df.columns):
        celda = t.rows[0].cells[i]
        celda.text = str(col)
        sombrear(celda, "1E3A8A")
        for run in celda.paragraphs[0].runs:
            run.font.bold = True
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(255, 255, 255)
    for _, fila in df.iterrows():
        celdas = t.add_row().cells
        for i, valor in enumerate(fila):
            if isinstance(valor, float):
                valor = f"{valor:,.3f}".rstrip("0").rstrip(".")
            celdas[i].text = str(valor)
            for run in celdas[i].paragraphs[0].runs:
                run.font.size = Pt(8.5)
    if anchos:
        for fila in t.rows:
            for i, ancho in enumerate(anchos):
                fila.cells[i].width = Inches(ancho)
    doc.add_paragraph()
    return t


def imagen(nombre, pie_texto, ancho=6.0):
    doc.add_picture(str(FIG / nombre), width=Inches(ancho))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(pie_texto, style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(100, 116, 139)


def salto():
    doc.add_page_break()


portada = pd.DataFrame([
    ["Nombre del proyecto", "Segmentación del mercado de videojuegos mediante K-Means"],
    ["Integrantes", "[Escribe aquí tu nombre o los nombres del equipo]"],
    ["Grupo", "[Escribe aquí el número de grupo]"],
    ["Fecha", "[Escribe aquí la fecha de entrega]"],
], columns=["Campo", "Dato"])

parrafo("1. Portada", "Heading 1")
parrafo("PROYECTO INTEGRADOR DE MINERÍA DE DATOS", centrado=True)
parrafo("Segmentación del mercado de videojuegos mediante K-Means y dashboard interactivo", "Heading 1")
parrafo("Temática: análisis de ventas y preferencias regionales de videojuegos", centrado=True, cursiva=True)
doc.add_paragraph()
tabla_df(portada, anchos=[2.0, 4.5])
parrafo("Esta portada es editable: reemplaza los marcadores entre corchetes con tus datos.", centrado=True, cursiva=True)
salto()

doc.add_heading("2. Introducción y planteamiento del problema", level=1)
parrafo(
    "La industria de los videojuegos genera grandes volúmenes de información sobre ventas por título, plataforma, género, "
    "editorial y región. Sin embargo, la simple observación de esos datos no permite distinguir qué títulos comparten "
    "comportamientos comerciales similares ni dónde se concentran sus ventas. Este proyecto aborda la necesidad de "
    "comprender la estructura del mercado a partir de datos históricos de ventas globales.")
parrafo(
    "El problema se plantea como la dificultad para identificar patrones de comportamiento comercial en un catálogo de "
    f"{R['registros_originales']:,} videojuegos: algunos títulos son éxitos masivos y equilibrados entre regiones, otros "
    "venden casi exclusivamente en Japón y otros dependen de Norteamérica o Europa. La fragmentación del mercado dificulta "
    "la toma de decisiones de editoriales, distribuidores y analistas. La agrupación no supervisada permite descubrir esos "
    "perfiles sin usar etiquetas previas y traducirlos en segmentos accionables.")
parrafo(
    "La importancia del proyecto radica en que transforma datos descriptivos en información útil para decidir dónde "
    "publicar, qué géneros priorizar y qué mercados requieren estrategias localizadas. Mediante K-Means se espera identificar "
    "agrupamientos por nivel de ventas, distribución regional (NA, EU, JP) y antigüedad del lanzamiento; posteriormente se "
    "interpretan sus centroides y se presentan en un dashboard interactivo de dos páginas.")

doc.add_heading("3. Objetivos", level=1)
doc.add_heading("Objetivo general", level=2)
parrafo("Aplicar el algoritmo K-Means para segmentar videojuegos según su desempeño comercial y preferencia regional, e interpretar los resultados mediante un dashboard interactivo que apoye la toma de decisiones.")
doc.add_heading("Objetivos específicos", level=2)
lista([
    "Explorar y caracterizar el dataset de ventas de videojuegos mediante estadísticas descriptivas y visualizaciones.",
    "Limpiar, transformar y escalar las variables relevantes para garantizar la calidad del agrupamiento.",
    "Evaluar distintos valores de K y seleccionar la configuración más adecuada con métricas internas.",
    "Interpretar los centroides y nombrar los grupos según sus características comerciales.",
    "Construir un dashboard interactivo con indicadores, filtros y visualizaciones de los segmentos.",
])

doc.add_heading("4. Descripción del dataset", level=1)
parrafo(
    "Se utilizó el dataset público Video Game Sales (Gregory Smith, Kaggle), una recopilación de ventas de juegos con más "
    "de 100,000 copias obtenida de VGChartz. Está disponible en Zenodo (DOI 10.5281/zenodo.5898311) y en un espejo público "
    "de GitHub; la copia utilizada se incluye en data/raw/vgsales.csv. El archivo original contiene "
    f"{R['registros_originales']:,} registros y {R['variables_originales']} variables, con años entre 1980 y 2020. "
    f"Tras la limpieza quedaron {R['registros_procesados']:,} registros.")
tabla_df(pd.DataFrame([
    ["Rank", "Numérica", "Posición en el ranking global de ventas"],
    ["Name", "Texto", "Nombre del videojuego"],
    ["Platform", "Categórica", "Plataforma de lanzamiento (PS2, Wii, DS, PC, ...)"],
    ["Year", "Numérica", "Año de lanzamiento; 271 valores ausentes"],
    ["Genre", "Categórica", "Género del juego (Action, Sports, Role-Playing, ...)"],
    ["Publisher", "Categórica", "Editorial; 58 valores 'Unknown' estandarizados"],
    ["NA/EU/JP/Other_Sales", "Numérica", "Ventas por región en millones de copias"],
    ["Global_Sales", "Numérica", "Ventas mundiales totales en millones de copias"],
], columns=["Variable", "Tipo", "Descripción"]), anchos=[1.8, 1.0, 3.7])
doc.add_heading("Variables derivadas", level=2)
tabla_df(pd.DataFrame([
    ["Log_Ventas_Globales", "log(1 + Global_Sales): atenúa la asimetría extrema de las ventas"],
    ["Cuota_NA / Cuota_EU / Cuota_JP", "Proporción de ventas de cada región respecto al total regional del juego"],
    ["Anio", "Año de lanzamiento imputado y convertido a entero"],
], columns=["Variable", "Definición"]), anchos=[2.1, 4.4])
parrafo(
    "Estas cinco variables se seleccionaron porque, en conjunto, describen las dos dimensiones que se quieren separar: "
    "el tamaño comercial del título y su orientación geográfica. El logaritmo de ventas evita que unos pocos éxitos "
    "masivos dominen la distancia; las tres cuotas regionales capturan el perfil de mercado sin depender del volumen "
    "absoluto; y el año incorpora la evolución temporal del catálogo. Género, plataforma y editorial se dejaron fuera "
    "del entrenamiento por ser categóricas de alta cardinalidad, y se usaron únicamente para interpretar los grupos.",
    cursiva=True)

doc.add_heading("5. Desarrollo del proyecto", level=1)
doc.add_heading("5.1 Limpieza y preparación", level=2)
parrafo(
    "Se normalizaron los textos (espacios y valores 'N/A'/'Unknown'), se convirtió Year a numérico y se imputaron los 271 "
    "años ausentes con la mediana (2007). Se eliminaron registros idénticos y juegos repetidos por combinación "
    "Nombre-Plataforma-Año, conservando la versión con mayores ventas. Las editoriales desconocidas se etiquetaron como "
    "'Desconocido'. Las ventas presentan valores atípicos extremos (máximo 82.74 M); en lugar de eliminarlos se aplicó "
    "logaritmo natural, una transformación que conserva la información y reduce su influencia. Finalmente se calcularon "
    "las cuotas regionales y se aplicó StandardScaler a las cinco variables de entrenamiento, dejando media 0 y desviación 1.")
tabla_df(limpieza, anchos=[5.0, 1.5])
doc.add_heading("5.2 Implementación de K-Means", level=2)
parrafo(
    "Se empleó KMeans de Scikit-learn con semilla 42 y n_init=25. Se evaluaron los valores K = 2, 3, 4, 5 y 6 con "
    "inercia, coeficiente de silueta, índice de Calinski-Harabasz e índice de Davies-Bouldin. Se seleccionó K = "
    f"{R['k_seleccionado']} por presentar la mayor silueta ({metricas['silueta'].max():.4f}). El modelo final se ajustó con "
    "fit_predict() para asignar un grupo a cada juego.")
tabla_df(metricas)
parrafo("Comparación de dos configuraciones:", "Heading 2")
tabla_df(comparacion[["configuracion", "silueta", "calinski_harabasz", "davies_bouldin", "inercia"]])
parrafo(
    "La configuración B (3 variables) obtiene una silueta ligeramente superior porque separa con más nitidez los ejes de "
    "ventas, Japón y año, pero ignora la distinción entre Norteamérica y Europa. La configuración A (5 variables) tiene una "
    "silueta algo menor y mayor inercia por la dimensión adicional, aunque produce segmentos más interpretables y accionables; "
    "por esa razón se eligió para el análisis final.", cursiva=True)

salto()
doc.add_heading("6. Resultados y análisis", level=1)
parrafo(
    f"El modelo final generó {R['k_seleccionado']} grupos con una silueta promedio de {metricas['silueta'].max():.3f} y un "
    f"índice de Davies-Bouldin de {float(metricas.loc[metricas['k'] == R['k_seleccionado'], 'davies_bouldin'].iat[0]):.3f}. "
    "La evolución de las métricas y la selección de K se muestran a continuación.")
imagen("06_seleccion_k.png", "Figura 1. Inercia y silueta según el número de clústeres; la línea roja marca K=4.")
doc.add_heading("6.1 Centroides", level=2)
tabla_df(centroides, anchos=[0.6, 1.8, 1.0, 0.8, 0.8, 0.8, 0.7])
parrafo(
    "Los centroides se expresan en unidades originales (inversión del escalamiento). El grupo 0 combina ventas altas con "
    "cuotas equilibradas; el grupo 1 casi no vende fuera de Japón; el grupo 2 depende fuertemente de Norteamérica y el grupo 3 "
    "de Europa, además de ser el más reciente.", cursiva=True)
doc.add_heading("6.2 Perfil y estadísticas por grupo", level=2)
tabla_df(perfil[["Cluster", "Nombre_Grupo", "Registros", "Ventas_Globales_Millones", "Cuota_NA", "Cuota_EU", "Cuota_JP", "Anio"]])
imagen("09_distribucion_clusters.png", "Figura 2. Distribución de juegos por clúster.")
imagen("07_clusters_pca.png", "Figura 3. Proyección PCA de los agrupamientos y sus centroides.")
imagen("10_perfil_relativo.png", "Figura 4. Perfil relativo de los grupos por ventas y cuotas regionales.")
doc.add_heading("6.3 Interpretación de los agrupamientos", level=2)
for _, f in perfil.iterrows():
    parrafo(
        f"{f['Nombre_Grupo']} (clúster {int(f['Cluster'])}): {int(f['Registros']):,} juegos; "
        f"ventas promedio {f['Ventas_Globales_Millones']:.2f} M; cuotas NA {f['Cuota_NA']:.1%}, EU {f['Cuota_EU']:.1%}, "
        f"JP {f['Cuota_JP']:.1%}; año promedio {f['Anio']:.1f}; género típico {f['Genero_mas_frecuente']}.")
doc.add_heading("6.4 Hallazgos relevantes", level=2)
participacion = datos.groupby("Nombre_Grupo")["Ventas_Globales_Millones"].sum()
participacion = (participacion / participacion.sum() * 100).sort_values(ascending=False)
blk = [g for g in participacion.index if "Blockbusters" in g][0]
jap = [g for g in participacion.index if "japonés" in g][0]
eur = [g for g in participacion.index if "Europa" in g][0]
n_blk = int(perfil.loc[perfil["Nombre_Grupo"] == blk, "Registros"].iat[0])
lista([
    f"El grupo {blk} concentra el {participacion[blk]:.1%} de las ventas totales con solo {n_blk / len(datos):.1%} de los títulos.",
    f"El grupo {jap} dirige el 96% de sus ventas a Japón, con un promedio bajo: es un nicho regional muy concentrado.",
    f"El grupo {eur} tiene los lanzamientos más recientes (2010.6 en promedio), frente a 2004.5 del grupo de blockbusters.",
    "Norteamérica sigue siendo el destino dominante para la mayor parte del catálogo (más de la mitad de los juegos).",
])

salto()
doc.add_heading("7. Dashboard", level=1)
parrafo(
    "Se desarrolló un dashboard en Streamlit con dos páginas. Todas las visualizaciones se generan a partir del dataset "
    "procesado y de los resultados exportados por el pipeline de Python. El panel lateral incluye filtros funcionales de "
    "género, plataforma y rango de años, más un filtro de grupo en la página de segmentación. El diseño aplica un tema "
    "oscuro con tipografía blanca.")
doc.add_heading("Página 1 · Análisis general", level=2)
parrafo(
    "Incluye cuatro KPI (juegos analizados, ventas globales, ventas promedio y año promedio), evolución anual de lanzamientos, "
    "ventas por región, top 10 de géneros y una tabla de estadísticas descriptivas que se actualiza con los filtros.")
imagen("dashboard_pagina1.png", "Figura 5. Captura de la página de análisis general.")
doc.add_heading("Página 2 · Segmentación mediante K-Means", level=2)
parrafo(
    "Presenta cuatro KPI del modelo, distribución de registros por clúster, gráfico de dispersión año vs. ventas (el tamaño "
    "representa la cuota japonesa), diagramas de caja de ventas y barras de preferencia regional, tabla de estadísticas por "
    "grupo, descripciones desplegables, hallazgos, recomendaciones y la proyección PCA.")
imagen("dashboard_pagina2.png", "Figura 6. Captura de la página de segmentación.")
doc.add_heading("Página de inicio", level=2)
imagen("dashboard_home.png", "Figura 7. Captura de la portada del dashboard.")

doc.add_heading("8. Conclusiones y recomendaciones", level=1)
doc.add_heading("Conclusiones", level=2)
parrafo(
    "K-Means permitió separar el catálogo en cuatro perfiles comerciales bien diferenciados. El agrupamiento confirma que el "
    "éxito global es minoritario pero concentra la mayor parte de las ventas, mientras que el resto del catálogo se reparte "
    "entre mercados regionales muy específicos. El escalamiento y la transformación logarítmica fueron determinantes para evitar "
    "que unos pocos títulos dominaran la distancia euclidiana.")
doc.add_heading("Recomendaciones", level=2)
lista([
    "Priorizar propuestas con atractivo en Norteamérica y Europa y lanzamientos multiplataforma para acercarse al perfil de blockbusters.",
    "Mantener una línea de contenido localizado para Japón, especialmente de Rol y portátiles, aceptando volúmenes menores pero alta concentración regional.",
    "Fortalecer la distribución en PC y canales digitales en Europa, donde aparecen los títulos más recientes.",
    "Utilizar el dashboard con los filtros de género, plataforma y año para revisar cada segmento antes de decidir inversiones.",
])
doc.add_heading("Limitaciones", level=2)
parrafo(
    "El dataset finaliza en 2020 y no incluye ventas digitales, precios, críticas ni campañas de marketing. Las cifras de "
    "VGChartz son estimaciones. La imputación del año puede introducir ruido y K-Means asume clústeres esféricos, por lo que "
    "los resultados dependen de la escala, la semilla y las variables seleccionadas; las etiquetas de los grupos son una "
    "interpretación de los centroides, no una verdad absoluta.")

doc.save(str(SALIDA))
print(f"DOCX generado: {SALIDA}")

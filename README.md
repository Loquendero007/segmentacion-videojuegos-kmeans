# Segmentación del mercado de videojuegos mediante K-Means

Proyecto integrador de minería de datos: análisis exploratorio, limpieza, agrupamiento no supervisado con **K-Means** y un **dashboard interactivo** de dos páginas construido con **Streamlit**.

## Temática y problema

La industria del videojuego concentra millones de títulos con comportamientos comerciales muy distintos. Este proyecto responde a la pregunta: **¿qué perfiles de ventas y preferencias regionales existen en un catálogo global de videojuegos y cómo pueden utilizarse para apoyar decisiones editoriales y de distribución?**

Los grupos que se buscan identificar son: títulos con éxito global, juegos con ventas concentradas en Japón, juegos dependientes de Norteamérica y juegos con predominio europeo/reciente.

## Objetivos

- Explorar el dataset con estadísticas descriptivas y gráficas.
- Limpiar, transformar y escalar las variables relevantes.
- Evaluar varios valores de K y justificar la configuración final.
- Interpretar centroides, nombrar los grupos y extraer recomendaciones.
- Publicar los resultados en un dashboard interactivo reproducible.

## Dataset

- **Fuente:** *Video Game Sales* (Gregory Smith, Kaggle), scraped de VGChartz.
- **Referencia pública:** [Zenodo DOI 10.5281/zenodo.5898311](https://doi.org/10.5281/zenodo.5898311) · [espejo en GitHub](https://github.com/molatosekgobela/Data-Science-Video-games-sales-dataset).
- **Original:** 16,598 filas y 11 columnas (1980-2020).
- **Procesado:** 16,596 filas con el clúster y el nombre del grupo asignados.
- **Variables de agrupamiento:** `Log_Ventas_Globales`, `Cuota_NA`, `Cuota_EU`, `Cuota_JP`, `Anio` (estandarizadas con `StandardScaler`).

## Resultados principales

- K seleccionado: **4** (mayor coeficiente de silueta: **0.4326**).
- Grupos: **Blockbusters globales**, **Fenómeno japonés**, **Favoritos de Norteamérica** y **Favoritos de Europa**.
- El grupo de blockbusters concentra aproximadamente dos tercios de las ventas totales con poco más del 10% de los juegos.
- Se comparó la configuración de 5 variables contra una de 3 variables; la de 5 variables se eligió por generar segmentos más interpretables.

## Estructura del repositorio

```text
segmentacion-videojuegos/
├── README.md                       Descripción e instrucciones
├── requirements.txt                Dependencias
├── data/
│   ├── raw/vgsales.csv             Dataset original
│   └── processed/                  Dataset con clústeres asignados
├── src/
│   ├── pipeline.py                 EDA, limpieza, K-Means y exportación
│   ├── generar_documento.py        Generación del PDF
│   └── capturar_dashboard.py       Capturas automáticas (opcional)
├── dashboard/
│   ├── app.py                      Página de inicio
│   ├── utils.py                    Carga de datos, filtros y gráficas
│   └── pages/
│       ├── 1_Analisis_general.py   Página 1
│       └── 2_Segmentacion_KMeans.py Página 2
├── outputs/
│   ├── figures/                    Gráficas y capturas del dashboard
│   ├── tablas/                     Tablas de EDA, métricas y centroides
│   ├── modelos/                    Modelo y scaler serializados
│   └── resumen.json                Resultados consumidos por el dashboard
└── docs/
    └── documentacion_proyecto.docx Documento editable (Word) del proyecto
```

## Instalación y ejecución

```bash
pip install -r requirements.txt
python src/pipeline.py
python src/generar_documento.py   # regenera el DOCX
streamlit run dashboard/app.py
```

El dashboard se abre en `http://localhost:8501`. En el menú lateral se encuentran los filtros de género, plataforma y rango de años; en la página de segmentación se añade el filtro por grupo.

Para regenerar las capturas del dashboard (requiere Google Chrome y el servidor de Streamlit ejecutándose):

```bash
python src/capturar_dashboard.py
```

## Herramientas

Python · Pandas · NumPy · Scikit-learn · Matplotlib · Seaborn · Streamlit · Altair · ReportLab

## Integrantes

Proyecto individual. Editar la portada del DOCX con tu nombre, grupo y fecha antes de entregar.

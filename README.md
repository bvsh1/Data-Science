# Detección de DDoS en redes IoMT y generalización entre dominios de red

Proyecto semestral de **Data Science (CIT3620, Universidad Diego Portales, 2026-2)**.
Nicolás Cerda · Juan José Cortés · Sebastián Navarrete · Javiera Sepúlveda.

El proyecto sigue la metodología **CRISP-DM** y estudia si un detector de ataques DDoS entrenado en una red sigue funcionando en otra.

## Problema y pregunta guía

En un hospital, los dispositivos médicos conectados (IoMT) dependen de la red para enviar la telemetría de los pacientes, y un ataque DDoS puede cortarla. Un detector entrenado en un tipo de red y desplegado en otra enfrenta dos cambios:

- **Domain shift:** cambia la distribución de las variables (otros dispositivos, protocolos y herramienta de captura).
- **Concept drift:** cambia la relación entre variables y ataque (otro día, otra red u otro tipo de ataque).

**Pregunta guía:** ¿cuánto rinde un detector fuera de su red de origen, y qué variables del tráfico se mantienen estables entre redes?

### Objetivos específicos

1. Homologar las variables de ambos dominios.
2. Entrenar modelos de clasificación binaria y multiclase.
3. Establecer una línea base dentro de cada dominio.
4. Medir la degradación del desempeño entre dominios.
5. Comparar con métricas adecuadas al desbalance (F1 macro, recall por clase, tasa de falsos positivos).
6. Identificar las variables estables entre dominios.

## Datos

| Dataset | Rol | Clases usadas |
|---|---|---|
| [CICIoMT2024](https://www.unb.ca/cic/datasets/iomt-dataset-2024.html) (Wi‑Fi/MQTT) | Dominio IoMT | Benigno, DDoS SYN, DDoS UDP, DDoS MQTT (Publish Flood) y DDoS ICMP |
| [CIC-DDoS2019](https://www.unb.ca/cic/datasets/ddos-2019.html) (03-11) | Dominio de red tradicional | Benigno, SYN flood, UDP flood |

| `clase` | Tráfico | Desde | ¿Existe en CIC-DDoS2019? |
|---|---|---|---|
| 0 | Benigno | Presentación 2 | Sí |
| 1 | DDoS SYN | Presentación 2 | Sí |
| 2 | DDoS UDP | Presentación 2 | Sí |
| 3 | DDoS MQTT (MQTT Publish Flood) | Etapa III | No |
| 4 | DDoS ICMP (ICMP flood) | Etapa III | No |

Los modelos dentro de IoMT usan las cinco clases (de MQTT e ICMP se toma una muestra de hasta 200.000 flujos cada uno). La evaluación cruzada entre redes usa solo las clases 0 a 2, que son las que existen en ambos datasets. Para volver a las tres clases de la Presentación 2, definir la variable de entorno `NIDS_ATAQUES_NUEVOS=0` antes de abrir Jupyter.

En IoMT se usan la partición de entrenamiento (80 % entrenamiento y 20 % validación, estratificado) y la **prueba oficial**, que es una captura separada y solo se usa al final. Los CSV no se versionan: `DESCARGA_DATOS.txt` explica qué archivos descargar y dónde guardarlos.

## Resultados principales

Resultados de la Presentación 2 (tres clases: benigno, SYN y UDP). Al ejecutar con las cinco clases, las cifras dentro de IoMT cambian; la evaluación cruzada no cambia porque usa las mismas tres clases.

| Resultado | Valor |
|---|---|
| Modelo final (elegido por F1 macro en validación) | LightGBM |
| F1 macro en la prueba oficial, binaria / multiclase | 0,9967 / 0,9973 |
| Falsas alarmas y ataques no detectados, prueba binaria | 0 de 37.607 y 456 de 378.051 |
| F1 macro multiclase, IoMT → red tradicional | 0,672 (caída de 0,32) |
| F1 macro multiclase, red tradicional → IoMT | 0,343 (caída de 0,65) |
| Variables estables entre redes | Proporción TCP/UDP y banderas FIN, CWR y ECE |
| Variables inestables entre redes | Longitudes de paquete, tasa de paquetes y bandera ACK |

Dentro de IoMT el problema es casi separable (un árbol de profundidad 2 con el tamaño medio del paquete ya logra 0,993 de exactitud balanceada), pero el detector pierde entre un tercio y dos tercios de su F1 macro en otra red, porque depende de variables que cambian entre redes y extractores.

## Estructura del repositorio

```text
├── data/
│   ├── raw/                  # CSV originales (no versionados, ver DESCARGA_DATOS.txt)
│   └── processed/            # Particiones y variables generadas por los notebooks 01 y 02
├── notebooks/
│   ├── 01_eda_and_cleaning.ipynb        # Calidad de datos, limpieza y EDA
│   ├── 02_preprocessing_fe.ipynb        # Partición, selección de variables y pesos de clase
│   ├── 03_baseline_models.ipynb         # Línea base: clase mayoritaria, regresión logística y árbol (Etapa II)
│   ├── 04_final_models_eval.ipynb       # Ensambles, modelo final, estabilidad y evaluación cruzada (Etapa III)
│   ├── 05_neural_network_mlp.ipynb      # Red neuronal MLP como alternativa no basada en árboles
│   └── 06_revision_y_ataque_no_visto.ipynb  # Filas repetidas y detector entrenado sin/con MQTT e ICMP
├── src/
│   ├── data_loader.py        # Carga y limpieza de CICIoMT2024 y CIC-DDoS2019
│   ├── features.py           # Selección de variables, preprocesamiento y homologación
│   ├── evaluate.py           # Métricas y gráficos
│   ├── evaluar_red_neuronal.py
│   ├── preparar_datos.py     # Alternativa a los notebooks 01 y 02 desde un parquet consolidado
│   ├── aplicar_split_80_20.py       # Experimento descartado (ver abajo)
│   └── reentrenar_cost_sensitive.py # Experimento descartado (ver abajo)
├── deliverables/
│   ├── figuras/              # Figuras exportadas de los notebooks
│   └── resultados/           # Tablas de métricas en CSV
├── app/app.html              # Dashboard interactivo (generado con build_app.py)
├── models/                   # Modelos entrenados (.joblib)
├── DESCARGA_DATOS.txt
└── requirements.txt
```

## Cómo reproducir

1. Instalar Python 3.12 y las dependencias:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Descargar los datos según `DESCARGA_DATOS.txt`, incluidos los ataques MQTT e ICMP (sección 6). Si los datos están en otra carpeta, se puede indicar con la variable de entorno `NIDS_DATA_DIR`, que debe apuntar a la carpeta que contiene `raw/`. Si todavía no se descargan MQTT e ICMP, usar `NIDS_ATAQUES_NUEVOS=0`:
   ```bash
   NIDS_DATA_DIR="/ruta/a/data" jupyter lab                         # cinco clases
   NIDS_DATA_DIR="/ruta/a/data" NIDS_ATAQUES_NUEVOS=0 jupyter lab   # tres clases (Presentación 2)
   ```
3. Ejecutar los notebooks en orden: 01 → 02 → 03 → 04 → 05 → 06. Los notebooks 01 y 02 generan `data/processed/`; el 04 puede tardar varios minutos por la búsqueda de hiperparámetros.

## Experimentos descartados

`src/aplicar_split_80_20.py` y `src/reentrenar_cost_sensitive.py` unen la prueba oficial con el entrenamiento y la vuelven a partir al azar (además de aplicar pesos de costo y calibrar el umbral). Con esa partición LightGBM llega a 0 errores, pero la prueba deja de ser una captura independiente y puede haber filas idénticas en entrenamiento y prueba, así que el resultado mide memoria de la captura y no generalización. Se conservan como iteración descartada y solo se ejecutan con `--confirmar`, porque sobrescriben `data/processed/` y tablas de `deliverables/resultados/`. Si se ejecutaron, basta con volver a correr los notebooks 01 y 02 para recuperar la partición original.

> **Ojo:** los archivos de `data/processed/` y `models/` que se subieron junto con el experimento de la rama `Prueba-con-MLP` corresponden a esa partición mezclada. Al ejecutar los notebooks 01, 02 y 04 se regeneran con la partición original, que es la que usan los resultados reportados.

## Fuentes de datos

Canadian Institute for Cybersecurity, University of New Brunswick: CICIoMT2024 y CIC-DDoS2019. Consultar las páginas oficiales para los requisitos de uso y citación.

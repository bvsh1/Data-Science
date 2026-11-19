"""Aplica una partición unificada y estratificada 80/20 sobre la totalidad de los datos.

Combina los flujos limpios de CICIoMT2024 (1,013,950 registros) y genera:
- 80% Conjunto de desarrollo (Train + Val)
  - Train: 85% de desarrollo (~689,486 flujos)
  - Val: 15% de desarrollo (~121,674 flujos)
- 20% Prueba oficial (Test: 202,790 flujos)
"""

# ---------------------------------------------------------------------------
# AVISO (Etapa III): este experimento NO se usa en los resultados finales.
# Mezcla la prueba oficial (captura separada y sin deduplicar) con el
# entrenamiento y la vuelve a partir al azar, por lo que la prueba deja de ser
# independiente y puede haber filas idénticas en ambos lados. Además
# sobrescribe data/processed/ y tablas de deliverables/resultados/.
# Se conserva como iteración descartada; para ejecutarlo hay que pedirlo
# explícitamente con --confirmar.
# ---------------------------------------------------------------------------


import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.data_loader import (
    CARPETA_PROCESADOS, CLASES,
    cargar_procesado, guardar_procesado, guardar_variables, cargar_variables
)

SEMILLA = 42

def regenerar_particiones_80_20():
    print("=" * 80)
    print("APLICANDO PARTICIÓN ESTRATIFICADA UNIFICADA 80/20")
    print("=" * 80)

    cfg = cargar_variables()
    variables = cfg["variables"]

    # Cargar datos procesados actuales
    print("\n1. Cargando datos existentes...")
    train_antiguo = cargar_procesado("train")
    val_antiguo = cargar_procesado("val")
    test_antiguo = cargar_procesado("test")

    df_total = pd.concat([train_antiguo, val_antiguo, test_antiguo], ignore_index=True)
    print(f"Total de registros limpios combinados: {len(df_total):,}")

    print("\nDistribución global de clases:")
    for k, nombre in CLASES.items():
        n = (df_total["clase"] == k).sum()
        pct = n / len(df_total) * 100
        print(f"  Clase {k} ({nombre:9s}): {n:7,} ({pct:5.2f}%)")

    # 1. Separar 80% Train+Val y 20% Test
    print("\n2. Realizando división estratificada 80% Desarrollo / 20% Prueba...")
    dev_df, test_df = train_test_split(
        df_total,
        test_size=0.20,
        stratify=df_total["clase"],
        random_state=SEMILLA,
    )

    # 2. Separar el 80% en 85% Train y 15% Val para ajuste de hiperparámetros/umbrales
    train_df, val_df = train_test_split(
        dev_df,
        test_size=0.15,
        stratify=dev_df["clase"],
        random_state=SEMILLA,
    )

    print(f"\nNuevas particiones generadas:")
    print(f"  - Train : {len(train_df):,} registros ({len(train_df)/len(df_total)*100:.1f}%)")
    print(f"  - Val   : {len(val_df):,} registros ({len(val_df)/len(df_total)*100:.1f}%)")
    print(f"  - Test  : {len(test_df):,} registros ({len(test_df)/len(df_total)*100:.1f}%) [20.0% estricto]")

    # Guardar particiones en parquet
    conjuntos = {
        "train": train_df.reset_index(drop=True),
        "val": val_df.reset_index(drop=True),
        "test": test_df.reset_index(drop=True),
    }

    print("\n3. Guardando nuevos archivos parquet...")
    for nombre, datos in conjuntos.items():
        ruta = guardar_procesado(datos, nombre)
        print(f"  Guardado {nombre:5s}: {datos.shape} en {ruta}")

    # Ponderación sensible al costo (Cost-Sensitive)
    # Se penaliza 4x el error de ataque en binaria y 4x el error en SYN
    pesos_bin = {0: 1.0, 1: 4.0}
    pesos_mul = {0: 1.0, 1: 4.0, 2: 1.5}

    cfg["pesos_binaria"] = pesos_bin
    cfg["pesos_multiclase"] = pesos_mul
    cfg["particion"] = "estratificada_80_20"
    cfg["tamano_train"] = len(train_df)
    cfg["tamano_val"] = len(val_df)
    cfg["tamano_test"] = len(test_df)
    
    guardar_variables(cfg)
    print("Configuración actualizada en variables.json.")
    print("=" * 80)
    print("Partición 80/20 completada exitosamente.")

if __name__ == "__main__":
    if "--confirmar" not in sys.argv:
        sys.exit(
            "Experimento descartado: sobrescribe data/processed/ y deliverables/resultados/.\n"
            "Si de verdad quieres ejecutarlo: python src/aplicar_split_80_20.py --confirmar\n"
            "Para volver a la partición original, ejecuta los notebooks 01 y 02."
        )
    regenerar_particiones_80_20()

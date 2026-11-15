"""Evaluación de Red Neuronal (Perceptrón Multicapa - MLP) para detección de intrusiones.

Compara la red neuronal con los modelos basados en árboles (Decision Tree, Random Forest,
LightGBM, XGBoost) y la regresión logística en las tareas binaria y multiclase.
"""

from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

from src.data_loader import (
    CARPETA_PROCESADOS, CARPETA_RESULTADOS, CLASES,
    cargar_procesado, cargar_variables
)
from src.features import preprocesador
from src.evaluate import (
    configurar_graficos, metricas_binarias, metricas_multiclase, puntaje_ataque
)

SEMILLA = 42

def entrenar_evaluar_mlp():
    print("=" * 70)
    print("INICIANDO EVALUACIÓN DE RED NEURONAL (MLP) PARA DETECCIÓN DE ATAQUES")
    print("=" * 70)

    # 1. Cargar datos procesados
    print("\n1. Cargando datos...")
    cfg = cargar_variables()
    variables = cfg["variables"]
    print(f"Número de características de entrada: {len(variables)}")

    train = cargar_procesado("train")
    val = cargar_procesado("val")
    test = cargar_procesado("test")

    print(f"Train: {train.shape[0]} | Val: {val.shape[0]} | Test: {test.shape[0]}")

    # Submuestra estratificada para entrenamiento rápido y eficiente de la red neuronal
    # 100,000 muestras proporcionan alta convergencia y representatividad estadística
    MUESTRA_TRAIN = 100_000
    if len(train) > MUESTRA_TRAIN:
        from sklearn.model_selection import train_test_split
        muestra_train, _ = train_test_split(
            train,
            train_size=MUESTRA_TRAIN,
            stratify=train["clase"],
            random_state=SEMILLA,
        )
    else:
        muestra_train = train

    print(f"Muestra de entrenamiento para MLP: {len(muestra_train)} registros")

    # 2. Definición del Pipeline con MLP
    # Arquitectura: 2 capas ocultas (128, 64 neuronas) con activación ReLU y regularización L2
    mlp_binario = Pipeline([
        ("preprocesador", preprocesador(escalar=True)),
        ("mlp", MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            solver="adam",
            alpha=0.001,
            batch_size=512,
            learning_rate_init=0.001,
            max_iter=60,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=8,
            random_state=SEMILLA,
            verbose=False,
        ))
    ])

    mlp_multi = Pipeline([
        ("preprocesador", preprocesador(escalar=True)),
        ("mlp", MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            solver="adam",
            alpha=0.001,
            batch_size=512,
            learning_rate_init=0.001,
            max_iter=60,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=8,
            random_state=SEMILLA,
            verbose=False,
        ))
    ])

    # -----------------------------------------------------------------------
    # TAREA 1: CLASIFICACIÓN BINARIA (Tráfico Benigno vs Ataque DDoS)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TAREA 1: CLASIFICACIÓN BINARIA (Benigno [0] vs Ataque DDoS [1])")
    print("=" * 70)

    t0 = time.perf_counter()
    mlp_binario.fit(muestra_train[variables], muestra_train["etiqueta"])
    t_train_bin = time.perf_counter() - t0
    print(f"Entrenamiento completado en {t_train_bin:.2f} s")

    # Inferencia en Test oficial
    t0 = time.perf_counter()
    pred_bin_test = mlp_binario.predict(test[variables])
    t_inf_bin = time.perf_counter() - t0
    proba_bin_test = mlp_binario.predict_proba(test[variables])[:, 1]

    metricas_bin_test = metricas_binarias(
        test["etiqueta"],
        pred_bin_test,
        puntaje=proba_bin_test,
        clase_real=test["clase"]
    )

    print("\nMétricas Binarias en Prueba Oficial (Test - 415,658 flujos):")
    for k, v in metricas_bin_test.items():
        if isinstance(v, float):
            print(f"  {k:25s}: {v:.6f}")
        else:
            print(f"  {k:25s}: {v}")
    print(f"  Tiempo inferencia total  : {t_inf_bin:.2f} s ({t_inf_bin/len(test)*1e6:.2f} µs/flujo)")

    # -----------------------------------------------------------------------
    # TAREA 2: CLASIFICACIÓN MULTICLASE (Benigno vs DDoS SYN vs DDoS UDP)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TAREA 2: CLASIFICACIÓN MULTICLASE (0: Benigno, 1: DDoS SYN, 2: DDoS UDP)")
    print("=" * 70)

    t0 = time.perf_counter()
    mlp_multi.fit(muestra_train[variables], muestra_train["clase"])
    t_train_mul = time.perf_counter() - t0
    print(f"Entrenamiento completado en {t_train_mul:.2f} s")

    # Inferencia en Test oficial
    t0 = time.perf_counter()
    pred_mul_test = mlp_multi.predict(test[variables])
    t_inf_mul = time.perf_counter() - t0

    metricas_mul_test = metricas_multiclase(test["clase"], pred_mul_test)

    print("\nMétricas Multiclase en Prueba Oficial (Test - 415,658 flujos):")
    for k, v in metricas_mul_test.items():
        if isinstance(v, float):
            print(f"  {k:25s}: {v:.6f}")
        else:
            print(f"  {k:25s}: {v}")
    print(f"  Tiempo inferencia total  : {t_inf_mul:.2f} s ({t_inf_mul/len(test)*1e6:.2f} µs/flujo)")

    # Matriz de confusión multiclase
    cm = confusion_matrix(test["clase"], pred_mul_test, labels=[0, 1, 2])
    print("\nMatriz de Confusión (Filas: Real, Columnas: Predicho):")
    print(f"               Pred Benigno  Pred SYN  Pred UDP")
    for i, nombre in CLASES.items():
        print(f"  Real {nombre:9s}: {cm[i][0]:12d} {cm[i][1]:9d} {cm[i][2]:9d}")

    # -----------------------------------------------------------------------
    # COMPARATIVA GENERAL: MLP vs ÁRBOLES Y LÍNEA BASE
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TABLA COMPARATIVA: RED NEURONAL (MLP) VS ÁRBOLES Y LÍNEA BASE")
    print("=" * 70)

    # Cargar métricas existentes de árboles
    ruta_ensambles = CARPETA_RESULTADOS / "metricas_multiclase_ensambles_test.csv"
    ruta_base = CARPETA_RESULTADOS / "metricas_multiclase_base_prueba_oficial.csv"

    filas_comparativa = []
    if ruta_base.exists():
        df_base = pd.read_csv(ruta_base)
        for _, row in df_base.iterrows():
            if row["Modelo"] != "Clase mayoritaria":
                filas_comparativa.append(row.to_dict())

    if ruta_ensambles.exists():
        df_ens = pd.read_csv(ruta_ensambles)
        for _, row in df_ens.iterrows():
            filas_comparativa.append(row.to_dict())

    # Agregar Red Neuronal (MLP)
    fila_mlp = {
        "Modelo": "Red Neuronal (MLP)",
        "Accuracy": metricas_mul_test["Accuracy"],
        "Precision macro": metricas_mul_test["Precision macro"],
        "Recall macro": metricas_mul_test["Recall macro"],
        "F1 macro": metricas_mul_test["F1 macro"],
        "Recall Benigno": metricas_mul_test["Recall Benigno"],
        "Recall DDoS SYN": metricas_mul_test["Recall DDoS SYN"],
        "Recall DDoS UDP": metricas_mul_test["Recall DDoS UDP"],
        "Tasa falsos positivos": metricas_mul_test["Tasa falsos positivos"],
    }
    filas_comparativa.append(fila_mlp)

    df_comp = pd.DataFrame(filas_comparativa).set_index("Modelo")
    print(df_comp.to_string())

    # Guardar resultados
    ruta_salida = CARPETA_RESULTADOS / "metricas_red_neuronal_mlp_test.csv"
    pd.DataFrame([fila_mlp]).to_csv(ruta_salida, index=False)
    print(f"\nResultados guardados en: {ruta_salida}")

    ruta_comp_completa = CARPETA_RESULTADOS / "comparacion_general_arboles_vs_mlp.csv"
    df_comp.reset_index().to_csv(ruta_comp_completa, index=False)
    print(f"Comparativa completa guardada en: {ruta_comp_completa}")

    return df_comp

if __name__ == "__main__":
    entrenar_evaluar_mlp()

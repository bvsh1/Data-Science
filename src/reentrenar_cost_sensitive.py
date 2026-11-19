"""Reentrenamiento de modelos con Aprendizaje Sensible al Costo (Cost-Sensitive Learning)
y calibración de umbrales operativos (Threshold Tuning) para minimizar los ataques no detectados.
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

import time
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

from src.data_loader import (
    CARPETA_MODELOS, CARPETA_RESULTADOS, CLASES,
    cargar_procesado, cargar_variables,
)
from src.features import preprocesador
from src.evaluate import (
    evaluar, calcular_umbral_optimo, predecir_con_umbral,
    metricas_binarias, metricas_multiclase, puntaje_ataque, guardar_tabla
)

SEMILLA = 42

def obtener_modelos_base():
    """Definición de modelos con hiperparámetros óptimos."""
    return {
        "Regresión logística": Pipeline([
            ("prep", preprocesador(escalar=True)),
            ("modelo", LogisticRegression(max_iter=500, random_state=SEMILLA)),
        ]),
        "Árbol de decisión": Pipeline([
            ("prep", preprocesador(escalar=False)),
            ("modelo", DecisionTreeClassifier(max_depth=20, min_samples_leaf=2, random_state=SEMILLA)),
        ]),
        "Random Forest": Pipeline([
            ("prep", preprocesador(escalar=False)),
            ("modelo", RandomForestClassifier(
                n_estimators=100, max_depth=25, min_samples_leaf=1,
                max_features="sqrt", n_jobs=-1, random_state=SEMILLA
            )),
        ]),
        "LightGBM": Pipeline([
            ("prep", preprocesador(escalar=False)),
            ("modelo", LGBMClassifier(
                n_estimators=180, learning_rate=0.20, num_leaves=40,
                min_child_samples=50, subsample=0.75, colsample_bytree=0.75,
                n_jobs=-1, random_state=SEMILLA, verbose=-1
            )),
        ]),
        "XGBoost": Pipeline([
            ("prep", preprocesador(escalar=False)),
            ("modelo", XGBClassifier(
                n_estimators=180, learning_rate=0.20, max_depth=6,
                min_child_weight=2, subsample=0.75, colsample_bytree=0.70,
                tree_method="hist", n_jobs=-1, random_state=SEMILLA
            )),
        ]),
        "Red Neuronal (MLP)": Pipeline([
            ("prep", preprocesador(escalar=True)),
            ("modelo", MLPClassifier(
                hidden_layer_sizes=(128, 64), activation="relu", solver="adam",
                alpha=0.001, batch_size=512, max_iter=50, early_stopping=True,
                validation_fraction=0.1, n_iter_no_change=8, random_state=SEMILLA
            )),
        ]),
    }

def main():
    print("=" * 80)
    print("REENTRENAMIENTO SENSIBLE AL COSTO (COST-SENSITIVE) Y AJUSTE DE UMBRALES")
    print("=" * 80)

    cfg = cargar_variables()
    variables = cfg["variables"]
    pesos_bin = cfg.get("pesos_binaria", {0: 1.0, 1: 4.0})
    pesos_mul = cfg.get("pesos_multiclase", {0: 1.0, 1: 4.0, 2: 1.5})
    # Asegurar claves enteras
    pesos_bin = {int(k): float(v) for k, v in pesos_bin.items()}
    pesos_mul = {int(k): float(v) for k, v in pesos_mul.items()}

    print(f"\nCaracterísticas de entrada: {len(variables)}")
    print(f"Ponderación de costos (Binaria)   : {pesos_bin} (Ataque penalizado {pesos_bin[1]/pesos_bin[0]:.1f}x)")
    print(f"Ponderación de costos (Multiclase): {pesos_mul} (SYN penalizado {pesos_mul[1]/pesos_mul[0]:.1f}x, UDP {pesos_mul[2]/pesos_mul[0]:.1f}x)")

    train = cargar_procesado("train")
    val = cargar_procesado("val")
    test = cargar_procesado("test")

    print(f"Registros -> Train: {len(train):,} | Val: {len(val):,} | Test: {len(test):,}")

    # Ponderaciones por muestra
    sw_bin_train = train["etiqueta"].map(pesos_bin).to_numpy()
    sw_mul_train = train["clase"].map(pesos_mul).to_numpy()

    # Muestra representativa para MLP si train es muy grande (120,000 flujos da alta precisión y rapidez)
    MUESTRA_MLP = 120_000
    if len(train) > MUESTRA_MLP:
        from sklearn.model_selection import train_test_split
        train_mlp, _ = train_test_split(
            train, train_size=MUESTRA_MLP, stratify=train["clase"], random_state=SEMILLA
        )
        sw_bin_mlp = train_mlp["etiqueta"].map(pesos_bin).to_numpy()
        sw_mul_mlp = train_mlp["clase"].map(pesos_mul).to_numpy()
    else:
        train_mlp = train
        sw_bin_mlp = sw_bin_train
        sw_mul_mlp = sw_mul_train

    # -----------------------------------------------------------------------
    # TAREA 1: CLASIFICACIÓN BINARIA
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("1. CLASIFICACIÓN BINARIA (Tráfico Benigno vs Ataque DDoS)")
    print("=" * 80)

    modelos_bin = obtener_modelos_base()
    resultados_bin = []
    umbrales_calibrados = {}

    for nombre, pipeline in modelos_bin.items():
        print(f"\nEntrenando {nombre}...")
        t0 = time.perf_counter()
        
        datos_fit = train_mlp if nombre == "Red Neuronal (MLP)" else train
        sw_fit = sw_bin_mlp if nombre == "Red Neuronal (MLP)" else sw_bin_train

        # Entrenar pasando sample_weight al modelo final si lo soporta
        if hasattr(pipeline.named_steps["modelo"], "fit"):
            try:
                pipeline.fit(datos_fit[variables], datos_fit["etiqueta"], modelo__sample_weight=sw_fit)
            except TypeError:
                pipeline.fit(datos_fit[variables], datos_fit["etiqueta"])
        t_fit = time.perf_counter() - t0
        print(f"  Entrenado en {t_fit:.2f} s")

        # Calibración de umbral óptimo en Validación (maximiza F2 con FPR <= 0.001)
        puntaje_val = puntaje_ataque(pipeline, val[variables])
        if puntaje_val is not None:
            th_opt, f2_opt = calcular_umbral_optimo(val["etiqueta"], puntaje_val, beta=2.0, max_fpr=0.001)
        else:
            th_opt = 0.5
        umbrales_calibrados[nombre] = th_opt
        print(f"  Umbral óptimo calibrado en Validación: {th_opt:.3f}")

        # Evaluación en Test Oficial con umbral calibrado
        puntaje_test = puntaje_ataque(pipeline, test[variables])
        pred_test = predecir_con_umbral(pipeline, test[variables], umbral=th_opt, tipo="binaria")
        
        met = metricas_binarias(test["etiqueta"], pred_test, puntaje=puntaje_test, clase_real=test["clase"])
        met["Modelo"] = nombre
        met["Umbral óptimo"] = th_opt
        resultados_bin.append(met)
        print(f"  Test -> Ataques no detectados: {met['Ataques no detectados']} | Falsas alarmas: {met['Falsas alarmas']} | Recall DDoS: {met['Recall DDoS']*100:.3f}%")

    df_bin_nuevo = pd.DataFrame(resultados_bin)
    cols_orden_bin = [
        "Modelo", "Accuracy", "Precision DDoS", "Recall DDoS", "F1 DDoS",
        "F1 macro", "Tasa falsos positivos", "PR-AUC", "Recall SYN",
        "Recall UDP", "Falsas alarmas", "Ataques no detectados", "Umbral óptimo"
    ]
    cols_existentes = [c for c in cols_orden_bin if c in df_bin_nuevo.columns]
    df_bin_nuevo = df_bin_nuevo[cols_existentes]

    # -----------------------------------------------------------------------
    # TAREA 2: CLASIFICACIÓN MULTICLASE
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("2. CLASIFICACIÓN MULTICLASE (0: Benigno, 1: DDoS SYN, 2: DDoS UDP)")
    print("=" * 80)

    modelos_mul = obtener_modelos_base()
    resultados_mul = []

    for nombre, pipeline in modelos_mul.items():
        print(f"\nEntrenando {nombre}...")
        t0 = time.perf_counter()

        datos_fit = train_mlp if nombre == "Red Neuronal (MLP)" else train
        sw_fit = sw_mul_mlp if nombre == "Red Neuronal (MLP)" else sw_mul_train

        try:
            pipeline.fit(datos_fit[variables], datos_fit["clase"], modelo__sample_weight=sw_fit)
        except TypeError:
            pipeline.fit(datos_fit[variables], datos_fit["clase"])
        t_fit = time.perf_counter() - t0
        print(f"  Entrenado en {t_fit:.2f} s")

        # Inferencia en Test Oficial
        th_opt = umbrales_calibrados.get(nombre, 0.5)
        pred_test = predecir_con_umbral(pipeline, test[variables], umbral=th_opt, tipo="multiclase")

        met = metricas_multiclase(test["clase"], pred_test)
        met["Modelo"] = nombre
        
        # Calcular FN y FP globales
        cm = pd.crosstab(test["clase"], pred_test)
        fn_total = int(((test["clase"] != 0) & (pred_test == 0)).sum())
        fp_total = int(((test["clase"] == 0) & (pred_test != 0)).sum())
        met["Ataques no detectados"] = fn_total
        met["Falsas alarmas"] = fp_total
        
        resultados_mul.append(met)
        print(f"  Test -> Ataques clasificados como benigno: {fn_total} | Falsas alarmas: {fp_total} | F1 macro: {met['F1 macro']:.4f}")

    df_mul_nuevo = pd.DataFrame(resultados_mul)
    cols_orden_mul = [
        "Modelo", "Accuracy", "Precision macro", "Recall macro", "F1 macro",
        "Recall Benigno", "Recall DDoS SYN", "Recall DDoS UDP",
        "Tasa falsos positivos", "Ataques no detectados", "Falsas alarmas"
    ]
    cols_existentes_mul = [c for c in cols_orden_mul if c in df_mul_nuevo.columns]
    df_mul_nuevo = df_mul_nuevo[cols_existentes_mul]

    # -----------------------------------------------------------------------
    # GUARDAR Y ACTUALIZAR ENTREGABLES
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("3. ACTUALIZACIÓN DE TABLAS Y ENTREGABLES")
    print("=" * 80)

    # 1. Comparación binaria oficial
    ruta_bin = CARPETA_RESULTADOS / "comparacion_binaria_prueba_oficial.csv"
    n_ataques_test = int((test["etiqueta"] == 1).sum())
    n_benignos_test = int((test["etiqueta"] == 0).sum())
    prec_may = n_ataques_test / len(test)
    fila_mayoritaria = {
        "Modelo": "Clase mayoritaria",
        "Accuracy": prec_may, "Precision DDoS": prec_may, "Recall DDoS": 1.0,
        "F1 DDoS": 2 * prec_may / (1 + prec_may), "F1 macro": prec_may / 2, "Tasa falsos positivos": 1.0,
        "PR-AUC": prec_may, "Recall SYN": 1.0, "Recall UDP": 1.0,
        "Falsas alarmas": n_benignos_test, "Ataques no detectados": 0, "Umbral óptimo": 0.5
    }
    df_bin_final = pd.concat([pd.DataFrame([fila_mayoritaria]), df_bin_nuevo], ignore_index=True)
    df_bin_final.to_csv(ruta_bin, index=False)
    print(f"Guardado: {ruta_bin}")

    # 2. Comparación multiclase oficial
    ruta_mul = CARPETA_RESULTADOS / "comparacion_multiclase_prueba_oficial.csv"
    clase_may = test["clase"].value_counts().idxmax()
    acc_may = (test["clase"] == clase_may).mean()
    fila_mayoritaria_mul = {
        "Modelo": "Clase mayoritaria",
        "Accuracy": acc_may, "Precision macro": acc_may / 3, "Recall macro": 1 / 3,
        "F1 macro": (2 * acc_may / (1 + acc_may)) / 3, "Recall Benigno": 0.0,
        "Recall DDoS SYN": 1.0 if clase_may == 1 else 0.0,
        "Recall DDoS UDP": 1.0 if clase_may == 2 else 0.0, "Tasa falsos positivos": 1.0,
        "Ataques no detectados": int(((test["clase"] != 0) & (clase_may == 0)).sum()),
        "Falsas alarmas": n_benignos_test if clase_may != 0 else 0
    }
    df_mul_final = pd.concat([pd.DataFrame([fila_mayoritaria_mul]), df_mul_nuevo], ignore_index=True)
    df_mul_final.to_csv(ruta_mul, index=False)
    print(f"Guardado: {ruta_mul}")

    # 3. Comparación general árboles vs MLP
    ruta_comp_mlp = CARPETA_RESULTADOS / "comparacion_general_arboles_vs_mlp.csv"
    df_mul_nuevo.to_csv(ruta_comp_mlp, index=False)
    print(f"Guardado: {ruta_comp_mlp}")

    # 4. Métricas red neuronal individual
    ruta_mlp_res = CARPETA_RESULTADOS / "metricas_red_neuronal_mlp_test.csv"
    df_mlp_res = df_mul_nuevo[df_mul_nuevo["Modelo"] == "Red Neuronal (MLP)"]
    df_mlp_res.to_csv(ruta_mlp_res, index=False)
    print(f"Guardado: {ruta_mlp_res}")

    # 5. Guardar mejores modelos en models/
    CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)
    mejor_modelo_bin = modelos_bin["LightGBM"]
    mejor_modelo_mul = modelos_mul["LightGBM"]
    joblib.dump({
        "modelo": mejor_modelo_bin,
        "nombre": "LightGBM (Cost-Sensitive)",
        "variables": variables,
        "umbral": umbrales_calibrados["LightGBM"],
        "clases": {0: "Benigno", 1: "Ataque DDoS"}
    }, CARPETA_MODELOS / "mejor_binaria.joblib")
    
    joblib.dump({
        "modelo": mejor_modelo_mul,
        "nombre": "LightGBM (Cost-Sensitive)",
        "variables": variables,
        "umbral": umbrales_calibrados["LightGBM"],
        "clases": CLASES
    }, CARPETA_MODELOS / "mejor_multiclase.joblib")
    print("Modelos guardados en:", CARPETA_MODELOS)

    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS TRAS REENTRENAMIENTO:")
    print("=" * 80)
    print("\n--- CLASIFICACIÓN BINARIA (Test Oficial) ---")
    print(df_bin_final[["Modelo", "Recall DDoS", "Recall SYN", "Falsas alarmas", "Ataques no detectados", "Umbral óptimo"]].to_string(index=False))

    print("\n--- CLASIFICACIÓN MULTICLASE (Test Oficial) ---")
    print(df_mul_final[["Modelo", "F1 macro", "Recall Benigno", "Recall DDoS SYN", "Recall DDoS UDP", "Ataques no detectados", "Falsas alarmas"]].to_string(index=False))

if __name__ == "__main__":
    if "--confirmar" not in sys.argv:
        sys.exit(
            "Experimento descartado: sobrescribe data/processed/ y deliverables/resultados/.\n"
            "Si de verdad quieres ejecutarlo: python src/reentrenar_cost_sensitive.py --confirmar\n"
            "Para volver a la partición original, ejecuta los notebooks 01 y 02."
        )
    main()

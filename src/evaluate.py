"""Métricas y visualizaciones para clasificación binaria y multiclase."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
)

from src.data_loader import CARPETA_RESULTADOS, CLASES


def configurar_graficos():
    """Estilo común: figuras más nítidas, texto más grande y cuadrícula suave."""
    plt.rcParams.update({
        "figure.dpi": 130,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def puntaje_ataque(modelo, X):
    """Probabilidad de DDoS, si el modelo la entrega (para PR-AUC)."""
    if hasattr(modelo, "predict_proba"):
        proba = modelo.predict_proba(X)
        if proba.shape[1] == 2:
            return proba[:, 1]
        return 1 - proba[:, 0]  # multiclase: probabilidad de no ser benigno
    return None


def metricas_binarias(y_true, y_pred, puntaje=None, clase_real=None):
    """Métricas para benigno (0) frente a DDoS (1).

    `clase_real` (etiqueta multiclase) permite ver qué variante de DDoS
    se detecta y cuál no.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    metricas = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision DDoS": precision_score(y_true, y_pred, zero_division=0),
        "Recall DDoS": recall_score(y_true, y_pred, zero_division=0),
        "F1 DDoS": f1_score(y_true, y_pred, zero_division=0),
        "F1 macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "Tasa falsos positivos": fp / (fp + tn) if fp + tn else np.nan,
    }
    if puntaje is not None and len(np.unique(y_true)) == 2:
        metricas["PR-AUC"] = average_precision_score(y_true, puntaje)

    if clase_real is not None:
        clase_real = np.asarray(clase_real)
        for clase, nombre in CLASES.items():
            if clase > 0 and (clase_real == clase).any():
                metricas[f"Recall {nombre.split()[-1]}"] = (
                    y_pred[clase_real == clase] == 1
                ).mean()

    metricas["Falsas alarmas"] = int(fp)
    metricas["Ataques no detectados"] = int(fn)
    return metricas


def metricas_multiclase(y_true, y_pred, clases=CLASES):
    """Métricas macro, recall por clase y tasa de falsos positivos.

    La tasa de falsos positivos considera como alarma cualquier benigno
    clasificado como alguna variante de DDoS.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    etiquetas = list(clases)
    benignos = y_true == 0

    metricas = {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision macro": precision_score(
            y_true, y_pred, labels=etiquetas, average="macro", zero_division=0
        ),
        "Recall macro": recall_score(
            y_true, y_pred, labels=etiquetas, average="macro", zero_division=0
        ),
        "F1 macro": f1_score(
            y_true, y_pred, labels=etiquetas, average="macro", zero_division=0
        ),
    }
    recalls = recall_score(
        y_true, y_pred, labels=etiquetas, average=None, zero_division=0
    )
    for clase, valor in zip(etiquetas, recalls):
        metricas[f"Recall {clases[clase]}"] = valor
    metricas["Tasa falsos positivos"] = (
        (y_pred[benignos] != 0).mean() if benignos.any() else np.nan
    )
    return metricas


def calcular_umbral_optimo(y_true, puntaje, beta=2.0, max_fpr=0.001, paso=0.01):
    """Encuentra el umbral de decisión en [0.01, 0.90] que maximiza F_beta
    sujeto a no superar una tasa máxima de falsos positivos (max_fpr).
    
    beta=2.0 da el doble de ponderación al Recall (detección de intrusiones)
    frente a la Precision (falsas alarmas).
    """
    y_true = np.asarray(y_true)
    puntaje = np.asarray(puntaje)
    umbrales = np.arange(0.01, 0.91, paso)
    
    mejor_umbral = 0.5
    mejor_fbeta = -1.0
    
    benignos = (y_true == 0)
    total_benignos = benignos.sum()
    
    for th in umbrales:
        y_pred = (puntaje >= th).astype(int)
        if total_benignos > 0:
            fpr = (y_pred[benignos] == 1).sum() / total_benignos
            if fpr > max_fpr:
                continue
        fb = fbeta_score(y_true, y_pred, beta=beta, zero_division=0)
        if fb > mejor_fbeta:
            mejor_fbeta = fb
            mejor_umbral = float(th)
            
    return mejor_umbral, mejor_fbeta


def predecir_con_umbral(modelo, X, umbral=0.5, tipo="binaria"):
    """Inferencia con umbral operativo personalizado."""
    if not hasattr(modelo, "predict_proba"):
        return modelo.predict(X)
        
    proba = modelo.predict_proba(X)
    if tipo == "binaria":
        p_ataque = proba[:, 1] if proba.shape[1] == 2 else (1.0 - proba[:, 0])
        return (p_ataque >= umbral).astype(int)
    else:
        # Multiclase: si P(Ataque) = 1 - P(Benigno) >= umbral, asignar al ataque con mayor prob
        p_benigno = proba[:, 0]
        es_ataque = (1.0 - p_benigno) >= umbral
        pred = modelo.predict(X)
        if not np.all(es_ataque == (pred != 0)):
            # Corregir asignaciones donde P(Ataque) >= umbral pero argmax dio benigno
            ataques_proba = proba[:, 1:]
            mejor_ataque = np.argmax(ataques_proba, axis=1) + 1
            pred = np.where(es_ataque, np.where(pred == 0, mejor_ataque, pred), 0)
        return pred


def evaluar(modelo, X, y, tipo="binaria", clase_real=None, umbral=None):
    if umbral is not None and hasattr(modelo, "predict_proba"):
        pred = predecir_con_umbral(modelo, X, umbral=umbral, tipo=tipo)
    else:
        pred = modelo.predict(X)
        
    if tipo == "binaria":
        return metricas_binarias(y, pred, puntaje_ataque(modelo, X), clase_real)
    return metricas_multiclase(y, pred)


def matriz_confusion(y_true, y_pred, tipo="binaria", titulo="", ax=None,
                     normalizar=None):
    """Dibuja la matriz de confusión con nombres de clase legibles."""
    if tipo == "binaria":
        etiquetas, nombres = [0, 1], ["Benigno", "DDoS"]
    else:
        etiquetas, nombres = list(CLASES), list(CLASES.values())

    ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred,
        labels=etiquetas,
        display_labels=nombres,
        normalize=normalizar,
        cmap="Blues",
        values_format=".3f" if normalizar else "d",
        colorbar=False,
        ax=ax,
    )
    ax = ax or plt.gca()
    ax.set_title(titulo)
    ax.set_xlabel("Clase predicha")
    ax.set_ylabel("Clase real")
    ax.grid(False)


def guardar_tabla(tabla, nombre):
    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_RESULTADOS / f"{nombre}.csv"
    tabla.to_csv(ruta)
    return ruta

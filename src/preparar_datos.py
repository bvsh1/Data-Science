"""Genera data/processed/ (train, val, test y variables.json) a partir de
wifi_mqtt_clean.parquet si los CSV individuales no están descomprimidos.
"""

import os
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

from src.data_loader import CARPETA_PROCESADOS, guardar_procesado, guardar_variables, limpiar
from src.features import VARIABLES_SOSPECHOSAS, seleccionar_variables

SEMILLA = 42
EXCLUIR_SOSPECHOSAS = True
UMBRAL_CORRELACION = 0.98

# Ruta al parquet consolidado de CICIoMT2024. Se define con la variable de
# entorno NIDS_PARQUET_RAW; por defecto se busca en data/raw/CICIoMT2024/.
# Si no existe, ejecutar los notebooks 01 y 02, que leen los CSV individuales.
PARQUET_RAW = Path(os.environ.get(
    "NIDS_PARQUET_RAW",
    CARPETA_PROCESADOS.parent / "raw" / "CICIoMT2024" / "wifi_mqtt_clean.parquet",
))

COLS_MAP = {
    "header_length": "Header_Length",
    "protocol_type": "Protocol Type",
    "duration": "Duration",
    "rate": "Rate",
    "srate": "Srate",
    "drate": "Drate",
    "fin_flag_number": "fin_flag_number",
    "syn_flag_number": "syn_flag_number",
    "rst_flag_number": "rst_flag_number",
    "psh_flag_number": "psh_flag_number",
    "ack_flag_number": "ack_flag_number",
    "ece_flag_number": "ece_flag_number",
    "cwr_flag_number": "cwr_flag_number",
    "ack_count": "ack_count",
    "syn_count": "syn_count",
    "fin_count": "fin_count",
    "rst_count": "rst_count",
    "http": "HTTP",
    "https": "HTTPS",
    "dns": "DNS",
    "telnet": "Telnet",
    "smtp": "SMTP",
    "ssh": "SSH",
    "irc": "IRC",
    "tcp": "TCP",
    "udp": "UDP",
    "dhcp": "DHCP",
    "arp": "ARP",
    "icmp": "ICMP",
    "igmp": "IGMP",
    "ipv": "IPv",
    "llc": "LLC",
    "tot_sum": "Tot sum",
    "min": "Min",
    "max": "Max",
    "avg": "AVG",
    "std": "Std",
    "tot_size": "Tot size",
    "iat": "IAT",
    "number": "Number",
    "magnitue": "Magnitue",
    "radius": "Radius",
    "covariance": "Covariance",
    "variance": "Variance",
    "weight": "Weight",
}

FILES_TRAIN = {
    "Benign_train.pcap.csv": 0,
    "TCP_IP-DDoS-SYN1_train.pcap.csv": 1,
    "TCP_IP-DDoS-UDP1_train.pcap.csv": 2,
}

FILES_TEST = {
    "Benign_test.pcap.csv": 0,
    "TCP_IP-DDoS-SYN_test.pcap.csv": 1,
    "TCP_IP-DDoS-UDP1_test.pcap.csv": 2,
}

def main():
    if (CARPETA_PROCESADOS / "train.parquet").exists() and (CARPETA_PROCESADOS / "variables.json").exists():
        print("Los datos procesados ya existen en:", CARPETA_PROCESADOS)
        return

    if not PARQUET_RAW.exists():
        raise SystemExit(
            f"No existe {PARQUET_RAW}.\n"
            "Define NIDS_PARQUET_RAW con la ruta al parquet, o ejecuta los notebooks 01 y 02, "
            "que generan data/processed/ desde los CSV de DESCARGA_DATOS.txt."
        )
    print("Cargando wifi_mqtt_clean.parquet...")
    df = pd.read_parquet(PARQUET_RAW)

    # Filtrar conjuntos
    train_raw = df[df["source_file"].isin(FILES_TRAIN.keys())].copy()
    train_raw["clase"] = train_raw["source_file"].map(FILES_TRAIN).astype(int)
    train_raw["etiqueta"] = (train_raw["clase"] > 0).astype(int)

    test_raw = df[df["source_file"].isin(FILES_TEST.keys())].copy()
    test_raw["clase"] = test_raw["source_file"].map(FILES_TEST).astype(int)
    test_raw["etiqueta"] = (test_raw["clase"] > 0).astype(int)

    # Renombrar columnas
    train_raw = train_raw.rename(columns=COLS_MAP)
    test_raw = test_raw.rename(columns=COLS_MAP)

    columnas_modelo = list(COLS_MAP.values()) + ["clase", "etiqueta"]
    train_raw = train_raw[columnas_modelo]
    test_raw = test_raw[columnas_modelo]

    print(f"Limpiando entrenamiento ({len(train_raw)} filas)...")
    train_limpio, informe_train = limpiar(train_raw, eliminar_filas=True)
    print(f"Entrenamiento limpio: {len(train_limpio)} filas")

    print(f"Limpiando prueba ({len(test_raw)} filas)...")
    test_limpio, informe_test = limpiar(test_raw, eliminar_filas=False)
    print(f"Prueba limpia: {len(test_limpio)} filas")

    variables_todas = list(COLS_MAP.values())

    entrenamiento, validacion = train_test_split(
        train_limpio,
        test_size=0.20,
        stratify=train_limpio["clase"],
        random_state=SEMILLA,
    )

    excluir = VARIABLES_SOSPECHOSAS if EXCLUIR_SOSPECHOSAS else []
    seleccionadas, informe = seleccionar_variables(
        entrenamiento[variables_todas], UMBRAL_CORRELACION, excluir
    )
    print(f"Variables seleccionadas: {len(seleccionadas)} de {len(variables_todas)}")

    columnas_finales = seleccionadas + ["clase", "etiqueta"]
    conjuntos = {
        "train": entrenamiento[columnas_finales].reset_index(drop=True),
        "val": validacion[columnas_finales].reset_index(drop=True),
        "test": test_limpio[columnas_finales].reset_index(drop=True),
    }

    for nombre, datos in conjuntos.items():
        ruta = guardar_procesado(datos, nombre)
        print(f"Guardado {nombre}: {datos.shape} en {ruta}")

    def pesos(y):
        clases = np.unique(y)
        valores = compute_class_weight("balanced", classes=clases, y=y)
        return dict(zip(clases.tolist(), valores.tolist()))

    config = {
        "variables": seleccionadas,
        "excluidas": informe["Motivo"].to_dict(),
        "excluir_sospechosas": EXCLUIR_SOSPECHOSAS,
        "umbral_correlacion": UMBRAL_CORRELACION,
        "pesos_binaria": pesos(entrenamiento["etiqueta"]),
        "pesos_multiclase": pesos(entrenamiento["clase"]),
        "semilla": SEMILLA,
    }
    ruta_cfg = guardar_variables(config)
    print("Configuración guardada en:", ruta_cfg)

if __name__ == "__main__":
    main()

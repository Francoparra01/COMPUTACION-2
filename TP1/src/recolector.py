import os
import time

def obtener_pids_activos():
    pids = []
    for nombre in os.listdir('/proc'):
        if nombre.isdigit():
            pids.append(int(nombre))
    return pids

def recolector_main(snapshot):
    print("[Recolector] Iniciado. Buscando procesos...")
    while True:
        pids = obtener_pids_activos()
        # Guardamos la lista en la memoria compartida para todos los analizadores
        snapshot["pids_activos"] = pids
        time.sleep(2)
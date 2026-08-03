import os
import time

def obtener_pids_activos():
    """Lee /proc y devuelve una lista de PIDs activos (carpetas numéricas)."""
    pids = []
    for nombre in os.listdir('/proc'):
        if nombre.isdigit():
            pids.append(int(nombre))
    return pids

def recolector_main(pids_queue):
    print("[Recolector] Iniciado. Buscando procesos...")
    while True:
        pids = obtener_pids_activos()
        print(f"[Recolector] Encontró {len(pids)} PIDs. Enviando a la cola...")
        
        # Vaciamos la cola vieja si se acumuló, para tener siempre datos frescos
        while not pids_queue.empty():
            pids_queue.get()
            
        # Mandamos la lista nueva
        pids_queue.put(pids)

        time.sleep(2)

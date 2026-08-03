import os
import time

def extraer_datos_threads(pid):
    """Extrae información de los threads (LWPs) de un proceso."""
    datos = {"pid": pid, "total_threads": 0, "lista_tids": []}
    task_dir = f"/proc/{pid}/task"
    
    try:
        if os.path.exists(task_dir):
            tids = os.listdir(task_dir)
            datos["total_threads"] = len(tids)
            
            # Agarramos una muestra de los primeros 5 threads para la UI
            for tid in tids[:5]:
                try:
                    with open(f"{task_dir}/{tid}/stat", "r") as f:
                        stat_cols = f.read().split()
                        if len(stat_cols) > 2:
                            estado = stat_cols[2]
                            datos["lista_tids"].append(f"TID:{tid} [{estado}]")
                except (FileNotFoundError, ProcessLookupError, PermissionError):
                    pass
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
        
    return datos

def analizador_threads_main(snapshot, intervalo_val):
    print("[Analizador Threads] Iniciado.")
    
    while True:
        pids_actuales = snapshot.get("pids_activos", [])
        
        if pids_actuales:
            threads_actualizados = {}
            for pid in pids_actuales:
                datos = extraer_datos_threads(pid)
                if datos["total_threads"] > 0:
                    threads_actualizados[pid] = datos
            
            snapshot["threads"] = threads_actualizados
            
        time.sleep(intervalo_val.value)
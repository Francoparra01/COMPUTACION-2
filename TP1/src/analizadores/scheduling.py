import time

def extraer_datos_scheduling(pid):
    """Extrae datos de scheduling y prioridad desde /proc/<pid>/stat."""
    datos = {"pid": pid, "nice": 0, "prioridad": 0}
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            cols = f.read().split()
            if len(cols) > 18:
                # El nice suele estar en la posición 18 (índice 18) y prioridad en la 17
                datos["prioridad"] = int(cols[17])
                datos["nice"] = int(cols[18])
    except (FileNotFoundError, ProcessLookupError, ValueError):
        pass
    return datos

def analizador_scheduling_main(snapshot, intervalo_val):
    print("[Analizador Scheduling] Iniciado.")
    while True:
        pids_actuales = snapshot.get("pids_activos", [])
        if pids_actuales:
            sched_actualizado = {}
            for pid in pids_actuales:
                datos = extraer_datos_scheduling(pid)
                sched_actualizado[pid] = datos
            snapshot["scheduling"] = sched_actualizado
        time.sleep(intervalo_val.value)
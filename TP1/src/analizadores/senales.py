import time

def extraer_datos_senales(pid):
    """Extrae las máscaras de señales del proceso desde status."""
    datos = {"pid": pid, "pendientes": "-", "bloqueadas": "-", "ignoradas": "-"}
    
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            for linea in f:
                if linea.startswith("SigPnd:"):
                    datos["pendientes"] = linea.split()[1]
                elif linea.startswith("SigBlk:"):
                    datos["bloqueadas"] = linea.split()[1]
                elif linea.startswith("SigIgn:"):
                    datos["ignoradas"] = linea.split()[1]
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
        
    return datos

def analizador_senales_main(snapshot, intervalo_val):
    print("[Analizador Señales] Iniciado.")
    
    while True:
        pids_actuales = snapshot.get("pids_activos", [])
        
        if pids_actuales:
            senales_actualizadas = {}
            for pid in pids_actuales:
                datos = extraer_datos_senales(pid)
                if datos["pendientes"] != "-":
                    senales_actualizadas[pid] = datos
            
            snapshot["senales"] = senales_actualizadas
            
        time.sleep(intervalo_val.value)
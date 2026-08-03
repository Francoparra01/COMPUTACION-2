import time

def extraer_datos_memoria(pid):
    """Extrae información de memoria desde /proc/<pid>/status."""
    datos = {"pid": pid, "vmsize": "0", "vmrss": "0"}
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            for linea in f:
                if linea.startswith("VmSize:"):
                    datos["vmsize"] = linea.split()[1] 
                elif linea.startswith("VmRSS:"):
                    datos["vmrss"] = linea.split()[1]
                    
    except (FileNotFoundError, ProcessLookupError):
        pass
        
    return datos

def analizador_memoria_main(snapshot, intervalo_val):
    print("[Analizador Memoria] Iniciado.")
    
    while True:
        pids_actuales = snapshot.get("pids_activos", [])
        
        if pids_actuales:
            memoria_actualizada = {}
            for pid in pids_actuales:
                datos = extraer_datos_memoria(pid)
                if datos["vmsize"] != "0":
                    memoria_actualizada[pid] = datos
            
            snapshot["memoria"] = memoria_actualizada
            
        time.sleep(intervalo_val.value)
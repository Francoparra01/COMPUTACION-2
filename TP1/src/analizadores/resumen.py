import time

def extraer_datos_resumen(pid):
    """Extrae la info básica del proceso leyendo los archivos virtuales."""
    datos = {"pid": pid, "estado": "?", "comando": "", "threads": 0}
    
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            stat_cols = f.read().split()
            if len(stat_cols) > 2:
                datos["estado"] = stat_cols[2]
        
        with open(f"/proc/{pid}/cmdline", "r") as f:
            cmdline = f.read().replace('\x00', ' ').strip()
            if cmdline:
                datos["comando"] = cmdline
            elif len(stat_cols) > 1:
                datos["comando"] = stat_cols[1].strip("()")

        with open(f"/proc/{pid}/status", "r") as f:
            for linea in f:
                if linea.startswith("Threads:"):
                    datos["threads"] = int(linea.split()[1])
                    break
                    
    except (FileNotFoundError, ProcessLookupError):
        pass
        
    return datos

def analizador_resumen_main(snapshot, intervalo_val):
    print("[Analizador Resumen] Iniciado.")
    
    while True:
        pids_actuales = snapshot.get("pids_activos", [])
        
        if pids_actuales:
            resumen_actualizado = {}
            for pid in pids_actuales:
                datos = extraer_datos_resumen(pid)
                if datos["estado"] != "?":
                    resumen_actualizado[pid] = datos
            
            snapshot["resumen"] = resumen_actualizado
            
        time.sleep(intervalo_val.value)
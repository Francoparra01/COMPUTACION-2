import time

def extraer_datos_memoria(pid):
    """Extrae información de memoria desde /proc/<pid>/status."""
    datos = {
        "pid": pid,
        "vmsize": "0",
        "vmrss": "0",
        "vmdata": "0",
        "vmstk": "0",
        "vmexe": "0",
        "vmlib": "0",
        "vmhwm": "0",
        "vmswap": "0",
        "minflt": "0",
        "cminflt": "0",
        "majflt": "0",
        "cmajflt": "0",
        "mapas": []
    }

    campos_status = {
        "VmSize:": "vmsize",
        "VmRSS:": "vmrss",
        "VmData:": "vmdata",
        "VmStk:": "vmstk",
        "VmExe:": "vmexe",
        "VmLib:": "vmlib",
        "VmHWM:": "vmhwm",
        "VmSwap:": "vmswap"
    }

    try:
        with open(f"/proc/{pid}/status", "r") as f:
            for linea in f:
                for campo, clave in campos_status.items():
                    if linea.startswith(campo):
                        datos[clave] = linea.split()[1]
                        break

        with open(f"/proc/{pid}/stat", "r") as f:
            contenido = f.readline().strip()
            fin_comm = contenido.rfind(")")
            if fin_comm != -1:
                partes = contenido[fin_comm + 2:].split()
                if len(partes) > 10:
                    datos["minflt"] = partes[7]
                    datos["cminflt"] = partes[8]
                    datos["majflt"] = partes[9]
                    datos["cmajflt"] = partes[10]

        with open(f"/proc/{pid}/maps", "r") as f:
            for linea in f:
                partes = linea.split()
                if len(partes) >= 2:
                    datos["mapas"].append({"rango": partes[0], "permisos": partes[1]})
                     
    except (FileNotFoundError, ProcessLookupError, PermissionError, IndexError):
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
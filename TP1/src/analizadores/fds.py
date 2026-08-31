import os
import time

MAX_FDS_MUESTRA = 25

def extraer_datos_fds(pid):
    """Cuenta y lista los File Descriptors de un proceso."""
    datos = {"pid": pid, "total_fds": 0, "lista_fds": []}
    fd_dir = f"/proc/{pid}/fd"
    
    try:
        if os.path.exists(fd_dir):
            # Listamos todos los enlaces simbólicos en la carpeta fd
            fds = sorted(os.listdir(fd_dir), key=lambda x: int(x) if x.isdigit() else x)
            datos["total_fds"] = len(fds)
            
            # Conservamos una muestra amplia para habilitar modo detallado en la vista
            for fd in fds[:MAX_FDS_MUESTRA]:
                try:
                    destino = os.readlink(f"{fd_dir}/{fd}")
                    datos["lista_fds"].append(f"{fd}->{destino}")
                except OSError:
                    pass
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
        
    return datos

def analizador_fds_main(snapshot, intervalo_val):
    print("[Analizador FDs] Iniciado.")
    
    while True:
        pids_actuales = snapshot.get("pids_activos", [])
        
        if pids_actuales:
            fds_actualizados = {}
            for pid in pids_actuales:
                datos = extraer_datos_fds(pid)
                if datos["total_fds"] > 0:
                    fds_actualizados[pid] = datos
            
            snapshot["fds"] = fds_actualizados
            
        time.sleep(intervalo_val.value)
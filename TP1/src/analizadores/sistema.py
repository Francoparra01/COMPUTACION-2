import time

def extraer_datos_sistema():
    """Extrae métricas globales de memoria desde /proc/meminfo."""
    datos = {"mem_total": "0", "mem_libre": "0"}
    try:
        with open("/proc/meminfo", "r") as f:
            for linea in f:
                if linea.startswith("MemTotal:"):
                    datos["mem_total"] = linea.split()[1]
                elif linea.startswith("MemAvailable:"):
                    datos["mem_libre"] = linea.split()[1]
    except (FileNotFoundError, PermissionError):
        pass
    return datos

def analizador_sistema_main(snapshot, intervalo_val):
    print("[Analizador Sistema] Iniciado.")
    while True:
        datos_sis = extraer_datos_sistema()
        snapshot["sistema"] = datos_sis
        time.sleep(intervalo_val.value)
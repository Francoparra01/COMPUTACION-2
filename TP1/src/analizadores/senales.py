import time
import signal

MASCARAS_STATUS = {
    "SigPnd": "pendientes",
    "ShdPnd": "pendientes_compartidas",
    "SigBlk": "bloqueadas",
    "SigIgn": "ignoradas",
    "SigCgt": "capturadas"
}

def decodificar_mascara(hex_mascara):
    if hex_mascara in ("-", ""):
        return "-"
    try:
        valor = int(hex_mascara, 16)
    except ValueError:
        return "-"

    if valor == 0:
        return "ninguna"

    senales_activas = []
    for bit in range(valor.bit_length()):
        if valor & (1 << bit):
            nro_senal = bit + 1
            try:
                nombre = signal.Signals(nro_senal).name
            except ValueError:
                nombre = f"SIG{nro_senal}"
            senales_activas.append(nombre)
    return ",".join(senales_activas) if senales_activas else "ninguna"

def extraer_datos_senales(pid):
    """Extrae las máscaras de señales del proceso desde status."""
    datos = {"pid": pid}
    for campo in MASCARAS_STATUS.values():
        datos[campo] = "-"
    
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            for linea in f:
                nombre_campo, _, valor = linea.partition(":")
                if nombre_campo in MASCARAS_STATUS:
                    clave = MASCARAS_STATUS[nombre_campo]
                    datos[clave] = decodificar_mascara(valor.strip())
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
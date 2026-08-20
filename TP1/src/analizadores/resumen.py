import os
import time

def extraer_datos_resumen(pid):
    """Extrae la info básica del proceso leyendo los archivos virtuales."""
    # Agregamos "jiffies" al diccionario base
    datos = {"pid": pid, "estado": "?", "comando": "", "threads": 0, "jiffies": 0}
    
    try:
        # Extraemos estado y jiffies (campos 14 y 15) de una sola leída
        with open(f"/proc/{pid}/stat", "r") as f:
            stat_cols = f.read().split()
            if len(stat_cols) > 15:
                datos["estado"] = stat_cols[2]
                datos["jiffies"] = int(stat_cols[13]) + int(stat_cols[14])
        
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
                    
    except (FileNotFoundError, ProcessLookupError, IndexError):
        pass
        
    return datos

def analizador_resumen_main(snapshot, intervalo_val):
    print("[Analizador Resumen] Iniciado con cálculo de CPU%.")
    
    # Obtenemos los ticks por segundo del kernel para el cálculo
    try:
        clk_tck = os.sysconf('SC_CLK_TCK')
    except ValueError:
        clk_tck = 100.0

    # Historial para calcular el delta entre lecturas
    historial_cpu = {}
    
    while True:
        inicio_ciclo = time.time()
        pids_actuales = snapshot.get("pids_activos", [])
        
        if pids_actuales:
            resumen_actualizado = {}
            pids_vistos = set()
            
            for pid in pids_actuales:
                pids_vistos.add(pid)
                datos = extraer_datos_resumen(pid)
                
                if datos["estado"] != "?":
                    # --- LÓGICA DE CÁLCULO DE CPU% ---
                    jiffies_actuales = datos["jiffies"]
                    tiempo_actual = time.time()
                    cpu_percent = 0.0
                    
                    if pid in historial_cpu:
                        jiffies_ant, tiempo_ant = historial_cpu[pid]
                        delta_jiffies = jiffies_actuales - jiffies_ant
                        delta_tiempo = tiempo_actual - tiempo_ant
                        
                        if delta_tiempo > 0:
                            cpu_percent = (delta_jiffies / clk_tck) / delta_tiempo * 100.0
                    
                    historial_cpu[pid] = (jiffies_actuales, tiempo_actual)
                    
                    # Preparamos los datos limpios para el display
                    datos["cpu_percent"] = round(cpu_percent, 2)
                    del datos["jiffies"] # Limpiamos los jiffies crudos
                    
                    resumen_actualizado[pid] = datos
            
            # Limpiamos el historial de los procesos que ya murieron
            pids_muertos = set(historial_cpu.keys()) - pids_vistos
            for pid_muerto in pids_muertos:
                del historial_cpu[pid_muerto]
            
            snapshot["resumen"] = resumen_actualizado
            
        # Respetamos el intervalo pero restando el tiempo que tardamos en procesar
        tiempo_procesamiento = time.time() - inicio_ciclo
        sleep_time = max(0, intervalo_val.value - tiempo_procesamiento)
        time.sleep(sleep_time)
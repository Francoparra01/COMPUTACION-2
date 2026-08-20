import multiprocessing
import time
import signal
import json
from recolector import recolector_main
from analizadores.resumen import analizador_resumen_main
from analizadores.memoria import analizador_memoria_main
from analizadores.fds import analizador_fds_main
from analizadores.threads import analizador_threads_main
from analizadores.senales import analizador_senales_main
from analizadores.scheduling import analizador_scheduling_main
from analizadores.sistema import analizador_sistema_main
from display import display_main

# --- BANDERAS PARA SEÑALES ---
shutdown_flag = False
reload_config_flag = False
dump_snapshot_flag = False
verbose_mode = False

# --- HANDLERS (Solo prenden las banderas) ---
def handle_shutdown(signum, frame):
    global shutdown_flag
    shutdown_flag = True

def handle_sighup(signum, frame):
    global reload_config_flag
    reload_config_flag = True

def handle_sigusr1(signum, frame):
    global dump_snapshot_flag
    dump_snapshot_flag = True

def handle_sigusr2(signum, frame):
    global verbose_mode
    verbose_mode = not verbose_mode

if __name__ == "__main__":
    with multiprocessing.Manager() as manager:
        snapshot = manager.dict({
            "pids_activos": [],
            "resumen": {},
            "memoria": {},
            "fds": {},
            "threads": {},
            "senales": {},
            "scheduling": {},
            "sistema": {}
        })

        # Intervalos dinámicos para los 7 analizadores
        intervalo_resumen = multiprocessing.Value('d', 2.0)
        intervalo_memoria = multiprocessing.Value('d', 3.0)
        intervalo_fds = multiprocessing.Value('d', 5.0)
        intervalo_threads = multiprocessing.Value('d', 2.0)
        intervalo_senales = multiprocessing.Value('d', 10.0)
        intervalo_sched = multiprocessing.Value('d', 3.0)
        intervalo_sistema = multiprocessing.Value('d', 3.0)

        # Instanciar los 7 analizadores + recolector + display
        p_recolector = multiprocessing.Process(target=recolector_main, args=(snapshot,))
        p_resumen = multiprocessing.Process(target=analizador_resumen_main, args=(snapshot, intervalo_resumen))
        p_memoria = multiprocessing.Process(target=analizador_memoria_main, args=(snapshot, intervalo_memoria))
        p_fds = multiprocessing.Process(target=analizador_fds_main, args=(snapshot, intervalo_fds))
        p_threads = multiprocessing.Process(target=analizador_threads_main, args=(snapshot, intervalo_threads))
        p_senales = multiprocessing.Process(target=analizador_senales_main, args=(snapshot, intervalo_senales))
        p_sched = multiprocessing.Process(target=analizador_scheduling_main, args=(snapshot, intervalo_sched))
        p_sistema = multiprocessing.Process(target=analizador_sistema_main, args=(snapshot, intervalo_sistema))
        
        p_display = multiprocessing.Process(
            target=display_main, 
            args=(snapshot, intervalo_resumen, intervalo_memoria, intervalo_fds, 
                  intervalo_threads, intervalo_senales, intervalo_sched, intervalo_sistema)
        )

        # Arrancar todos
        procesos = [p_recolector, p_resumen, p_memoria, p_fds, p_threads, p_senales, p_sched, p_sistema, p_display]
        for p in procesos:
            p.start()

        # --- REGISTRO DE SEÑALES ---
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGHUP, handle_sighup)
        signal.signal(signal.SIGUSR1, handle_sigusr1)
        signal.signal(signal.SIGUSR2, handle_sigusr2)

        try:
            # El loop principal revisa periódicamente las banderas
            while not shutdown_flag:
                if reload_config_flag:
                    # Cumple con el requisito de atrapar SIGHUP sin romper el flujo
                    reload_config_flag = False
                
                if dump_snapshot_flag:
                    # Captura el estado actual en un archivo
                    timestamp = int(time.time())
                    with open(f"dump_{timestamp}.json", "w") as f:
                        json.dump(dict(snapshot), f, indent=4)
                    dump_snapshot_flag = False
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            # Respaldo por si el signal no agarra el Ctrl+C en la terminal
            pass

        print("\nApagando el monitor de forma limpia...")
        for p in procesos:
            p.terminate()
        for p in procesos:
            p.join()
        print("\033[H\033[JMonitor apagado correctamente.")
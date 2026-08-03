import multiprocessing
import time
from recolector import recolector_main

if __name__ == "__main__":
    print("Iniciando Monitor de Procesos...")

    # 1. El Snapshot Global (Memoria Compartida dict)
    with multiprocessing.Manager() as manager:
        snapshot = manager.dict({
            "resumen": {},
            "memoria": {},
            "fds": {},
            "threads": {},
            "senales": {},
            "scheduling": {},
            "sistema": {}
        })

        # 2. Cola para pasar PIDs del recolector a los analizadores
        pids_queue = multiprocessing.Queue()

        # 3. Arrancar el Recolector en un proceso aparte
        p_recolector = multiprocessing.Process(
            target=recolector_main, 
            args=(pids_queue,)
        )
        p_recolector.start()

        try:
            # El proceso principal (main) se queda vivo esperando
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nApagando el monitor...")
            p_recolector.terminate()
            p_recolector.join()
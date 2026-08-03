import time
import sys
import select

def display_main(snapshot, int_resumen, int_memoria, int_fds, int_threads, int_senales, int_sched, int_sistema):
    vista_activa = '1'
    print("[Display] Iniciado.")

    while True:
        if select.select([sys.stdin], [], [], 0)[0]:
            tecla = sys.stdin.read(1)
            
            if tecla == '1': vista_activa = '1'
            elif tecla == '2': vista_activa = '2'
            elif tecla == '3': vista_activa = '3'
            elif tecla == '4': vista_activa = '4'
            elif tecla == '5': vista_activa = '5'
            elif tecla == '6': vista_activa = '6'
            elif tecla == '7': vista_activa = '7'
            
            elif tecla == '+':
                if vista_activa == '1': int_resumen.value += 0.5
                elif vista_activa == '2': int_memoria.value += 0.5
                elif vista_activa == '3': int_fds.value += 0.5
                elif vista_activa == '4': int_threads.value += 0.5
                elif vista_activa == '5': int_senales.value += 1.0
                elif vista_activa == '6': int_sched.value += 1.0
                elif vista_activa == '7': int_sistema.value += 1.0
            elif tecla == '-':
                if vista_activa == '1' and int_resumen.value > 0.5: int_resumen.value -= 0.5
                elif vista_activa == '2' and int_memoria.value > 1.0: int_memoria.value -= 0.5
                elif vista_activa == '3' and int_fds.value > 2.0: int_fds.value -= 0.5
                elif vista_activa == '4' and int_threads.value > 0.5: int_threads.value -= 0.5
                elif vista_activa == '5' and int_senales.value > 5.0: int_senales.value -= 1.0
                elif vista_activa == '6' and int_sched.value > 1.0: int_sched.value -= 1.0
                elif vista_activa == '7' and int_sistema.value > 1.0: int_sistema.value -= 1.0
            elif tecla.lower() == 'q':
                break

        print("\033[H\033[J", end="")

        if vista_activa == '1':
            print(f"=== VISTA 1: RESUMEN | Refresco: {int_resumen.value:.1f}s ===")
            print(f"{'PID':<10} | {'ESTADO':<8} | {'THREADS':<8} | {'COMANDO'}")
            print("-" * 70)
            for pid, datos in list(snapshot.get("resumen", {}).items())[:20]:
                comando = str(datos.get("comando", ""))[:40]
                print(f"{pid:<10} | {datos.get('estado', '?'):<8} | {datos.get('threads', 0):<8} | {comando}")

        elif vista_activa == '2':
            print(f"=== VISTA 2: MEMORIA | Refresco: {int_memoria.value:.1f}s ===")
            print(f"{'PID':<10} | {'VmSize (kB)':<15} | {'VmRSS (kB)':<15}")
            print("-" * 70)
            for pid, datos in list(snapshot.get("memoria", {}).items())[:20]:
                print(f"{pid:<10} | {datos.get('vmsize', '0'):<15} | {datos.get('vmrss', '0'):<15}")

        elif vista_activa == '3':
            print(f"=== VISTA 3: FDs | Refresco: {int_fds.value:.1f}s ===")
            print(f"{'PID':<10} | {'TOTAL FDs':<10} | {'MUESTRA DE DESTINOS'}")
            print("-" * 70)
            for pid, datos in list(snapshot.get("fds", {}).items())[:20]:
                destinos = ", ".join(datos.get("lista_fds", []))[:45]
                print(f"{pid:<10} | {datos.get('total_fds', 0):<10} | {destinos}")
                
        elif vista_activa == '4':
            print(f"=== VISTA 4: THREADS | Refresco: {int_threads.value:.1f}s ===")
            print(f"{'PID':<10} | {'TOTAL':<8} | {'MUESTRA DE TIDs'}")
            print("-" * 70)
            for pid, datos in list(snapshot.get("threads", {}).items())[:20]:
                muestra = ", ".join(datos.get("lista_tids", []))[:45]
                print(f"{pid:<10} | {datos.get('total_threads', 0):<8} | {muestra}")

        elif vista_activa == '5':
            print(f"=== VISTA 5: SEÑALES | Refresco: {int_senales.value:.1f}s ===")
            print(f"{'PID':<10} | {'PENDIENTES':<18} | {'BLOQUEADAS':<18}")
            print("-" * 70)
            for pid, datos in list(snapshot.get("senales", {}).items())[:20]:
                print(f"{pid:<10} | {datos.get('pendientes', '-'):<18} | {datos.get('bloqueadas', '-'):<18}")

        elif vista_activa == '6':
            print(f"=== VISTA 6: SCHEDULING | Refresco: {int_sched.value:.1f}s ===")
            print(f"{'PID':<10} | {'PRIORIDAD':<12} | {'NICE':<10}")
            print("-" * 70)
            for pid, datos in list(snapshot.get("scheduling", {}).items())[:20]:
                print(f"{pid:<10} | {datos.get('prioridad', 0):<12} | {datos.get('nice', 0):<10}")

        elif vista_activa == '7':
            print(f"=== VISTA 7: SISTEMA GLOBAL | Refresco: {int_sistema.value:.1f}s ===")
            print("-" * 70)
            sis = snapshot.get("sistema", {})
            print(f"Memoria Total del Sistema: {sis.get('mem_total', '0')} kB")
            print(f"Memoria Disponible (Libre): {sis.get('mem_libre', '0')} kB")
            print("-" * 70)

        print("-" * 70)
        print("Vistas: [1]Res [2]Mem [3]FDs [4]Threads [5]Señales [6]Sched [7]Sistema | [+] [-] | [q] Salir")
        
        time.sleep(0.5)
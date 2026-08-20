# TP1 — Monitor de Procesos y Threads

**Alumno:** Franco Parra
**Materia:** Computación II — Cohorte 2026
**Institución:** Universidad de Mendoza

---

## 1. Descripción general

Este proyecto implementa un monitor del sistema en tiempo real para entornos Linux, inspirado en herramientas clásicas como `htop`. El objetivo principal es inspeccionar la anatomía interna de los procesos del sistema mediante la lectura directa del pseudo-filesystem `/proc`, prescindiendo por completo de librerías de abstracción de alto nivel como `psutil`.

El sistema está diseñado bajo una arquitectura fuertemente orientada al multiprocesamiento. Un recolector central distribuye el trabajo a 7 analizadores especializados que se ejecutan de manera concurrente (como procesos independientes, no threads), cada uno encargado de una dimensión específica del sistema (Resumen, Memoria, File Descriptors, Threads, Señales, Scheduling y Sistema). Los datos se consolidan en memoria compartida y son renderizados por una Interfaz de Texto (TUI) interactiva.

---

## 2. Diagrama de arquitectura

```
       ┌────────────────────────────────────────────────────────┐
       │                   SNAPSHOT GLOBAL                       │
       │              (Manager dict compartido)                  │
       │                                                          │
       │  "resumen" : {...}     "memoria" : {...}                │
       │  "fds"     : {...}     "threads" : {...}                │
       │  "senales" : {...}     "sistema" : {...}                │
       └────────▲──────────────────────────────────────▲────────┘
                │ escriben                              │ lee
   ┌────────────┼─────────┬───────────┬─────────┐       │
   │            │         │           │         │       │
┌──▼───────┐ ┌──▼──────┐ ┌▼───────┐  ...    ┌────▼─────┐
│Recolector│ │Analizador│ │Analizador│       │ Display  │
│ (main)   │ │ Memoria  │ │   FDs    │       │  (TUI)   │
└──────────┘ └──────────┘ └──────────┘       └──────────┘

      7 analizadores independientes (multiprocessing.Process)
```

---

## 3. Decisiones de diseño argumentadas

**Uso de `multiprocessing.Value` para la comunicación de intervalos:**
Para lograr que la TUI cambie dinámicamente la velocidad de refresco de cada vista, instancié un `Value('d')` por cada una. No utilicé un argumento estándar porque, tras realizar el fork, cada analizador opera en su propio espacio de memoria. Utilizar un segmento de memoria compartida real permite que el display escriba la nueva tasa de refresco y el analizador la lea de manera segura y atómica en cada iteración de su ciclo `while`.

**Consolidación del snapshot con `Manager.dict`:**
Se eligió un diccionario administrado por un Manager para centralizar la recolección de datos. Al tener una arquitectura con múltiples procesos escritores (los 7 analizadores) operando de forma asíncrona y un lector continuo (el Display), el `Manager.dict` maneja implícitamente los bloqueos de concurrencia (locks), evitando condiciones de carrera al leer y escribir el estado del sistema.

**Secuencia de Shutdown (`terminate` seguido de `join` en bucles separados):**
Ante la interrupción del programa, el apagado de los procesos hijos se realiza en dos etapas. Primero, un bucle ejecuta `.terminate()` sobre los 9 subprocesos. Luego, un segundo bucle independiente ejecuta `.join()` sobre cada uno. Al hacerlo en dos bucles, la interrupción es paralela y la espera es limpia sin bloquearse en serie.

**Manejo de Señales y Async-Signal-Safe:**
Los handlers del módulo `signal` (`SIGINT`, `SIGTERM`, `SIGHUP`, `SIGUSR1`, `SIGUSR2`) fueron diseñados para ser mínimos: solo encienden flags globales. Es el bucle principal de `main.py` el que reacciona a estos flags (ej. guardando el JSON del snapshot). Esto respeta la naturaleza impredecible de las señales sin interrumpir operaciones de I/O a la mitad.

**Lectura de Teclado (Modo Cbreak) en Entorno Dockerizado:**
Por defecto, la librería `multiprocessing` desconecta `sys.stdin` de los procesos hijos para evitar conflictos de lectura. Para lograr que el subproceso del Display reaccione a las pulsaciones sin necesidad de apretar la tecla Enter, se forzó la apertura directa del dispositivo de terminal nativo (`os.open('/dev/tty')`) combinado con `tty.setcbreak()`.

**Cálculo de CPU% mediante Jiffies:**
Dado que `/proc/<pid>/stat` no entrega un porcentaje directo sino una sumatoria de tiempos (jiffies), el analizador mantiene un diccionario histórico en memoria. En cada iteración calcula el delta de jiffies contra el delta temporal, normalizado por la constante `os.sysconf('SC_CLK_TCK')`.

---

## 4. Conceptos del curso aplicados

**Prevención de procesos Zombies (Clase 4):**
La implementación estricta de `.join()` durante el shutdown garantiza que el proceso principal (padre) invoque la llamada al sistema `wait()`, limpiando la tabla de procesos del kernel y evitando fugas de recursos.

**Aislamiento de memoria e IPC (Clases 7 y 9):**
Como los analizadores son `Process` y no threads, no comparten el Global Interpreter Lock (GIL) ni el espacio de memoria por defecto. La utilización de `Manager` y `Value` es la aplicación práctica de la comunicación entre procesos (IPC).

**Inspección del Kernel vía Archivos (Clase 3):**
El sistema interactúa con las estructuras internas del kernel leyendo archivos virtuales en `/proc` (como `stat`, `status`, `fd`, `cmdline`), demostrando el principio de que en Linux "todo es un archivo".

---

## 5. Limitaciones conocidas (estado de desarrollo actual)

- **Máscaras de señales crudas:** Los valores de `SigPnd`, `SigBlk` y `SigIgn` se extraen correctamente de `/proc/<pid>/status`, pero se muestran en la TUI en su formato hexadecimal original (64 bits). Resta implementar la decodificación bit a bit para mapearlos a nombres legibles.

- **Profundidad de lectura parcial:**
  - La vista de Memoria lee campos vitales de `status`, pero aún no abre y procesa `/proc/<pid>/maps` para desglosar y agrupar las regiones del mapa de memoria (heap, stack, etc).
  - Las listas de visualización de Threads y File Descriptors están siendo truncadas a un máximo de 5 elementos desde la etapa de análisis, implicando una limitación estática de los datos que llegan al agregador.
  - La vista del Sistema Global solo renderiza memoria general, omitiendo la agregación de CPU global y conteo de estados.

---

## 6. Cómo correr y testear

El proyecto se encuentra dockerizado para asegurar su funcionamiento en el entorno `linux/amd64` requerido. Es importante correrlo en formato interactivo (con TTY).

### Levantar el monitor

```bash
docker compose run --rm monitor
```

> **Nota:** Se utiliza `run` en lugar de `up` para que Docker asigne una terminal interactiva (TTY) al contenedor, permitiendo el funcionamiento del modo cbreak.

### Uso de la interfaz (TUI)

- **Navegación:** Utilice los números del `1` al `7` (o sus atajos `r`, `m`, `f`, `t`, `s`, `p`, `g`) para alternar fluidamente entre las diferentes vistas.
- **Intervalos:** Presione `+` y `-` para ajustar dinámicamente la velocidad de refresco de la vista activa.
- **Salir:** Presione la tecla `q` o envíe la señal correspondiente.

### Testeo de señales (desde otra terminal al contenedor host)

- `kill -SIGUSR1 <pid_main>`: Genera un volcado del estado actual en formato JSON.
- `kill -SIGHUP <pid_main>`: Dispara una simulación de recarga de configuración.
- `Ctrl+C` (`SIGINT`) en la terminal principal: Gatilla el apagado limpio y la recolección de los 8 subprocesos.
# TP1 — Monitor de Procesos y Threads

**Alumno:** Franco Parra
**Materia:** Computación II — Cohorte 2026
**Institución:** Universidad de Mendoza

## Descripción general

Este proyecto implementa un monitor del sistema en tiempo real para entornos Linux, inspirado en herramientas clásicas como `htop`. El objetivo principal es inspeccionar la anatomía interna de los procesos del sistema mediante la lectura directa del pseudo-filesystem `/proc`, prescindiendo por completo de librerías de abstracción de alto nivel como `psutil`.

El sistema está diseñado bajo una arquitectura fuertemente orientada al multiprocesamiento. Un recolector central distribuye el trabajo a 7 analizadores especializados que se ejecutan de manera concurrente (como procesos independientes, no threads), cada uno encargado de una dimensión específica del sistema (Resumen, Memoria, File Descriptors, Threads, Señales, Scheduling y Sistema). Los datos se consolidan en memoria compartida y son renderizados por una Interfaz de Texto (TUI) interactiva.

## Diagrama de arquitectura

```
┌────────────────────────────────────────────────────────┐
│                    SNAPSHOT GLOBAL                      │
│               (Manager dict compartido)                 │
│                                                           │
│   "resumen" : {...}      "memoria" : {...}              │
│   "fds"     : {...}      "threads" : {...}              │
│   "senales" : {...}      "sistema" : {...}               │
└────────▲──────────────────────────────────────▲────────┘
         │ escriben                              │ lee
    ┌────┼────────┬───────────┬─────────┐        │
    │    │        │           │         │        │
┌───▼────────┐ ┌──▼───────┐ ┌─▼────────┐   ┌─────▼─────┐
│ Recolector │ │Analizador│ │Analizador│...│  Display  │
│   (main)   │ │ Memoria  │ │   FDs    │   │   (TUI)   │
└────────────┘ └──────────┘ └──────────┘   └───────────┘

        7 analizadores independientes (multiprocessing.Process)
```

## Decisiones de diseño argumentadas

**Uso de `multiprocessing.Value` para la comunicación de intervalos:**
Para lograr que la TUI cambie dinámicamente la velocidad de refresco de cada vista, instancié un `Value('d')` por cada una. No utilicé un argumento estándar porque, tras realizar el fork, cada analizador opera en su propio espacio de memoria. Utilizar un segmento de memoria compartida real permite que el display escriba la nueva tasa de refresco y el analizador la lea de manera segura y atómica en cada iteración de su ciclo `while`.

**Consolidación del snapshot con `Manager.dict`:**
Se eligió un diccionario administrado por un Manager para centralizar la recolección de datos. Al tener una arquitectura con múltiples procesos escritores (los 7 analizadores) operando de forma asíncrona y un lector continuo (el Display), el `Manager.dict` maneja implícitamente los bloqueos de concurrencia (locks), evitando condiciones de carrera al leer y escribir el estado del sistema.

**Secuencia de Shutdown (`terminate` seguido de `join` en bucles separados):**
Ante la interrupción del programa, el apagado de los procesos hijos se realiza en dos etapas. Primero, un bucle ejecuta `.terminate()` sobre los 9 subprocesos (recolector, 7 analizadores y display). Luego, un segundo bucle independiente ejecuta `.join()` sobre cada uno. Si estas operaciones se hicieran juntas en un solo bucle, el programa esperaría la finalización de cada proceso de manera secuencial, demorando el apagado. Al hacerlo en dos bucles, la interrupción es paralela y la espera es limpia.

## Conceptos del curso aplicados

**Prevención de procesos Zombies (Clase 4):**
En el sistema operativo, un proceso zombie ocurre cuando un hijo termina su ejecución pero su padre no recolecta su estado de salida. La implementación estricta de `.join()` durante el shutdown garantiza que el proceso principal (padre) invoque la llamada al sistema `wait()`, limpiando la tabla de procesos del kernel y evitando fugas de recursos.

**Aislamiento de memoria e IPC (Clases 7 y 9):**
El diseño del programa aplica los conceptos teóricos del aislamiento de procesos. Como los analizadores son `Process` y no threads, no comparten el Global Interpreter Lock (GIL) ni el espacio de memoria por defecto. La utilización de `Manager` y `Value` es la aplicación práctica de la comunicación entre procesos (IPC) para sortear esta barrera arquitectónica.

**Inspección del Kernel vía Archivos (Clase 3):**
Todo el analizador se basa en el principio fundamental de UNIX/Linux de que "todo es un archivo". Se interactúa con las estructuras internas del kernel leyendo archivos virtuales en `/proc` (como `stat`, `status`, `fd`), interpretando sus descriptores y symlinks en tiempo real.

## Limitaciones conocidas (estado de desarrollo actual)

- **Manejo de señales:** Aún no se implementaron los handlers personalizados mediante el módulo `signal` (faltan `SIGINT`, `SIGTERM`, `SIGHUP`, `SIGUSR1` y `SIGUSR2`). El apagado actual se maneja capturando la excepción `KeyboardInterrupt`, que es el comportamiento por defecto de Python, en lugar de un handler seguro.

- **Cálculo de CPU%:** El monitor no calcula el porcentaje de CPU real de los procesos. `/proc/<pid>/stat` expone jiffies acumulados, por lo que es necesario implementar un delta temporal entre dos lecturas y cruzarlo con la constante `SC_CLK_TCK` del kernel.

- **Máscaras de señales:** Los valores de `SigPnd`, `SigBlk` y `SigIgn` se están extrayendo de `/proc/<pid>/status` pero se muestran en formato hexadecimal crudo. Falta decodificar los 64 bits para mostrar los nombres legibles de las señales.

- **Interactividad de la terminal:** La terminal opera en modo "cooked", requiriendo que el usuario presione Enter para que el programa registre las teclas. Falta aplicar `tty.setcbreak()` para poner la entrada en modo raw y lograr una respuesta instantánea de la TUI. Faltan implementar gran parte de los keybindings.

- **Profundidad de lectura en Memoria y FDs:** La vista de memoria lee campos básicos pero aún no abre `/proc/<pid>/maps` para desglosar el mapa completo. Por otro lado, las listas de Threads y File Descriptors están siendo truncadas a 5 elementos directamente en la etapa de análisis, lo que significa una pérdida de datos antes de llegar al Display. La vista del sistema global solo muestra memoria básica.

## Cómo correr y testear

El proyecto se encuentra dockerizado para asegurar su funcionamiento independientemente de la distribución del host, cumpliendo con el entorno `linux/amd64` requerido.

1. **Levantar el entorno interactivo:**

   ```bash
   docker compose up --build
   ```

2. **Uso de la interfaz (TUI):**

   - Utilice los números del `1` al `7` (seguidos de la tecla Enter momentáneamente, dada la limitación explicada) para alternar entre las diferentes vistas.
   - Utilice las teclas `+` y `-` (seguidas de Enter) para ajustar dinámicamente la velocidad de refresco (intervalo) de la vista que se encuentra activa en ese momento.

3. **Apagado:**

   Presione `Ctrl+C` para gatillar la secuencia de finalización limpia y observar cómo el proceso padre recolecta a los procesos hijos.

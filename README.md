# PFO3_PSRedes_SabrinaChoque_ComisionD

# Alumno: Sabrina Choque

# Comision: D

# GitHub: https://github.com/SabrinaChoque/PFO3_PSRedes_SabrinaChoque_ComisionD
# Descripcion del PFO3:
En este proyecto implementaremos un sistema distribuido donde múltiples clientes se comunican con un servidor mediante sockets TCP.  
El servidor distribuye las tareas a varios *workers* a través de una cola de mensajes (simulando RabbitMQ).  
Los resultados se almacenan en SQLite y archivos JSON (simulando S3).

# Diagrama del sistema distribuido:
El diagrama representa la arquitectura distribuida implementada en este proyecto, basada en el modelo **cliente-servidor** con procesamiento paralelo mediante *workers* y comunicación por colas de mensajes.

- **Clientes (CLI, Web o Móvil)**
Son los puntos de acceso donde se originan las tareas. En este trabajo se implementó un cliente de consola (CLI) que simula las peticiones desde distintos clientes, aunque en un entorno real podría reemplazarse por clientes web o móviles.

- **Balanceador (Nginx / HAProxy)**
 Representa el componente encargado de distribuir las conexiones entre varios servidores. En este proyecto su función se muestra en el diagrama como parte de la arquitectura, pero no se implementa de forma real, ya que el foco está en la comunicación por sockets.

- **Servidor / Socket**
Es el núcleo del sistema. Escucha las peticiones de los clientes mediante sockets TCP, recibe las tareas y las distribuye a través de una cola de mensajes a los *workers*. También gestiona las respuestas y las envía de nuevo al cliente.

- **Cola de mensajes (QueueBus)**
 Simula el funcionamiento de un sistema como RabbitMQ. Aquí se almacenan temporalmente las tareas que serán tomadas por los *workers*. Se implementó mediante la clase `queue.Queue()` de Python, lo que permite concurrencia segura entre hilos.

- **Workers**: Son los encargados de procesar las tareas en paralelo. Cada *worker* toma una tarea de la cola, ejecuta la operación correspondiente (por ejemplo: `uppercase`, `hash`, `echo`), guarda los resultados y notifica al servidor. Representan el pool de hilos o nodos de trabajo distribuidos.

- **Almacenamiento distribuido**: Se simulan dos tipos de almacenamiento:
  - **SQLite** (en `results.sqlite`): actúa como base de datos relacional local, simulando PostgreSQL.
  - **Archivos JSON (en carpeta `data/`)**: simulan un almacenamiento tipo S3 para guardar los resultados de forma estructurada.

Este diseño permite ilustrar el funcionamiento de un sistema distribuido real, donde los clientes se comunican con un servidor central que delega el trabajo a múltiples *workers*, logrando escalabilidad y procesamiento paralelo.

![Diagrama del sistema distribuido](diagrama_pfo3.png)

## server.py
El archivo `server.py` actúa como el **centro del sistema distribuido**.  
Se encarga de escuchar conexiones TCP desde los clientes, recibir tareas en formato JSON y distribuirlas entre varios *workers* (hilos) mediante una **cola de mensajes**.

### Funciones principales:
- **Recibir tareas:** escucha en el puerto 5001 y acepta conexiones.
- **Distribuir trabajo:** coloca cada tarea en la cola `task_queue` (simulando RabbitMQ).
- **Esperar respuesta:** usa una cola de respuesta para obtener el resultado del *worker*.
- **Responder al cliente:** devuelve el resultado en formato JSON.

### Ejemplo de funcionamiento:
1. El cliente envía una tarea como:
   ```json
   {"op": "uppercase", "data": "hola mundo"}

2. El servidor la encola para que un worker la procese.

3. Cuando el worker termina, el servidor responde al cliente con:

{"status": "ok", "worker": "worker-1", "result": "HOLA MUNDO"}

## worker.py
El archivo `worker.py` representa a los **nodos de trabajo** (workers) que procesan las tareas en paralelo.

Cada *worker* se ejecuta en un hilo independiente, escucha la **cola de tareas** y realiza la operación solicitada (por ejemplo `uppercase`, `hash` o `echo`).

### Funciones principales:
- **Tomar tareas de la cola:** el *worker* se mantiene en espera hasta que llega una nueva tarea.
- **Procesar la información:** según la operación indicada:
  - `uppercase` → convierte el texto a mayúsculas.  
  - `hash` → genera un código único (hash SHA256).  
  - `echo` → devuelve el mismo texto recibido (simula una respuesta directa).
- **Guardar los resultados:** registra cada resultado en la base de datos SQLite y en un archivo JSON (simulando almacenamiento distribuido tipo S3).
- **Enviar respuesta:** devuelve el resultado al servidor mediante una cola de respuesta.

### Resumen:
Los *workers* permiten que el sistema distribuya la carga de trabajo.  
Mientras el servidor atiende nuevas conexiones, los *workers* procesan las tareas en segundo plano, logrando **paralelismo y mejor rendimiento**.

## queue_bus.py
El archivo `queue_bus.py` implementa la **cola de mensajes** que conecta al servidor con los *workers*.  
Simula el comportamiento de un sistema como **RabbitMQ**, pero usando la librería estándar de Python.

### Función principal:
- Define una **cola global** llamada `task_queue` que almacena las tareas enviadas por los clientes.
- Permite que los *workers* tomen tareas disponibles una por una.
- Garantiza comunicación segura entre hilos gracias al módulo `queue`.

### Código base:
python:
from queue import Queue

#Cola global de tareas (simula RabbitMQ)
task_queue = Queue()

## storage.py
El archivo `storage.py` gestiona el **almacenamiento de resultados**.  
Simula dos tipos de almacenamiento distribuidos usados en entornos reales:

- **SQLite** → reemplaza a PostgreSQL (base de datos local relacional).  
- **Archivos JSON** → simulan un sistema de archivos distribuido tipo S3.

### Funciones principales:
- **init_sqlite()**: crea la base de datos `results.sqlite` y la tabla `results` si no existen.
- **save_result_sqlite()**: guarda en la base cada tarea procesada y su resultado.
- **save_result_s3like()**: genera un archivo JSON en la carpeta `data/` con la información de la tarea y su salida.

### Ejemplo:
Cuando un *worker* termina de procesar una tarea (por ejemplo `uppercase hola mundo`), se guardan dos registros:
- En `results.sqlite`: la tarea, el resultado y la hora.  
- En `data/result_<id>.json`: una copia del mismo resultado.

### Resumen:
De esta forma el sistema conserva trazabilidad de todas las tareas procesadas, simulando una base de datos distribuida (PostgreSQL) y almacenamiento externo (S3) sin depender de servicios externos.

## client.py
El archivo `client.py` representa al **cliente del sistema**, encargado de enviar tareas al servidor y mostrar los resultados.

### Funciones principales:
- **Conexión TCP:** se conecta al servidor (127.0.0.1:5001) mediante sockets.
- **Enviar solicitudes:** construye mensajes JSON con la operación (`op`) y los datos (`data`).
- **Recibir respuestas:** interpreta el resultado que el servidor devuelve en formato JSON.
- **Interfaz de usuario simple:** presenta un menú de comandos en la consola para probar el sistema.

### Comandos disponibles:
![Comandos Disponibles](comandos.png)

### Ejemplo de flujo:
1. El cliente envía → `{"op":"uppercase","data":"hola mundo"}`
2. El servidor procesa y devuelve → `{"status":"ok","worker":"worker-1","result":"HOLA MUNDO"}`
3. El cliente muestra el resultado en pantalla.

### Resumen:
`client.py` permite simular el rol de un usuario que interactúa con el sistema distribuido.  
Sirve para comprobar la comunicación completa: **Cliente → Servidor → Cola → Worker → Almacenamiento → Respuesta.**



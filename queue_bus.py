# Cola simple para pasar tareas a los workers
from queue import Queue

# Una cola para tareas (simula RabbitMQ)
task_queue = Queue()

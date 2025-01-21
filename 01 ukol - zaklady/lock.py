#LOCK
from threading import Thread, Lock
import time
import random

# Sdílený čítač
counter = 0
m = 10

# Vytvoření zámku
lock = Lock()

# Funkce, kterou každé vlákno provede
def increment_counter():
    global counter
    for _ in range(m):
        time.sleep(random.uniform(0.01, 0.05))  # Simulace práce mimo kritickou sekci
        with lock:  # Použití zámku k synchronizaci přístupu ke kritické sekci
            local_counter = counter
            time.sleep(random.uniform(0.01, 0.05))  # Simulace práce v kritické sekci
            local_counter += 1
            counter = local_counter

# Funkce pro vytvoření a spuštění vláken
def run_threads(n):
    threads = []
    for _ in range(n):
        thread = Thread(target=increment_counter)
        threads.append(thread)
        thread.start()

    # Počkáme na dokončení všech vláken
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    n = 10  # Počet vláken
    run_threads(n)

    print(f"Expected value: {m * n}")
    print(f"Real value: {counter}")

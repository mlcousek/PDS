import threading
import time
import random

# Počet vláken, které budou soutěžit o přístup ke sdílenému čítači
n = 5
counter = 0
m = 10 # Kolikrát se má každé vlákno inkrementovat

choosing = [False] * n  # Zda si vlákno vybírá lístek
ticket = [0] * n        # Čísla lístků pro každé vlákno

def get_max_ticket():
    return max(ticket)

def bakery_lock(thread_id):
    choosing[thread_id] = True
    ticket[thread_id] = get_max_ticket() + 1  # Každé vlákno si vezme lístek
    choosing[thread_id] = False

    for i in range(n):
        if i == thread_id:
            continue
        while choosing[i]:
            pass
        while ticket[i] != 0 and (ticket[i] < ticket[thread_id] or (ticket[i] == ticket[thread_id] and i < thread_id)):
            pass

def bakery_unlock(thread_id):
    ticket[thread_id] = 0  # Zneplatníme lístek

def lamp_bakery(thread_id):
    global counter

    for _ in range(m):
        bakery_lock(thread_id)  # Lamport bakery zámek
        # Kritická sekce
        local_counter = counter
        time.sleep(random.uniform(0.01, 0.05))  # Simulace práce
        local_counter += 1
        counter = local_counter
        bakery_unlock(thread_id)  # Uvolnění zámku

def run_threads(n):
    threads = []
    for i in range(n):
        thread = threading.Thread(target=lamp_bakery, args=(i,))
        threads.append(thread)
        thread.start()

    # Počkáme na dokončení všech vláken
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    run_threads(n)

    print(f"Expected value: {m * n}")
    print(f"Real value: {counter}")
